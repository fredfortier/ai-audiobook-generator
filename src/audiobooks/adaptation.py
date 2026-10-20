"""Bounded adaptation packets, reviewed acceptance, and ordered script export."""
from __future__ import annotations

import json
from difflib import SequenceMatcher
import re
import shutil
import uuid
from pathlib import Path
from typing import Literal

import typer
from pydantic import Field, model_validator

from audiobooks.files import read_json, write_atomic
from audiobooks.script_contract import Parameters, Record, Script, Speech, read_script, write_script
from audiobooks.source_units import Unit, admit, identity, partition, sections
from audiobooks.sentences import sentence_spans
from audiobooks.workspaces import work_path

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


class Choice(Record):
    trigger: str = Field(min_length=1)
    avoid: str = Field(min_length=1)
    parameters: Parameters


Action = Literal['CLARIFY', 'PROBE', 'CONVINCE', 'WARN', 'INVITE', 'EXALT', 'URGE', 'RESOLVE']

ACTION_MEANINGS: dict[Action, str] = {
    'CLARIFY': 'make a relation, premise, qualification, or example intelligible',
    'PROBE': 'recruit the listener into a genuinely unresolved question',
    'CONVINCE': 'seek acceptance or rejection through reasons, counterexample, or inference',
    'WARN': 'make an adverse consequence or moral danger matter',
    'INVITE': 'make the listener receptive to a possibility, image, or inward prospect',
    'EXALT': 'enlarge an earned vision, magnitude, wonder, or desire',
    'URGE': 'move the listener to undertake a commanded act',
    'RESOLVE': 'land and retain a concluding distinction or settled alternative',
}

ACTION_PARAMETERS: dict[Action, Parameters] = {
    'CLARIFY': Parameters(exaggeration=.55, cfg_weight=.40, temperature=.80,
                          repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'PROBE': Parameters(exaggeration=.78, cfg_weight=.30, temperature=.80,
                        repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'CONVINCE': Parameters(exaggeration=.84, cfg_weight=.30, temperature=.80,
                           repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'WARN': Parameters(exaggeration=.90, cfg_weight=.28, temperature=.80,
                       repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'INVITE': Parameters(exaggeration=.76, cfg_weight=.30, temperature=.80,
                         repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'EXALT': Parameters(exaggeration=1.00, cfg_weight=.26, temperature=.80,
                        repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'URGE': Parameters(exaggeration=.94, cfg_weight=.28, temperature=.80,
                       repetition_penalty=1.20, min_p=.05, top_p=1.00),
    'RESOLVE': Parameters(exaggeration=.72, cfg_weight=.34, temperature=.80,
                          repetition_penalty=1.20, min_p=.05, top_p=1.00),
}


def action_registry():
    return {action: {'meaning': ACTION_MEANINGS[action],
                     'parameters': ACTION_PARAMETERS[action].model_dump()}
            for action in ACTION_MEANINGS}


class ProductionCue(Record):
    id: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    avoid: str = Field(min_length=1)
    priority: int = 0
    unit_ids: list[str] = Field(min_length=1)


class DirectionContext(Record):
    addressee: str = Field(min_length=1)
    throughline: str = Field(min_length=1)
    stakes: str = Field(min_length=1)
    macro_trajectory: list[str] = Field(min_length=1)
    performance_limits: list[str] = Field(min_length=1)
    user_cues: list[ProductionCue] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_unique_cues(self):
        if len({cue.id for cue in self.user_cues}) != len(self.user_cues):
            raise ValueError('duplicate user cue IDs')
        return self


class Rule(Record):
    id: str
    unit_ids: list[str] = Field(min_length=1)
    evidence: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    disposition: Literal['narrated', 'excluded'] | None = None
    allow_digits: bool = False


class Brief(Record):
    brief_version: Literal[1, 2] = 1
    prepared_source_hash: str
    survey_unit_ids: list[str] = Field(min_length=1)
    narrator: str
    voices: dict[str, str]
    defaults: Parameters
    performance_choices: dict[str, Choice]
    section_baselines: dict[str, str | None]
    rules: list[Rule]
    pronunciation_watchlist: list[str]
    section_dependencies: dict[str, list[str]]
    unresolved_questions: list[str]
    direction: DirectionContext | None = None

    @model_validator(mode='after')
    def validate_complete_brief(self):
        if self.narrator not in self.voices:
            raise ValueError('narrator must have a binding')
        if self.direction is None:
            if (not self.performance_choices
                    or any(v not in self.performance_choices for v in self.section_baselines.values())):
                raise ValueError('undirected brief requires a baseline choice')
        elif self.performance_choices or any(v is not None for v in self.section_baselines.values()):
            raise ValueError('directed brief uses registered actions, not performance choices')
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError('duplicate rule IDs')
        if self.brief_version == 2 and self.direction is None:
            raise ValueError('version-two brief requires direction context')
        return self


class Edit(Record):
    before: str
    after: str
    reason: str = Field(min_length=1)


class Beat(Record):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    voice: str
    action: Action | None = None
    choice: str | None = None
    parameters: Parameters
    score_move_ids: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_control_identity(self):
        if (self.action is None) == (self.choice is None):
            raise ValueError('beat requires exactly one action or legacy choice')
        return self


class Disposition(Record):
    id: str
    disposition: Literal['narrated', 'excluded', 'unresolved']
    normalized_text: str | None = None
    edits: list[Edit] = Field(default_factory=list)
    beats: list[Beat] = Field(default_factory=list)
    reason: str | None = None
    applied_rule_ids: list[str] = Field(default_factory=list)


class Result(Record):
    result_version: Literal[1] = 1
    batch_id: str
    attempt_id: str
    prepared_hash: str
    plan_hash: str
    configuration_hash: str
    brief_hash: str
    acting_score_hash: str | None = None
    predecessor_hash: str
    units: list[Disposition]
    continuity: str
    issues: list[str]


class FragmentResult(Record):
    result: Result
    fragment_id: str
    fragment_plan_hash: str
    fragment_predecessor_hash: str
    source_start: int = Field(ge=0)
    source_end: int = Field(gt=0)


class Review(Record):
    result_hash: str
    reviewed_unit_ids: list[str]
    editorial_changes_checked: bool
    boundary_checked: bool
    fidelity_and_performance_checked: bool
    notes: str = Field(min_length=1)


class DirectorMove(Record):
    id: str = Field(min_length=1)
    unit_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    action: Action
    objective: str = Field(min_length=1)
    textual_evidence: str = Field(min_length=1)

    @model_validator(mode='after')
    def validate_listener_objective(self):
        prefix = f'{self.action} the listener to '
        if not (self.objective.startswith(prefix) and ' by ' in self.objective[len(prefix):]
                and self.objective.endswith('.')):
            raise ValueError('director move requires the registered listener objective form')
        return self


class ScoreDraft(Record):
    score_version: Literal[2] = 2
    task_id: str
    task_hash: str
    prepared_hash: str
    brief_hash: str
    configuration_hash: str
    direction_context_hash: str
    scope_section_ids: list[str] = Field(min_length=1)
    moves: list[DirectorMove] = Field(min_length=1)


class ScoreReview(Record):
    score_hash: str
    reviewed_move_ids: list[str] = Field(min_length=1)
    source_coverage_checked: bool
    direction_context_checked: bool
    action_and_objective_checked: bool
    continuity_checked: bool
    notes: str = Field(min_length=1)


class ActingScore(Record):
    score_version: Literal[2] = 2
    prepared_hash: str
    brief_hash: str
    configuration_hash: str
    direction_context_hash: str
    component_hashes: list[str] = Field(min_length=1)
    moves: list[DirectorMove] = Field(min_length=1)


@app.command()
def schema(kind: str):
    """Print the typed brief, result, fragment or review contract."""
    models = {'brief': Brief, 'result': Result, 'fragment': FragmentResult, 'review': Review,
              'score': ScoreDraft, 'score-review': ScoreReview, 'acting-score': ActingScore}
    if kind not in models:
        raise ValueError('unknown schema kind')
    typer.echo(json.dumps(models[kind].model_json_schema(), indent=2))


def brief_configuration(brief: Brief):
    configuration = {'voices': brief.voices, 'defaults': brief.defaults.model_dump()}
    if brief.direction is None:
        configuration['performance_choices'] = {
            name: choice.model_dump() for name, choice in brief.performance_choices.items()
        }
    else:
        configuration['action_registry'] = action_registry()
    return configuration


def load_workspace_state(root: Path):
    manifest, units = admit(root / 'prepared')
    plan = read_json(root / 'plan.json')
    brief = Brief.model_validate_json((root / 'text-brief.json').read_text())
    saved = read_json(root / 'manifest.json')
    if identity(manifest) != saved['prepared_hash'] or identity(plan) != saved['plan_hash']:
        raise ValueError('prepared bundle or plan changed; create an explicit revision')
    if identity(brief.model_dump()) != saved['brief_hash']:
        raise ValueError('brief changed; create an explicit revision')
    if identity(brief_configuration(brief)) != saved['configuration_hash']:
        raise ValueError('configuration changed')
    if manifest['prepared_text_version'] == 2:
        prepared_sections = [section.model_dump() for section in sections(root / 'prepared', manifest, units)]
        if identity(prepared_sections) != saved.get('prepared_sections_hash'):
            raise ValueError('prepared section contract changed')
    expected_plan = (partition(units, max_batch_pages=4, max_batch_words=2400)
                     if plan.get('plan_version') == 1 else partition(
                         units, max_batch_pages=plan.get('max_batch_pages', 0),
                         max_batch_words=plan.get('max_batch_words', 0)))
    if plan.get('plan_version') == 1:
        expected_plan = {**expected_plan, 'plan_version': 1}
        expected_plan.pop('max_batch_pages')
        expected_plan.pop('max_batch_words')
    if plan != expected_plan:
        raise ValueError('plan does not match prepared-unit partition')
    if 'reuse_hash' in saved and identity(read_json(root / 'reuse.json')) != saved['reuse_hash']:
        raise ValueError('revision reuse record changed')
    if saved.get('acting_score_hash'):
        score = ActingScore.model_validate_json((root / saved['acting_score_file']).read_text())
        if identity(score.model_dump()) != saved['acting_score_hash']:
            raise ValueError('accepted acting score changed')
        if (score.prepared_hash != saved['prepared_hash'] or score.brief_hash != saved['brief_hash']
                or score.configuration_hash != saved['configuration_hash']):
            raise ValueError('accepted acting score is stale')
        if brief.direction is None or score.direction_context_hash != identity(brief.direction.model_dump()):
            raise ValueError('accepted acting score direction context changed')
        check_score_moves(score.moves, score_units(units, brief), brief)
    return saved, units, plan, brief


def find_batch(plan, batch_id):
    matches = [b for b in plan['batches'] if b['id'] == batch_id]
    if len(matches) != 1:
        raise ValueError('unknown batch ID')
    return matches[0]


def load_accepted_batches(root, saved, plan):
    records = {}
    for batch in plan['batches']:
        path = root / 'work' / (batch['id'] + '.json')
        if not path.exists():
            continue
        record = read_json(path)
        result = Result.model_validate_json(json.dumps(record['result']))
        if any(getattr(result, k) != saved[k] for k in ('prepared_hash', 'plan_hash', 'configuration_hash', 'brief_hash')):
            raise ValueError('stale accepted work: ' + batch['id'])
        if record['result_hash'] != identity(record['result']):
            raise ValueError('changed accepted record: ' + batch['id'])
        review = Review.model_validate_json(json.dumps(record['review']))
        if review.result_hash != record['result_hash'] or not all((review.editorial_changes_checked, review.boundary_checked, review.fidelity_and_performance_checked)):
            raise ValueError('missing exact-result review: ' + batch['id'])
        if [u.id for u in result.units] != batch['unit_ids']:
            raise ValueError('accepted ownership differs from plan')
        records[batch['id']] = record
    return records


def preceding_batch_context(batch, plan, records):
    section = [b for b in plan['batches'] if b['section_id'] == batch['section_id']]
    position = section.index(batch)
    if position == 0:
        return 'section-start', ''
    previous = section[position - 1]['id']
    if previous not in records:
        raise ValueError('preceding batch is not accepted')
    record = records[previous]
    return record['result_hash'], record['result']['continuity']


def expected_disposition(unit: Unit, brief: Brief):
    dispositions = {rule.disposition for rule in brief.rules
                    if unit.id in rule.unit_ids and rule.disposition is not None}
    if len(dispositions) > 1:
        raise ValueError('conflicting disposition rules: ' + unit.id)
    return next(iter(dispositions), 'excluded' if unit.role == 'paratext'
                else 'narrated' if unit.role == 'body' else None)


def score_units(units: list[Unit], brief: Brief):
    selected = []
    for unit in units:
        disposition = expected_disposition(unit, brief)
        if disposition is None:
            raise ValueError('direction requires resolved source disposition: ' + unit.id)
        if disposition == 'narrated':
            selected.append(unit)
    return selected


def check_score_moves(moves: list[DirectorMove], owned: list[Unit], brief: Brief):
    if brief.direction is None:
        raise ValueError('acting score requires direction context')
    if len({move.id for move in moves}) != len(moves):
        raise ValueError('duplicate director move IDs')
    expected_unit_ids = [unit.id for unit in owned]
    actual_unit_ids = list(dict.fromkeys(move.unit_id for move in moves))
    if actual_unit_ids != expected_unit_ids:
        raise ValueError('director moves must cover owned units exactly in order')
    by_unit = {unit.id: unit for unit in owned}
    for unit_id in expected_unit_ids:
        unit = by_unit[unit_id]
        unit_moves = [move for move in moves if move.unit_id == unit_id]
        cursor = 0
        for move in unit_moves:
            if move.start != cursor or move.end <= move.start or move.end > len(unit.prepared_text):
                raise ValueError('director moves do not partition source text: ' + unit_id)
            evidence = ' '.join(move.textual_evidence.split())
            source = ' '.join(unit.prepared_text[move.start:move.end].split())
            if evidence not in source:
                raise ValueError('textual evidence is outside its move: ' + move.id)
            cursor = move.end
        if cursor != len(unit.prepared_text):
            raise ValueError('incomplete director coverage: ' + unit_id)
    return moves


def accepted_direction_records(root: Path, saved, units, brief):
    records = []
    work = root / 'direction' / 'work'
    if not work.exists():
        return records
    for path in sorted(work.glob('*.json')):
        record = read_json(path)
        score = ScoreDraft.model_validate_json(json.dumps(record['score']))
        review = ScoreReview.model_validate_json(json.dumps(record['review']))
        digest = identity(score.model_dump())
        if record['score_hash'] != digest or review.score_hash != digest:
            raise ValueError('changed accepted direction record: ' + path.stem)
        if any(getattr(score, key) != saved[key] for key in
               ('prepared_hash', 'brief_hash', 'configuration_hash')):
            raise ValueError('stale accepted direction record: ' + path.stem)
        if brief.direction is None or score.direction_context_hash != identity(brief.direction.model_dump()):
            raise ValueError('stale direction context: ' + path.stem)
        owned = [unit for unit in score_units(units, brief) if unit.section_id in score.scope_section_ids]
        check_score_moves(score.moves, owned, brief)
        records.append(record)
    return records


def accepted_acting_score(root: Path, saved, units, brief):
    if not saved.get('acting_score_hash'):
        return None
    score = ActingScore.model_validate_json((root / saved['acting_score_file']).read_text())
    check_score_moves(score.moves, score_units(units, brief), brief)
    return score


def retained_note_call(unit: Unit, normalized: str) -> bool:
    """Check indexed source positions, not identical characters elsewhere."""
    if not unit.note_call_spans:
        return False
    without_calls = unit.prepared_text
    for start, end in reversed(unit.note_call_spans):
        without_calls = without_calls[:start] + without_calls[end:]
    canonical = '\n'.join(' '.join(line.split()) for line in without_calls.split('\n'))
    if normalized == canonical:
        return False
    # Exact call removal above handles adjacent identical letters unambiguously.
    # Other speech normalizations can move offsets; align retained source text.
    blocks = SequenceMatcher(a=unit.prepared_text, b=normalized,
                             autojunk=False).get_matching_blocks()
    # Indexed calls may include layout whitespace or reference punctuation.
    # After another normalization, alignment can assign a surviving sentence
    # period to a deleted reference's period. Require call content, rather
    # than common punctuation; symbolic footnote markers remain content.
    return any(unit.prepared_text[max(block.a, start):min(block.a + block.size, end)]
               .strip(' \t\r\n[](){}.,:;–—-')
               for block in blocks for start, end in unit.note_call_spans
               if block.a < end and start < block.a + block.size)


def check_disposition(item: Disposition, unit: Unit, brief: Brief,
                      score_moves: list[DirectorMove] | None = None):
    rules = [r for r in brief.rules if item.id in r.unit_ids]
    rule_ids = {r.id for r in rules}
    if set(item.applied_rule_ids) - rule_ids:
        raise ValueError('unscoped rule: ' + item.id)
    dispositions = {r.disposition for r in rules if r.disposition is not None}
    if len(dispositions) > 1:
        raise ValueError('conflicting disposition rules')
    expected = next(iter(dispositions), 'excluded' if unit.role == 'paratext' else 'narrated' if unit.role == 'body' else None)
    if item.disposition == 'unresolved' or expected is None or item.disposition != expected:
        raise ValueError('unresolved or incorrect disposition: ' + item.id)
    if item.disposition == 'excluded':
        if not item.reason or item.normalized_text is not None or item.beats or item.edits:
            raise ValueError('exclusion needs a reason and no speech')
        if score_moves:
            raise ValueError('excluded unit cannot have director moves')
        return
    text = item.normalized_text
    if not text or text != '\n'.join(' '.join(line.split()) for line in text.split('\n')):
        raise ValueError('missing or noncanonical normalized text')
    if text != unit.prepared_text and not item.edits:
        raise ValueError('changed text needs edit reasons')
    if re.search(r'\d', text) and not any(r.allow_digits and r.id in item.applied_rule_ids for r in rules):
        raise ValueError('unexpanded digit without scoped exception')
    if retained_note_call(unit, text):
        raise ValueError('retained citation call')
    cursor = 0
    for beat in item.beats:
        if beat.start != cursor or beat.end <= beat.start or beat.end > len(text):
            raise ValueError('beat spans do not form an exact partition')
        if not text[beat.start:beat.end].strip():
            raise ValueError('empty beat')
        if beat.voice not in brief.voices:
            raise ValueError('unknown voice')
        if score_moves is None:
            if beat.action is not None or beat.choice not in brief.performance_choices:
                raise ValueError('undirected beat requires a known legacy choice')
            if beat.parameters != brief.performance_choices[beat.choice].parameters:
                raise ValueError('parameters differ from approved legacy choice')
        else:
            if beat.choice is not None or beat.action is None:
                raise ValueError('directed beat requires one registered action')
            if beat.parameters != ACTION_PARAMETERS[beat.action]:
                raise ValueError('parameters differ from registered action vector')
        cursor = beat.end
    if cursor != len(text):
        raise ValueError('incomplete beat coverage')
    if unit.kind == 'heading' and len(item.beats) != 1:
        raise ValueError('heading must be spoken once in one beat')
    if score_moves is not None:
        if not score_moves:
            raise ValueError('narrated unit lacks director moves')
        expected_ids = [move.id for move in score_moves]
        known = {move.id: move for move in score_moves}
        mapped = []
        for beat in item.beats:
            if not beat.score_move_ids or any(move_id not in known for move_id in beat.score_move_ids):
                raise ValueError('beat lacks accepted score lineage')
            if any(known[move_id].action != beat.action for move_id in beat.score_move_ids):
                raise ValueError('beat action differs from its director move')
            for move_id in beat.score_move_ids:
                if not mapped or mapped[-1] != move_id:
                    mapped.append(move_id)
        if mapped != expected_ids:
            raise ValueError('beats omit or reorder director moves')


def validate_result(root: Path, draft: Path, stored_result: Result | None = None):
    saved, units, plan, brief = load_workspace_state(root)
    result = stored_result or Result.model_validate_json(draft.read_text())
    batch = find_batch(plan, result.batch_id)
    task_path = root / 'tasks' / result.batch_id / (result.attempt_id + '.json')
    packet = read_json(task_path)
    if packet['draft_path'] != str(draft.resolve()):
        raise ValueError('draft path differs from assigned output')
    if packet['batch_id'] != result.batch_id or packet['attempt_id'] != result.attempt_id:
        raise ValueError('task identity differs from result')
    if [unit['id'] for unit in packet['owned_units']] != batch['unit_ids']:
        raise ValueError('packet ownership differs from frozen plan')
    for key in ('prepared_hash', 'plan_hash', 'configuration_hash', 'brief_hash'):
        if getattr(result, key) != saved[key] or packet[key] != saved[key]:
            raise ValueError('stale task/result ' + key)
    score = accepted_acting_score(root, saved, units, brief)
    expected_score_hash = saved.get('acting_score_hash')
    if result.acting_score_hash != expected_score_hash or packet.get('acting_score_hash') != expected_score_hash:
        raise ValueError('stale or missing acting score identity')
    records = load_accepted_batches(root, saved, plan)
    pred, _ = preceding_batch_context(batch, plan, records)
    if result.predecessor_hash != pred or packet['predecessor_hash'] != pred:
        raise ValueError('stale continuity')
    active = root / 'tasks' / result.batch_id / 'active.json'
    if stored_result is None and result.batch_id not in records:
        if not active.exists() or read_json(active)['attempt_id'] != result.attempt_id:
            raise ValueError('attempt is no longer active')
    if [u.id for u in result.units] != batch['unit_ids']:
        raise ValueError('result must cover exactly the ordered owned units')
    if result.issues or len(result.continuity.split()) > 300:
        raise ValueError('unresolved issues or oversized continuity')
    by_id = {u.id: u for u in units}
    fixed = read_json(root / 'reuse.json')['units'] if (root / 'reuse.json').exists() else {}
    score_by_unit = ({unit_id: [move for move in score.moves if move.unit_id == unit_id]
                      for unit_id in batch['unit_ids']} if score else {})
    for item in result.units:
        unit = by_id[item.id]
        if item.id in fixed and item.model_dump() != fixed[item.id]['result']:
            raise ValueError('unchanged reviewed unit was reinterpreted: ' + item.id)
        check_disposition(item, unit, brief, score_by_unit.get(item.id) if score else None)
    if packet.get('fragments'):
        if identity(packet['fragments']) != packet['fragment_plan_hash']:
            raise ValueError('changed fragment boundary plan')
        snapshots = read_json(root / 'work' / (result.batch_id + '.json'))['fragment_results'] if stored_result is not None else None
        expected, _ = assembled_fragments(root, packet, brief, snapshots)
        if expected != result:
            raise ValueError('paragraph draft differs from verified fragment chain')
    return result, saved, units, plan, brief, packet


@app.command()
def init(prepared: Path, brief_path: Path, workspace: Path):
    """Freeze an admitted bundle, surveyed brief and deterministic plan."""
    workspace = work_path(workspace)
    if workspace.exists():
        raise ValueError('workspace exists; use status to resume')
    manifest, units = admit(prepared, required_version=2)
    prepared_sections = [section.model_dump() for section in sections(prepared, manifest, units)]
    brief = Brief.model_validate_json(brief_path.read_text())
    prepared_hash = identity(manifest)
    if brief.prepared_source_hash != prepared_hash or brief.unresolved_questions:
        raise ValueError('stale brief or unresolved survey')
    ids = {u.id for u in units}
    if set(brief.survey_unit_ids) - ids or any(set(r.unit_ids) - ids for r in brief.rules):
        raise ValueError('brief refers to unknown units')
    if brief.direction is not None and any(set(cue.unit_ids) - ids for cue in brief.direction.user_cues):
        raise ValueError('direction cue refers to unknown units')
    if set(brief.section_baselines) != set(manifest['section_ids']):
        raise ValueError('every source section needs a baseline')
    dependencies = brief.section_dependencies
    if set(dependencies) != set(manifest['section_ids']) or any(set(v) - set(dependencies) for v in dependencies.values()):
        raise ValueError('invalid section dependencies')
    def visit(section, trail):
        if section in trail:
            raise ValueError('cyclic section dependencies')
        for dependency in dependencies[section]:
            visit(dependency, trail | {section})
    for section in dependencies:
        visit(section, set())
    plan = partition(units)
    workspace.mkdir(parents=True)
    shutil.copytree(prepared, workspace / 'prepared')
    write_atomic(workspace / 'text-brief.json', brief.model_dump())
    write_atomic(workspace / 'plan.json', plan)
    write_atomic(workspace / 'manifest.json', {'adapt_text_version': 2, 'prepared_hash': prepared_hash,
           'prepared_sections_hash': identity(prepared_sections),
           'plan_hash': identity(plan), 'brief_hash': identity(brief.model_dump()),
           'configuration_hash': identity(brief_configuration(brief)), 'title': manifest['title'],
           'author': manifest.get('author'),
           'script_files': [], 'scope': manifest['scope'], **brief_configuration(brief)})
    typer.echo(f'{len(units)} units; {len(plan["pages"])} pages; {len(plan["batches"])} batches')


@app.command('direction-task')
def direction_task(workspace: Path, section_ids: str | None = typer.Option(None, '--sections')):
    """Freeze a whole-short-work or complete-section packet for a semantic director."""
    workspace = work_path(workspace)
    saved, units, plan, brief = load_workspace_state(workspace)
    if brief.direction is None:
        raise ValueError('text brief has no direction context')
    if saved.get('acting_score_hash'):
        raise ValueError('acting score already accepted')
    narratable = score_units(units, brief)
    all_sections = list(dict.fromkeys(unit.section_id for unit in narratable))
    accepted_records = accepted_direction_records(workspace, saved, units, brief)
    accepted_sections = {section for record in accepted_records for section in record['score']['scope_section_ids']}
    active_paths = list((workspace / 'direction' / 'tasks').glob('*.active.json'))
    active_sections = {section for path in active_paths
                       for section in read_json(path)['scope_section_ids']}
    if section_ids is None:
        pending = [section for section in all_sections if section not in accepted_sections | active_sections]
        pending_words = sum(len(unit.prepared_text.split()) for unit in narratable if unit.section_id in pending)
        if pending_words > 6000:
            raise ValueError('long work requires explicit complete section IDs')
        selected = pending
    else:
        selected = [value.strip() for value in section_ids.split(',') if value.strip()]
    if not selected or len(set(selected)) != len(selected) or any(section not in all_sections for section in selected):
        raise ValueError('direction task needs unique narratable section IDs')
    if selected != [section for section in all_sections if section in selected]:
        raise ValueError('direction sections must follow source order')
    if set(selected) & (accepted_sections | active_sections):
        raise ValueError('direction section is accepted or already active')
    for section in selected:
        missing = set(brief.section_dependencies[section]) - accepted_sections - set(selected)
        if missing:
            raise ValueError('direction dependencies are not accepted: ' + ', '.join(sorted(missing)))
    owned = [unit for unit in narratable if unit.section_id in selected]
    task_id = 'd' + uuid.uuid4().hex[:12]
    draft = (workspace / 'direction' / 'drafts' / (task_id + '.json')).resolve()
    core = {'packet_version': 1, 'task_id': task_id,
            **{key: saved[key] for key in ('prepared_hash', 'brief_hash', 'configuration_hash')},
            'direction_context_hash': identity(brief.direction.model_dump()),
            'scope_section_ids': selected, 'owned_units': [unit.model_dump() for unit in owned],
            'direction': brief.direction.model_dump(),
            'action_meanings': ACTION_MEANINGS,
            'reference_paths': [str((Path(__file__).resolve().parents[2] / 'skills' / 'adapt-text' /
                                     'references' / 'acting-direction.md').resolve())],
            'score_schema': ScoreDraft.model_json_schema(), 'draft_path': str(draft)}
    packet = {**core, 'task_hash': identity(core)}
    path = workspace / 'direction' / 'tasks' / (task_id + '.json')
    write_atomic(path, packet)
    write_atomic(path.with_suffix('.active.json'), {'task_id': task_id, 'packet_path': str(path.resolve()),
                                              'scope_section_ids': selected})
    draft.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(str(path.resolve()))


def validate_score_draft(workspace: Path, draft: Path):
    saved, units, plan, brief = load_workspace_state(workspace)
    score = ScoreDraft.model_validate_json(draft.read_text())
    task_path = workspace / 'direction' / 'tasks' / (score.task_id + '.json')
    packet = read_json(task_path)
    active = task_path.with_suffix('.active.json')
    if not active.exists() or read_json(active)['task_id'] != score.task_id:
        raise ValueError('direction attempt is no longer active')
    if packet['draft_path'] != str(draft.resolve()) or packet['task_hash'] != score.task_hash:
        raise ValueError('score differs from its assigned task')
    for key in ('prepared_hash', 'brief_hash', 'configuration_hash'):
        if getattr(score, key) != saved[key] or packet[key] != saved[key]:
            raise ValueError('stale score ' + key)
    direction_hash = identity(brief.direction.model_dump()) if brief.direction else None
    if score.direction_context_hash != direction_hash or packet['direction_context_hash'] != direction_hash:
        raise ValueError('stale direction context')
    if score.scope_section_ids != packet['scope_section_ids']:
        raise ValueError('score scope differs from task')
    owned = [unit for unit in score_units(units, brief) if unit.section_id in score.scope_section_ids]
    if owned != [Unit.model_validate_json(json.dumps(item)) for item in packet['owned_units']]:
        raise ValueError('score task ownership changed')
    check_score_moves(score.moves, owned, brief)
    return score, saved, units, brief, packet


@app.command('validate-score')
def validate_score(workspace: Path, draft: Path):
    workspace = work_path(workspace)
    score, *_ = validate_score_draft(workspace, draft)
    typer.echo(f'{score.task_id}: {len(score.moves)} director moves structurally valid; semantic review required')


@app.command('accept-score')
def accept_score(workspace: Path, draft: Path, review_path: Path):
    """Accept reviewed direction and freeze the global score once coverage is complete."""
    workspace = work_path(workspace)
    score, saved, units, brief, packet = validate_score_draft(workspace, draft)
    review = ScoreReview.model_validate_json(review_path.read_text())
    digest = identity(score.model_dump())
    checks = (review.source_coverage_checked, review.direction_context_checked,
              review.action_and_objective_checked, review.continuity_checked)
    if review.score_hash != digest or not all(checks):
        raise ValueError('score review does not attest this exact draft')
    move_ids = {move.id for move in score.moves}
    if set(review.reviewed_move_ids) != move_ids:
        raise ValueError('every director move in the task requires semantic review')
    target = workspace / 'direction' / 'work' / (score.task_id + '.json')
    if target.exists():
        raise ValueError('accepted direction cannot be overwritten')
    write_atomic(target, {'score': score.model_dump(), 'score_hash': digest,
                          'review': review.model_dump()})
    (workspace / 'direction' / 'tasks' / (score.task_id + '.active.json')).unlink()
    records = accepted_direction_records(workspace, saved, units, brief)
    expected = score_units(units, brief)
    moves = [DirectorMove.model_validate(move) for record in records for move in record['score']['moves']]
    if {move.unit_id for move in moves} == {unit.id for unit in expected}:
        order = {unit.id: position for position, unit in enumerate(expected)}
        moves.sort(key=lambda move: (order[move.unit_id], move.start))
        check_score_moves(moves, expected, brief)
        global_score = ActingScore(prepared_hash=saved['prepared_hash'], brief_hash=saved['brief_hash'],
                                   configuration_hash=saved['configuration_hash'],
                                   direction_context_hash=identity(brief.direction.model_dump()),
                                   component_hashes=[record['score_hash'] for record in records], moves=moves)
        path = workspace / 'acting-score.json'
        write_atomic(path, global_score.model_dump())
        current = read_json(workspace / 'manifest.json')
        write_atomic(workspace / 'manifest.json', {**current, 'acting_score_file': 'acting-score.json',
                                             'acting_score_hash': identity(global_score.model_dump())})
        typer.echo(f'accepted {score.task_id}; complete acting score frozen with {len(moves)} moves')
    else:
        typer.echo(f'accepted {score.task_id}; additional direction sections remain')


@app.command('abandon-direction')
def abandon_direction(workspace: Path, task_id: str, reason: str):
    """Retire a stopped direction attempt so its complete sections can be reassigned."""
    workspace = work_path(workspace)
    active = workspace / 'direction' / 'tasks' / (task_id + '.active.json')
    value = read_json(active)
    write_atomic(active.with_suffix('.abandoned.json'), {**value, 'reason': reason})
    active.unlink()


@app.command('migrate-brief')
def migrate_brief(version_one: Path, version_two: Path, brief_path: Path, output: Path):
    """Rebind a surveyed brief when section migration leaves every source unit unchanged."""
    if output.exists():
        raise ValueError('new brief path required')
    old_manifest, old_units = admit(version_one, required_version=1)
    new_manifest, new_units = admit(version_two, required_version=2)
    brief = Brief.model_validate_json(brief_path.read_text())
    if brief.prepared_source_hash != identity(old_manifest):
        raise ValueError('brief is not bound to the supplied version-one bundle')
    if old_units != new_units:
        raise ValueError('section-only brief migration requires identical prepared units')
    migrated = brief.model_copy(update={'prepared_source_hash': identity(new_manifest)})
    write_atomic(output, migrated.model_dump())
    typer.echo(f'brief rebound to version two; {len(new_units)} unchanged surveyed units')


def unit_contract(unit: Unit, brief: Brief):
    """The interpretation inputs capable of changing one unit's accepted result."""
    return {'unit': unit.model_dump(), 'narrator': brief.narrator,
            'configuration': brief_configuration(brief),
            'baseline': brief.section_baselines[unit.section_id],
            'rules': [r.model_dump() for r in brief.rules if unit.id in r.unit_ids],
            'pronunciation_watchlist': brief.pronunciation_watchlist,
            'dependencies': brief.section_dependencies[unit.section_id]}


@app.command()
def revise(workspace: Path, prepared: Path, brief_path: Path, revised_workspace: Path):
    """Freeze an explicit revision and reuse only unchanged reviewed unit contracts."""
    workspace = work_path(workspace)
    revised_workspace = work_path(revised_workspace)
    old_saved, old_units, old_plan, old_brief = load_workspace_state(workspace)
    records = load_accepted_batches(workspace, old_saved, old_plan)
    _, new_units = admit(prepared)
    new_brief = Brief.model_validate_json(brief_path.read_text())
    init(prepared, brief_path, revised_workspace)
    old_by_id = {u.id: u for u in old_units}
    new_by_id = {u.id: u for u in new_units}
    same = {u.id for u in new_units if u.id in old_by_id
            and unit_contract(u, new_brief) == unit_contract(old_by_id[u.id], old_brief)}
    old_order = [u.id for u in old_units]
    new_order = [u.id for u in new_units]
    def neighbors(order, key):
        position = order.index(key)
        return order[max(0, position - 1):position] + order[position + 1:position + 2]
    unchanged = {key for key in same if neighbors(old_order, key) == neighbors(new_order, key)
                 and all(neighbor in same for neighbor in neighbors(new_order, key))}
    changed_sections = {u.section_id for u in new_units if u.id not in same}
    dependency_changed = set(changed_sections)
    while True:
        expanded = dependency_changed | {section for section, deps in new_brief.section_dependencies.items()
                                         if set(deps) & dependency_changed}
        if expanded == dependency_changed:
            break
        dependency_changed = expanded
    dependent_sections = dependency_changed - changed_sections
    unchanged -= {u.id for u in new_units if u.section_id in dependent_sections}
    reused = {}
    for batch_id, record in records.items():
        for raw in record['result']['units']:
            if raw['id'] in unchanged:
                reused[raw['id']] = {'result': raw, 'review': record['review'],
                                     'origin_result_hash': record['result_hash']}
    reuse = {'reuse_version': 1, 'previous_prepared_hash': old_saved['prepared_hash'], 'units': reused}
    write_atomic(revised_workspace / 'reuse.json', reuse)
    saved = read_json(revised_workspace / 'manifest.json')
    write_atomic(revised_workspace / 'manifest.json', {**saved, 'reuse_hash': identity(reuse)})
    typer.echo(f'{len(reused)} unchanged reviewed units frozen for reuse; remaining units need adaptation')


@app.command()
def task(workspace: Path, batch_id: str, fragment_boundaries: Path | None = typer.Option(None),
         owned_word_budget: int = typer.Option(6000, min=1)):
    """Create one bounded worker packet; refuse accepted or already active work."""
    workspace = work_path(workspace)
    saved, units, plan, brief = load_workspace_state(workspace)
    score = accepted_acting_score(workspace, saved, units, brief)
    if brief.direction is not None and score is None:
        raise ValueError('accept complete acting direction before adapter dispatch')
    batch = find_batch(plan, batch_id)
    records = load_accepted_batches(workspace, saved, plan)
    if batch_id in records:
        raise ValueError('batch already accepted')
    active = workspace / 'tasks' / batch_id / 'active.json'
    if active.exists():
        raise ValueError('active attempt exists; inspect its packet or abandon explicitly')
    for dependency in brief.section_dependencies[batch['section_id']]:
        if any(b['id'] not in records for b in plan['batches'] if b['section_id'] == dependency):
            raise ValueError('dependent section is incomplete')
    pred, continuity = preceding_batch_context(batch, plan, records)
    owned = [u for u in units if u.id in batch['unit_ids']]
    fragments = []
    if fragment_boundaries is not None:
        if len(owned) != 1 or owned[0].kind not in ('paragraph', 'list_item'):
            raise ValueError('fragment boundaries require one nonheading source unit')
        boundaries = read_json(fragment_boundaries)
        text = owned[0].prepared_text
        sentence_starts = {start for start, end in sentence_spans(text)}
        if (not isinstance(boundaries, list) or len(boundaries) < 3
                or any(type(value) is not int for value in boundaries)
                or boundaries[0] != 0 or boundaries[-1] != len(text)
                or any(a >= b for a, b in zip(boundaries, boundaries[1:]))):
            raise ValueError('boundaries must partition the original Unicode characters exactly')
        for position, (a, b) in enumerate(zip(boundaries, boundaries[1:]), 1):
            part = text[a:b]
            if not part.strip() or len(part.split()) > owned_word_budget:
                raise ValueError('fragment is empty or exceeds owned-word budget')
            if b < len(text) and b not in sentence_starts:
                raise ValueError('fragment boundary must be a verified English sentence start')
            if any(start < b < end or start < a < end for start, end in owned[0].note_call_spans):
                raise ValueError('fragment boundary splits a citation call')
            fragments.append({'id': f'f{position:06d}', 'start': a, 'end': b})
    elif any(len(u.prepared_text.split()) > owned_word_budget for u in owned):
        raise ValueError('oversized unit requires verified fragments and a sequential contract before dispatch')
    start = units.index(owned[0])
    stop = units.index(owned[-1])
    context = []
    for neighbor in ([units[start - 1]] if start else []) + ([units[stop + 1]] if stop + 1 < len(units) else []):
        words = neighbor.prepared_text.split()
        context.append({'id': neighbor.id, 'context_only': True, 'text': ' '.join(words[:400]), 'truncated': len(words) > 400})
    attempt = uuid.uuid4().hex
    draft = (workspace / 'drafts' / batch_id / (attempt + '.json')).resolve()
    draft.parent.mkdir(parents=True, exist_ok=True)
    packet = {'packet_version': 1, 'batch_id': batch_id, 'attempt_id': attempt, 'owned_word_budget': owned_word_budget,
              **{k: saved[k] for k in ('prepared_hash', 'plan_hash', 'brief_hash', 'configuration_hash')},
              'acting_score_hash': saved.get('acting_score_hash'),
              'section_id': batch['section_id'], 'pages': [p for p in plan['pages'] if p['id'] in batch['page_ids']],
              'owned_units': [u.model_dump() for u in owned], 'context_only': context,
              'predecessor_hash': pred, 'continuity': continuity, 'narrator': brief.narrator,
              **brief_configuration(brief),
              **({'baseline': brief.section_baselines[batch['section_id']]}
                 if brief.direction is None else {}),
              'rules': [r.model_dump() for r in brief.rules if set(r.unit_ids) & set(batch['unit_ids'])],
              'fixed_results': {key: value['result'] for key, value in
                                (read_json(workspace / 'reuse.json')['units'].items()
                                 if (workspace / 'reuse.json').exists() else [])
                                if key in batch['unit_ids']},
              'pronunciation_watchlist': brief.pronunciation_watchlist,
              'reference_paths': [str((Path(__file__).resolve().parents[2] / 'skills' / 'adapt-text' / 'references' / name).resolve()) for name in
                                  ('worker-procedure.md', 'source-and-normalization.md', 'acting-direction.md')],
              'result_schema': Result.model_json_schema(), 'draft_path': str(draft)}
    if score is not None:
        packet['acting_score_moves'] = [move.model_dump() for move in score.moves if move.unit_id in batch['unit_ids']]
    if fragments:
        packet['fragments'] = fragments
        packet['fragment_plan_hash'] = identity(fragments)
    path = workspace / 'tasks' / batch_id / (attempt + '.json')
    write_atomic(path, packet)
    write_atomic(active, {'attempt_id': attempt, 'packet_path': str(path.resolve())})
    typer.echo(str(path.resolve()))


def active_packet(workspace: Path, batch_id: str):
    saved, units, plan, brief = load_workspace_state(workspace)
    active = read_json(workspace / 'tasks' / batch_id / 'active.json')
    packet = read_json(Path(active['packet_path']))
    if packet['attempt_id'] != active['attempt_id'] or any(packet[key] != saved[key] for key in
             ('prepared_hash', 'plan_hash', 'brief_hash', 'configuration_hash')):
        raise ValueError('stale fragment coordinator')
    if not packet.get('fragments') or identity(packet['fragments']) != packet['fragment_plan_hash']:
        raise ValueError('missing or changed fragment plan')
    return packet, brief


def fragment_unit(packet, fragment):
    original = Unit.model_validate_json(json.dumps(packet['owned_units'][0]))
    part = original.prepared_text[fragment['start']:fragment['end']]
    shift = fragment['start'] + len(part) - len(part.lstrip())
    spans = [(a - shift, b - shift) for a, b in original.note_call_spans
             if fragment['start'] <= a < b <= fragment['end']]
    return original.model_copy(update={'prepared_text': part.strip(), 'source_text': part.strip(),
                                        'note_call_spans': spans})


def fragment_paths(workspace, packet, fragment_id):
    stem = workspace / 'tasks' / packet['batch_id'] / packet['attempt_id'] / fragment_id
    return stem.with_suffix('.json'), (workspace / 'drafts' / packet['batch_id'] /
                                     packet['attempt_id'] / (fragment_id + '.json')).resolve()


def checked_fragment(workspace, packet, brief, position, previous_hash, stored_result=None):
    fragment = packet['fragments'][position]
    path, draft = fragment_paths(workspace, packet, fragment['id'])
    child = read_json(path)
    result = stored_result or FragmentResult.model_validate_json(draft.read_text())
    for key in ('batch_id', 'attempt_id', 'prepared_hash', 'plan_hash', 'configuration_hash',
                'brief_hash', 'acting_score_hash', 'predecessor_hash'):
        if getattr(result.result, key) != packet[key] or child[key] != packet[key]:
            raise ValueError('fragment identity changed: ' + key)
    if (result.fragment_plan_hash != packet['fragment_plan_hash'] or child['fragment_plan_hash'] != packet['fragment_plan_hash']
            or result.fragment_id != fragment['id'] or result.source_start != fragment['start']
            or result.source_end != fragment['end'] or result.fragment_predecessor_hash != previous_hash
            or child['fragment_predecessor_hash'] != previous_hash):
        raise ValueError('fragment coverage or continuity differs')
    unit = fragment_unit(packet, fragment)
    inner = result.result
    if len(inner.units) != 1 or inner.units[0].id != unit.id or inner.issues or len(inner.continuity.split()) > 300:
        raise ValueError('fragment has extra ownership or unresolved issues')
    check_disposition(inner.units[0], unit, brief)
    return result


@app.command()
def fragment_task(workspace: Path, batch_id: str, fragment_id: str):
    """Emit the next bounded packet after verifying preceding fragment continuity."""
    workspace = work_path(workspace)
    packet, brief = active_packet(workspace, batch_id)
    ids = [fragment['id'] for fragment in packet['fragments']]
    if fragment_id not in ids:
        raise ValueError('unknown fragment')
    position = ids.index(fragment_id)
    previous_hash = 'fragment-start'
    continuity = packet['continuity']
    for preceding in range(position):
        previous = checked_fragment(workspace, packet, brief, preceding, previous_hash)
        previous_hash = identity(previous.model_dump())
        continuity = previous.result.continuity
    fragment = packet['fragments'][position]
    unit = fragment_unit(packet, fragment)
    path, draft = fragment_paths(workspace, packet, fragment_id)
    original_text = packet['owned_units'][0]['prepared_text']
    context = []
    for label, text in [('previous-fragment', original_text[:fragment['start']]),
                        ('next-fragment', original_text[fragment['end']:])]:
        words = text.split()
        if words:
            context.append({'id': label, 'context_only': True,
                            'text': ' '.join(words[-400:] if label == 'previous-fragment' else words[:400]),
                            'truncated': len(words) > 400})
    child = {**{k: v for k, v in packet.items() if k not in ('fragments', 'owned_units', 'pages', 'fixed_results')},
             'fragment_id': fragment_id, 'source_start': fragment['start'], 'source_end': fragment['end'],
             'fragment_predecessor_hash': previous_hash, 'continuity': continuity,
             'owned_units': [unit.model_dump()], 'context_only': context,
             'pages': [{'id': packet['pages'][0]['id'], 'unit_ids': [unit.id]}],
             'result_schema': FragmentResult.model_json_schema(), 'draft_path': str(draft)}
    if packet.get('acting_score_moves'):
        child['acting_score_moves'] = [
            {**move, 'source_start': max(move['start'], fragment['start']),
             'source_end': min(move['end'], fragment['end']),
             'fragment_start': max(move['start'], fragment['start']) - fragment['start'],
             'fragment_end': min(move['end'], fragment['end']) - fragment['start']}
            for move in packet['acting_score_moves']
            if move['start'] < fragment['end'] and move['end'] > fragment['start']]
    if path.exists() and read_json(path) != child:
        raise ValueError('existing fragment packet differs; repair preceding result explicitly')
    write_atomic(path, child)
    draft.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(str(path.resolve()))


def assembled_fragments(workspace, packet, brief, stored_fragments=None):
    results = []
    previous_hash = 'fragment-start'
    for position in range(len(packet['fragments'])):
        stored = FragmentResult.model_validate_json(json.dumps(stored_fragments[position])) if stored_fragments is not None else None
        result = checked_fragment(workspace, packet, brief, position, previous_hash, stored_result=stored)
        results.append(result)
        previous_hash = identity(result.model_dump())
    items = [result.result.units[0] for result in results]
    if len({item.disposition for item in items}) != 1:
        raise ValueError('fragments disagree on paragraph disposition')
    first = items[0]
    edits = [edit for item in items for edit in item.edits]
    rules = list(dict.fromkeys(rule for item in items for rule in item.applied_rule_ids))
    if first.disposition == 'narrated':
        parts = []
        beats = []
        offset = 0
        for item in items:
            if parts:
                parts.append(' ')
                offset += 1
                beats[-1].end += 1
            parts.append(item.normalized_text)
            beats.extend(beat.model_copy(update={'start': beat.start + offset, 'end': beat.end + offset}) for beat in item.beats)
            offset += len(item.normalized_text)
        combined = Disposition(id=first.id, disposition='narrated', normalized_text=''.join(parts),
                               edits=edits, beats=beats, applied_rule_ids=rules)
    else:
        combined = Disposition(
            id=first.id,
            disposition='excluded',
            reason='; '.join(dict.fromkeys(item.reason for item in items)),
            applied_rule_ids=rules,
        )
    result = Result(**{key: packet[key] for key in ('batch_id', 'attempt_id', 'prepared_hash', 'plan_hash',
                      'configuration_hash', 'brief_hash', 'acting_score_hash', 'predecessor_hash')},
                    units=[combined], continuity=results[-1].result.continuity, issues=[])
    return result, [fragment.model_dump() for fragment in results]


@app.command()
def combine_fragments(workspace: Path, batch_id: str):
    """Assemble a complete sequential fragment chain into one paragraph draft."""
    workspace = work_path(workspace)
    packet, brief = active_packet(workspace, batch_id)
    result, _ = assembled_fragments(workspace, packet, brief)
    draft = Path(packet['draft_path'])
    write_atomic(draft, result.model_dump())
    validate_result(workspace, draft)
    typer.echo(str(draft))


@app.command()
def abandon(workspace: Path, batch_id: str, reason: str):
    """Retire an attempt after checking that its worker has stopped."""
    workspace = work_path(workspace)
    active = workspace / 'tasks' / batch_id / 'active.json'
    value = read_json(active)
    write_atomic(active.with_name(value['attempt_id'] + '.abandoned.json'),
                 {**value, 'reason': reason})
    active.unlink()


@app.command()
def validate(workspace: Path, draft: Path):
    workspace = work_path(workspace)
    result, *_ = validate_result(workspace, draft)
    typer.echo(f'{result.batch_id}: {len(result.units)} owned units valid; editorial review still required')


@app.command()
def accept(workspace: Path, draft: Path, review_path: Path):
    """Commit a valid draft only with the main agent's source review record."""
    workspace = work_path(workspace)
    result, saved, units, plan, brief, packet = validate_result(workspace, draft)
    review = Review.model_validate_json(review_path.read_text())
    active = workspace / 'tasks' / result.batch_id / 'active.json'
    digest = identity(result.model_dump())
    if review.result_hash != digest or not all((review.editorial_changes_checked, review.boundary_checked, review.fidelity_and_performance_checked)):
        raise ValueError('review does not attest this exact result')
    required = {u.id for u in result.units if u.edits or u.disposition == 'excluded'}
    section_batches = [b for b in plan['batches'] if b['section_id'] == packet['section_id']]
    if section_batches[0]['id'] == result.batch_id:
        required.update(u.id for u in result.units)
    owned = {u.id for u in result.units}
    if set(review.reviewed_unit_ids) - owned or not required <= set(review.reviewed_unit_ids):
        raise ValueError('pilot, exclusions and editorial changes must be reviewed')
    target = workspace / 'work' / (result.batch_id + '.json')
    if target.exists():
        if read_json(target)['result_hash'] != digest:
            raise ValueError('accepted batch cannot be overwritten')
    else:
        if not active.exists() or read_json(active)['attempt_id'] != result.attempt_id:
            raise ValueError('attempt is no longer active')
        fragment_results = assembled_fragments(workspace, packet, brief)[1] if packet.get('fragments') else []
        write_atomic(target, {'result': result.model_dump(), 'result_hash': digest, 'review': review.model_dump(),
                        'fragment_results': fragment_results})
    active.unlink(missing_ok=True)
    typer.echo(f'accepted {result.batch_id}')


@app.command()
def status(workspace: Path):
    workspace = work_path(workspace)
    saved, units, plan, brief = load_workspace_state(workspace)
    records = load_accepted_batches(workspace, saved, plan)
    cursors = {}
    for section in brief.section_baselines:
        cursor = None
        for batch in [b for b in plan['batches'] if b['section_id'] == section]:
            if batch['id'] not in records:
                cursor = batch['id']
                break
        cursors[section] = cursor
    typer.echo(json.dumps({'accepted_batches': list(records), 'section_next_batch': cursors,
                           'complete': len(records) == len(plan['batches'])}, indent=2))


@app.command()
def export(workspace: Path):
    """Compile complete accepted coverage in source order and verify round trips."""
    workspace = work_path(workspace)
    saved, units, plan, brief = load_workspace_state(workspace)
    records = load_accepted_batches(workspace, saved, plan)
    if len(records) != len(plan['batches']):
        raise ValueError('source coverage incomplete')
    indexed = {u.id: u for u in units}
    speeches = {}
    coverage = []
    count = 0
    for batch in plan['batches']:
        result = Result.model_validate_json(json.dumps(records[batch['id']]['result']))
        # Revalidate the original packet/result at export; reviews cannot bypass coverage.
        draft = Path(read_json(workspace / 'tasks' / batch['id'] /
                               (result.attempt_id + '.json'))['draft_path'])
        validate_result(workspace, draft, stored_result=result)
        for item in result.units:
            unit = indexed[item.id]
            coverage.append({'unit_id': item.id, 'disposition': item.disposition, 'reason': item.reason})
            if item.disposition != 'narrated':
                continue
            for beat in item.beats:
                count += 1
                text = item.normalized_text[beat.start:beat.end].strip()
                speech = Speech(id=f's{count:06d}', voice=beat.voice, parameters=beat.parameters,
                                paragraphs=[text], heading_level=unit.heading_level)
                speeches.setdefault(unit.section_id, []).append(speech)
                coverage[-1].setdefault('speech_spans', []).append(
                    {'speech_id': speech.id, 'start': beat.start, 'end': beat.end,
                     'score_move_ids': beat.score_move_ids,
                     **({'action': beat.action} if beat.action else {'choice': beat.choice}),
                     'proposed_parameters': beat.parameters.model_dump()})
    files = []
    script_by_section = {}
    for n, section in enumerate((section for section in dict.fromkeys(u.section_id for u in units) if section in speeches), 1):
        script = Script(title=saved['title'], voices=brief.voices, defaults=brief.defaults, speech=speeches[section])
        markdown = write_script(script)
        if read_script(markdown) != script:
            raise ValueError('codec round trip changed accepted speech')
        name = f'script/{n:04d}.md'
        write_atomic(workspace / name, markdown)
        files.append(name)
        script_by_section[section] = name
    prepared_manifest = json.loads((workspace / 'prepared' / 'manifest.json').read_text())
    prepared_sections = sections(workspace / 'prepared', prepared_manifest, units)
    coverage_by_unit = {item['unit_id']: item for item in coverage}
    speech_by_id = {speech.id: speech for values in speeches.values() for speech in values}
    exported_sections = []
    for section in prepared_sections:
        record = section.model_dump()
        if section.section_id in script_by_section:
            record['script_file'] = script_by_section[section.section_id]
        if section.delivery_chapter:
            if section.start_unit_id != section.title_unit_id:
                raise ValueError('delivery chapter must start at its title unit: ' + section.section_id)
            spans = coverage_by_unit[section.title_unit_id].get('speech_spans', [])
            if len(spans) != 1:
                raise ValueError('delivery title must normalize to exactly one speech record: ' + section.section_id)
            speech = speech_by_id[spans[0]['speech_id']]
            if speech.heading_level is None or len(speech.paragraphs) != 1:
                raise ValueError('delivery title speech must remain a heading: ' + section.section_id)
            record.update({'title_speech_id': speech.id, 'normalized_title': speech.paragraphs[0]})
        exported_sections.append(record)
    write_atomic(workspace / 'coverage.json', coverage)
    write_atomic(workspace / 'sections.json', exported_sections)
    write_atomic(workspace / 'manifest.json', {**saved, 'script_files': files, 'coverage_hash': identity(coverage),
                                       'section_file': 'sections.json',
                                       'sections_hash': identity(exported_sections),
                                       'complete': True, 'audio_quality_verified': False})
    typer.echo(f'{len(files)} scripts; {count} speech blocks; {len(coverage)} source dispositions')


if __name__ == '__main__':
    app()

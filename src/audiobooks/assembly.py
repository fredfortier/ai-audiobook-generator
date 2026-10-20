"""Lossless ordered assembly with explicit reviewed gaps and realized navigation."""
from pathlib import Path
import json
import re
from typing import Literal

import typer
from pydantic import Field

from audiobooks.files import write_atomic
from audiobooks.rendering import audio_properties, load_plan, verified_segment
from audiobooks.script_contract import Record
from audiobooks.source_units import identity, sha256
from audiobooks.workspaces import work_path


class Gap(Record):
    after_segment_id: str
    frames: int = Field(ge=0)
    reason: str = Field(min_length=1)


class ChapterTitleReview(Record):
    section_id: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    title: str = Field(min_length=1)
    coherence: str = Field(min_length=1)
    plausibility: str = Field(min_length=1)


class ChapterTitleReviewSet(Record):
    style: Literal['English title case']
    chapters: list[ChapterTitleReview] = Field(min_length=1)


_minor_title_words = {
    'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'nor', 'of',
    'on', 'or', 'per', 'the', 'to', 'via', 'with',
}


def _is_title_case(title: str) -> bool:
    """Accept reviewed English title case without damaging acronyms or mixed-case names."""
    words = title.split()
    if not words or title != ' '.join(words) or title.isupper():
        return False
    for index, token in enumerate(words):
        letters = ''.join(character for character in token if character.isalpha())
        if not letters:
            continue
        sentence_start = index == 0 or words[index - 1].endswith(('.', '?', '!'))
        if not sentence_start and index != len(words) - 1 and letters.casefold() in _minor_title_words:
            if letters != letters.casefold():
                return False
            continue
        if letters.isupper() or any(character.isupper() for character in letters[1:]):
            continue
        if letters[0].isupper():
            continue
        return False
    return True


def reviewed_chapter_titles(plan: dict, path: Path) -> dict[str, ChapterTitleReview]:
    review = ChapterTitleReviewSet.model_validate_json(path.read_text())
    planned = plan.get('delivery_sections', [])
    expected = [chapter['section_id'] for chapter in planned]
    actual = [chapter.section_id for chapter in review.chapters]
    if actual != expected or len(set(actual)) != len(actual):
        raise ValueError('chapter-title review must cover delivery sections exactly in order')
    result = {}
    for source, approved in zip(planned, review.chapters, strict=True):
        if not approved.coherence.strip() or not approved.plausibility.strip():
            raise ValueError('chapter-title review requires contextual evidence')
        if approved.source_title != source['title']:
            raise ValueError('chapter-title review source differs from the frozen render plan')
        comparable_source = re.sub(r'\s+', ' ', approved.source_title).strip().casefold()
        comparable_title = re.sub(r'\s+', ' ', approved.title).strip().casefold()
        if comparable_title != comparable_source:
            raise ValueError('chapter display title must preserve the source title wording')
        if not _is_title_case(approved.title):
            raise ValueError('chapter display title must use consistent English title case')
        result[approved.section_id] = approved
    return result


def escape_metadata(text):
    return ''.join('\\' + char if char in '\\\n=;#' else char for char in text)


def assemble(workspace: Path, output: Path, gaps: Path, chapter_titles: Path,
             container: str = 'WAV'):
    """Assemble every verified request; write FLOAT PCM and FFmetadata chapters."""
    import numpy as np
    import soundfile as sf

    workspace = work_path(workspace)
    output = work_path(output)
    gaps = work_path(gaps)
    chapter_titles = work_path(chapter_titles)
    if output.exists() or container not in ('WAV', 'RF64'):
        raise ValueError('new output directory and WAV or RF64 container required')
    plan = load_plan(workspace)
    title_reviews = reviewed_chapter_titles(plan, chapter_titles)
    records = [verified_segment(workspace, plan, segment) for segment in plan['segments']]
    if not records or any(record is None for record in records):
        raise ValueError('verified audio required for every planned segment')
    declared = [Gap.model_validate(item) for item in json.loads(gaps.read_text())]
    by_id = {gap.after_segment_id: gap for gap in declared}
    allowed = {segment['id'] for segment in plan['segments'][:-1]}
    if (len(by_id) != len(declared) or not set(by_id) <= allowed
            or any(not gap.reason.strip() for gap in declared)):
        raise ValueError('unique known nonterminal gap positions and scoped reasons required')
    rate = records[0]['properties']['sample_rate']
    channels = records[0]['properties']['channels']
    if any((r['properties']['sample_rate'], r['properties']['channels']) != (rate, channels)
           for r in records):
        raise ValueError('native audio rates and channels must agree')
    output.mkdir(parents=True)
    path = output / 'assembly.wav'
    positions = []
    chapters = []
    chapter_by_segment = {chapter['start_segment_id']: chapter
                          for chapter in plan.get('delivery_sections', [])}
    if len(chapter_by_segment) != len(plan.get('delivery_sections', [])):
        raise ValueError('delivery section starts must be unique')
    with sf.SoundFile(path, 'w', samplerate=rate, channels=channels,
                      format=container, subtype='FLOAT') as destination:
        for segment, record in zip(plan['segments'], records):
            source = workspace / 'audio' / (segment['id'] + '.wav')
            if verified_segment(workspace, plan, segment) != record:
                raise ValueError('source audio changed during assembly')
            start = destination.tell()
            audio, _ = sf.read(source, dtype='float32', always_2d=True)
            destination.write(audio)
            end = destination.tell()
            if segment['id'] in chapter_by_segment:
                chapter = chapter_by_segment[segment['id']]
                approved = title_reviews[chapter['section_id']]
                chapters.append({'section_id': chapter['section_id'],
                                 'source_title': chapter['title'],
                                 'title': approved.title, 'start': start})
            gap_frames = by_id[segment['id']].frames if segment['id'] in by_id else 0
            remaining = gap_frames
            while remaining:
                block = min(remaining, 65536)
                destination.write(np.zeros((block, channels), dtype='float32'))
                remaining -= block
            positions.append({'segment_id': segment['id'], 'audio_hash': record['audio_hash'],
                              'start': start, 'end': end, 'gap_frames': gap_frames})
        frames = destination.tell()
    with sf.SoundFile(path) as assembled:
        for position in positions:
            source = workspace / 'audio' / (position['segment_id'] + '.wav')
            audio, _ = sf.read(source, dtype='float32', always_2d=True)
            if sha256(source) != position['audio_hash'] or not np.array_equal(
                    assembled.read(len(audio), dtype='float32', always_2d=True), audio):
                raise ValueError('assembled samples differ from verified source')
            remaining = position['gap_frames']
            while remaining:
                block = min(remaining, 65536)
                silence = assembled.read(block, dtype='float32', always_2d=True)
                if len(silence) != block or silence.any():
                    raise ValueError('declared assembly gap differs')
                remaining -= block
        if assembled.tell() != assembled.frames or assembled.frames != frames:
            raise ValueError('assembly frame count differs')
    if load_plan(workspace) != plan:
        raise ValueError('generation plan changed during assembly')
    if not chapters or chapters[0]['start'] != 0 or len(chapters) != len(chapter_by_segment):
        raise ValueError('explicit delivery chapters must cover audio from the first frame')
    metadata = [';FFMETADATA1', 'title=' + escape_metadata(plan['title'])]
    if plan.get('author'):
        metadata.append('artist=' + escape_metadata(plan['author']))
    for number, chapter in enumerate(chapters):
        chapter['end'] = chapters[number + 1]['start'] if number + 1 < len(chapters) else frames
        metadata.extend(['[CHAPTER]', f'TIMEBASE=1/{rate}', f"START={chapter['start']}",
                         f"END={chapter['end']}", 'title=' + escape_metadata(chapter['title'])])
    metadata_path = output / 'chapters.ffmetadata'
    metadata_path.write_text('\n'.join(metadata) + '\n')
    write_atomic(output / 'assembly.json', {'plan_hash': identity(plan), 'assembly_runtime_hash': sha256(Path(__file__)),
           'gaps_hash': sha256(gaps), 'gaps': [gap.model_dump() for gap in declared],
           'chapter_titles_hash': sha256(chapter_titles),
           'chapter_title_style': 'English title case',
           'chapter_title_reviews': [item.model_dump() for item in title_reviews.values()],
           'book_metadata': {'title': plan['title'], 'author': plan.get('author')},
           'metadata_hash': sha256(metadata_path),
           'audio_hash': sha256(path), 'properties': audio_properties(path),
           'exact_samples_preserved': True, 'segments': positions, 'chapters': chapters,
           'audio_quality_verified': False})
    typer.echo(f'{len(positions)} ordered segments; {frames / rate:.2f}s lossless assembly; quality unreviewed')


if __name__ == '__main__':
    typer.run(assemble)

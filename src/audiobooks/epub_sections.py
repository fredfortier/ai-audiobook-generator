"""Conservative EPUB section reconciliation and selection.

Standard navigation is authoritative when it is usable.  Structural recovery is
deliberately narrow: semantic sectioning, or a sectioning element with an
authored accessible heading.  Generic headings and filename patterns are kept
as evidence but are never promoted by themselves.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from ebooklib import epub
from lxml import etree
from pydantic import Field

from audiobooks.epub_structure import EpubInventory, NavigationNode, NavigationSource
from audiobooks.script_contract import Record

SourceKind = Literal["epub3-nav", "epub2-ncx", "content-structure", "calibre-candidate", "manual"]


class SelectionEvidence(Record):
    source_kind: SourceKind
    source_location: str
    raw_value: str | None
    resolved_value: str | None
    decision: str
    reason: str


class SectionBoundary(Record):
    section_id: str
    ordinal: int = Field(ge=1)
    parent_section_id: str | None
    source: SourceKind
    source_node_id: str
    resource_href: str
    fragment: str | None
    spine_ordinal: int = Field(ge=1)
    dom_ordinal: int = Field(ge=0)
    level: int = Field(ge=1)
    raw_title: str
    title: str
    title_origin: Literal["content-heading", "navigation-label-projection", "accessible-name"]
    title_path: list[str]
    content_label: str | None
    delivery_chapter: bool
    evidence: list[SelectionEvidence] = Field(min_length=1)
    issues: list[str]


class SectionSelection(Record):
    primary_source: Literal["epub3-nav", "epub2-ncx", "content-structure"] | None
    status: Literal["ready", "blocked"]
    boundaries: list[SectionBoundary]
    issues: list[str]


class StructuralCandidate(Record):
    id: str
    resource_href: str
    spine_ordinal: int = Field(ge=1)
    dom_ordinal: int = Field(ge=0)
    source_location: str
    fragment: str | None
    level: int = Field(ge=1)
    title: str | None
    title_location: str | None
    semantic_role: str | None
    signals: list[str]
    selected: bool
    rejection_reason: str | None


class CalibreCandidate(Record):
    resource_href: str
    fragment: str | None
    title: str
    source_location: str


_whitespace_pattern = re.compile(r"\s+")
_nonword_pattern = re.compile(r"[^\w]+", re.UNICODE)
_section_roles = {"chapter", "part", "prologue", "epilogue"}
_paratext_labels = {"cover", "contents", "table of contents"}


def _local_name(value: object) -> str:
    return str(value).rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def comparable_label(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    return _whitespace_pattern.sub(" ", _nonword_pattern.sub(" ", normalized)).strip()


def _navigation_nodes(inventory: EpubInventory, source: NavigationSource) -> list[NavigationNode]:
    return [node for node in inventory.navigation if node.source == source]


def _target_nodes(inventory: EpubInventory, source: NavigationSource) -> list[NavigationNode]:
    return [
        node
        for node in _navigation_nodes(inventory, source)
        if node.raw_target is not None and node.linear is True
    ]


def _navigation_title_path(node: NavigationNode, all_nodes: list[NavigationNode]) -> list[str]:
    by_id = {item.id: item for item in all_nodes}
    values: list[str] = []
    current: NavigationNode | None = node
    seen: set[str] = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        if current.raw_label.strip():
            values.append(current.raw_label.strip())
        current = by_id.get(current.parent_id) if current.parent_id else None
    return list(reversed(values))


def _target_key(node: NavigationNode) -> tuple[str | None, str | None]:
    return node.resource_href, node.fragment


def _benign_extras(nodes: list[NavigationNode]) -> bool:
    return all(
        node.linear is False or comparable_label(node.raw_label) in _paratext_labels
        for node in nodes
    )


def _compare_sources(primary: list[NavigationNode], secondary: list[NavigationNode]) -> list[str]:
    """Return material disagreements; known paratext-only extras are benign."""
    if not primary or not secondary:
        return []
    primary_by_key = {_target_key(node): node for node in primary}
    secondary_by_key = {_target_key(node): node for node in secondary}
    common = [key for key in primary_by_key if key in secondary_by_key]
    issues: list[str] = []
    primary_common = [key for key in map(_target_key, primary) if key in secondary_by_key]
    secondary_common = [key for key in map(_target_key, secondary) if key in primary_by_key]
    if primary_common != secondary_common:
        issues.append("NAV/NCX target order materially disagrees")
    for key in common:
        left, right = primary_by_key[key], secondary_by_key[key]
        if comparable_label(left.raw_label) != comparable_label(right.raw_label):
            issues.append(f"NAV/NCX labels materially disagree at {key[0]}#{key[1] or ''}")
        if left.level != right.level:
            issues.append(f"NAV/NCX hierarchy materially disagrees at {key[0]}#{key[1] or ''}")
    primary_extra = [node for node in primary if _target_key(node) not in secondary_by_key]
    secondary_extra = [node for node in secondary if _target_key(node) not in primary_by_key]
    if primary_extra and not _benign_extras(primary_extra):
        issues.append("primary navigation contains distinct plausible boundaries")
    if secondary_extra and not _benign_extras(secondary_extra):
        issues.append("secondary navigation contains distinct plausible boundaries")
    return list(dict.fromkeys(issues))


def _select_primary_navigation(
    inventory: EpubInventory,
) -> tuple[NavigationSource | None, list[NavigationNode], list[NavigationNode]]:
    nav = _target_nodes(inventory, "epub3-nav")
    ncx = _target_nodes(inventory, "epub2-ncx")
    try:
        major = int((inventory.package_version or "0").split(".", 1)[0])
    except ValueError:
        major = 0
    # Resource-present broken fragments remain selectable evidence: the later
    # resolver permits one unambiguous resource-start degradation and blocks a
    # many-to-one collapse.
    nav_resolvable = any(node.resource_exists for node in nav)
    ncx_resolvable = any(node.resource_exists for node in ncx)
    if major >= 3 and nav and nav_resolvable:
        return "epub3-nav", nav, ncx
    if ncx and ncx_resolvable:
        return "epub2-ncx", ncx, nav
    if nav and nav_resolvable:
        return "epub3-nav", nav, ncx
    return None, [], nav + ncx


def _resolve_navigation_positions(
    nodes: list[NavigationNode],
) -> tuple[list[str], dict[str, int]]:
    issues: list[str] = []
    missing = Counter(
        node.resource_href
        for node in nodes
        if node.resource_exists and node.fragment is not None and node.fragment_exists is False
    )
    fallback_positions: dict[str, int] = {}
    for node in nodes:
        if not node.resource_exists:
            issues.append(f"missing navigation resource: {node.raw_target}")
        elif node.fragment is not None and node.fragment_exists is False:
            if missing[node.resource_href] == 1:
                fallback_positions[node.id] = 0
            else:
                issues.append(
                    f"multiple unresolved fragments would collapse in {node.resource_href}"
                )
        elif node.dom_ordinal is None:
            issues.append(f"navigation target has no DOM position: {node.raw_target}")
    return list(dict.fromkeys(issues)), fallback_positions


def _coalesce_stacked_boundaries(
    nodes: list[NavigationNode], fallback_positions: dict[str, int]
) -> tuple[list[NavigationNode], dict[str, list[NavigationNode]], list[str]]:
    groups: dict[tuple[int | None, int | None], list[NavigationNode]] = {}
    for node in nodes:
        groups.setdefault(
            (node.spine_ordinal, fallback_positions.get(node.id, node.dom_ordinal)), []
        ).append(node)
    selected: list[NavigationNode] = []
    stacks: dict[str, list[NavigationNode]] = {}
    issues: list[str] = []
    for group in groups.values():
        if len(group) == 1:
            selected.append(group[0])
            continue
        by_id = {node.id: node for node in group}
        deepest = max(group, key=lambda node: node.level)
        current = deepest
        chain = {deepest.id}
        while current.parent_id in by_id:
            current = by_id[current.parent_id]
            chain.add(current.id)
        if len(chain) != len(group):
            issues.append("unrelated navigation boundaries occupy one DOM position")
            selected.extend(group)
            continue
        selected.append(deepest)
        stacks[deepest.id] = group
    selected.sort(
        key=lambda node: (
            node.spine_ordinal or 0,
            fallback_positions.get(node.id, node.dom_ordinal or 0),
        )
    )
    return selected, stacks, issues


def _element_text(node: etree._Element | None) -> str | None:
    if node is None:
        return None
    value = _whitespace_pattern.sub(" ", "".join(node.itertext())).strip()
    return value or None


def structural_candidates(path: Path, inventory: EpubInventory) -> list[StructuralCandidate]:
    """Inventory fallback evidence without promoting generic headings."""
    book = epub.read_epub(path)
    by_href = {item.file_name: item for item in book.get_items()}
    candidates: list[StructuralCandidate] = []
    for spine_item in inventory.spine:
        if not spine_item.linear:
            continue
        item = by_href.get(spine_item.href)
        if item is None:
            continue
        root = etree.fromstring(
            item.get_content(),
            parser=etree.XMLParser(recover=True, resolve_entities=False, no_network=True),
        )
        elements = [node for node in root.iter() if isinstance(node.tag, str)]
        for dom_ordinal, node in enumerate(elements):
            tag = _local_name(node.tag).lower()
            type_value = " ".join(
                value for key, value in node.attrib.items() if _local_name(key) == "type"
            )
            roles = {
                part.casefold().removeprefix("doc-")
                for part in (type_value + " " + (node.get("role") or "")).split()
            }
            semantic = next((role for role in _section_roles if role in roles), None)
            heading = (
                node
                if tag in {f"h{n}" for n in range(1, 7)}
                else next(
                    (
                        child
                        for child in node.iterdescendants()
                        if _local_name(child.tag).lower() in {f"h{n}" for n in range(1, 7)}
                    ),
                    None,
                )
            )
            title = _element_text(heading) or (node.get("aria-label") or node.get("title"))
            title = title.strip() if title else None
            signals: list[str] = []
            if semantic:
                signals.append(f"epub-semantic:{semantic}")
            if tag in {"section", "article"}:
                signals.append("sectioning-element")
            if heading is not None:
                signals.append("authored-heading")
            convention = " ".join(filter(None, [node.get("id"), node.get("class")]))
            if any(token in convention.casefold() for token in _section_roles):
                signals.append("stable-id-or-class")
            if tag in {f"h{n}" for n in range(1, 7)} and not semantic:
                signals.append("generic-heading")
            page_type = (
                "pagebreak" in roles or (node.get("role") or "").casefold() == "doc-pagebreak"
            )
            relevant = bool(signals) or page_type
            if not relevant:
                continue
            selected = bool(
                title
                and not page_type
                and (
                    semantic or ("sectioning-element" in signals and "authored-heading" in signals)
                )
            )
            reason = (
                None
                if selected
                else (
                    "page-break markers are not section boundaries"
                    if page_type
                    else "candidate lacks semantic or corroborated sectioning evidence"
                )
            )
            candidates.append(
                StructuralCandidate(
                    id=f"candidate-{len(candidates)+1:06d}",
                    resource_href=spine_item.href,
                    spine_ordinal=spine_item.ordinal,
                    dom_ordinal=dom_ordinal,
                    source_location=f"{spine_item.href}{root.getroottree().getpath(node)}",
                    fragment=node.get("id"),
                    level=int(_local_name(heading.tag)[1]) if heading is not None else 1,
                    title=title,
                    title_location=(
                        f"{spine_item.href}{root.getroottree().getpath(heading)}"
                        if heading is not None
                        else None
                    ),
                    semantic_role=semantic,
                    signals=signals,
                    selected=selected,
                    rejection_reason=reason,
                )
            )
    return candidates


def _boundary_from_node(
    node: NavigationNode,
    all_nodes: list[NavigationNode],
    ordinal: int,
    fallback_positions: dict[str, int],
) -> SectionBoundary:
    label = node.raw_label.strip()
    content = node.content_label.strip() if node.content_label else None
    if content:
        title, origin = content, "content-heading"
    else:
        title, origin = label, "navigation-label-projection"
    evidence = [
        SelectionEvidence(
            source_kind=node.source,
            source_location=node.source_location,
            raw_value=node.raw_target,
            resolved_value=node.resolved_location,
            decision="selected",
            reason="primary standard navigation boundary",
        )
    ]
    if node.id in fallback_positions:
        evidence.append(
            SelectionEvidence(
                source_kind=node.source,
                source_location=node.source_location,
                raw_value=node.fragment,
                resolved_value=node.resource_href,
                decision="degraded-to-resource-start",
                reason="only unresolved boundary in the resource",
            )
        )
    return SectionBoundary(
        section_id=f"sec-{ordinal:04d}",
        ordinal=ordinal,
        parent_section_id=None,
        source=node.source,
        source_node_id=node.id,
        resource_href=node.resource_href or "",
        fragment=node.fragment,
        spine_ordinal=node.spine_ordinal or 0,
        dom_ordinal=fallback_positions.get(node.id, node.dom_ordinal or 0),
        level=node.level,
        raw_title=label,
        title=title,
        title_origin=origin,
        title_path=_navigation_title_path(node, all_nodes),
        content_label=content,
        delivery_chapter=True,
        evidence=evidence,
        issues=[],
    )


def select_sections(
    inventory: EpubInventory,
    *,
    epub_path: Path | None = None,
    calibre_candidates: list[CalibreCandidate] | None = None,
) -> SectionSelection:
    """Select monotonic, evidenced boundaries or return an actionable blocked plan."""
    primary_name, primary, secondary = _select_primary_navigation(inventory)
    issues: list[str] = []
    candidate_cache: list[StructuralCandidate] | None = None
    if primary and len(primary) <= 1 and epub_path is not None:
        candidate_cache = structural_candidates(epub_path, inventory)
        if sum(candidate.selected for candidate in candidate_cache) > len(primary):
            primary_name, primary = None, []
    if primary:
        issues.extend(_compare_sources(primary, secondary))
        resolution_issues, fallback_positions = _resolve_navigation_positions(primary)
        issues.extend(resolution_issues)
        usable = [
            node
            for node in primary
            if node.resource_exists
            and (
                node.fragment is None
                or node.fragment_exists is True
                or node.id in fallback_positions
            )
        ]
        raw_ordered = sorted(
            usable,
            key=lambda node: (
                node.spine_ordinal or 0,
                fallback_positions.get(node.id, node.dom_ordinal or 0),
            ),
        )
        if [node.id for node in usable] != [node.id for node in raw_ordered]:
            issues.append("selected navigation boundaries are not monotonic in reading order")
        ordered, stacks, stack_issues = _coalesce_stacked_boundaries(
            raw_ordered, fallback_positions
        )
        issues.extend(stack_issues)
        for node in ordered:
            if not node.raw_label.strip():
                issues.append(f"selected boundary has no authored label: {node.source_location}")
            if node.content_label and comparable_label(node.content_label) != comparable_label(
                node.raw_label
            ):
                issues.append(
                    f"navigation/content title materially differs: {node.source_location}"
                )
        boundaries = [
            _boundary_from_node(
                node, _navigation_nodes(inventory, primary_name), index, fallback_positions
            )
            for index, node in enumerate(ordered, 1)
        ]
        section_by_node = {
            node.id: boundary.section_id for node, boundary in zip(ordered, boundaries, strict=True)
        }
        all_by_id = {node.id: node for node in _navigation_nodes(inventory, primary_name)}
        for boundary, node in zip(boundaries, ordered, strict=True):
            parent_id = node.parent_id
            while parent_id is not None and parent_id not in section_by_node:
                parent_id = all_by_id[parent_id].parent_id if parent_id in all_by_id else None
            boundary.parent_section_id = section_by_node.get(parent_id)
            for stacked in stacks.get(node.id, []):
                if stacked.id != node.id:
                    boundary.evidence.append(
                        SelectionEvidence(
                            source_kind=stacked.source,
                            source_location=stacked.source_location,
                            raw_value=stacked.raw_target,
                            resolved_value=stacked.resolved_location,
                            decision="stacked-hierarchy",
                            reason="authored ancestor shares one audio start",
                        )
                    )
        return SectionSelection(
            primary_source=primary_name,
            status="blocked" if issues else "ready",
            boundaries=boundaries,
            issues=list(dict.fromkeys(issues)),
        )

    if epub_path is None:
        return SectionSelection(
            primary_source=None,
            status="blocked",
            boundaries=[],
            issues=["standard navigation is absent or unresolvable; structural evidence required"],
        )
    candidates = (
        candidate_cache
        if candidate_cache is not None
        else structural_candidates(epub_path, inventory)
    )
    calibre_by_candidate: dict[str, CalibreCandidate] = {}
    for external in calibre_candidates or []:
        matches = [
            candidate
            for candidate in candidates
            if candidate.resource_href == external.resource_href
            and (
                (external.fragment is not None and candidate.fragment == external.fragment)
                or (
                    external.fragment is None
                    and comparable_label(candidate.title) == comparable_label(external.title)
                )
            )
        ]
        if len(matches) == 1 and matches[0].title and matches[0].signals:
            candidate = matches[0]
            if not candidate.selected:
                position = candidates.index(candidate)
                candidate = candidate.model_copy(
                    update={
                        "selected": True,
                        "rejection_reason": None,
                        "signals": candidate.signals + ["calibre-corroboration"],
                    }
                )
                candidates[position] = candidate
            calibre_by_candidate[candidate.id] = external
    selected = [candidate for candidate in candidates if candidate.selected]
    if not selected:
        return SectionSelection(
            primary_source=None,
            status="blocked",
            boundaries=[],
            issues=["no corroborated structural section candidates"],
        )
    selected.sort(key=lambda candidate: (candidate.spine_ordinal, candidate.dom_ordinal))
    positions = [(candidate.spine_ordinal, candidate.dom_ordinal) for candidate in selected]
    if len(set(positions)) != len(positions):
        issues.append("structural candidates collide at one DOM position")
    boundaries = [
        SectionBoundary(
            section_id=f"sec-{index:04d}",
            ordinal=index,
            parent_section_id=None,
            source="content-structure",
            source_node_id=candidate.id,
            resource_href=candidate.resource_href,
            fragment=candidate.fragment,
            spine_ordinal=candidate.spine_ordinal,
            dom_ordinal=candidate.dom_ordinal,
            level=candidate.level,
            raw_title=candidate.title or "",
            title=candidate.title or "",
            title_origin="content-heading" if candidate.title_location else "accessible-name",
            title_path=[candidate.title or ""],
            content_label=candidate.title,
            delivery_chapter=True,
            evidence=[
                SelectionEvidence(
                    source_kind="content-structure",
                    source_location=candidate.source_location,
                    raw_value=candidate.title,
                    resolved_value=candidate.title_location,
                    decision="selected",
                    reason=" + ".join(candidate.signals),
                )
            ]
            + (
                [
                    SelectionEvidence(
                        source_kind="calibre-candidate",
                        source_location=calibre_by_candidate[candidate.id].source_location,
                        raw_value=calibre_by_candidate[candidate.id].title,
                        resolved_value=candidate.source_location,
                        decision="corroborated",
                        reason="matched independent content structure",
                    )
                ]
                if candidate.id in calibre_by_candidate
                else []
            ),
            issues=[],
        )
        for index, candidate in enumerate(selected, 1)
    ]
    hierarchy: list[SectionBoundary] = []
    for boundary in boundaries:
        while hierarchy and hierarchy[-1].level >= boundary.level:
            hierarchy.pop()
        boundary.parent_section_id = hierarchy[-1].section_id if hierarchy else None
        hierarchy.append(boundary)
    return SectionSelection(
        primary_source="content-structure",
        status="blocked" if issues else "ready",
        boundaries=boundaries,
        issues=issues,
    )

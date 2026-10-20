"""Standards-first EPUB reading-order and navigation inventory.

EbookLib owns package loading and manifest/spine interpretation.  Navigation is
read from both EPUB 3 NAV and EPUB 2 NCX resources with lxml so that choosing one
source never erases evidence from the other.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import unquote, urlsplit

from ebooklib import epub
from lxml import etree
from pydantic import Field

from audiobooks.script_contract import Record

NavigationSource = Literal["epub3-nav", "epub2-ncx"]


class ReadingOrderItem(Record):
    ordinal: int = Field(ge=1)
    idref: str
    href: str
    media_type: str
    linear: bool


class NavigationNode(Record):
    id: str
    ordinal: int = Field(ge=1)
    source: NavigationSource
    parent_id: str | None
    level: int = Field(ge=1)
    source_location: str
    raw_label: str
    raw_target: str | None
    resource_href: str | None
    fragment: str | None
    resource_exists: bool
    fragment_exists: bool | None
    resolved_location: str | None
    dom_ordinal: int | None
    content_label: str | None
    content_label_location: str | None
    content_heading_level: int | None
    spine_ordinal: int | None
    linear: bool | None
    issues: list[str]


class EpubInventory(Record):
    source_path: str
    package_version: str | None
    title: str | None
    creators: list[str]
    spine: list[ReadingOrderItem]
    navigation: list[NavigationNode]


_whitespace_pattern = re.compile(r"\s+")


def _element_text(node: etree._Element | None) -> str:
    if node is None:
        return ""
    return _whitespace_pattern.sub(" ", "".join(node.itertext())).strip()


def _local_name(node: etree._Element) -> str:
    tag = str(node.tag)
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _children_named(node: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in node if isinstance(child.tag, str) and _local_name(child) == name]


def normalize_target(
    raw_target: str, navigation_href: str
) -> tuple[str | None, str | None, list[str]]:
    """Resolve a local navigation target without losing malformed-target evidence."""
    issues: list[str] = []
    parsed = urlsplit(raw_target)
    if parsed.scheme or parsed.netloc:
        return None, None, ["external navigation target"]
    try:
        path = unquote(parsed.path, errors="strict")
        fragment = unquote(parsed.fragment, errors="strict") or None
    except UnicodeDecodeError:
        return None, None, ["invalid percent-encoded UTF-8 in navigation target"]
    base = str(PurePosixPath(navigation_href).parent)
    resource = posixpath.normpath(posixpath.join(base, path)) if path else navigation_href
    if resource == ".":
        resource = navigation_href
    if resource == ".." or resource.startswith("../"):
        issues.append("navigation target escapes package root")
    return resource, fragment, issues


def _parse_document(content: bytes) -> etree._Element:
    return etree.fromstring(
        content, parser=etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
    )


def _raw_nav_nodes(item: epub.EpubNav) -> list[dict]:
    root = _parse_document(item.get_content())
    toc_nodes = root.xpath(
        ".//*[local-name()='nav' and " "(@*[local-name()='type']='toc' or @role='doc-toc')]"
    )
    if not toc_nodes:
        return []
    ols = _children_named(toc_nodes[0], "ol")
    if not ols:
        return []
    records: list[dict] = []

    def walk(ol: etree._Element, parent: int | None, level: int, path: str) -> None:
        for position, li in enumerate(_children_named(ol, "li"), 1):
            label_node = next((child for child in li if _local_name(child) in {"a", "span"}), None)
            raw_target = (
                label_node.get("href")
                if label_node is not None and _local_name(label_node) == "a"
                else None
            )
            index = len(records)
            records.append(
                {
                    "parent": parent,
                    "level": level,
                    "label": _element_text(label_node),
                    "target": raw_target,
                    "location": f"{item.file_name}:{path}/li[{position}]",
                }
            )
            nested = _children_named(li, "ol")
            if nested:
                walk(nested[0], index, level + 1, f"{path}/li[{position}]/ol[1]")

    walk(ols[0], None, 1, "nav[1]/ol[1]")
    return records


def _raw_ncx_nodes(item: epub.EpubNcx) -> list[dict]:
    root = _parse_document(item.get_content())
    maps = root.xpath(".//*[local-name()='navMap']")
    if not maps:
        return []
    records: list[dict] = []

    def walk(parent_node: etree._Element, parent: int | None, level: int, path: str) -> None:
        for position, point in enumerate(_children_named(parent_node, "navPoint"), 1):
            labels = point.xpath("./*[local-name()='navLabel']/*[local-name()='text']")
            contents = _children_named(point, "content")
            index = len(records)
            records.append(
                {
                    "parent": parent,
                    "level": level,
                    "label": _element_text(labels[0]) if labels else "",
                    "target": contents[0].get("src") if contents else None,
                    "location": f"{item.file_name}:{path}/navPoint[{position}]",
                }
            )
            walk(point, index, level + 1, f"{path}/navPoint[{position}]")

    walk(maps[0], None, 1, "navMap[1]")
    return records


def _metadata_text(book: epub.EpubBook, name: str) -> list[str]:
    return [str(value).strip() for value, _ in book.get_metadata("DC", name) if str(value).strip()]


def inventory_epub(path: Path) -> EpubInventory:
    """Inventory package order and independently preserve every NAV/NCX node."""
    book = epub.read_epub(path)
    item_by_id = {item.id: item for item in book.get_items()}
    item_by_href = {item.file_name: item for item in book.get_items()}
    reading_order: list[ReadingOrderItem] = []
    for ordinal, (idref, linear_value) in enumerate(book.spine, 1):
        item = item_by_id.get(idref)
        if item is None:
            raise ValueError(f"spine references missing manifest item: {idref}")
        reading_order.append(
            ReadingOrderItem(
                ordinal=ordinal,
                idref=idref,
                href=item.file_name,
                media_type=item.media_type,
                linear=linear_value.lower() != "no",
            )
        )
    reading_order_by_href = {item.href: item for item in reading_order}
    document_by_href: dict[str, etree._Element | None] = {}

    def resolve_content_label(
        target: etree._Element,
    ) -> tuple[str | None, str | None, int | None]:
        heading = (
            target
            if _local_name(target).lower() in {f"h{level}" for level in range(1, 7)}
            else None
        )
        if heading is None:
            heading = next(
                (
                    node
                    for node in target.iterdescendants()
                    if isinstance(node.tag, str)
                    and _local_name(node).lower() in {f"h{level}" for level in range(1, 7)}
                ),
                None,
            )
        if heading is not None and _element_text(heading):
            return (
                _element_text(heading),
                heading.getroottree().getpath(heading),
                int(_local_name(heading)[1]),
            )
        accessible = target.get("aria-label") or target.get("title")
        return (
            (accessible.strip(), target.getroottree().getpath(target), None)
            if accessible and accessible.strip()
            else (None, None, None)
        )

    def resolve_target(
        resource: str | None, fragment: str | None
    ) -> tuple[
        bool, bool | None, str | None, int | None, str | None, str | None, int | None, list[str]
    ]:
        if resource is None:
            return False, None, None, None, None, None, None, []
        item = item_by_href.get(resource)
        if item is None:
            return (
                False,
                False if fragment else None,
                None,
                None,
                None,
                None,
                None,
                ["target resource is absent from manifest"],
            )
        if resource not in document_by_href:
            try:
                document_by_href[resource] = _parse_document(item.get_content())
            except etree.XMLSyntaxError:
                document_by_href[resource] = None
        root = document_by_href[resource]
        if root is None:
            return True, False, None, None, None, None, None, ["target resource DOM is unparseable"]
        elements = [node for node in root.iter() if isinstance(node.tag, str)]
        if not fragment:
            body = next((node for node in elements if _local_name(node).lower() == "body"), root)
            label, label_location, heading_level = resolve_content_label(body)
            return True, None, resource, 0, label, label_location, heading_level, []
        matches = root.xpath("//*[@id=$fragment or @name=$fragment]", fragment=fragment)
        if len(matches) == 1:
            match = matches[0]
            label, label_location, heading_level = resolve_content_label(match)
            return (
                True,
                True,
                f"{resource}{root.getroottree().getpath(match)}",
                elements.index(match),
                label,
                label_location,
                heading_level,
                [],
            )
        if not matches:
            return True, False, None, None, None, None, None, ["target fragment is absent"]
        return (
            True,
            False,
            None,
            None,
            None,
            None,
            None,
            ["target fragment resolves to multiple elements"],
        )

    nodes: list[NavigationNode] = []
    navigation_sources: list[tuple[NavigationSource, epub.EpubItem, list[dict]]] = []
    for item in book.get_items():
        if isinstance(item, epub.EpubNav):
            navigation_sources.append(("epub3-nav", item, _raw_nav_nodes(item)))
        elif isinstance(item, epub.EpubNcx):
            navigation_sources.append(("epub2-ncx", item, _raw_ncx_nodes(item)))
    counters = {"epub3-nav": 0, "epub2-ncx": 0}
    for source, item, raw_nodes in navigation_sources:
        index_to_id: dict[int, str] = {}
        for raw_index, raw_node in enumerate(raw_nodes):
            counters[source] += 1
            node_id = ("nav" if source == "epub3-nav" else "ncx") + f"-{counters[source]:06d}"
            index_to_id[raw_index] = node_id
            issues: list[str] = []
            resource = fragment = None
            if raw_node["target"] is not None:
                resource, fragment, normalization_issues = normalize_target(
                    raw_node["target"], item.file_name
                )
                issues.extend(normalization_issues)
            (
                resource_exists,
                fragment_exists,
                resolved_location,
                dom_ordinal,
                label,
                label_location,
                heading_level,
                resolution_issues,
            ) = resolve_target(resource, fragment)
            issues.extend(resolution_issues)
            reading_order_item = reading_order_by_href.get(resource) if resource else None
            nodes.append(
                NavigationNode(
                    id=node_id,
                    ordinal=counters[source],
                    source=source,
                    parent_id=index_to_id.get(raw_node["parent"]),
                    level=raw_node["level"],
                    source_location=raw_node["location"],
                    raw_label=raw_node["label"],
                    raw_target=raw_node["target"],
                    resource_href=resource,
                    fragment=fragment,
                    resource_exists=resource_exists,
                    fragment_exists=fragment_exists,
                    resolved_location=resolved_location,
                    dom_ordinal=dom_ordinal,
                    content_label=label,
                    content_label_location=label_location,
                    content_heading_level=heading_level,
                    spine_ordinal=reading_order_item.ordinal if reading_order_item else None,
                    linear=reading_order_item.linear if reading_order_item else None,
                    issues=issues,
                )
            )
    package_version = book.version
    titles = _metadata_text(book, "title")
    return EpubInventory(
        source_path=str(path),
        package_version=package_version,
        title=titles[0] if titles else None,
        creators=_metadata_text(book, "creator"),
        spine=reading_order,
        navigation=nodes,
    )

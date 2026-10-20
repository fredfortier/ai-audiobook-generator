from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from audiobooks.epub_sections import CalibreCandidate, select_sections, structural_candidates
from audiobooks.epub_structure import EpubInventory, inventory_epub

CONTAINER_XML = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
 <rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""


def write_epub(
    path: Path,
    *,
    body: str,
    nav_entries: str = "",
    ncx_entries: str = "",
    version: str = "3.0",
    extra_resource: bool = False,
    second_body: str | None = None,
) -> None:
    manifest_nav = (
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        if nav_entries
        else ""
    )
    manifest_ncx = (
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        if ncx_entries
        else ""
    )
    extra_manifest = (
        '<item id="notes" href="notes.xhtml" media-type="application/xhtml+xml"/>'
        if extra_resource
        else ""
    )
    second_manifest = (
        '<item id="second" href="second.xhtml" media-type="application/xhtml+xml"/>'
        if second_body
        else ""
    )
    toc = ' toc="ncx"' if ncx_entries else ""
    extra_spine = '<itemref idref="notes" linear="no"/>' if extra_resource else ""
    second_spine = '<itemref idref="second"/>' if second_body else ""
    package = f"""<package xmlns="http://www.idpf.org/2007/opf" version="{version}" unique-identifier="uid">
 <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">fixture</dc:identifier><dc:title>Fixture</dc:title><dc:language>en</dc:language></metadata>
 <manifest>{manifest_nav}{manifest_ncx}<item id="book" href="book.xhtml" media-type="application/xhtml+xml"/>{second_manifest}{extra_manifest}</manifest>
 <spine{toc}><itemref idref="book"/>{second_spine}{extra_spine}</spine></package>"""
    nav = f"""<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>
 <nav epub:type="toc"><ol>{nav_entries}</ol></nav></body></html>"""
    ncx = f"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap>{ncx_entries}</navMap></ncx>"""
    content_document = f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>{body}</body></html>'
    with ZipFile(path, "w") as archive:
        mimetype = ZipInfo("mimetype")
        mimetype.compress_type = ZIP_STORED
        archive.writestr(mimetype, "application/epub+zip")
        files = {
            "META-INF/container.xml": CONTAINER_XML,
            "EPUB/package.opf": package,
            "EPUB/book.xhtml": content_document,
        }
        if nav_entries:
            files["EPUB/nav.xhtml"] = nav
        if ncx_entries:
            files["EPUB/toc.ncx"] = ncx
        if extra_resource:
            files["EPUB/notes.xhtml"] = (
                '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="notes">Notes</h1></body></html>'
            )
        if second_body:
            files["EPUB/second.xhtml"] = (
                f'<html xmlns="http://www.w3.org/1999/xhtml"><body>{second_body}</body></html>'
            )
        for name, value in files.items():
            archive.writestr(name, value, compress_type=ZIP_DEFLATED)


def navigation_entry(label: str, fragment: str, nested: str = "") -> str:
    return f'<li><a href="book.xhtml#{fragment}">{label}</a>{f"<ol>{nested}</ol>" if nested else ""}</li>'


def ncx_entry(label: str, fragment: str, nested: str = "") -> str:
    return f'<navPoint><navLabel><text>{label}</text></navLabel><content src="book.xhtml#{fragment}"/>{nested}</navPoint>'


class EpubSectionSelectionTest(unittest.TestCase):
    def create_epub(
        self,
        *,
        body: str,
        nav_entries: str = "",
        ncx_entries: str = "",
        version: str = "3.0",
        extra_resource: bool = False,
        second_body: str | None = None,
    ) -> tuple[Path, EpubInventory]:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "fixture.epub"
        write_epub(
            path,
            body=body,
            nav_entries=nav_entries,
            ncx_entries=ncx_entries,
            version=version,
            extra_resource=extra_resource,
            second_body=second_body,
        )
        return path, inventory_epub(path)

    def test_agreeing_nav_ncx_many_fragments_and_navigation_projection(self) -> None:
        body = (
            '<section id="one"><h1>Chapter One</h1><p>A.</p></section><div id="two"><p>B.</p></div>'
        )
        nav_entries = navigation_entry("Chapter One", "one") + navigation_entry(
            "Chapter Two", "two"
        )
        ncx_entries = ncx_entry("Chapter One", "one") + ncx_entry("Chapter Two", "two")
        path, inventory = self.create_epub(
            body=body, nav_entries=nav_entries, ncx_entries=ncx_entries
        )
        result = select_sections(inventory, epub_path=path)

        self.assertEqual(result.status, "ready")
        self.assertEqual(
            [(item.fragment, item.title_origin) for item in result.boundaries],
            [("one", "content-heading"), ("two", "navigation-label-projection")],
        )
        self.assertEqual(result.boundaries[1].title, "Chapter Two")
        self.assertLess(result.boundaries[0].dom_ordinal, result.boundaries[1].dom_ordinal)

    def test_targetless_parent_path_and_stacked_hierarchy_are_preserved(self) -> None:
        body = '<section id="start"><h2>Chapter One</h2><p>A.</p></section>'
        nested_nav = navigation_entry("Chapter One", "start")
        nav_entries = f"<li><span>Part I</span><ol>{nested_nav}</ol></li>"
        nested_ncx = ncx_entry("Chapter One", "start")
        ncx_entries = f"<navPoint><navLabel><text>Part I</text></navLabel>{nested_ncx}</navPoint>"
        path, inventory = self.create_epub(
            body=body, nav_entries=nav_entries, ncx_entries=ncx_entries
        )
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.boundaries[0].title_path, ["Part I", "Chapter One"])

        stacked = navigation_entry("Part I", "start", navigation_entry("Chapter One", "start"))
        stacked_ncx = ncx_entry("Part I", "start", ncx_entry("Chapter One", "start"))
        path2, inventory2 = self.create_epub(
            body=body, nav_entries=stacked, ncx_entries=stacked_ncx
        )
        result2 = select_sections(inventory2, epub_path=path2)
        self.assertEqual(result2.status, "ready")
        self.assertEqual(len(result2.boundaries), 1)
        self.assertTrue(
            any(item.decision == "stacked-hierarchy" for item in result2.boundaries[0].evidence)
        )

        body3 = (
            '<section id="part"><h1>Part I</h1></section>'
            '<section id="start"><h2>Chapter One</h2></section>'
        )
        nested3 = navigation_entry("Part I", "part", navigation_entry("Chapter One", "start"))
        ncx3 = ncx_entry("Part I", "part", ncx_entry("Chapter One", "start"))
        path3, inventory3 = self.create_epub(body=body3, nav_entries=nested3, ncx_entries=ncx3)
        result3 = select_sections(inventory3, epub_path=path3)
        self.assertEqual(result3.boundaries[1].parent_section_id, result3.boundaries[0].section_id)

    def test_material_source_or_content_label_disagreement_blocks(self) -> None:
        body = '<section id="one"><h1>A Different Work</h1></section><section id="two"><h1>Second</h1></section>'
        path, inventory = self.create_epub(
            body=body,
            nav_entries=navigation_entry("First", "one") + navigation_entry("Second", "two"),
            ncx_entries=ncx_entry("First", "one") + ncx_entry("Alternative", "two"),
        )
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.status, "blocked")
        self.assertTrue(any("labels materially disagree" in issue for issue in result.issues))
        self.assertTrue(
            any("navigation/content title materially differs" in issue for issue in result.issues)
        )

    def test_single_missing_fragment_degrades_but_multiple_missing_fragments_block(self) -> None:
        body = "<h1>Opening</h1><p>Body.</p>"
        path, inventory = self.create_epub(
            body=body, nav_entries=navigation_entry("Opening", "missing")
        )
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.boundaries[0].dom_ordinal, 0)
        self.assertTrue(
            any(
                item.decision == "degraded-to-resource-start"
                for item in result.boundaries[0].evidence
            )
        )

        path2, inventory2 = self.create_epub(
            body=body,
            nav_entries=(
                navigation_entry("One", "missing-one") + navigation_entry("Two", "missing-two")
            ),
        )
        result2 = select_sections(inventory2, epub_path=path2)
        self.assertEqual(result2.status, "blocked")
        self.assertTrue(any("multiple unresolved fragments" in issue for issue in result2.issues))

    def test_structural_fallback_requires_semantics_or_section_plus_heading(self) -> None:
        body = """<section id="one" epub:type="chapter"><h1>One</h1><p>A.</p></section>
<section id="two"><h1>Two</h1><p>B.</p></section>
<h1 id="false">Decorative Heading</h1><span epub:type="pagebreak" id="p1">1</span>
<div id="chapter-three"><h1>Three</h1></div>"""
        path, inventory = self.create_epub(body=body)
        candidates = structural_candidates(path, inventory)
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.status, "ready")
        self.assertEqual([item.title for item in result.boundaries], ["One", "Two"])
        rejected = {item.title: item.rejection_reason for item in candidates if not item.selected}
        self.assertIn("Decorative Heading", rejected)
        self.assertIn("Three", rejected)
        self.assertTrue(any("page-break" in (item.rejection_reason or "") for item in candidates))

    def test_deficient_navigation_yields_to_stronger_repeated_structure_and_ignores_nonlinear(
        self,
    ) -> None:
        body = (
            '<section id="one" epub:type="chapter"><h1>One</h1></section>'
            '<section id="two" epub:type="chapter"><h1>Two</h1></section>'
        )
        path, inventory = self.create_epub(
            body=body, nav_entries=navigation_entry("One", "one"), extra_resource=True
        )
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.primary_source, "content-structure")
        self.assertEqual([item.title for item in result.boundaries], ["One", "Two"])
        self.assertTrue(all(item.resource_href == "book.xhtml" for item in result.boundaries))

    def test_calibre_candidate_requires_and_records_content_corroboration(self) -> None:
        body = '<div id="chapter-one"><h1>One</h1><p>A.</p></div>'
        path, inventory = self.create_epub(body=body)
        self.assertEqual(select_sections(inventory, epub_path=path).status, "blocked")
        result = select_sections(
            inventory,
            epub_path=path,
            calibre_candidates=[
                CalibreCandidate(
                    resource_href="book.xhtml",
                    fragment="chapter-one",
                    title="One",
                    source_location="calibre:fixture:1",
                )
            ],
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual([item.title for item in result.boundaries], ["One"])
        self.assertTrue(
            any(item.source_kind == "calibre-candidate" for item in result.boundaries[0].evidence)
        )

    def test_package_version_selects_primary_navigation_when_both_sources_exist(self) -> None:
        body = '<section id="one"><h1>One</h1></section>'
        for version, expected in [("2.0", "epub2-ncx"), ("3.0", "epub3-nav")]:
            with self.subTest(version=version):
                path, inventory = self.create_epub(
                    body=body,
                    nav_entries=navigation_entry("One", "one"),
                    ncx_entries=ncx_entry("One", "one"),
                    version=version,
                )
                result = select_sections(inventory, epub_path=path)
                self.assertEqual((result.status, result.primary_source), ("ready", expected))

    def test_one_boundary_per_linear_resource_preserves_reading_order(self) -> None:
        entries = navigation_entry("One", "one") + '<li><a href="second.xhtml#two">Two</a></li>'
        path, inventory = self.create_epub(
            body='<section id="one"><h1>One</h1></section>',
            nav_entries=entries,
            second_body='<section id="two"><h1>Two</h1></section>',
        )
        result = select_sections(inventory, epub_path=path)
        self.assertEqual(result.status, "ready")
        self.assertEqual(
            [(item.resource_href, item.spine_ordinal) for item in result.boundaries],
            [("book.xhtml", 1), ("second.xhtml", 2)],
        )

        reversed_entries = '<li><a href="second.xhtml#two">Two</a></li>' + navigation_entry(
            "One", "one"
        )
        reversed_path, reversed_inventory = self.create_epub(
            body='<section id="one"><h1>One</h1></section>',
            nav_entries=reversed_entries,
            second_body='<section id="two"><h1>Two</h1></section>',
        )
        reversed_result = select_sections(reversed_inventory, epub_path=reversed_path)
        self.assertEqual(reversed_result.status, "blocked")
        self.assertTrue(any("not monotonic" in issue for issue in reversed_result.issues))

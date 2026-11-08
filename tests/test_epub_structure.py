import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from epub_structure.inventory import inventory_epub, normalize_target

from tests.test_epub_sections import CONTAINER_XML


def write_epub(path: Path, *, broken_fragments: bool = False) -> None:
    fragment = "missing-a" if broken_fragments else "ch%201"
    second = "missing-b" if broken_fragments else "ch%201"
    package = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
 <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">fixture</dc:identifier><dc:title>Fixture Book</dc:title><dc:language>en</dc:language><dc:creator>Fixture Author</dc:creator></metadata>
 <manifest>
  <item id="nav" href="nav/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  <item id="one" href="text/ch 1.xhtml" media-type="application/xhtml+xml"/>
  <item id="notes" href="text/notes.xhtml" media-type="application/xhtml+xml"/>
 </manifest>
 <spine toc="ncx"><itemref idref="one"/><itemref idref="notes" linear="no"/></spine>
</package>"""
    nav = f"""<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>
 <nav epub:type="toc"><ol><li><span>Part I</span><ol>
  <li><a href="../text/ch%201.xhtml?edition=1#{fragment}">Chapter One</a></li>
  <li><a href="../text/ch%201.xhtml#{second}">Chapter Duplicate</a></li>
 </ol></li></ol></nav></body></html>"""
    ncx = f"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap>
 <navPoint id="n1"><navLabel><text>Chapter One</text></navLabel><content src="text/ch%201.xhtml?edition=1#{fragment}"/></navPoint>
 <navPoint id="n2"><navLabel><text>Chapter Duplicate</text></navLabel><content src="text/ch%201.xhtml#{second}"/></navPoint>
</navMap></ncx>"""
    chapter = """<html xmlns="http://www.w3.org/1999/xhtml"><body><section id="ch 1"><h1>Chapter One</h1><p>Body.</p></section></body></html>"""
    notes = """<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Note.</p></body></html>"""
    with ZipFile(path, "w") as archive:
        mimetype = ZipInfo("mimetype")
        mimetype.compress_type = ZIP_STORED
        archive.writestr(mimetype, "application/epub+zip")
        for name, text in {
            "META-INF/container.xml": CONTAINER_XML,
            "EPUB/package.opf": package,
            "EPUB/nav/nav.xhtml": nav,
            "EPUB/toc.ncx": ncx,
            "EPUB/text/ch 1.xhtml": chapter,
            "EPUB/text/notes.xhtml": notes,
        }.items():
            archive.writestr(name, text, compress_type=ZIP_DEFLATED)


class EpubStructureTest(unittest.TestCase):
    def test_inventory_preserves_both_navigation_sources_and_targetless_hierarchy(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "both.epub"
            write_epub(path)
            inventory = inventory_epub(path)

        assert [item.href for item in inventory.spine] == ["text/ch 1.xhtml", "text/notes.xhtml"]
        assert [item.linear for item in inventory.spine] == [True, False]
        nav = [node for node in inventory.navigation if node.source == "epub3-nav"]
        ncx = [node for node in inventory.navigation if node.source == "epub2-ncx"]
        assert len(nav) == 3
        assert len(ncx) == 2
        assert nav[0].raw_target is None
        assert nav[1].parent_id == nav[0].id
        assert nav[1].resource_href == "text/ch 1.xhtml"
        assert nav[1].fragment == "ch 1"
        assert nav[1].fragment_exists
        assert nav[1].spine_ordinal == 1
        assert ncx[0].fragment_exists

    def test_multiple_missing_fragments_remain_distinct_fail_stop_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "broken.epub"
            write_epub(path, broken_fragments=True)
            inventory = inventory_epub(path)

        nav_targets = [
            node for node in inventory.navigation if node.source == "epub3-nav" and node.raw_target
        ]
        assert [node.fragment for node in nav_targets] == ["missing-a", "missing-b"]
        assert all((node.resource_exists for node in nav_targets))
        assert all((node.fragment_exists is False for node in nav_targets))
        assert all(("target fragment is absent" in node.issues for node in nav_targets))

    def test_target_normalization_rejects_external_and_package_escape(self) -> None:
        assert normalize_target("https://example.test/ch1", "nav/toc.xhtml") == (
            None,
            None,
            ["external navigation target"],
        )
        resource, fragment, issues = normalize_target("../../outside.xhtml#x", "nav/toc.xhtml")
        assert (resource, fragment) == ("../outside.xhtml", "x")
        assert "navigation target escapes package root" in issues

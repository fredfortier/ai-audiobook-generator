from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import soundfile as sf

from audiobooks import delivery
from audiobooks.assembly import assemble, reviewed_chapter_titles
from audiobooks.delivery import encode_m4b
from audiobooks.rendering import audio_properties, generation_identity, runtime_hashes
from audiobooks.source_units import identity, sha256


def write_delivery(
    path: Path,
    *,
    contents: bytes,
    verified: bool = True,
    author: str = "Plotinus",
    title: str = "An Essay on the Beautiful",
) -> None:
    """Write the smallest hash-bound delivery fixture accepted by export_m4b."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                "delivery_version": 1,
                "output_hash": sha256(path),
                "verification_passed": verified,
                "probe": {"format": {"tags": {"artist": author, "title": title}}},
            }
        )
    )


class DeliveryTest(unittest.TestCase):
    def test_chapter_title_review_capitalizes_minor_word_after_full_stop(self) -> None:
        with TemporaryDirectory() as directory:
            review = Path(directory) / "chapter-titles.json"
            source = "Man is spirit. The spirit of the lover is in the beloved"
            plan = {"delivery_sections": [{"section_id": "letter", "title": source}]}
            entry = {
                "section_id": "letter",
                "source_title": source,
                "title": "Man Is Spirit. The Spirit of the Lover Is in the Beloved",
                "coherence": "Both authored sentences name the letter's argument.",
                "plausibility": "Only case changes; all authored wording remains.",
            }
            review.write_text(json.dumps({"style": "English title case", "chapters": [entry]}))
            self.assertEqual(reviewed_chapter_titles(plan, review)["letter"].title, entry["title"])

            entry["title"] = "Man Is Spirit. the Spirit of the Lover Is in the Beloved"
            review.write_text(json.dumps({"style": "English title case", "chapters": [entry]}))
            with self.assertRaisesRegex(ValueError, "consistent English title case"):
                reviewed_chapter_titles(plan, review)

    def test_chapter_title_review_rejects_inconsistent_minor_word_casing(self) -> None:
        with TemporaryDirectory() as directory:
            review = Path(directory) / "chapter-titles.json"
            review.write_text(
                json.dumps(
                    {
                        "style": "English title case",
                        "chapters": [
                            {
                                "section_id": "essay",
                                "source_title": "CONCERNING THE BEAUTIFUL",
                                "title": "Concerning The Beautiful",
                                "coherence": "Names the essay beginning at the authored heading.",
                                "plausibility": "Preserves the authored wording.",
                            }
                        ],
                    }
                )
            )
            plan = {
                "delivery_sections": [
                    {
                        "section_id": "essay",
                        "title": "CONCERNING THE BEAUTIFUL",
                    }
                ]
            }

            with self.assertRaisesRegex(ValueError, "consistent English title case"):
                reviewed_chapter_titles(plan, review)

    def test_chapter_title_review_requires_contextual_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            review = Path(directory) / "chapter-titles.json"
            review.write_text(
                json.dumps(
                    {
                        "style": "English title case",
                        "chapters": [
                            {
                                "section_id": "essay",
                                "source_title": "CONCERNING THE BEAUTIFUL",
                                "title": "Concerning the Beautiful",
                                "coherence": "   ",
                                "plausibility": "Preserves the authored wording.",
                            }
                        ],
                    }
                )
            )
            plan = {
                "delivery_sections": [
                    {
                        "section_id": "essay",
                        "title": "CONCERNING THE BEAUTIFUL",
                    }
                ]
            }

            with self.assertRaisesRegex(ValueError, "contextual evidence"):
                reviewed_chapter_titles(plan, review)

    def test_export_requires_configured_directory(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "EXPORT_DIR"):
                delivery.export_m4b(Path("book.m4b"))

    def test_verified_variant_exports_beside_existing_base_delivery(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "delivery" / "spirited.m4b"
            write_delivery(source, contents=b"verified spirited audiobook")
            export_directory = root / "exports"
            book_directory = export_directory / "plotinus.an-essay-on-the-beautiful"
            book_directory.mkdir(parents=True)
            base = book_directory / "essay-on-the-beautiful.m4b"
            base.write_bytes(b"restrained audiobook")

            with patch.dict(os.environ, {"EXPORT_DIR": str(export_directory)}, clear=True):
                exported = delivery.export_m4b(source, variant="spirited")

            expected = book_directory / "essay-on-the-beautiful-spirited.m4b"
            self.assertEqual(exported, expected)
            self.assertEqual(exported.read_bytes(), source.read_bytes())
            self.assertEqual(base.read_bytes(), b"restrained audiobook")

    def test_verified_variant_replaces_only_the_expected_existing_export(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "delivery" / "spirited.m4b"
            write_delivery(source, contents=b"corrected verified audiobook")
            target = (
                root
                / "exports"
                / "plotinus.an-essay-on-the-beautiful"
                / "essay-on-the-beautiful-spirited.m4b"
            )
            target.parent.mkdir(parents=True)
            target.write_bytes(b"prior verified audiobook")
            prior_hash = sha256(target)

            with patch.dict(os.environ, {"EXPORT_DIR": str(root / "exports")}, clear=True):
                with self.assertRaisesRegex(ValueError, "expected existing hash"):
                    delivery.export_m4b(source, variant="spirited", replace_hash="0" * 64)
                self.assertEqual(target.read_bytes(), b"prior verified audiobook")
                exported = delivery.export_m4b(source, variant="spirited", replace_hash=prior_hash)

            self.assertEqual(exported, target)
            self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_export_rejects_unverified_delivery(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.m4b"
            write_delivery(
                source,
                contents=b"unverified audiobook",
                verified=False,
                author="Fixture Author",
                title="Fixture Book",
            )

            with patch.dict(os.environ, {"EXPORT_DIR": str(root / "exports")}, clear=True):
                with self.assertRaisesRegex(ValueError, "verified delivery"):
                    delivery.export_m4b(source)
            self.assertFalse((root / "exports").exists())

    def test_explicit_three_chapter_assembly_and_aac_m4b_round_trip(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "render"
            audio_directory = workspace / "audio"
            audio_directory.mkdir(parents=True)
            sample_rate = 24000
            segment_definitions = [
                ("g000001", "s000001", "OPENING", 1),
                ("g000002", "s000002", "Subsection", 2),
                ("g000003", "s000003", "CHAPTER TWO", 1),
                ("g000004", "s000004", "CLOSING", 1),
            ]
            segments = [
                {
                    "id": segment_id,
                    "script": "script/0001.md",
                    "speech_id": speech_id,
                    "paragraph": 0,
                    "start": 0,
                    "end": len(text),
                    "text": text,
                    "native_text": text,
                    "native_tokens": len(text),
                    "voice": "narrator",
                    "parameters": {},
                    "seed": index,
                    "heading_level": heading_level,
                }
                for index, (segment_id, speech_id, text, heading_level) in enumerate(
                    segment_definitions
                )
            ]
            plan = {
                "render_version": 1,
                "title": "Synthetic Book",
                "author": "Fixture Author",
                "runtime_hashes": runtime_hashes(),
                "input_hashes": {},
                "segments": segments,
                "delivery_sections": [
                    {
                        "section_id": "one",
                        "title": "OPENING",
                        "title_speech_id": "s000001",
                        "start_segment_id": "g000001",
                    },
                    {
                        "section_id": "two",
                        "title": "CHAPTER TWO",
                        "title_speech_id": "s000003",
                        "start_segment_id": "g000003",
                    },
                    {
                        "section_id": "three",
                        "title": "CLOSING",
                        "title_speech_id": "s000004",
                        "start_segment_id": "g000004",
                    },
                ],
            }
            (workspace / "plan.json").write_text(json.dumps(plan))
            (workspace / "manifest.json").write_text(json.dumps({"plan_hash": identity(plan)}))
            for index, segment in enumerate(segments, 1):
                frames = sample_rate // 4
                sample_times = np.arange(frames, dtype=np.float64) / sample_rate
                audio = (0.05 * np.sin(2 * np.pi * (200 + index * 20) * sample_times)).astype(
                    np.float32
                )
                path = audio_directory / f"{segment['id']}.wav"
                sf.write(path, audio, sample_rate, format="WAV", subtype="FLOAT")
                record = {
                    "generation_hash": generation_identity(plan, segment),
                    "audio_hash": sha256(path),
                    "properties": audio_properties(path),
                }
                path.with_suffix(".json").write_text(json.dumps(record))
            gaps = root / "gaps.json"
            gaps.write_text("[]\n")
            chapter_titles = root / "chapter-titles.json"
            chapter_titles.write_text(
                json.dumps(
                    {
                        "style": "English title case",
                        "chapters": [
                            {
                                "section_id": "one",
                                "source_title": "OPENING",
                                "title": "Opening",
                                "coherence": "Names the opening section at its exact first speech.",
                                "plausibility": "The reviewed title is the authored heading with display casing.",
                            },
                            {
                                "section_id": "two",
                                "source_title": "CHAPTER TWO",
                                "title": "Chapter Two",
                                "coherence": "Names the second section at its exact first speech.",
                                "plausibility": "The reviewed title is the authored heading with display casing.",
                            },
                            {
                                "section_id": "three",
                                "source_title": "CLOSING",
                                "title": "Closing",
                                "coherence": "Names the closing section at its exact first speech.",
                                "plausibility": "The reviewed title is the authored heading with display casing.",
                            },
                        ],
                    }
                )
            )
            assembly = root / "assembly"
            with patch.dict(os.environ, {"WORKSPACE_DIR": str(root)}):
                assemble(workspace, assembly, Path("gaps.json"), Path("chapter-titles.json"))
            assembly_record = json.loads((assembly / "assembly.json").read_text())
            self.assertEqual(
                [chapter["title"] for chapter in assembly_record["chapters"]],
                ["Opening", "Chapter Two", "Closing"],
            )
            self.assertEqual(
                [chapter["source_title"] for chapter in assembly_record["chapters"]],
                ["OPENING", "CHAPTER TWO", "CLOSING"],
            )
            self.assertNotIn("Subsection", (assembly / "chapters.ffmetadata").read_text())

            output = root / "synthetic.m4b"
            manifest = encode_m4b(assembly, output, bitrate="64k", gain_db=-1.0)
            self.assertTrue(output.is_file())
            self.assertTrue(manifest["verification_passed"])
            self.assertEqual(
                [chapter["title"] for chapter in manifest["chapters"]],
                ["Opening", "Chapter Two", "Closing"],
            )
            self.assertEqual(manifest["probe"]["streams"][0]["codec_name"], "aac")
            self.assertEqual(manifest["input_audio_hash"], assembly_record["audio_hash"])

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anki = load_module("anki_setup_under_test", "vocab/anki_setup.py")


class TagifyTests(unittest.TestCase):
    def test_keeps_letters_and_hyphens(self):
        self.assertEqual(anki.tagify("Results-Discussion"), "Results-Discussion")

    def test_replaces_spaces_and_ampersands(self):
        self.assertEqual(anki.tagify("Results & Discussion"), "Results_Discussion")

    def test_keeps_colons_for_nested_tags(self):
        self.assertEqual(anki.tagify("section::Intro"), "section::Intro")

    def test_empty_becomes_misc(self):
        self.assertEqual(anki.tagify("  "), "misc")

    def test_keeps_cjk(self):
        self.assertEqual(anki.tagify("讨论"), "讨论")


class ImportSeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "seed.csv"
        with self.path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["section", "function", "chinese_cue", "template", "example", "source"])
            writer.writerow(
                ["Results", "report trend", "报告上升趋势", "X increased from [a] to [b].", "Mobility rose.", "Own"]
            )
        self._original_call = anki.call

    def tearDown(self):
        anki.call = self._original_call
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        added, skipped = anki.import_seed("http://unused", "D", "M", self.path, dry_run=True)
        self.assertEqual((added, skipped), (0, 0))

    def test_import_maps_fields_and_tags(self):
        calls: list[tuple[str, dict]] = []

        def fake_call(url, action, **params):
            calls.append((action, params))
            if action == "findNotes":
                return []
            if action == "canAddNotes":
                return [True]
            if action == "addNotes":
                return [42]
            raise AssertionError(action)

        anki.call = fake_call
        added, skipped = anki.import_seed("http://unused", "Prism::Phrases", "AE Phrase", self.path, False)
        self.assertEqual((added, skipped), (1, 0))

        note = next(params["notes"][0] for action, params in calls if action == "canAddNotes")
        self.assertEqual(note["fields"]["Template"], "X increased from [a] to [b].")
        self.assertEqual(note["fields"]["ChineseCue"], "报告上升趋势")
        self.assertIn("section::Results", note["tags"])
        self.assertIn("phrasebank", note["tags"])
        self.assertEqual(note["options"]["allowDuplicate"], True)

    def test_existing_notes_are_skipped(self):
        def fake_call(url, action, **params):
            if action == "findNotes":
                return []
            if action == "canAddNotes":
                return [False]
            raise AssertionError(action)

        anki.call = fake_call
        added, skipped = anki.import_seed("http://unused", "D", "M", self.path, False)
        self.assertEqual((added, skipped), (0, 1))


if __name__ == "__main__":
    unittest.main()

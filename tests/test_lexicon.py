from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# app.core reads the suite root at import time; point it at a scratch folder so
# the tests never touch E:/LumenSuite.
os.environ["LUMEN_SUITE"] = tempfile.mkdtemp(prefix="prism-suite-")
sys.path.insert(0, str(ROOT))

from app.services import anki, lexicon  # noqa: E402


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


get_dict = load_script("get_dict_under_test", "scripts/get_dict.py")


def build_dictionary(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(get_dict.SCHEMA)
    connection.execute(
        "INSERT INTO words VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "disorder",
            "dɪs'ɔ:də",
            # the builder decodes the CSV's literal \n before it reaches the index
            get_dict.split_translation("n. 混乱；骚动\\nv. 使序乱"),
            "A state of confusion.",
            "cet4 cet6 toefl gre frq",
            "d:disordered/i:disordering/s:disorders",
            1200,
            3100,
            0,
            3,
        ),
    )
    connection.commit()
    connection.close()


class DictionaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="prism-lex-"))
        self.db = self.tmp / "ecdict.sqlite"
        build_dictionary(self.db)
        self._db_path = lexicon.DB_PATH
        lexicon.DB_PATH = self.db

    def tearDown(self):
        lexicon.DB_PATH = self._db_path

    def test_normalise_strips_quotes_and_punctuation(self):
        self.assertEqual(lexicon.normalize('  "the  disorder! "'), "the disorder")

    def test_lookup_is_case_insensitive(self):
        for query in ("Disorder", "DISORDER", " disorder "):
            result = lexicon.lookup(query)
            self.assertTrue(result["installed"])
            self.assertEqual(result["entry"]["word"], "disorder")

    def test_lookup_decodes_escapes_and_labels(self):
        entry = lexicon.lookup("disorder")["entry"]
        self.assertIn("\n", entry["translation"])
        self.assertNotIn("\\n", entry["translation"])
        self.assertEqual(entry["tags"], ["CET4", "CET6", "TOEFL", "GRE", "高频"])
        self.assertEqual(entry["exchange"], ["过去分词 disordered", "现在分词 disordering", "复数/三单 disorders"])

    def test_missing_word_reports_no_entry(self):
        self.assertIsNone(lexicon.lookup("sesquipedalianism")["entry"])

    def test_missing_database_reports_uninstalled(self):
        lexicon.DB_PATH = self.tmp / "absent.sqlite"
        self.assertEqual(lexicon.lookup("disorder"), {"query": "disorder", "entry": None, "installed": False})


class ClipInboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="prism-clips-"))
        self._clips_path = lexicon.CLIPS_PATH
        lexicon.CLIPS_PATH = self.tmp / "clips.jsonl"

    def tearDown(self):
        lexicon.CLIPS_PATH = self._clips_path

    def add(self, word: str = "disorder", **extra):
        payload = {"word": word, "context": "The disorder was obvious.", "url": "https://example.com/a/b", "title": "A page"}
        payload.update(extra)
        return lexicon.add_clip(payload)

    def test_add_then_list_counts_pending(self):
        self.add()
        self.add(word="hysteresis")
        data = lexicon.clips()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["pending"], 2)
        self.assertEqual({row["word"] for row in data["items"]}, {"disorder", "hysteresis"})
        self.assertEqual(data["items"][0]["status"], "new")

    def test_blank_word_is_rejected(self):
        with self.assertRaises(ValueError):
            lexicon.add_clip({"word": "   "})

    def test_corrupt_lines_are_skipped(self):
        self.add()
        with lexicon.CLIPS_PATH.open("a", encoding="utf-8") as handle:
            handle.write("{not json}\n")
        self.assertEqual(lexicon.clips()["total"], 1)

    def test_drop_removes_only_the_named_rows(self):
        keep = self.add()
        gone = self.add(word="hysteresis")
        self.assertEqual(lexicon.drop([gone["id"]]), 1)
        self.assertEqual([row["id"] for row in lexicon.clips()["items"]], [keep["id"]])

    def test_note_uses_vocab_fields_and_page_host(self):
        record = self.add()
        note = lexicon._note(record, "Prism::Vocab", "AE Vocab")
        self.assertEqual(note["deckName"], "Prism::Vocab")
        self.assertEqual(note["modelName"], "AE Vocab")
        self.assertEqual(note["tags"], ["web-clip", "prism"])
        self.assertEqual(note["fields"]["Word"], "disorder")
        self.assertEqual(note["fields"]["Source"], "example.com")
        self.assertIn("disorder", json.dumps(note, ensure_ascii=False))

    def test_import_marks_rows_and_creates_the_deck_if_absent(self):
        first = self.add()
        second = self.add(word="hysteresis")
        calls = []

        def fake_call(action, timeout=None, **params):
            calls.append((action, params))
            if action == "deckNames":
                return ["Default"]
            if action == "modelNames":
                return ["AE Vocab", "AE Phrase"]
            if action == "canAddNotes":
                return [True, False]
            if action == "addNotes":
                return [111]
            return 6

        original = anki.call
        anki.call = fake_call
        try:
            result = lexicon.import_clips()
        finally:
            anki.call = original

        self.assertEqual(result["added"], 1)
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual([name for name, _ in calls], ["version", "deckNames", "createDeck", "modelNames", "canAddNotes", "addNotes"])
        self.assertEqual(calls[2][1], {"deck": "Prism::Vocab"})
        rows = {row["id"]: row for row in lexicon.clips()["items"]}
        self.assertEqual(rows[first["id"]]["status"], "imported")
        self.assertEqual(rows[first["id"]]["noteId"], 111)
        self.assertEqual(rows[second["id"]]["status"], "new")
        self.assertEqual(lexicon.clips()["pending"], 1)

    def test_import_without_payload_says_so(self):
        self.assertEqual(lexicon.import_clips()["added"], 0)

    def test_missing_note_type_is_explained_not_counted_as_duplicate(self):
        self.add()
        original = anki.call

        def fake_call(action, timeout=None, **params):
            if action == "deckNames":
                return ["Prism::Vocab"]
            if action == "modelNames":
                return ["Basic"]
            return 6

        anki.call = fake_call
        try:
            with self.assertRaises(anki.AnkiError) as caught:
                lexicon.import_clips()
        finally:
            anki.call = original
        self.assertIn("初始化牌组", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

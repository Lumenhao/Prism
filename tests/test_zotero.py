from __future__ import annotations

import importlib.util
import os
import sqlite3
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


zotero = load_module("zotero_under_test", "vocab/zotero_to_anki.py")


class CleanTests(unittest.TestCase):
    def test_strips_tags_and_entities(self):
        self.assertEqual(zotero.clean("<p>Hello&nbsp;<b>world</b></p>"), "Hello world")

    def test_collapses_whitespace(self):
        self.assertEqual(zotero.clean("  a \n\t b  "), "a b")

    def test_none_and_empty(self):
        self.assertEqual(zotero.clean(None), "")
        self.assertEqual(zotero.clean(""), "")


class ExpandPathTests(unittest.TestCase):
    def test_expands_home(self):
        self.assertEqual(zotero.expand_path("~/Zotero/zotero.sqlite"), Path.home() / "Zotero" / "zotero.sqlite")

    def test_expands_environment_variable(self):
        os.environ["P2T_TEST_DIR"] = str(Path.home())
        try:
            self.assertEqual(zotero.expand_path("$P2T_TEST_DIR/Zotero"), Path.home() / "Zotero")
        finally:
            del os.environ["P2T_TEST_DIR"]


class ZoteroProfileTests(unittest.TestCase):
    def test_parses_escaped_windows_path(self):
        prefs = (
            'user_pref("extensions.zotero.useDataDir", true);\n'
            'user_pref("extensions.zotero.dataDir", "E:\\\\XuLab in Westlake University\\\\Zotero");\n'
        )
        self.assertEqual(
            zotero.parse_zotero_data_dir(prefs),
            Path("E:/XuLab in Westlake University/Zotero"),
        )

    def test_missing_pref_returns_none(self):
        self.assertIsNone(zotero.parse_zotero_data_dir('user_pref("x", 1);'))

    def test_env_override_wins(self):
        os.environ["ZOTERO_DB"] = str(Path.home() / "custom.sqlite")
        try:
            self.assertEqual(zotero.resolve_db("~/ignored.sqlite"), Path.home() / "custom.sqlite")
        finally:
            del os.environ["ZOTERO_DB"]


class BuildNoteTests(unittest.TestCase):
    def base_row(self, **overrides):
        row = {
            "annotation_id": 7,
            "text": "<b>F4-TCNQ</b>",
            "comment": "四氟四氰基喹啉二甲烷",
            "page": "3",
            "added": "2026-10-02 12:00:00",
            "paper_key": "PAPERKEY",
            "title": "My Paper",
            "doi": "10.1234/xyz",
        }
        row.update(overrides)
        return row

    def test_maps_fields_and_source(self):
        note = zotero.build_note(self.base_row(), "Prism::Vocab", "AE Vocab")
        self.assertEqual(note["fields"]["Word"], "F4-TCNQ")
        self.assertEqual(note["fields"]["Translation"], "四氟四氰基喹啉二甲烷")
        self.assertEqual(note["fields"]["Source"], "My Paper (p. 3)")
        self.assertEqual(note["fields"]["Link"], "zotero://select/library/items/PAPERKEY")
        self.assertEqual(note["fields"]["Added"], "2026-10-02")
        self.assertEqual(note["_annotation_id"], 7)
        self.assertNotIn("needs_translation", note["tags"])

    def test_falls_back_to_doi_and_marks_missing_translation(self):
        note = zotero.build_note(
            self.base_row(paper_key=None, comment="", page=""), "D", "M"
        )
        self.assertEqual(note["fields"]["Source"], "My Paper")
        self.assertEqual(note["fields"]["Link"], "https://doi.org/10.1234/xyz")
        self.assertIn("needs_translation", note["tags"])

    def test_unknown_source_is_explicit(self):
        note = zotero.build_note(self.base_row(title=""), "D", "M")
        self.assertEqual(note["fields"]["Source"], "Unknown source (p. 3)")


class SnapshotTests(unittest.TestCase):
    def test_snapshot_is_readable_and_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "zotero.sqlite"
            con = sqlite3.connect(source)
            con.execute("CREATE TABLE t (v TEXT)")
            con.execute("INSERT INTO t VALUES ('ok')")
            con.commit()
            con.close()

            snapshot = zotero.snapshot_db(source)
            try:
                self.assertNotEqual(snapshot, source)
                self.assertTrue(snapshot.exists())
                check = sqlite3.connect(snapshot)
                self.assertEqual(check.execute("SELECT v FROM t").fetchone()[0], "ok")
                check.close()
            finally:
                snapshot.unlink(missing_ok=True)


class FetchRowsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "zotero.sqlite"
        con = sqlite3.connect(self.db)
        con.executescript(
            """
            CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT, dateAdded TEXT);
            CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INTEGER);
            CREATE TABLE itemAnnotations (
                itemID INTEGER PRIMARY KEY, parentItemID INTEGER,
                text TEXT, comment TEXT, pageLabel TEXT
            );
            CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
            CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
            CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER);

            INSERT INTO items VALUES (1, 'PAPERKEY', '2026-10-01 09:00:00');
            INSERT INTO items VALUES (2, 'ATTKEY', '2026-10-01 09:00:00');
            INSERT INTO items VALUES (3, 'ANNKEY', '2026-10-02 12:00:00');
            INSERT INTO itemAttachments VALUES (2, 1);
            INSERT INTO itemAnnotations VALUES (3, 2, '<b>F4-TCNQ</b>', '掺杂剂', '3');
            INSERT INTO fields VALUES (1, 'title');
            INSERT INTO fields VALUES (2, 'DOI');
            INSERT INTO itemDataValues VALUES (1, 'My Paper');
            INSERT INTO itemDataValues VALUES (2, '10.1234/xyz');
            INSERT INTO itemData VALUES (1, 1, 1);
            INSERT INTO itemData VALUES (1, 2, 2);
            """
        )
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolves_title_through_attachment(self):
        rows = zotero.fetch_rows(self.db, None, None)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "My Paper")
        self.assertEqual(rows[0]["doi"], "10.1234/xyz")
        self.assertEqual(rows[0]["paper_key"], "PAPERKEY")
        self.assertEqual(rows[0]["comment"], "掺杂剂")

    def test_since_filters_older_annotations(self):
        rows = zotero.fetch_rows(self.db, "2026-10-02", None)
        self.assertEqual(len(rows), 1)
        rows = zotero.fetch_rows(self.db, "2026-10-03", None)
        self.assertEqual(rows, [])

    def test_limit(self):
        self.assertEqual(len(zotero.fetch_rows(self.db, None, 1)), 1)


if __name__ == "__main__":
    unittest.main()

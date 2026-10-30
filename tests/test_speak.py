from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


speak = load_module("speak_under_test", "speaking/speak.py")


class CleanMarkdownTests(unittest.TestCase):
    def test_removes_comments_fences_images_and_links(self):
        source = (
            "<!-- note: do not read this -->\n"
            "# Heading\n\n"
            "A **bold** claim with a [link](https://example.com) and `code`.\n\n"
            "```text\nnot spoken\n```\n"
        )
        cleaned = speak.clean_markdown(source)
        self.assertNotIn("note:", cleaned)
        self.assertNotIn("#", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("not spoken", cleaned)
        self.assertIn("bold", cleaned)
        self.assertIn("link", cleaned)
        self.assertIn("code", cleaned)

    def test_drops_whole_blockquote_lines(self):
        cleaned = speak.clean_markdown("Speak this.\n> instruction only\nNext line.\n")
        self.assertNotIn("instruction only", cleaned)
        self.assertIn("Speak this.", cleaned)
        self.assertIn("Next line.", cleaned)

    def test_keeps_double_bracket_terms_as_plain_text(self):
        self.assertEqual(speak.clean_markdown("Read [[F4-TCNQ]] now."), "Read F4-TCNQ now.")


class PronunciationTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {
            "F4-TCNQ": "F four T C N Q",
            "TCNQ": "T C N Q",
            "hBN": "h B N",
        }

    def test_longest_key_wins(self):
        self.assertEqual(
            speak.apply_pronunciation("We doped F4-TCNQ.", self.mapping),
            "We doped F four T C N Q.",
        )

    def test_does_not_replace_inside_a_longer_word(self):
        self.assertEqual(speak.apply_pronunciation("XTCNQ", self.mapping), "XTCNQ")

    def test_replaces_standalone_token(self):
        self.assertEqual(speak.apply_pronunciation("pure TCNQ film", self.mapping), "pure T C N Q film")


class TokenizeTests(unittest.TestCase):
    def test_lowercases_and_normalizes_apostrophes(self):
        self.assertEqual(speak.tokenize("Don’t stop"), ["don't", "stop"])

    def test_keeps_hyphenated_terms(self):
        self.assertEqual(speak.tokenize("F4-TCNQ and h-BN"), ["f4-tcnq", "and", "h-bn"])

    def test_converts_number_words(self):
        self.assertEqual(speak.tokenize("three layers"), ["3", "layers"])

    def test_drops_punctuation_only_tokens(self):
        self.assertEqual(speak.tokenize("— ok ..."), ["ok"])


class AlignTests(unittest.TestCase):
    def test_counts_missing_words(self):
        blocks, subs, dels, ins = speak.align(
            ["we", "measure", "the", "band"], ["we", "measure", "band"]
        )
        self.assertEqual((subs, dels, ins), (0, 1, 0))
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "delete")

    def test_counts_replace_and_insert(self):
        blocks, subs, dels, ins = speak.align(["a", "b", "c"], ["a", "x", "y", "c"])
        self.assertEqual(subs, 1)
        self.assertEqual(dels, 0)
        self.assertEqual(ins, 1)

    def test_identical_sequences_have_no_blocks(self):
        blocks, subs, dels, ins = speak.align(["a", "b"], ["a", "b"])
        self.assertEqual(blocks, [])
        self.assertEqual((subs, dels, ins), (0, 0, 0))


class MeaningfulTests(unittest.TestCase):
    def test_stopword_only_block_is_not_meaningful(self):
        self.assertFalse(
            speak.meaningful({"type": "replace", "ref": ["the", "of"], "hyp": ["a"]})
        )

    def test_content_word_block_is_meaningful(self):
        self.assertTrue(
            speak.meaningful({"type": "replace", "ref": ["band"], "hyp": []})
        )


if __name__ == "__main__":
    unittest.main()

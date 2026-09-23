import json
import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass

from core.align import build_text, save_words, section_timings
from core.script import parse_script

SCRIPT = """\
## S01
こんにちは、ヒロキです。
## S02
まず結論から言うと、
収益ゼロを覚悟してください。
## S03
[a] 画面を見てください。
[b] 結果が表示されます。
"""


@dataclass
class W:
    word: str
    start: float
    end: float
    probability: float = 0.9


def words_for(sections, starts, split=3):
    """セクションごとの原稿を split 文字ずつの「単語」に分け、start から 0.3 秒間隔で時刻を振る"""
    words = []
    for sec, t in zip(sections, starts):
        text = sec.text
        for i in range(0, len(text), split):
            words.append(W(text[i:i + split], t, t + 0.3))
            t += 0.3
    return words


class AlignTest(unittest.TestCase):
    def setUp(self):
        self.sections = parse_script(SCRIPT).sections

    def test_build_text(self):
        self.assertEqual(build_text(self.sections),
                         "こんにちは、ヒロキです。まず結論から言うと、収益ゼロを覚悟してください。画面を見てください。結果が表示されます。")

    def test_build_text_keeps_space_between_english_words(self):
        sections = parse_script("## S01\nClaude\nCode を使う。\n## S02\nAI\nツール。\n").sections
        self.assertEqual(build_text(sections), "Claude Code を使う。AIツール。")

    def test_exact_match(self):
        words = words_for(self.sections, [0.4, 3.0, 8.5, 11.2])
        timings, ratio = section_timings(self.sections, words)
        self.assertEqual(ratio, 1.0)
        # 最初のセクションは 0 秒から。以降は最初の単語の開始時刻
        self.assertEqual([t.start for t in timings], [0.0, 3.0, 8.5, 11.2])
        self.assertTrue(all(abs(t.confidence - 0.9) < 1e-9 for t in timings))

    def test_words_with_spaces_and_case(self):
        sections = parse_script("## S01\nClaude Code です。\n## S02\n次へ。\n").sections
        words = [W(" claude", 0.1, 0.4), W(" code", 0.4, 0.8), W("です。", 0.8, 1.2), W("次へ。", 2.5, 3.0)]
        timings, ratio = section_timings(sections, words)
        self.assertEqual(ratio, 1.0)
        self.assertEqual(timings[1].start, 2.5)

    def test_word_crossing_section_boundary(self):
        # 「。ま」のように単語がセクション境界をまたいでも、その単語の開始時刻を使う
        words = words_for(self.sections, [0.0, 3.0, 8.5, 11.2], split=5)
        timings, _ = section_timings(self.sections, words)
        self.assertLessEqual(timings[1].start, 3.0)
        self.assertGreater(timings[1].start, 2.0)

    def test_small_text_difference(self):
        # アライメント結果の文字が台本と少し違っても（句読点の欠落など）位置を追える
        words = words_for(self.sections, [0.0, 3.0, 8.5, 11.2])
        for w in words:
            w.word = w.word.replace("、", "")
        timings, ratio = section_timings(self.sections, words)
        self.assertLess(ratio, 1.0)
        self.assertEqual([t.start for t in timings], [0.0, 3.0, 8.5, 11.2])

    def test_low_probability(self):
        words = words_for(self.sections, [0.0, 3.0, 8.5, 11.2])
        for w in words:
            if w.start >= 8.5 and w.start < 11.2:
                w.probability = 0.1
        timings, _ = section_timings(self.sections, words)
        self.assertAlmostEqual(timings[2].confidence, 0.1)
        self.assertAlmostEqual(timings[3].confidence, 0.9)

    def test_empty_words_are_skipped(self):
        words = [W("", 0.0, 0.0)] + words_for(self.sections, [0.0, 3.0, 8.5, 11.2]) + [W("  ", 20, 20)]
        timings, _ = section_timings(self.sections, words)
        self.assertEqual(timings[3].start, 11.2)

    def test_save_words(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        path = save_words([W("こん", 0.1, 0.3, 0.8)], folder)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), [{"word": "こん", "start": 0.1, "end": 0.3, "probability": 0.8}])
        self.assertEqual(os.path.basename(path), "alignment.json")

    def test_no_words(self):
        with self.assertRaises(ValueError):
            section_timings(self.sections, [])


if __name__ == "__main__":
    unittest.main()

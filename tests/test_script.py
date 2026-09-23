import unittest

from core.script import parse_script

EXAMPLE = """\
## S01
こんにちは、ヒロキです。今日はAI副業の始め方を話します。

## S02
まず結論から言うと、最初の3ヶ月は収益ゼロを覚悟してください。

## S03
[a] 実際の画面を見てください。ここで設定を開きます。
[b] すると、このように結果が表示されます。
"""


class ParseScriptTest(unittest.TestCase):
    def test_spec_example(self):
        r = parse_script(EXAMPLE)
        self.assertEqual(r.errors, [])
        self.assertEqual([s.id for s in r.scenes], ["S01", "S02", "S03"])
        self.assertEqual([s.key for s in r.sections], ["S01", "S02", "S03a", "S03b"])
        self.assertEqual(r.sections[0].text, "こんにちは、ヒロキです。今日はAI副業の始め方を話します。")
        self.assertEqual(r.sections[3].text, "すると、このように結果が表示されます。")

    def test_multiline_section(self):
        r = parse_script("## S01\n一行目。\n二行目。\n")
        self.assertEqual(r.sections[0].lines, ["一行目。", "二行目。"])
        self.assertEqual(r.sections[0].text, "一行目。二行目。")

    def test_marker_spans_until_next_marker(self):
        r = parse_script("## S01\n[a] 一。\n続き。\n[b] 二。\n")
        self.assertEqual(r.errors, [])
        self.assertEqual(r.sections[0].lines, ["一。", "続き。"])
        self.assertEqual(r.sections[1].lines, ["二。"])

    def test_marker_on_its_own_line(self):
        r = parse_script("## S01\n[a]\n一。\n[b]\n二。\n")
        self.assertEqual(r.errors, [])
        self.assertEqual([s.text for s in r.sections], ["一。", "二。"])

    def test_comments_and_other_headings_are_ignored(self):
        r = parse_script("# タイトル\n## S01\n// メモ\n### 小見出し\n本文。\n")
        self.assertEqual(r.errors, [])
        self.assertEqual(r.sections[0].lines, ["本文。"])

    def test_crlf_and_bom_free_whitespace(self):
        r = parse_script("## S01\r\n  本文。  \r\n")
        self.assertEqual(r.sections[0].lines, ["本文。"])

    def test_no_scenes(self):
        r = parse_script("本文だけ。\n")
        self.assertTrue(any("より前に原稿" in e for e in r.errors))
        self.assertTrue(any("1つもありません" in e for e in r.errors))

    def test_text_before_first_scene(self):
        r = parse_script("前置き。\n## S01\n本文。\n")
        self.assertEqual(len(r.errors), 1)
        self.assertIn("1行目", r.errors[0])

    def test_malformed_heading(self):
        for heading in ("## S1", "## S001", "## s01", "# S01"):
            with self.subTest(heading=heading):
                r = parse_script(f"{heading}\n本文。\n")
                self.assertTrue(any("書式が違います" in e for e in r.errors), r.errors)

    def test_duplicate_scene(self):
        r = parse_script("## S01\n一。\n## S01\n二。\n")
        self.assertTrue(any("重複" in e for e in r.errors))

    def test_descending_scene_is_warning(self):
        r = parse_script("## S02\n一。\n## S01\n二。\n")
        self.assertEqual(r.errors, [])
        self.assertEqual(len(r.warnings), 1)

    def test_empty_scene(self):
        r = parse_script("## S01\n## S02\n本文。\n")
        self.assertTrue(any("S01 の原稿が空" in e for e in r.errors))

    def test_text_before_first_marker(self):
        r = parse_script("## S01\n前置き。\n[a] 一。\n[b] 二。\n")
        self.assertTrue(any("最初のマーカーより前" in e for e in r.errors))

    def test_marker_order(self):
        for body in ("[a] 一。\n[c] 二。", "[b] 一。\n[c] 二。", "[a] 一。\n[a] 二。"):
            with self.subTest(body=body):
                r = parse_script(f"## S01\n{body}\n")
                self.assertTrue(any("[a] から順に" in e for e in r.errors), r.errors)

    def test_empty_marker_section(self):
        r = parse_script("## S01\n[a] 一。\n[b]\n")
        self.assertTrue(any("S01[b] の原稿が空" in e for e in r.errors))

    def test_uppercase_marker(self):
        r = parse_script("## S01\n[A] 一。\n")
        self.assertTrue(any("小文字" in e for e in r.errors))

    def test_bracket_in_middle_is_text(self):
        r = parse_script("## S01\n画面の[a]ボタンを押します。\n")
        self.assertEqual(r.errors, [])
        self.assertIsNone(r.sections[0].sub)


if __name__ == "__main__":
    unittest.main()

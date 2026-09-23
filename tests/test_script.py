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


    def test_numbered_markers(self):
        r = parse_script("## S01\n[1] 一。\n[2] 二。\n")
        self.assertEqual(r.errors, [])
        self.assertEqual([s.key for s in r.sections], ["S01a", "S01b"])
        self.assertTrue(any("[1]〜[26]" in e for e in parse_script("## S01\n[0] 一。\n").errors))


STORYBOARD = """\
## S01
テロップ：ついに、想像を超えた
テロップ：iPhoneが来る。
効果音：K01
ついに、私たちの想像を超えたiPhoneがやって来ます。

## S02
テロップ：シーン全体
効果音：Ｋ０２ ＋1.5秒
[1] 一つ目。
テロップ：一つ目だけ
[2] 二つ目。
効果音: K01 +0.5
SE：K03
"""


class DirectiveTest(unittest.TestCase):
    def test_telop_and_sfx(self):
        r = parse_script(STORYBOARD)
        self.assertEqual(r.errors, [])
        s1, s2 = r.scenes
        # テロップ・効果音の行は読み上げ原稿に入らない
        self.assertEqual(s1.sections[0].text, "ついに、私たちの想像を超えたiPhoneがやって来ます。")
        self.assertEqual(s1.telops, ["ついに、想像を超えた", "iPhoneが来る。"])
        self.assertEqual(s1.sfx, [("K01", 0.0)])
        self.assertEqual(s2.telops, ["シーン全体"])
        self.assertEqual(s2.sfx, [("K02", 1.5)])
        self.assertEqual(s2.sections[0].telops, ["一つ目だけ"])
        self.assertEqual(s2.sections[1].sfx, [("K01", 0.5), ("K03", 0.0)])
        self.assertEqual(r.sfx_ids, ["K01", "K02", "K03"])

    def test_directive_after_text_in_unmarked_scene(self):
        r = parse_script("## S01\n一。\nテロップ：あと\n")
        self.assertEqual(r.sections[0].telops, ["あと"])
        self.assertEqual(r.sections[0].text, "一。")

    def test_bad_directives(self):
        r = parse_script("## S01\n一。\nテロップ：\n効果音：ピンポン\n")
        self.assertTrue(any("テロップの文字がありません" in e for e in r.errors), r.errors)
        self.assertTrue(any("効果音は「効果音：K01」" in e for e in r.errors), r.errors)

    def test_scene_with_only_directives_is_empty(self):
        r = parse_script("## S01\nテロップ：だけ\n")
        self.assertTrue(any("原稿が空" in e for e in r.errors))


if __name__ == "__main__":
    unittest.main()

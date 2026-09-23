import os
import shutil
import tempfile
import unittest

from core.checks import check_project
from core.media import find_audio, scan_media, scan_sfx
from core.report import build_report

SCRIPT = """\
## S01
一。
## S02
二。
## S03
[a] 三のA。
[b] 三のB。
"""
MEDIA = ["S01_opening.mp4", "S02_graph.png", "S03a_screen.mp4", "S03b_result.PNG"]


class FolderTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def make(self, script=SCRIPT, media=MEDIA, audio=("narration.wav",)):
        if script is not None:
            with open(os.path.join(self.dir, "script.md"), "w", encoding="utf-8") as f:
                f.write(script)
        for sub, names in (("media", media), ("audio", audio)):
            if names is None:
                continue
            os.makedirs(os.path.join(self.dir, sub), exist_ok=True)
            for name in names:
                open(os.path.join(self.dir, sub, name), "wb").close()
        return self.dir

    def errors_of(self, **kw):
        return check_project(self.make(**kw)).errors

    def assertError(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), f"{fragment!r} がエラーにない: {errors}")


class ScanMediaTest(FolderTestCase):
    def scan(self, names):
        self.make(media=names)
        return scan_media(os.path.join(self.dir, "media"))

    def test_valid_names(self):
        files, errors = self.scan(MEDIA + ["S04_x.MOV", "S05_y.jpeg", "S06_z.jpg"])
        self.assertEqual(errors, [])
        self.assertEqual([(f.key, f.kind) for f in files], [
            ("S01", "video"), ("S02", "image"), ("S03a", "video"), ("S03b", "image"),
            ("S04", "video"), ("S05", "image"), ("S06", "image")])

    def test_free_text_may_contain_underscore_and_japanese(self):
        files, errors = self.scan(["S01_画面_その1.mp4"])
        self.assertEqual(errors, [])
        self.assertEqual(files[0].key, "S01")

    def test_naming_violations(self):
        for name in ("S1_a.mp4", "S001_a.mp4", "s01_a.mp4", "S01a.mp4", "S01_.mp4", "S01A_a.mp4", "opening.mp4"):
            with self.subTest(name=name):
                shutil.rmtree(os.path.join(self.dir, "media"), ignore_errors=True)
                _, errors = self.scan([name])
                self.assertError(errors, "命名ルール違反")

    def test_storyboard_names(self):
        files, errors = self.scan(["M01.mp4", "M02_グラフ.png", "M03_1.mp4", "M03_2_結果.PNG", "m04_12.mov"])
        self.assertEqual(errors, [])
        self.assertEqual([f.key for f in files], ["S01", "S02", "S03a", "S03b", "S04l"])

    def test_storyboard_names_violations(self):
        for name in ("M1.mp4", "M01_27.mp4", "M01_0.mp4", "K01.mp4"):
            with self.subTest(name=name):
                shutil.rmtree(os.path.join(self.dir, "media"), ignore_errors=True)
                _, errors = self.scan([name])
                self.assertError(errors, "命名ルール違反")

    def test_unsupported_extension(self):
        _, errors = self.scan(["S01_a.gif"])
        self.assertError(errors, "対応していない拡張子")

    def test_mixed_suffix(self):
        _, errors = self.scan(["S03_a.mp4", "S03a_b.png"])
        self.assertError(errors, "混在")

    def test_duplicate(self):
        _, errors = self.scan(["S01_a.mp4", "S01_b.png"])
        self.assertError(errors, "複数あります")
        shutil.rmtree(os.path.join(self.dir, "media"))
        _, errors = self.scan(["S03a_a.mp4", "S03a_b.png"])
        self.assertError(errors, "複数あります")

    def test_ignores_system_files_and_subfolders(self):
        self.make(media=["S01_a.mp4", "Thumbs.db", "desktop.ini", ".hidden"])
        os.makedirs(os.path.join(self.dir, "media", "_freeze"))
        open(os.path.join(self.dir, "media", "_freeze", "S01_last.png"), "wb").close()
        files, errors = scan_media(os.path.join(self.dir, "media"))
        self.assertEqual(errors, [])
        self.assertEqual(len(files), 1)


class SfxTest(FolderTestCase):
    def make_se(self, names):
        os.makedirs(os.path.join(self.dir, "se"), exist_ok=True)
        for name in names:
            open(os.path.join(self.dir, "se", name), "wb").close()

    def test_scan(self):
        self.make_se(["K01.wav", "K02_ドン.mp3", "k03 pon.m4a"])
        found, errors = scan_sfx(os.path.join(self.dir, "se"))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(found), ["K01", "K02", "K03"])

    def test_scan_errors(self):
        self.make_se(["K01.wav", "K01_again.wav", "pon.wav", "K02.mp4"])
        _, errors = scan_sfx(os.path.join(self.dir, "se"))
        self.assertEqual(len(errors), 3, errors)

    def test_check_project(self):
        self.make_se(["K01_pon.wav", "K09_unused.wav"])
        check = check_project(self.make(script=SCRIPT.replace("一。", "一。\n効果音：K01\n効果音：K02")))
        self.assertError(check.errors, "効果音 K02 のファイルがありません")
        self.assertEqual(list(check.sfx), ["K01"])
        self.assertTrue(any("K09_unused.wav" in w for w in check.warnings))

    def test_storyboard_media_in_check(self):
        check = check_project(self.make(media=["M01.mp4", "M02.png", "M03_1.mp4", "M03_2.png"]))
        self.assertEqual(check.errors, [])
        os.remove(os.path.join(self.dir, "media", "M03_2.png"))
        errors = check_project(self.dir).errors
        self.assertError(errors, "S03[b] に対応する素材がありません（M03_2.mp4")


class FindAudioTest(FolderTestCase):
    def test_one(self):
        for name in ("n.wav", "n.MP3", "n.m4a"):
            with self.subTest(name=name):
                shutil.rmtree(os.path.join(self.dir, "audio"), ignore_errors=True)
                self.make(audio=[name, "memo.txt"])
                path, errors = find_audio(os.path.join(self.dir, "audio"))
                self.assertEqual(errors, [])
                self.assertEqual(os.path.basename(path), name)

    def test_none(self):
        self.make(audio=["memo.txt"])
        _, errors = find_audio(os.path.join(self.dir, "audio"))
        self.assertError(errors, "ありません")

    def test_two(self):
        self.make(audio=["a.wav", "b.mp3"])
        _, errors = find_audio(os.path.join(self.dir, "audio"))
        self.assertError(errors, "1本だけ")

    def test_missing_folder(self):
        _, errors = find_audio(os.path.join(self.dir, "audio"))
        self.assertError(errors, "audio フォルダがありません")


class CheckProjectTest(FolderTestCase):
    def test_ok(self):
        check = check_project(self.make())
        self.assertEqual(check.errors, [])
        self.assertEqual([(e.section.key, e.media.name) for e in check.entries], [
            ("S01", "S01_opening.mp4"), ("S02", "S02_graph.png"),
            ("S03a", "S03a_screen.mp4"), ("S03b", "S03b_result.PNG")])
        self.assertEqual(os.path.basename(check.audio), "narration.wav")

    def test_missing_script(self):
        self.assertError(self.errors_of(script=None), "script.md がありません")

    def test_shift_jis_script_is_warning(self):
        folder = self.make()
        with open(os.path.join(folder, "script.md"), "wb") as f:
            f.write("## S01\n一。\n## S02\n二。\n## S03\n[a] 三。\n[b] 四。\n".encode("cp932"))
        check = check_project(folder)
        self.assertEqual(check.errors, [])
        self.assertTrue(any("UTF-8" in w for w in check.warnings))

    def test_scene_without_media(self):
        errors = self.errors_of(media=["S01_a.mp4", "S03a_b.mp4", "S03b_c.png"])
        self.assertEqual(errors, ["台本の S02 に対応する素材がありません（M02.mp4 や S02_〜 のファイルが必要）"])

    def test_marker_without_media(self):
        errors = self.errors_of(media=["S01_a.mp4", "S02_b.png", "S03a_c.mp4"])
        self.assertEqual(errors, ["台本の S03[b] に対応する素材がありません（M03_2.mp4 や S03b_〜 のファイルが必要）"])

    def test_media_scene_not_in_script(self):
        errors = self.errors_of(media=MEDIA + ["S04_extra.mp4"])
        self.assertEqual(errors, ["素材 S04_extra.mp4 のシーン S04 が台本にありません"])

    def test_media_marker_not_in_script(self):
        errors = self.errors_of(media=MEDIA + ["S03c_extra.png"])
        self.assertEqual(errors, ["素材 S03c_extra.png に対応するマーカー [c] が台本の S03 にありません"])

    def test_script_has_markers_but_media_not_split(self):
        errors = self.errors_of(media=["S01_a.mp4", "S02_b.png", "S03_c.mp4"])
        self.assertEqual(len(errors), 1)
        self.assertIn("台本は [a] [b] … で分かれていますが", errors[0])

    def test_media_split_but_script_has_no_markers(self):
        script = "## S01\n一。\n## S02\n二。\n## S03\n三。\n"
        errors = self.errors_of(script=script)
        self.assertEqual(len(errors), 1)
        self.assertIn("台本に [a] [b] … のマーカーがありません", errors[0])

    def test_audio_errors_are_collected_with_others(self):
        errors = self.errors_of(media=["S01_a.mp4"], audio=[])
        self.assertError(errors, "音声ファイル")
        self.assertError(errors, "S02")

    def test_script_errors_skip_matching(self):
        errors = self.errors_of(script="## S1\n一。\n", media=["S01_a.mp4"])
        self.assertError(errors, "書式が違います")
        self.assertFalse(any("台本にありません" in e for e in errors))

    def test_report(self):
        check = check_project(self.make(media=["S01_a.mp4", "S02_b.png", "S03a_c.mp4"]))
        report = build_report(check)
        self.assertIn("## エラー（1件）", report)
        self.assertIn("S03[b]", report)

    def test_report_table(self):
        check = check_project(self.make())
        report = build_report(check)
        self.assertIn("| S03[a] | — | — | S03a_screen.mp4 |  |", report)
        # Windows のファイル名には使えないが、表の区切り文字は必ずエスケープする
        rows = [{"key": "S01", "start": 65.5, "duration": 1.25, "media": "a|b.mp4", "warnings": ["w1", "w2"]}]
        self.assertIn("| S01 | 1:05.50 | 0:01.25 | a\\|b.mp4 | w1 / w2 |", build_report(check, rows))


if __name__ == "__main__":
    unittest.main()

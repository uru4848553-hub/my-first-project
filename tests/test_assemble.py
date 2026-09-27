import os
import shutil
import tempfile
import unittest
from datetime import datetime

from core.assemble import assemble, auto_assign, safe_name, validate
from core.checks import check_project
from core.script import parse_script

SCRIPT = "## S01\n一。\n## S02\n二。\n## S03\n[a] 三。\n[b] 四。\n"


class AssembleTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.src = os.path.join(self.dir, "素材")
        os.makedirs(self.src)
        self.sections = parse_script(SCRIPT).sections

    def f(self, name, data=b"x"):
        path = os.path.join(self.src, name)
        with open(path, "wb") as fp:
            fp.write(data)
        return path

    def test_auto_assign_by_name_then_order(self):
        keys = [s.key for s in self.sections]
        paths = [self.f("b_graph.png"), self.f("S03b_result.jpg"), self.f("a_opening.mp4"), self.f("s03A-screen.mov")]
        result, left = auto_assign(keys, paths)
        self.assertEqual({k: os.path.basename(v) for k, v in result.items()},
                         {"S03b": "S03b_result.jpg", "S03a": "s03A-screen.mov",
                          "S01": "a_opening.mp4", "S02": "b_graph.png"})
        self.assertEqual(left, [])

    def test_auto_assign_storyboard_names(self):
        keys = [s.key for s in self.sections] + ["K01", "K02"]
        paths = [self.f("M03_2.png"), self.f("M01.mp4"), self.f("m03_1_画面.mov"), self.f("zz.png"),
                 self.f("K02_don.wav"), self.f("pon.mp3"), self.f("K01.mp4")]
        result, left = auto_assign(keys, paths)
        self.assertEqual({k: os.path.basename(v) for k, v in result.items()},
                         {"S01": "M01.mp4", "S03a": "m03_1_画面.mov", "S03b": "M03_2.png",
                          "K02": "K02_don.wav", "K01": "pon.mp3", "S02": "K01.mp4"})
        self.assertEqual([os.path.basename(p) for p in left], ["zz.png"])

    def test_auto_assign_keeps_existing_and_reports_leftovers(self):
        keys = [s.key for s in self.sections]
        existing = {"S01": self.f("keep.mp4")}
        result, left = auto_assign(keys, [self.f(f"{i}.png") for i in range(5)], existing)
        self.assertEqual(os.path.basename(result["S01"]), "keep.mp4")
        self.assertEqual([os.path.basename(p) for p in left], ["3.png", "4.png"])

    def test_validate(self):
        narration = self.f("n.mp3")
        materials = {"S01": self.f("a.mp4"), "S02": self.f("b.png"), "S03a": self.f("c.mov"), "S03b": self.f("d.jpg")}
        self.assertEqual(validate(self.sections, narration, materials), [])
        # 同じファイルを複数のシーンに使ってもよい
        self.assertEqual(validate(self.sections, narration, dict(materials, S02=materials["S01"])), [])

        del materials["S03b"]
        materials["S02"] = self.f("b.gif")
        problems = validate(self.sections, "", materials, bgm=self.f("bgm.txt"))
        text = "\n".join(problems)
        self.assertIn("BGM は wav / mp3 / m4a", text)
        self.assertIn("素材が選ばれていないシーンがあります: S03[b]", text)
        self.assertIn("S02 の素材は mp4", text)

    def test_without_narration(self):
        materials = {"S01": self.f("a.mp4"), "S02": self.f("b.png"), "S03a": self.f("c.mov"), "S03b": self.f("d.jpg")}
        self.assertEqual(validate(self.sections, "", materials), [])
        folder = assemble(self.dir, "動画", SCRIPT, "", materials, log=lambda m: None)
        self.assertFalse(os.path.exists(os.path.join(folder, "audio")))
        check = check_project(folder)
        self.assertEqual(check.errors, [])
        self.assertIsNone(check.audio)

    def test_validate_sfx(self):
        narration = self.f("n.mp3")
        materials = {"S01": self.f("a.mp4"), "S02": self.f("b.png"), "S03a": self.f("c.mov"), "S03b": self.f("d.jpg")}
        text = "\n".join(validate(self.sections, narration, dict(materials, K01=self.f("k.mp4")), sfx_ids=["K01", "K02"]))
        self.assertIn("効果音のファイルが選ばれていません: K02", text)
        self.assertIn("効果音 K01 は wav", text)

    def test_assemble_with_storyboard_names_and_sfx(self):
        script = "## S01\n効果音：K01\n一。\n## S02\n二。\n"
        materials = {"S01": self.f("M01.mp4"), "S02": self.f("S02_graph.png"), "K01": self.f("K01_pon.wav")}
        folder = assemble(self.dir, "動画", script, self.f("n.mp3"), materials, log=lambda m: None)
        self.assertEqual(sorted(os.listdir(os.path.join(folder, "media"))), ["S01_M01.mp4", "S02_graph.png"])
        self.assertEqual(os.listdir(os.path.join(folder, "se")), ["K01_pon.wav"])
        check = check_project(folder)
        self.assertEqual(check.errors, [])
        self.assertEqual(list(check.sfx), ["K01"])

    def test_safe_name(self):
        self.assertEqual(safe_name('動画:AI/副業?"'), "動画_AI_副業_")
        self.assertEqual(safe_name("  "), "動画")

    def test_assemble_makes_a_valid_folder(self):
        narration = self.f("ElevenLabs_2026 - Voice, v3.mp3")
        bgm = self.f("bgm.wav")
        materials = {"S01": self.f("opening.mp4"), "S02": self.f("graph.png"),
                     "S03a": self.f("screen.mov"), "S03b": self.f("opening.mp4")}
        folder = assemble(self.dir, "動画:テスト", SCRIPT, narration, materials, bgm, log=lambda m: None,
                          now=datetime(2026, 9, 27, 10, 30, 5))
        self.assertEqual(folder, os.path.join(self.dir, "動画_テスト", "20260927_103005"))
        self.assertEqual(sorted(os.listdir(os.path.join(folder, "media"))),
                         ["S01_opening.mp4", "S02_graph.png", "S03a_screen.mov", "S03b_opening.mp4"])
        self.assertEqual(os.listdir(os.path.join(folder, "audio")), ["ElevenLabs_2026 - Voice, v3.mp3"])
        self.assertEqual(os.listdir(os.path.join(folder, "bgm")), ["bgm.wav"])

        check = check_project(folder)
        self.assertEqual(check.errors, [])
        self.assertEqual([e.section.key for e in check.entries], ["S01", "S02", "S03a", "S03b"])
        self.assertEqual(os.path.basename(check.bgm), "bgm.wav")

    def test_assemble_again_keeps_previous_runs(self):
        narration = self.f("n.mp3")
        materials = {k: self.f(f"{k}.mp4") for k in ("S01", "S02", "S03a", "S03b")}
        now = datetime(2026, 9, 27, 10, 30, 5)
        first = assemble(self.dir, "動画", SCRIPT, narration, materials, self.f("bgm.mp3"), log=lambda m: None, now=now)
        os.makedirs(os.path.join(first, "media", "_stills"))
        before = sorted(os.listdir(os.path.join(first, "media")))
        # 2回目（同じ時刻でも別のフォルダ）：台本を変え、S02 を差し替え、BGM を外す。S01 は1回目のフォルダ内のファイルを選ぶ
        script2 = "## S01\n一。\n## S02\n二。\n"
        inside = os.path.join(first, "media", "S01_S01.mp4")
        second = assemble(self.dir, "動画", script2, narration, {"S01": inside, "S02": self.f("new.png", b"new")},
                          None, log=lambda m: None, now=now)
        self.assertEqual(second, first + "_2")
        self.assertEqual(sorted(os.listdir(os.path.join(second, "media"))), ["S01_S01.mp4", "S02_new.png"])
        self.assertFalse(os.path.exists(os.path.join(second, "bgm")))
        self.assertEqual(check_project(second).errors, [])
        # 1回目のフォルダはそのまま（消えない・上書きされない）
        self.assertEqual(sorted(os.listdir(os.path.join(first, "media"))), before)
        self.assertEqual(os.listdir(os.path.join(first, "bgm")), ["bgm.mp3"])
        with open(os.path.join(first, "script.md"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), SCRIPT)
        self.assertEqual(check_project(first).errors, [])

if __name__ == "__main__":
    unittest.main()

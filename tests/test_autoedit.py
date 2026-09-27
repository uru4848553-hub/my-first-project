"""autoedit.py の通しテスト。Whisper だけ偽物に差し替え、それ以外（ffprobe・ffmpeg を含む）は本物を使う。"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from unittest import mock

import autoedit
from tests.test_fit import HAS_FFMPEG, make_video

SCRIPT = """\
## S01
こんにちは、ヒロキです。
## S02
まず結論から。
## S03
[a] 画面を見てください。
[b] 結果です。
"""


@dataclass
class W:
    word: str
    start: float
    end: float
    probability: float = 0.9


def fake_words(starts):
    """各セクションの原稿を1語として、指定の開始時刻を振る"""
    texts = ["こんにちは、ヒロキです。", "まず結論から。", "画面を見てください。", "結果です。"]
    return [W(t, s, s + 0.8) for t, s in zip(texts, starts)]


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg / ffprobe がない")
class AutoeditTest(unittest.TestCase):
    def setUp(self):
        self.dir = os.path.join(tempfile.mkdtemp(), "動画_テスト")
        self.addCleanup(shutil.rmtree, os.path.dirname(self.dir))
        media = os.path.join(self.dir, "media")
        audio = os.path.join(self.dir, "audio")
        os.makedirs(media)
        os.makedirs(audio)
        with open(os.path.join(self.dir, "script.md"), "w", encoding="utf-8") as f:
            f.write(SCRIPT)
        make_video(os.path.join(media, "S01_opening.mp4"), ["red"], [5])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=64x64:d=1",
                        "-frames:v", "1", os.path.join(media, "S02_graph.png")], check=True)
        make_video(os.path.join(media, "S03a_screen.mp4"), ["red", "blue"], [0.5, 0.5])   # 1秒しかない
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1",
                        "-frames:v", "1", os.path.join(media, "S03b_result.jpg")], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=12",
                        os.path.join(audio, "narration.wav")], check=True)

    def run_autoedit(self, starts):
        out = io.StringIO()
        with mock.patch("core.align.load_model", return_value=None), \
                mock.patch("core.align.run_alignment", return_value=fake_words(starts)), \
                contextlib.redirect_stdout(out):
            code = autoedit.main([self.dir, "--no-resolve"])
        with open(os.path.join(self.dir, "output", "plan.json"), encoding="utf-8") as f:
            return code, json.load(f), out.getvalue()

    def test_full_run(self):
        code, plan, out = self.run_autoedit([0.3, 3.0, 5.0, 9.0])
        self.assertEqual(code, 0, out)
        self.assertEqual(plan["errors"], [])
        self.assertEqual(plan["total_frames"], 360)
        clips = [(s["label"], c["type"], c["record_frame"], c["frames"]) for s in plan["sections"] for c in s["clips"]]
        self.assertEqual(clips, [
            ("S01", "video", 0, 90),        # 5秒の動画を3秒で切る
            ("S02", "image", 90, 60),
            ("S03[a]", "video", 150, 30),   # 1秒の動画
            ("S03[a]", "freeze", 180, 90),  # 残り3秒を最終フレームで埋める
            ("S03[b]", "image", 270, 90),   # 音声の終端（12秒）まで
        ])
        # 隙間も重なりもない
        ends = [c["record_frame"] + c["frames"] for s in plan["sections"] for c in s["clips"]]
        starts = [c["record_frame"] for s in plan["sections"] for c in s["clips"]]
        self.assertEqual(ends[:-1], starts[1:])
        self.assertEqual(ends[-1], plan["total_frames"])
        freeze = plan["sections"][2]["clips"][1]["path"]
        self.assertTrue(os.path.isfile(freeze))
        self.assertTrue(os.path.basename(freeze).startswith("S03a_screen_last_"))

        with open(os.path.join(self.dir, "output", "report.md"), encoding="utf-8") as f:
            report = f.read()
        self.assertIn("| S03[a] | 0:05.00 | 0:04.00 | S03a_screen.mp4 | 静止フレームで埋めた尺が3.0秒（素材不足の可能性） |", report)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "output", "alignment.json")))

    def test_fake_align(self):
        out = io.StringIO()
        with mock.patch("core.align.load_model") as load, contextlib.redirect_stdout(out):
            code = autoedit.main([self.dir, "--fake-align", "--no-resolve"])
        self.assertEqual(code, 0, out.getvalue())
        load.assert_not_called()
        with open(os.path.join(self.dir, "output", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        self.assertTrue(plan["fake_align"])
        self.assertEqual(plan["sections"][-1]["clips"][-1]["record_frame"] + plan["sections"][-1]["clips"][-1]["frames"],
                         plan["total_frames"])
        self.assertIn("仮のアライメント", out.getvalue())

    def test_title_run_and_text_telops(self):
        with open(os.path.join(self.dir, "script.md"), "a", encoding="utf-8") as f:
            f.write("テロップ：結果です\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = autoedit.main([self.dir, "--fake-align", "--no-resolve", "--title", "iPhone未来予測", "--telop-bg", "on"])
        self.assertEqual(code, 0, out.getvalue())
        with open(os.path.join(self.dir, "output", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        self.assertEqual((plan["name"], plan["run"]), ("iPhone未来予測", "動画_テスト"))
        self.assertEqual(plan["telop_mode"], "text")
        self.assertTrue(plan["telop_background"])
        self.assertEqual(plan["telops"][0]["lines"], ["結果です"])
        self.assertNotIn("path", plan["telops"][0])
        self.assertFalse(os.path.exists(os.path.join(self.dir, "media", "_telop")))   # テキストなので動画は作らない

    def test_rerun_keeps_previous_output(self):
        for _ in range(2):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(autoedit.main([self.dir, "--fake-align", "--no-resolve"]), 0)
        past = os.path.join(self.dir, "output", "過去")
        runs = os.listdir(past)
        self.assertEqual(len(runs), 1)
        self.assertEqual(sorted(os.listdir(os.path.join(past, runs[0]))), ["plan.json", "report.md"])
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "output", "plan.json")))

    def test_without_narration_uses_media_lengths(self):
        shutil.rmtree(os.path.join(self.dir, "audio"))
        out = io.StringIO()
        with mock.patch("core.align.load_model") as load, contextlib.redirect_stdout(out):
            code = autoedit.main([self.dir, "--no-resolve"])
        self.assertEqual(code, 0, out.getvalue())
        load.assert_not_called()                     # 読み上げの解析はしない
        with open(os.path.join(self.dir, "output", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        self.assertIsNone(plan["audio"])
        self.assertTrue(plan["no_narration"])
        # 動画はその長さ（5秒・1秒）、画像は3秒
        self.assertEqual([(s["label"], s["start_frame"], s["duration_frames"]) for s in plan["sections"]],
                         [("S01", 0, 150), ("S02", 150, 90), ("S03[a]", 240, 30), ("S03[b]", 270, 90)])
        self.assertEqual(plan["total_frames"], 360)
        self.assertEqual([s["freeze_frames"] for s in plan["sections"]], [0, 0, 0, 0])
        self.assertEqual([s["warnings"] for s in plan["sections"]], [[], [], [], []])
        with open(os.path.join(self.dir, "output", "report.md"), encoding="utf-8") as f:
            self.assertIn("ナレーション: なし", f.read())

    def test_from_plan_without_plan(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(autoedit.main([self.dir, "--from-plan"]), 1)
        self.assertIn("plan.json がありません", out.getvalue())

    def test_alignment_error_stops_before_fit(self):
        code, plan, out = self.run_autoedit([0.0, 6.0, 5.0, 9.0])
        self.assertEqual(code, 1)
        self.assertTrue(plan["errors"])
        self.assertNotIn("clips", plan["sections"][0])
        self.assertFalse(os.path.exists(os.path.join(self.dir, "media", "_freeze")))


if __name__ == "__main__":
    unittest.main()

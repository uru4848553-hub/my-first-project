import json
import os
import shutil
import tempfile
import unittest

from core.align import SectionTiming
from core.checks import check_project
from core.config import DEFAULTS, ConfigError, load_config
from core.plan import build_plan, report_rows, to_frames, write_plan
from core.report import build_report

SCRIPT = """\
## S01
こんにちは、ヒロキです。今日はAI副業の始め方を話します。
## S02
まず結論から。
## S03
[a] 画面を見てください。
[b] 結果です。
"""
MEDIA = ["S01_opening.mp4", "S02_graph.png", "S03a_screen.mp4", "S03b_result.png"]


def timings(*starts, confidence=0.9):
    return [SectionTiming(start=s, confidence=confidence, word_count=5) for s in starts]


class ToFramesTest(unittest.TestCase):
    def test_no_gap_no_overlap(self):
        spans, total = to_frames([0.0, 2.016, 5.5, 7.49], 10.0, 30)
        self.assertEqual(spans, [(0, 60), (60, 165), (165, 225), (225, 300)])
        self.assertEqual(total, 300)
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertEqual(end, start)

    def test_first_section_starts_at_zero(self):
        spans, _ = to_frames([0.7, 2.0], 4.0, 30)
        self.assertEqual(spans[0][0], 0)

    def test_last_section_covers_audio_end(self):
        # 音声の最後の端数フレームも覆う（切り上げ）
        _, total = to_frames([0.0], 10.01, 30)
        self.assertEqual(total, 301)
        _, total = to_frames([0.0], 10.0, 30)
        self.assertEqual(total, 300)


class BuildPlanTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        with open(os.path.join(self.dir, "script.md"), "w", encoding="utf-8") as f:
            f.write(SCRIPT)
        for sub, names in (("media", MEDIA), ("audio", ["narration.wav"])):
            os.makedirs(os.path.join(self.dir, sub))
            for n in names:
                open(os.path.join(self.dir, sub, n), "wb").close()
        self.check = check_project(self.dir)
        self.assertEqual(self.check.errors, [])
        self.config = dict(DEFAULTS)

    def build(self, ts, duration=12.0, ratio=1.0):
        return build_plan(self.check, ts, duration, self.config, ratio)

    def test_plan(self):
        plan, errors, warnings = self.build(timings(0.0, 4.0, 6.5, 9.0))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(plan["fps"], 30)
        self.assertEqual((plan["width"], plan["height"]), (1080, 1920))
        self.assertEqual(plan["total_frames"], 360)
        secs = plan["sections"]
        self.assertEqual([s["key"] for s in secs], ["S01", "S02", "S03a", "S03b"])
        self.assertEqual([(s["start_frame"], s["end_frame"]) for s in secs],
                         [(0, 120), (120, 195), (195, 270), (270, 360)])
        self.assertEqual([s["duration_frames"] for s in secs], [120, 75, 75, 90])
        self.assertEqual(secs[0]["media"]["kind"], "video")
        self.assertEqual(secs[1]["media"]["kind"], "image")

    def test_markers_only_at_scene_start(self):
        plan, _, _ = self.build(timings(0.0, 4.0, 6.5, 9.0))
        markers = [s["marker"] for s in plan["sections"]]
        self.assertEqual(markers[0], {"name": "S01", "note": "こんにちは、ヒロキです。今日はAI副業の"})
        self.assertEqual(len(markers[0]["note"]), 20)
        self.assertEqual(markers[1], {"name": "S02", "note": "まず結論から。"})
        # S03 のメモは [a][b] をまとめたシーン原稿の冒頭
        self.assertEqual(markers[2], {"name": "S03", "note": "画面を見てください。結果です。"})
        self.assertIsNone(markers[3])

    def test_short_section_warning(self):
        _, errors, warnings = self.build(timings(0.0, 4.0, 4.5, 9.0))
        self.assertEqual(errors, [])
        self.assertTrue(any("S02: 尺が1秒未満" in w for w in warnings), warnings)

    def test_low_confidence_warning(self):
        ts = timings(0.0, 4.0, 6.5, 9.0)
        ts[2].confidence = 0.2
        ts[3].confidence = None
        _, _, warnings = self.build(ts)
        self.assertTrue(any(w.startswith("S03[a]: アライメント信頼度が低い") for w in warnings), warnings)
        self.assertTrue(any(w.startswith("S03[b]: 台本の文字と対応する単語がない") for w in warnings), warnings)

    def test_low_match_ratio_warning(self):
        _, _, warnings = self.build(timings(0.0, 4.0, 6.5, 9.0), ratio=0.7)
        self.assertTrue(any("一致度" in w for w in warnings))

    def test_out_of_order_is_error(self):
        _, errors, _ = self.build(timings(0.0, 6.0, 5.0, 9.0))
        self.assertTrue(any("S03[a] の開始時刻" in e for e in errors), errors)

    def test_zero_length_is_error(self):
        plan, errors, _ = self.build(timings(0.0, 4.0, 4.01, 9.0))
        self.assertTrue(any("S02 の尺が0フレーム" in e for e in errors), errors)
        self.assertEqual(plan["errors"], errors)

    def test_start_after_audio_end_is_error(self):
        _, errors, _ = self.build(timings(0.0, 4.0, 6.5, 13.0))
        self.assertTrue(any("音声の長さ" in e for e in errors), errors)

    def test_bgm(self):
        self.assertIsNone(self.build(timings(0.0, 4.0, 6.5, 9.0))[0]["bgm"])
        bgm = os.path.join(self.dir, "bgm", "bgm.mp3")
        os.makedirs(os.path.dirname(bgm))
        open(bgm, "wb").close()
        self.check = check_project(self.dir)
        plan, _, warnings = build_plan(self.check, timings(0.0, 4.0, 6.5, 9.0), 12.0, self.config, 1.0, bgm_duration=60.0)
        self.assertEqual(plan["bgm"]["frames"], 360)   # ナレーションの終わりまで
        self.assertEqual(warnings, [])
        plan, _, warnings = build_plan(self.check, timings(0.0, 4.0, 6.5, 9.0), 12.0, self.config, 1.0, bgm_duration=5.0)
        self.assertEqual(plan["bgm"]["frames"], 150)
        self.assertTrue(any("BGM" in w and "短い" in w for w in warnings))

    def test_write_plan_and_report(self):
        plan, _, _ = self.build(timings(0.0, 4.0, 6.5, 9.0))
        path = write_plan(plan, self.dir)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["sections"][3]["label"], "S03[b]")
        report = build_report(self.check, report_rows(plan))
        self.assertIn("| S02 | 0:04.00 | 0:02.50 | S02_graph.png |  |", report)


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.path = os.path.join(self.dir, "config.json")

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_defaults_are_merged(self):
        self.write('{"fps": 60}')
        config = load_config(self.path)
        self.assertEqual(config["fps"], 60)
        self.assertEqual(config["sizing"], "fit")

    def test_repo_config(self):
        self.assertEqual(load_config()["fps"], 30)

    def test_invalid(self):
        for text in ('{"fps": 0}', '{"sizing": "stretch"}', '{"width": "1080"}', '{broken'):
            with self.subTest(text=text):
                self.write(text)
                with self.assertRaises(ConfigError):
                    load_config(self.path)


if __name__ == "__main__":
    unittest.main()

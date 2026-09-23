import os
import shutil
import subprocess
import tempfile
import unittest

from core.ffmpeg import extract_last_frame, probe_video
from core.fit import apply_fit, freeze_path_for, section_clips, video_frames

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def section(kind, start=90, frames=120, path="/m/S01_a.mp4"):
    return {"label": "S01", "start_frame": start, "duration_frames": frames, "warnings": [],
            "media": {"kind": kind, "path": path, "name": os.path.basename(path)}}


class SectionClipsTest(unittest.TestCase):
    def test_image_uses_whole_section(self):
        clips, freeze = section_clips(section("image", path="/m/S02_g.png"), 30)
        self.assertEqual(clips, [{"type": "image", "path": "/m/S02_g.png", "record_frame": 90, "frames": 120}])
        self.assertEqual(freeze, 0)

    def test_long_video_is_cut(self):
        clips, freeze = section_clips(section("video"), 30, available_frames=300)
        self.assertEqual(clips, [{"type": "video", "path": "/m/S01_a.mp4", "record_frame": 90, "frames": 120,
                                  "source_in_sec": 0.0, "source_out_sec": 4.0}])
        self.assertEqual(freeze, 0)

    def test_exact_length_video(self):
        clips, freeze = section_clips(section("video"), 30, available_frames=120)
        self.assertEqual(len(clips), 1)
        self.assertEqual(freeze, 0)

    def test_short_video_is_followed_by_freeze(self):
        clips, freeze = section_clips(section("video"), 30, available_frames=45, freeze_path="/m/_freeze/x.png")
        self.assertEqual(freeze, 75)
        self.assertEqual(clips[0]["frames"], 45)
        self.assertEqual(clips[0]["source_out_sec"], 1.5)
        self.assertEqual(clips[1], {"type": "freeze", "path": "/m/_freeze/x.png", "record_frame": 135, "frames": 75})
        # 隙間なく並ぶ
        self.assertEqual(clips[0]["record_frame"] + clips[0]["frames"], clips[1]["record_frame"])
        self.assertEqual(clips[1]["record_frame"] + clips[1]["frames"], 90 + 120)

    def test_video_frames(self):
        self.assertEqual(video_frames(2.0, 30), 60)
        self.assertEqual(video_frames(2.033333, 30), 60)
        self.assertEqual(video_frames(2.0333334, 30), 61)
        self.assertEqual(video_frames(1.001, 30), 30)

    def test_freeze_path(self):
        self.assertEqual(freeze_path_for(os.path.join("m", "S03a_screen.mp4")),
                         os.path.join("m", "_freeze", "S03a_screen_last.png"))


def make_video(path, colors, seconds, fps=30, size="64x64"):
    """色ごとに seconds 秒ずつ並べた動画を作る（最後の色が最終フレーム）"""
    inputs = []
    for c, d in zip(colors, seconds):
        inputs += ["-f", "lavfi", "-i", f"color=c={c}:s={size}:r={fps}:d={d}"]
    n = len(colors)
    graph = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p[v]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "[v]", path], check=True)


def pixel(png):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-f", "rawvideo", "-pix_fmt", "rgb24", "-frames:v", "1", "-"],
                         capture_output=True, check=True).stdout
    return tuple(out[:3])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg / ffprobe がない")
class FFmpegTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def test_probe_video(self):
        path = os.path.join(self.dir, "S01_a.mp4")
        make_video(path, ["red"], [2], size="1920x1080")
        info = probe_video(path)
        self.assertAlmostEqual(info["duration"], 2.0, delta=0.05)
        self.assertAlmostEqual(info["fps"], 30.0)
        self.assertEqual((info["width"], info["height"]), (1920, 1080))

    def test_extract_last_frame(self):
        for secs in ([1.5, 0.5], [0.2, 0.1]):   # 1秒より短い動画でも最終フレームを取れる
            with self.subTest(secs=secs):
                path = os.path.join(self.dir, "v.mp4")
                make_video(path, ["red", "blue"], secs)
                png = extract_last_frame(path, os.path.join(self.dir, "last.png"))
                r, g, b = pixel(png)
                self.assertGreater(b, 200)
                self.assertLess(r, 60)

    def test_apply_fit(self):
        media = os.path.join(self.dir, "media")
        os.makedirs(media)
        short = os.path.join(media, "S01_short.mp4")
        long_ = os.path.join(media, "S02_long.mov")
        image = os.path.join(media, "S03_still.png")
        make_video(short, ["red", "green"], [0.5, 0.5])      # 1秒
        make_video(long_, ["red"], [5])                       # 5秒
        open(image, "wb").close()
        plan = {"fps": 30, "errors": [], "sections": [
            section("video", 0, 105, short),     # 3.5秒 → 動画1秒＋静止2.5秒（警告）
            section("video", 105, 60, long_),    # 2秒 → 動画を2秒で切る
            section("image", 165, 45, image),
        ]}
        plan["sections"][0]["label"] = "S01"
        plan["sections"][1]["label"] = "S02"
        plan["sections"][2]["label"] = "S03"

        errors, warnings = apply_fit(plan, log=lambda m: None)
        self.assertEqual(errors, [])
        s1, s2, s3 = plan["sections"]

        self.assertEqual([(c["type"], c["record_frame"], c["frames"]) for c in s1["clips"]],
                         [("video", 0, 30), ("freeze", 30, 75)])
        freeze_png = s1["clips"][1]["path"]
        self.assertEqual(freeze_png, os.path.join(media, "_freeze", "S01_short_last.png"))
        self.assertGreater(pixel(freeze_png)[1], 100)   # 最終フレーム＝緑
        self.assertEqual(s1["freeze_frames"], 75)
        self.assertEqual(warnings, ["S01: 静止フレームで埋めた尺が2.5秒（素材不足の可能性）"])
        self.assertEqual(s1["warnings"], ["静止フレームで埋めた尺が2.5秒（素材不足の可能性）"])
        self.assertAlmostEqual(s1["media"]["duration_sec"], 1.0, delta=0.05)

        self.assertEqual([(c["type"], c["frames"], c["source_out_sec"]) for c in s2["clips"]], [("video", 60, 2.0)])
        self.assertEqual(s2["freeze_frames"], 0)
        self.assertFalse(os.path.exists(freeze_path_for(long_)))   # 足りている動画の静止画は作らない

        self.assertEqual(s3["clips"], [{"type": "image", "path": image, "record_frame": 165, "frames": 45}])

        # 動画を差し替えて再実行すると、静止画も新しい動画の最終フレームになる
        make_video(short, ["red", "blue"], [0.5, 0.5])
        apply_fit({"fps": 30, "errors": [], "sections": [dict(section("video", 0, 105, short), label="S01")]},
                  log=lambda m: None)
        self.assertGreater(pixel(freeze_png)[2], 200)   # 青

    def test_broken_video_is_error(self):
        path = os.path.join(self.dir, "S01_broken.mp4")
        with open(path, "wb") as f:
            f.write(b"not a video")
        plan = {"fps": 30, "errors": [], "sections": [section("video", 0, 60, path)]}
        errors, _ = apply_fit(plan, log=lambda m: None)
        self.assertEqual(len(errors), 1)
        self.assertIn("動画を読めません", errors[0])
        self.assertEqual(plan["errors"], errors)


if __name__ == "__main__":
    unittest.main()

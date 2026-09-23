import os
import shutil
import subprocess
import tempfile
import unittest

from core.ffmpeg import extract_last_frame, probe_video
from core.fit import apply_fit, freeze_dir_for, section_clips, video_frames

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

    def test_freeze_dir(self):
        self.assertEqual(freeze_dir_for(os.path.join("m", "S03a_screen.mp4")), os.path.join("m", "_freeze"))


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
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=magenta:s=101x75,format=rgb24",
                        "-frames:v", "1", image], check=True)   # 奇数サイズの画像
        plan = {"fps": 30, "errors": [], "sections": [
            dict(section("video", 0, 105, short), label="S01"),     # 3.5秒 → 動画1秒＋静止2.5秒（警告）
            dict(section("video", 105, 60, long_), label="S02"),    # 2秒 → 動画を2秒で切る
            dict(section("image", 165, 45, image), label="S03"),
        ]}

        errors, warnings = apply_fit(plan, log=lambda m: None)
        self.assertEqual(errors, [])
        s1, s2, s3 = plan["sections"]

        self.assertEqual([(c["type"], c["record_frame"], c["frames"]) for c in s1["clips"]],
                         [("video", 0, 30), ("freeze", 30, 75)])
        freeze = s1["clips"][1]
        # 最終フレームの PNG と、それを 75フレーム続けた動画
        self.assertEqual(os.path.dirname(freeze["image"]), os.path.join(media, "_freeze"))
        self.assertRegex(os.path.basename(freeze["image"]), r"^S01_short_last_[0-9a-f]{8}\.png$")
        self.assertGreater(pixel(freeze["image"])[1], 100)   # 最終フレーム＝緑
        self.assertRegex(os.path.basename(freeze["path"]), r"^S01_short_last_[0-9a-f]{8}_75f\.mp4$")
        info = probe_video(freeze["path"])
        self.assertAlmostEqual(info["duration"] * 30, 75, delta=0.5)
        self.assertEqual(info["fps"], 30.0)
        self.assertGreater(pixel(freeze["path"])[1], 100)
        self.assertEqual(s1["freeze_frames"], 75)
        self.assertEqual(warnings, ["S01: 静止フレームで埋めた尺が2.5秒（素材不足の可能性）"])
        self.assertEqual(s1["warnings"], ["静止フレームで埋めた尺が2.5秒（素材不足の可能性）"])
        self.assertAlmostEqual(s1["media"]["duration_sec"], 1.0, delta=0.05)

        self.assertEqual([(c["type"], c["frames"], c["source_out_sec"]) for c in s2["clips"]], [("video", 60, 2.0)])
        self.assertEqual(s2["freeze_frames"], 0)
        # 足りている動画の静止画は作らない。作業用の一時ファイルも残らない
        self.assertEqual(sorted(os.listdir(os.path.join(media, "_freeze"))),
                         sorted([os.path.basename(freeze["image"]), os.path.basename(freeze["path"])]))

        # 素材の画像は media/_stills/ に 45フレームの動画として作る。奇数サイズは偶数にする
        clip = s3["clips"][0]
        self.assertEqual((clip["type"], clip["record_frame"], clip["frames"], clip["image"]), ("image", 165, 45, image))
        self.assertEqual(os.path.dirname(clip["path"]), os.path.join(media, "_stills"))
        info = probe_video(clip["path"])
        self.assertAlmostEqual(info["duration"] * 30, 45, delta=0.5)
        self.assertEqual((info["width"], info["height"]), (102, 76))
        r, g, b = pixel(clip["path"])
        self.assertGreater(r, 200)
        self.assertGreater(b, 200)
        self.assertLess(g, 60)

        # 同じ素材・同じ長さで再実行すると、同じファイルを使い回す（作り直さない）
        mtime = os.path.getmtime(clip["path"])
        again = {"fps": 30, "errors": [], "sections": [dict(section("video", 0, 105, short), label="S01"),
                                                       dict(section("image", 165, 45, image), label="S03")]}
        apply_fit(again, log=lambda m: None)
        self.assertEqual(again["sections"][0]["clips"][1]["path"], freeze["path"])
        self.assertEqual(again["sections"][1]["clips"][0]["path"], clip["path"])
        self.assertEqual(os.path.getmtime(clip["path"]), mtime)

        # 動画を差し替えると別名の新しい静止画になり、古い静止画は上書きしない
        make_video(short, ["red", "blue"], [0.5, 0.5])
        again = {"fps": 30, "errors": [], "sections": [dict(section("video", 0, 105, short), label="S01")]}
        apply_fit(again, log=lambda m: None)
        new = again["sections"][0]["clips"][1]
        self.assertNotEqual(new["image"], freeze["image"])
        self.assertNotEqual(new["path"], freeze["path"])
        self.assertGreater(pixel(new["path"])[2], 200)        # 青
        self.assertGreater(pixel(freeze["path"])[1], 100)     # 古い方は緑のまま

    def test_broken_image_is_error(self):
        image = os.path.join(self.dir, "S01_broken.png")
        with open(image, "wb") as f:
            f.write(b"not an image")
        plan = {"fps": 30, "errors": [], "sections": [section("image", 0, 60, image)]}
        errors, _ = apply_fit(plan, log=lambda m: None)
        self.assertEqual(len(errors), 1)
        self.assertIn("静止画を動画にできません", errors[0])
        self.assertNotIn("clips", plan["sections"][0])

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

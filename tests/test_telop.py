"""テロップの画像・動画づくりのテスト（ffmpeg と Pillow を実際に使う）"""
import os
import shutil
import tempfile
import unittest

from core.config import DEFAULTS
from core.ffmpeg import probe_video
from core.telop import TelopError, apply_telops, find_font, wrap

try:
    import PIL  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class FakeFont:
    def getlength(self, text):
        return len(text) * 10


class WrapTest(unittest.TestCase):
    def test_wrap(self):
        self.assertEqual(wrap("あいうえおかきくけこ", FakeFont(), 40), ["あいうえ", "おかきく", "けこ"])

    def test_punctuation_stays_on_previous_line(self):
        self.assertEqual(wrap("あいうえ。お", FakeFont(), 40), ["あいうえ。", "お"])


@unittest.skipUnless(HAS_PIL, "Pillow が入っていません（run.bat -m pip install pillow）")
@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg がありません")
class ApplyTelopsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.config = dict(DEFAULTS, width=360, height=640, telop_size=40)
        try:
            find_font(self.config)
        except TelopError:
            self.skipTest("日本語フォントがありません")

    def plan(self):
        return {"folder": self.dir, "fps": 30, "errors": [], "telops": [
            {"label": "S03[a]", "lines": ["ついに、想像を超えたiPhoneが来る。"], "record_frame": 0, "frames": 15, "lane": 0}]}

    def test_png_and_video(self):
        plan = self.plan()
        self.assertEqual(apply_telops(plan, self.config, log=lambda m: None), [])
        t = plan["telops"][0]
        self.assertTrue(t["path"].endswith("_15f.mov"))
        self.assertIn(os.path.join("media", "_telop", "S03a_"), t["path"])
        from PIL import Image
        with Image.open(t["image"]) as im:
            self.assertEqual((im.size, im.mode), ((360, 640), "RGBA"))
            self.assertEqual(im.getpixel((0, 0))[3], 0)            # 文字のない所は透明
            self.assertGreater(im.getchannel("A").getextrema()[1], 0)
        info = probe_video(t["path"])
        self.assertEqual((info["width"], info["height"]), (360, 640))
        self.assertAlmostEqual(info["duration"], 0.5, places=2)

        # 同じ文字・同じ長さなら作り直さない
        mtime = os.path.getmtime(t["path"])
        plan2 = self.plan()
        apply_telops(plan2, self.config, log=lambda m: None)
        self.assertEqual(plan2["telops"][0]["path"], t["path"])
        self.assertEqual(os.path.getmtime(t["path"]), mtime)

    def test_bad_font_is_error(self):
        plan = self.plan()
        errors = apply_telops(plan, dict(self.config, telop_font="C:/nothing.ttf"), log=lambda m: None)
        self.assertTrue(errors and "telop_font" in errors[0])
        self.assertEqual(plan["errors"], errors)


if __name__ == "__main__":
    unittest.main()

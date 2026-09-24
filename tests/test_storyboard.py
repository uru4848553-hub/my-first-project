"""絵コンテ画像 → 台本テキストのテスト（Claude API は偽物に差し替える）"""
import json
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace

from core.storyboard import StoryboardError, convert

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SCRIPT = "## S01\n// 動画：M01\nテロップ：ついに\nついに来ます。\n"


class FakeMessages:
    def __init__(self, text, stop_reason="end_turn"):
        self.text, self.stop_reason, self.calls = text, stop_reason, []

    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(stop_reason=self.stop_reason,
                               content=[SimpleNamespace(type="text", text=self.text)])


def fake_client(text, stop_reason="end_turn"):
    messages = FakeMessages(text, stop_reason)
    return SimpleNamespace(beta=SimpleNamespace(messages=messages)), messages


@unittest.skipUnless(HAS_PIL, "Pillow が入っていません")
class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.png = os.path.join(self.dir, "絵コンテ.png")
        Image.new("RGB", (3000, 1500), "white").save(self.png)

    def test_convert(self):
        client, messages = fake_client(json.dumps({"script": SCRIPT, "corrections": ["S01：直した"]}))
        script, corrections, problems = convert([self.png, self.png], client=client)
        self.assertEqual(script, SCRIPT)
        self.assertEqual(corrections, ["S01：直した"])
        self.assertEqual(problems, [])
        call = messages.calls[0]
        self.assertEqual(call["model"], "claude-opus-5")
        self.assertEqual(call["output_config"]["format"]["type"], "json_schema")
        content = call["messages"][0]["content"]
        images = [c for c in content if c["type"] == "image"]
        self.assertEqual(len(images), 2)                 # 複数枚はそのまま順に送る
        from base64 import b64decode
        import io
        with Image.open(io.BytesIO(b64decode(images[0]["source"]["data"]))) as im:
            self.assertEqual(max(im.size), 2400)         # 大きい画像は縮小して送る

    def test_script_problems_are_returned(self):
        client, _ = fake_client(json.dumps({"script": "S01 だけ", "corrections": []}))
        _, _, problems = convert([self.png], client=client)
        self.assertTrue(problems)

    def test_refusal_and_bad_json(self):
        client, _ = fake_client("", stop_reason="refusal")
        with self.assertRaisesRegex(StoryboardError, "断りました"):
            convert([self.png], client=client)
        client, _ = fake_client("not json")
        with self.assertRaisesRegex(StoryboardError, "読み取れません"):
            convert([self.png], client=client)

    def test_not_an_image(self):
        txt = os.path.join(self.dir, "a.txt")
        open(txt, "w").close()
        with self.assertRaisesRegex(StoryboardError, "png"):
            convert([txt], client=fake_client("")[0])
        broken = os.path.join(self.dir, "b.png")
        open(broken, "wb").close()
        with self.assertRaisesRegex(StoryboardError, "画像を読めません"):
            convert([broken], client=fake_client("")[0])


if __name__ == "__main__":
    unittest.main()

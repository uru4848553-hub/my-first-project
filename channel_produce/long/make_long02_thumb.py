"""長尺第2弾のサムネ（1280×720）：縦長の Midjourney の絵（ショート11と同じ案 5A）を右に置き、左に文字。

python channel_produce/long/make_long02_thumb.py
→ channel_produce/long/02_辞めた職場/サムネイル.jpg
新しい Midjourney を使わない（ショートの残りの案を横長に組み直す）。予告ショートと同じ絵なので、つながりも分かる。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_long01_thumb import AMBER, CYAN, WHITE, font, heavy  # noqa: E402

SRC = HERE.parent / "shorts" / "11_辞めます" / "サムネ素材_mj.png"
OUT = HERE / "02_辞めた職場" / "サムネイル.jpg"


def main():
    w, h = 1280, 720
    pic = Image.open(SRC).convert("RGB")
    pic = pic.resize((round(pic.width * h / pic.height), h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 50, 3))
    base = Image.new("RGB", (w, h), pic.getpixel((4, h // 2)))
    x0 = w - pic.width - 60
    # 絵の左右の端をぼかして背景になじませる
    mask = Image.new("L", pic.size, 255)
    md = ImageDraw.Draw(mask)
    for x in range(90):
        v = int(255 * x / 90)
        md.line([(x, 0), (x, h)], fill=v)
        md.line([(pic.width - 1 - x, 0), (pic.width - 1 - x, h)], fill=v)
    base.paste(pic, (x0, 0), mask)
    d = ImageDraw.Draw(base)
    x = 56
    heavy(d, (x, 70), "頼りにされていた人が", 62, WHITE)
    heavy(d, (x, 170), "辞めた職場の", 104, WHITE)
    b = heavy(d, (x, 300), "10年後", 150, AMBER)
    d.rounded_rectangle([x, 520, x + 470, 598], radius=10, fill=AMBER)
    d.text((x + 235, 559), "役職別に見える世界", font=font(44), fill=(10, 20, 46), anchor="mm",
           stroke_width=1, stroke_fill=(10, 20, 46))
    d.text((x, 625), "人生の断面図", font=font(42), fill=CYAN, stroke_width=1, stroke_fill=CYAN)
    base.save(OUT, quality=92)
    print("ok:", OUT, b)


if __name__ == "__main__":
    main()

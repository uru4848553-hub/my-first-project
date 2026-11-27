"""長尺第1弾のサムネ：Midjourney の文字なしの絵（右3分の1にビルの断面）に、Pillow で文字を入れる。

python channel_produce/long/make_long01_thumb.py <Midjourneyの絵.png>
→ channel_produce/long/01_年収と時間/サムネイル.jpg（1280×720）

GPT Image を使わず Pillow で文字を入れるのはクレジット節約のため（文字の位置と字形も確実）。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shorts"))
from blueprint import font  # noqa: E402

AMBER = (255, 176, 32)
WHITE = (255, 255, 255)
CYAN = (120, 200, 255)


def heavy(d, xy, s, size, fill, stroke=10):
    """太字の代わり：同じ色の細い縁で太らせ、その外に黒の縁"""
    f = font(size)
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(5, 10, 28))
    d.text(xy, s, font=f, fill=fill, stroke_width=2, stroke_fill=fill)
    return d.textbbox(xy, s, font=f)


def main(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = 1280, 720
    im = im.resize((w, int(im.height * w / im.width)))
    im = im.crop((0, (im.height - h) // 2, w, (im.height - h) // 2 + h))
    # ビルを右へ寄せて、左に文字の場所を空ける（空いた所は絵の左端の紺で埋める）
    shift = 190
    base = Image.new("RGB", (w, h), im.getpixel((5, h // 2)))
    base.paste(im.crop((0, 0, w - shift, h)), (shift, 0))
    im = base
    # 左側を少し暗くして文字を立たせる
    shade = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shade)
    for x in range(w):
        sd.line([(x, 0), (x, h)], fill=int(150 * max(0, 1 - x / 820)))
    im = Image.composite(Image.new("RGB", (w, h), (4, 8, 24)), im, shade)
    d = ImageDraw.Draw(im)
    x = 60
    heavy(d, (x, 100), "お金がない人ほど", 84, WHITE)
    b = heavy(d, (x, 225), "時間も", 136, WHITE)
    b = heavy(d, (b[2] + 6, 225), "ない", 136, AMBER)
    heavy(d, (b[2] - 10, 225), "？", 136, WHITE)
    # 下：何別か＋チャンネル名
    d.rounded_rectangle([x, 480, x + 560, 560], radius=10, fill=AMBER)
    d.text((x + 280, 520), "年収別に見える世界", font=font(50), fill=(10, 20, 46), anchor="mm",
           stroke_width=1, stroke_fill=(10, 20, 46))
    d.text((x, 600), "人生の断面図", font=font(44), fill=CYAN, stroke_width=1, stroke_fill=CYAN)
    im = im.filter(ImageFilter.UnsharpMask(1, 60, 2))
    im.save(dst, quality=92)
    print("ok:", dst)


if __name__ == "__main__":
    main(sys.argv[1], HERE / "01_年収と時間" / "サムネイル.jpg")

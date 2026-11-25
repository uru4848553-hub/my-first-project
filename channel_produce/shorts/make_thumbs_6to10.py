"""ショート6〜10のサムネ：各回の絵（設計図風）に Pillow で問いの文字を入れる（クレジットを使わない）。

python channel_produce/shorts/make_thumbs_6to10.py → 各フォルダの サムネイル.jpg（1080×1920）
"""
from pathlib import Path

from PIL import Image, ImageDraw

from blueprint import AMBER, NAVY, WHITE, font

HERE = Path(__file__).resolve().parent
CYAN = (120, 200, 255)

# フォルダ, 下絵, 1行目（白）, 2行目（アンバー）
THUMBS = [
    ("06_大雪の朝", "S07_起きる時間.png", "同じ大雪", "朝の長さが違う"),
    ("07_自分の時間30分", "S03_ユイの1日.png", "自分の時間は", "1日30分"),
    ("08_時間を買う", "S03_土曜の朝.png", "家事にお金を", "払う？払わない？"),
    ("09_ちょっとした知り合い", "S06_知り合いの数.png", "仕事を運ぶのは", "親友じゃない"),
    ("10_20年後の手紙", "S04_リクの手紙.png", "20年前の自分から", "手紙が届いた"),
]


def big(d, xy, s, size, fill):
    f = font(size)
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=12, stroke_fill=(5, 10, 28))
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=2, stroke_fill=fill)


def fit(s, max_w, start):
    size = start
    while size > 40 and font(size).getlength(s) > max_w:
        size -= 4
    return size


def main():
    for folder, base, l1, l2 in THUMBS:
        im = Image.open(HERE / folder / "media" / base).convert("RGB")
        # 絵を少し下げて、上に文字の場所を作る
        canvas = Image.new("RGB", im.size, NAVY)
        canvas.paste(im, (0, 150))
        d = ImageDraw.Draw(canvas)
        big(d, (540, 330), l1, fit(l1, 980, 120), WHITE)
        big(d, (540, 500), l2, fit(l2, 1000, 140), AMBER)
        d.rounded_rectangle([190, 1770, 890, 1870], radius=14, fill=AMBER)
        d.text((540, 1820), "年収別｜人生の断面図", font=font(52), fill=(10, 20, 46), anchor="mm",
               stroke_width=1, stroke_fill=(10, 20, 46))
        out = HERE / folder / "サムネイル.jpg"
        canvas.save(out, quality=92)
        print("ok:", out)


if __name__ == "__main__":
    main()

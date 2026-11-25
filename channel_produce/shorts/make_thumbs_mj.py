"""ショートのサムネ：Midjourney の文字なしの絵（ビルの断面のミニチュア）に、Pillow で文字を入れる。

python channel_produce/shorts/make_thumbs_mj.py        → 10本とも
python channel_produce/shorts/make_thumbs_mj.py 6 7    → 指定した回だけ

各フォルダの「サムネ素材_mj.png」（Midjourney の 9:16）を下絵にして「サムネイル.jpg」（1080×1920）を書き出す。

文字の位置（2026-11-25 ヒロキの指摘）：チャンネルのショート一覧は 9:16 の上下を約8%ずつ切って 2:3 で見せるため、
1行目が隠れていた。文字と帯は上から 230px より下にまとめ、一番下には何も置かない（一覧で切られ、1階の部屋も隠れるため）。
文字は GPT Image を使わず Pillow で入れる（クレジット節約、字も崩れない）。
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from blueprint import font

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
SAFE = 230            # 一覧で切られる上下の幅（約150px）＋余白
AMBER = (255, 176, 32)
WHITE = (255, 255, 255)
NAVY = (8, 16, 40)

# 回: (フォルダ, 1行目, 2行目, 下の帯)。{ } で囲んだ所がアンバー
THUMBS = {
    1: ("01_年収_同じ3万円", "同じ{3万円}が", "なぜこんなに{重い}？", "年収別｜人生の断面図"),
    2: ("02_世代_同じニュース", "株価最高値", "なぜ{世代}で違う？", "世代別｜人生の断面図"),
    3: ("03_IQ_同じ迷路", "同じ迷路が", "{IQ}でこう見える", "IQ別｜人生の断面図"),
    4: ("04_AI_同じ明日までに", "明日までに", "{AI}で帰る時間が違う", "AIの使い方別｜人生の断面図"),
    5: ("05_会社の大きさ_同じアイデア", "同じアイデア", "{判子}の数が違う", "会社の大きさ別｜人生の断面図"),
    6: ("06_大雪の朝", "同じ大雪", "{朝の長さ}が違う", "年収別｜人生の断面図"),
    7: ("07_自分の時間30分", "自分の時間は", "1日{30分}", "年収別｜人生の断面図"),
    8: ("08_時間を買う", "家事にお金を", "{払う}？払わない？", "年収別｜人生の断面図"),
    9: ("09_ちょっとした知り合い", "仕事を運ぶのは", "{親友}じゃない", "年収別｜人生の断面図"),
    10: ("10_20年後の手紙", "20年前の自分から", "{手紙}が届いた", "年収別｜人生の断面図"),
}


def parts(s):
    """「同じ{3万円}が」→ [("同じ", 白), ("3万円", アンバー), ("が", 白)]"""
    out = []
    for k, piece in enumerate(re.split(r"[{}]", s)):
        if piece:
            out.append((piece, AMBER if k % 2 else WHITE))
    return out


def line_width(s, size):
    return font(size).getlength(s.replace("{", "").replace("}", ""))


def heavy_line(d, cy, s, size):
    """1行を中央ぞろえで描く。黒紺の太い縁＋同じ色の細い縁で極太に見せる"""
    f = font(size)
    x = (W - line_width(s, size)) / 2
    for piece, color in parts(s):
        d.text((x, cy), piece, font=f, fill=color, anchor="lm", stroke_width=16, stroke_fill=NAVY)
        x += f.getlength(piece)
    x = (W - line_width(s, size)) / 2
    for piece, color in parts(s):
        d.text((x, cy), piece, font=f, fill=color, anchor="lm", stroke_width=3, stroke_fill=color)
        x += f.getlength(piece)


def fit(s, max_w, start):
    size = start
    while size > 50 and line_width(s, size) > max_w:
        size -= 4
    return size


def make(n):
    folder, l1, l2, band = THUMBS[n]
    src = HERE / folder / "サムネ素材_mj.png"
    im = Image.open(src).convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    im = im.filter(ImageFilter.UnsharpMask(2, 50, 3))
    # 文字の後ろ（上の方）と帯の後ろ（下の方）だけ暗くする
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        top = max(0.0, 1 - max(0, y - 640) / 240) if y < 880 else 0.0
        sd.line([(0, y), (W, y)], fill=int(210 * top))
    im = Image.composite(Image.new("RGB", (W, H), NAVY), im, shade)
    d = ImageDraw.Draw(im)
    s1 = fit(l1, W - 90, 150)
    s2 = fit(l2, W - 70, 170)
    y_1 = SAFE + 80
    y_2 = y_1 + s1 // 2 + s2 // 2 + 40
    heavy_line(d, y_1, l1, s1)
    heavy_line(d, y_2, l2, s2)
    # 帯は問いのすぐ下（一番下に置くと、一覧で切られるうえ、1階の部屋を隠すため）
    bs = fit(band, W - 300, 52)
    bw = font(bs).getlength(band) + 70
    by = y_2 + s2 // 2 + 50
    d.rounded_rectangle([(W - bw) / 2, by, (W + bw) / 2, by + 84], radius=14, fill=NAVY, outline=AMBER, width=4)
    d.text((W / 2, by + 42), band, font=font(bs), fill=WHITE, anchor="mm", stroke_width=1, stroke_fill=WHITE)
    out = HERE / folder / "サムネイル.jpg"
    im.save(out, quality=92)
    print("ok:", out)


if __name__ == "__main__":
    for n in ([int(a) for a in sys.argv[1:]] or sorted(THUMBS)):
        make(n)

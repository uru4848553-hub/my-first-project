"""新チャンネルのアイコン・バナーを作る（Pillow）。

python channel_produce/make_brand.py
→ 本命「人生の断面図」：icon.png（800×800）、banner.png（2560×1440）、banner_safe_preview.png
→ 予備「差の設計図」：icon_alt.png、banner_alt.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"  # Windows なら C:/Windows/Fonts/meiryob.ttc など

NAVY = (10, 20, 46)
GRID_MINOR = (22, 40, 80)
GRID_MAJOR = (34, 62, 118)
LINE = (120, 200, 255)     # 図面の線（シアン）
AMBER = (255, 176, 32)     # 「差」の強調
WHITE = (245, 248, 255)


def font(size):
    return ImageFont.truetype(FONT, size)


def grid(d, w, h, step):
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=GRID_MAJOR if (x // step) % 5 == 0 else GRID_MINOR, width=1 if (x // step) % 5 else 2)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=GRID_MAJOR if (y // step) % 5 == 0 else GRID_MINOR, width=1 if (y // step) % 5 else 2)


def arrow_head(d, tip, direction, size, color):
    x, y = tip
    if direction == "up":
        pts = [(x, y), (x - size / 2, y + size), (x + size / 2, y + size)]
    elif direction == "down":
        pts = [(x, y), (x - size / 2, y - size), (x + size / 2, y - size)]
    elif direction == "left":
        pts = [(x, y), (x + size, y - size / 2), (x + size, y + size / 2)]
    else:
        pts = [(x, y), (x - size, y - size / 2), (x - size, y + size / 2)]
    d.polygon(pts, fill=color)


def text_center(d, xy, s, f, fill, stroke=0, stroke_fill=None):
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=stroke_fill or fill)


def bars_with_gap(d, x0, base_y, bar_w, h_low, h_high, gap, scale=1.0, label_font=None):
    """低い棒（シアン枠）と高い棒（アンバー）＋高さの差の寸法線。"""
    lw = max(2, int(4 * scale))
    x1 = x0 + bar_w + gap
    d.rectangle([x0, base_y - h_low, x0 + bar_w, base_y], outline=LINE, width=lw)
    d.rectangle([x1, base_y - h_high, x1 + bar_w, base_y], fill=AMBER)
    # 補助線（低い棒の上端を右へ延ばす）
    for xx in range(int(x0 + bar_w), int(x1 + bar_w + 30 * scale), int(14 * scale)):
        d.line([(xx, base_y - h_low), (xx + 7 * scale, base_y - h_low)], fill=LINE, width=max(1, lw // 2))
    # 寸法線
    dx = x1 + bar_w + 22 * scale
    d.line([(dx - 10 * scale, base_y - h_high), (dx + 10 * scale, base_y - h_high)], fill=LINE, width=max(1, lw // 2))
    d.line([(dx, base_y - h_high + 4), (dx, base_y - h_low - 4)], fill=LINE, width=lw)
    arrow_head(d, (dx, base_y - h_high), "up", 16 * scale, LINE)
    arrow_head(d, (dx, base_y - h_low), "down", 16 * scale, LINE)
    if label_font:
        text_center(d, (dx + 38 * scale, base_y - (h_high + h_low) / 2), "差", label_font, AMBER)
    d.line([(x0 - 20 * scale, base_y), (x1 + bar_w + 20 * scale, base_y)], fill=WHITE, width=lw)


def make_icon_alt():
    S = 800
    im = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(im)
    grid(d, S, S, 40)
    # 丸く切り抜かれても収まるよう、中央の直径 ~640 に要素を置く
    text_center(d, (S / 2, 330), "差", font(400), WHITE, stroke=6, stroke_fill=WHITE)
    # 文字の下に横方向の寸法線（図面の「寸法」）
    y = 590
    d.line([(190, y), (610, y)], fill=AMBER, width=10)
    arrow_head(d, (170, y), "left", 44, AMBER)
    arrow_head(d, (630, y), "right", 44, AMBER)
    for x in (170, 630):
        d.line([(x, y - 60), (x, y + 30)], fill=AMBER, width=6)
    text_center(d, (S / 2, 655), "BLUEPRINT OF GAPS", font(38), LINE)
    im.save(OUT / "icon_alt.png")


def make_banner_alt():
    W, H = 2560, 1440
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    grid(d, W, H, 40)
    # 図面の外枠と表題欄風の線（安全領域の外＝PCの大画面でだけ見える飾り）
    d.rectangle([60, 60, W - 60, H - 60], outline=GRID_MAJOR, width=4)

    # 安全領域 1546×423（全デバイスで見える範囲）
    sx0, sy0 = (W - 1546) // 2, (H - 423) // 2
    sx1, sy1 = sx0 + 1546, sy0 + 423

    # 左：棒グラフ＋寸法線
    bars_with_gap(d, sx0 + 40, sy1 - 40, 110, 140, 320, 40, scale=1.4, label_font=font(64))

    # 右：タイトル・コピー
    tx = sx0 + 500
    d.text((tx, sy0 + 40), "差の設計図", font=font(170), fill=WHITE, stroke_width=3, stroke_fill=WHITE)
    d.text((tx + 6, sy0 + 250), "研究とデータで、人生の“分かれ道”を図面にする。", font=font(44), fill=LINE)
    d.text((tx + 6, sy0 + 330), "毎日ショート ／ 反応が良かったテーマは長尺で深掘り", font=font(38), fill=AMBER)
    im.save(OUT / "banner_alt.png")



def building(d, x0, y0, w, h, floors, hi, scale=1.0):
    """建物の断面図。floors 階、下から数えて hi 階目（0始まり）をアンバーで強調。"""
    lw = max(3, int(6 * scale))
    fh = h / floors
    # 屋根
    d.polygon([(x0 - 14 * scale, y0), (x0 + w / 2, y0 - 60 * scale), (x0 + w + 14 * scale, y0)], outline=WHITE, width=lw)
    for i in range(floors):
        top = y0 + h - (i + 1) * fh
        bot = y0 + h - i * fh
        if i == hi:
            d.rectangle([x0, top, x0 + w, bot], fill=AMBER)
            col = NAVY
        else:
            col = LINE
        # 部屋の中身（窓・机・人）を簡略化した記号
        pad = 16 * scale
        d.rectangle([x0 + pad, top + pad, x0 + pad + w * 0.22, top + pad + fh * 0.35], outline=col, width=max(2, lw // 2))
        d.line([(x0 + w * 0.45, bot - fh * 0.25), (x0 + w * 0.85, bot - fh * 0.25)], fill=col, width=max(2, lw // 2))
        d.ellipse([x0 + w * 0.58, bot - fh * 0.72, x0 + w * 0.58 + fh * 0.22, bot - fh * 0.50], outline=col, width=max(2, lw // 2))
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=WHITE, width=lw)
    for i in range(1, floors):
        y = y0 + h - i * fh
        d.line([(x0, y), (x0 + w, y)], fill=WHITE, width=lw)
    d.line([(x0 - 40 * scale, y0 + h), (x0 + w + 40 * scale, y0 + h)], fill=WHITE, width=lw)
    # 右側の寸法線（下から強調階まで＝「差」）
    dx = x0 + w + 30 * scale
    ytop = y0 + h - (hi + 1) * fh
    d.line([(dx, ytop + 4), (dx, y0 + h - 4)], fill=AMBER, width=lw)
    arrow_head(d, (dx, ytop), "up", 22 * scale, AMBER)
    arrow_head(d, (dx, y0 + h), "down", 22 * scale, AMBER)


def make_icon():
    S = 800
    im = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(im)
    grid(d, S, S, 40)
    building(d, 250, 190, 270, 430, 4, 2, scale=1.3)
    text_center(d, (S / 2, 690), "人生の断面図", font(66), WHITE, stroke=1)
    im.save(OUT / "icon.png")


def make_banner():
    W, H = 2560, 1440
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    grid(d, W, H, 40)
    d.rectangle([60, 60, W - 60, H - 60], outline=GRID_MAJOR, width=4)
    sx0, sy0 = (W - 1546) // 2, (H - 423) // 2
    sx1, sy1 = sx0 + 1546, sy0 + 423
    building(d, sx0 + 70, sy0 + 70, 190, 320, 4, 2, scale=0.9)
    tx = sx0 + 400
    d.text((tx, sy0 + 40), "人生の断面図", font=font(170), fill=WHITE, stroke_width=3, stroke_fill=WHITE)
    d.text((tx + 6, sy0 + 250), "年収・世代・IQ。階ごとの“視えている世界”を切って見せる。", font=font(38), fill=LINE)
    d.text((tx + 6, sy0 + 330), "毎日ショート ／ 反応が良かったテーマは長尺で深掘り", font=font(38), fill=AMBER)
    im.save(OUT / "banner.png")
    pv = im.copy()
    ImageDraw.Draw(pv).rectangle([sx0, sy0, sx1, sy1], outline=(255, 60, 60), width=4)
    pv.save(OUT / "banner_safe_preview.png")


if __name__ == "__main__":
    make_icon()
    make_banner()
    make_icon_alt()
    make_banner_alt()
    print("ok:", OUT)

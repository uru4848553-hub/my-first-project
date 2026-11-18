"""「人生の断面図」ショート用の素材を描く部品（Pillow）。

画面は 1080×1920（縦）。紺の方眼の上に、シアンの線と、"差"だけアンバー。
ショートの画面の上と下は YouTube の文字やボタンに隠れるので、
- 上 25% あたり（y=330〜620）は自動配置ツールが置くテロップの場所として空けておく
- 絵は y=640〜1560、x=70〜910（右端はいいね等のボタン）に収める
"""
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30

NAVY = (10, 20, 46)
GRID_MINOR = (20, 36, 74)
GRID_MAJOR = (32, 58, 112)
LINE = (120, 200, 255)
LINE_DIM = (70, 120, 170)
AMBER = (255, 176, 32)
WHITE = (240, 245, 255)
RED = (255, 110, 110)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
]

FLOOR_LABELS = ["1F", "2F", "3F", "4F"]


def font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def canvas():
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    step = 40
    for i, x in enumerate(range(0, W, step)):
        d.line([(x, 0), (x, H)], fill=GRID_MAJOR if i % 5 == 0 else GRID_MINOR, width=2 if i % 5 == 0 else 1)
    for i, y in enumerate(range(0, H, step)):
        d.line([(0, y), (W, y)], fill=GRID_MAJOR if i % 5 == 0 else GRID_MINOR, width=2 if i % 5 == 0 else 1)
    return im, d


def text(d, xy, s, size, fill=WHITE, anchor="mm", stroke=0):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=NAVY)


def arrow(d, p0, p1, color=AMBER, width=6, head=24):
    d.line([p0, p1], fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1):
        a = ang + math.pi - s * 0.45
        d.line([p1, (p1[0] + head * math.cos(a), p1[1] + head * math.sin(a))], fill=color, width=width)


def dashed(d, p0, p1, color=LINE, width=3, dash=14):
    length = math.dist(p0, p1)
    n = max(1, int(length // (dash * 2)))
    for i in range(n + 1):
        t0 = i * 2 * dash / length
        t1 = min(1, t0 + dash / length)
        if t0 >= 1:
            break
        a = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
        b = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
        d.line([a, b], fill=color, width=width)


# ---- 人（シルエット）----

def person(d, cx, base_y, h=260, color=LINE, fill=None, pose="stand", width=5):
    """設計図の記号のような人。base_y が足元。pose: stand / sit / look_up / look_down"""
    head_r = h * 0.11
    if pose == "sit":
        hip_y = base_y - h * 0.32
        top_y = hip_y - h * 0.42
    else:
        hip_y = base_y - h * 0.45
        top_y = hip_y - h * 0.40
    head_c = (cx, top_y - head_r * 1.15)
    if pose == "look_down":
        head_c = (cx + head_r * 0.35, top_y - head_r * 0.95)
    if pose == "look_up":
        head_c = (cx - head_r * 0.15, top_y - head_r * 1.3)
    bx = h * 0.13
    body = [(cx - bx, top_y), (cx + bx, top_y), (cx + bx * 0.85, hip_y), (cx - bx * 0.85, hip_y)]
    d.polygon(body, outline=color, fill=fill, width=width)
    d.ellipse([head_c[0] - head_r, head_c[1] - head_r, head_c[0] + head_r, head_c[1] + head_r],
              outline=color, fill=fill, width=width)
    if pose == "sit":
        d.line([(cx - bx * 0.6, hip_y), (cx + h * 0.22, hip_y), (cx + h * 0.22, base_y)], fill=color, width=width)
        d.line([(cx - bx * 0.2, hip_y), (cx + h * 0.30, hip_y), (cx + h * 0.30, base_y)], fill=color, width=width)
    else:
        d.line([(cx - bx * 0.45, hip_y), (cx - bx * 0.55, base_y)], fill=color, width=width)
        d.line([(cx + bx * 0.45, hip_y), (cx + bx * 0.55, base_y)], fill=color, width=width)
    return head_c, head_r


def bubble(d, box, s, size=40, color=LINE, fill=NAVY, tail=None, text_color=WHITE, width=4):
    """考えごとの吹き出し（楕円）。tail は吹き出しの先の点（小さな丸を3つ並べる）"""
    d.ellipse(box, outline=color, fill=fill, width=width)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    if s:
        text(d, (cx, cy), s, size, fill=text_color)
    if tail:
        for i, r in enumerate((14, 10, 7)):
            t = (i + 1) / 4
            x = cx + (tail[0] - cx) * (0.55 + t * 0.45)
            y = (box[3] if tail[1] > cy else box[1]) + (tail[1] - (box[3] if tail[1] > cy else box[1])) * t
            d.ellipse([x - r, y - r, x + r, y + r], outline=color, fill=fill, width=3)


# ---- ビルの断面図 ----

def building(d, x0, y0, w, h, labels=None, highlight=None, dim_others=False, roof=True, width=6,
             label_size=44, side_labels=True):
    """4階建ての断面図。labels は1F〜4Fの右側の文字、highlight は強調する階（0〜3）のリスト。
    戻り値：各階の (x0, y0, x1, y1)（下の階から）"""
    floors = []
    fh = h / 4
    for i in range(4):
        top = y0 + h - (i + 1) * fh
        bot = y0 + h - i * fh
        floors.append((x0, top, x0 + w, bot))
    for i, (a, top, b, bot) in enumerate(floors):
        on = highlight is not None and i in highlight
        if on:
            d.rectangle([a, top, b, bot], fill=(44, 34, 10))
        col = AMBER if on else (LINE_DIM if dim_others and highlight else LINE)
        d.rectangle([a, top, b, bot], outline=col, width=width)
        if side_labels:
            text(d, (a + 18, top + 16), FLOOR_LABELS[i], 30, fill=col, anchor="lt")
        if labels:
            text(d, (b + 22, (top + bot) / 2), labels[i], label_size, fill=AMBER if on else WHITE, anchor="lm")
    if roof:
        d.polygon([(x0 - 20, y0), (x0 + w / 2, y0 - 90), (x0 + w + 20, y0)], outline=LINE, width=width)
    d.line([(x0 - 60, y0 + h), (x0 + w + 60, y0 + h)], fill=WHITE, width=width)
    return floors


def keyplan(d, x0, y0, floor, w=110, h=150):
    """右上の小さなキープラン（今どの階か）"""
    building(d, x0, y0, w, h, highlight=[floor], roof=False, width=3, side_labels=False)
    text(d, (x0 + w / 2, y0 + h + 30), "KEY PLAN", 22, fill=LINE_DIM)


def room(d, floor, title, title_size=46):
    """1つの階を大きく切り出した部屋。戻り値は部屋の枠 (x0, y0, x1, y1)"""
    box = (80, 760, 900, 1500)
    d.rectangle(box, outline=AMBER, width=8)
    d.line([(40, box[3]), (940, box[3])], fill=WHITE, width=6)
    text(d, (box[0], 700), title, title_size, fill=AMBER, anchor="lm")
    keyplan(d, 790, 560, floor)
    # 寸法線（階高）
    dx = box[0] - 40
    d.line([(dx, box[1] + 6), (dx, box[3] - 6)], fill=LINE_DIM, width=3)
    for y in (box[1], box[3]):
        d.line([(dx - 14, y), (dx + 14, y)], fill=LINE_DIM, width=3)
    return box


# ---- 小物 ----

def phone(d, x, y, w=90, h=160, cracked=False, color=LINE, crack_t=1.0):
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, outline=color, width=5)
    d.rectangle([x + 10, y + 18, x + w - 10, y + h - 22], outline=LINE_DIM, width=2)
    if cracked:
        cx, cy = x + w * 0.62, y + h * 0.38
        rays = [(-1, -1.2), (1.1, -0.6), (0.9, 1.3), (-0.8, 1.5), (-1.3, 0.2), (0.2, -1.6)]
        for k, (dx, dy) in enumerate(rays):
            L = 0.55 * w * min(1, crack_t * 1.4)
            mid = (cx + dx * L * 0.5 + (6 if k % 2 else -6), cy + dy * L * 0.5)
            end = (cx + dx * L, cy + dy * L)
            d.line([(cx, cy), mid, end], fill=WHITE, width=3)


def bill(d, x, y, label, w=150, h=96, color=LINE):
    d.rectangle([x, y, x + w, y + h], outline=color, width=4)
    text(d, (x + w / 2, y + 30), label, 30, fill=color)
    for k in range(2):
        d.line([(x + 18, y + 58 + k * 16), (x + w - 18, y + 58 + k * 16)], fill=LINE_DIM, width=2)


def calendar(d, x, y, mark=None, w=200, h=180):
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=4)
    d.rectangle([x, y, x + w, y + 34], fill=LINE_DIM)
    cw, ch = w / 7, (h - 34) / 5
    for r in range(5):
        for c in range(7):
            cx, cy = x + c * cw + cw / 2, y + 34 + r * ch + ch / 2
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=LINE_DIM)
    if mark:
        r, c, s = mark
        cx, cy = x + c * cw + cw / 2, y + 34 + r * ch + ch / 2
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], outline=AMBER, width=5)
        text(d, (cx, cy + 50), s, 28, fill=AMBER)


def window(d, x, y, w=220, h=260):
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=5)
    d.line([(x + w / 2, y), (x + w / 2, y + h)], fill=LINE, width=3)
    d.line([(x, y + h / 2), (x + w, y + h / 2)], fill=LINE, width=3)


def desk(d, x, y, w=300):
    d.line([(x, y), (x + w, y)], fill=LINE, width=6)
    d.line([(x + 20, y), (x + 20, y + 120)], fill=LINE, width=5)
    d.line([(x + w - 20, y), (x + w - 20, y + 120)], fill=LINE, width=5)


def bar_chart(d, x, y, values, labels, h=300, bw=110, gap=60, colors=None, size=34):
    top = max(values)
    for i, v in enumerate(values):
        bx = x + i * (bw + gap)
        bh = h * v / top
        col = colors[i] if colors else LINE
        d.rectangle([bx, y + h - bh, bx + bw, y + h], fill=col)
        text(d, (bx + bw / 2, y + h + 34), labels[i], size, fill=WHITE)
    d.line([(x - 20, y + h), (x + len(values) * (bw + gap), y + h)], fill=WHITE, width=4)


# ---- 書き出し ----

def save_png(im, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def save_mp4(frames, path, fps=FPS):
    """PIL の画像の列を H.264 の mp4 にする（BT.709・4:2:0）"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
         "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
         "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        proc.stdin.write(f.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"mp4 を書き出せません: {path}")
    return path


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ---- 全話共通の場面 ----

BX, BY, BW, BH = 150, 760, 520, 780   # ビル全体を見せるときの位置


def building_scene(d, labels, names, highlight=None, poses=None, label_size=44):
    """4人が1人ずつ住むビルの全体。戻り値：各階の枠（下から）"""
    floors = building(d, BX, BY, BW, BH, labels=labels, highlight=highlight, label_size=label_size)
    for i, (a, top, b, bot) in enumerate(floors):
        on = highlight is not None and i in highlight
        pose = poses[i] if poses else "stand"
        person(d, a + 170, bot - 14, h=150, color=AMBER if on else LINE, pose=pose, width=4)
        if names:
            text(d, (a + 300, bot - 40), names[i], 30, fill=LINE_DIM)
    return floors


def intro_stack(labels, names, photo_title, label_size=44):
    """写真（4人並び）にひびが入り、ビルが1階ずつ積み上がり、1階から順に光る（約3.2秒）。
    効果音「トン」は、この場面の頭から +0.4 +0.6 +0.8 +1.0 秒"""
    frames = []
    fh = BH / 4
    for f in range(48):
        im, d = canvas()
        t = f / FPS
        if t < 0.4:
            d.rectangle([120, 820, 960, 1300], outline=WHITE, width=6)
            text(d, (540, 780), photo_title, 40, fill=LINE_DIM)
            for i in range(4):
                person(d, 230 + i * 205, 1250, h=320, color=LINE, width=5)
            if t > 0.27:
                for i in range(1, 4):
                    x = 120 + i * 210
                    d.line([(x, 820), (x + 12, 1060), (x - 8, 1300)], fill=AMBER, width=6)
        else:
            k = (t - 0.4) / 0.2
            shown = min(4, int(k) + 1)
            for i in range(shown):
                top, bot = BY + BH - (i + 1) * fh, BY + BH - i * fh
                drop = (1 - ease(min(1, (k - i) * 1.6))) if i == shown - 1 and k < 4 else 0
                off = -140 * drop
                d.rectangle([BX, top + off, BX + BW, bot + off], outline=LINE, width=6)
                text(d, (BX + 18, top + off + 16), FLOOR_LABELS[i], 30, fill=LINE, anchor="lt")
                person(d, BX + 170, bot - 14 + off, h=150, color=LINE, width=4)
                if names:
                    text(d, (BX + 300, bot - 40 + off), names[i], 30, fill=LINE_DIM)
                text(d, (BX + BW + 22, (top + bot) / 2 + off), labels[i], label_size, fill=WHITE, anchor="lm")
            d.line([(BX - 60, BY + BH), (BX + BW + 60, BY + BH)], fill=WHITE, width=6)
        frames.append(im)
    for i in range(4):
        im, d = canvas()
        building_scene(d, labels, names, highlight=[i], label_size=label_size)
        frames += [im] * 12
    im, d = canvas()
    building_scene(d, labels, names, label_size=label_size)
    frames += [im] * 12
    return frames


def loop_end(labels, names, label_size=44):
    """最後の絵＝intro_stack の最後の絵（ループで冒頭へ戻ったとき、つなぎ目を目立たせない）"""
    im, d = canvas()
    building_scene(d, labels, names, label_size=label_size)
    return im


def clock(d, cx, cy, hour, minute=0, r=70, color=LINE, label=None):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=5)
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(cx + math.sin(a) * r * 0.82, cy - math.cos(a) * r * 0.82),
                (cx + math.sin(a) * r * 0.95, cy - math.cos(a) * r * 0.95)], fill=color, width=3)
    ah = math.radians((hour % 12 + minute / 60) * 30)
    am = math.radians(minute * 6)
    d.line([(cx, cy), (cx + math.sin(ah) * r * 0.5, cy - math.cos(ah) * r * 0.5)], fill=AMBER, width=6)
    d.line([(cx, cy), (cx + math.sin(am) * r * 0.78, cy - math.cos(am) * r * 0.78)], fill=WHITE, width=4)
    if label:
        text(d, (cx, cy + r + 30), label, 30, fill=AMBER)


def sky(d, box, kind):
    """窓の外の空。kind: fireworks / rain / cloudy / sunrise / moon"""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = x1 - x0, y1 - y0
    if kind == "fireworks":
        for (fx, fy, r) in [(0.3, 0.3, 0.18), (0.7, 0.45, 0.14)]:
            px, py, rr = x0 + w * fx, y0 + h * fy, w * r
            for k in range(12):
                a = math.radians(k * 30)
                d.line([(px + math.cos(a) * rr * 0.3, py + math.sin(a) * rr * 0.3),
                        (px + math.cos(a) * rr, py + math.sin(a) * rr)], fill=AMBER, width=3)
    elif kind == "rain":
        for k in range(14):
            x = x0 + 15 + (k * 37) % (w - 30)
            y = y0 + 15 + (k * 53) % (h - 50)
            d.line([(x, y), (x - 10, y + 30)], fill=LINE, width=3)
    elif kind == "cloudy":
        for (fx, fy) in [(0.35, 0.35), (0.62, 0.5)]:
            px, py = x0 + w * fx, y0 + h * fy
            for dx, rr in [(-30, 26), (0, 36), (32, 26)]:
                d.ellipse([px + dx - rr, py - rr, px + dx + rr, py + rr], outline=LINE, width=3)
    elif kind == "sunrise":
        d.pieslice([cx - w * 0.25, y1 - h * 0.3, cx + w * 0.25, y1 + h * 0.2], 180, 360, outline=AMBER, width=4)
        for k in range(5):
            a = math.radians(200 + k * 35)
            d.line([(cx + math.cos(a) * w * 0.3, y1 - h * 0.05 + math.sin(a) * w * 0.3),
                    (cx + math.cos(a) * w * 0.42, y1 - h * 0.05 + math.sin(a) * w * 0.42)], fill=AMBER, width=4)
    elif kind == "moon":
        d.ellipse([cx - 30, cy - 50, cx + 30, cy + 10], outline=WHITE, width=4)
        d.ellipse([cx - 12, cy - 60, cx + 42, cy - 2], fill=NAVY)

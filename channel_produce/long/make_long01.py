"""長尺第1弾「なぜお金がない人ほど、時間もないのか」の場面の絵（16:9・1920×1080）を作る。

python channel_produce/long/make_long01.py → channel_produce/long/01_年収と時間/media/S01a_〜.png …
絵の部品はショートと同じ blueprint.py を横長の画面で使う（下の160pxは字幕の場所として空ける）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shorts"))
import blueprint as bp  # noqa: E402

bp.W, bp.H = 1920, 1080
from blueprint import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, bill, bubble, building, calendar, clock,  # noqa: E402
                       dashed, desk, person, phone, save_png, sky, text, window)

OUT = HERE / "01_年収と時間" / "media"
NAMES = ["ケンタ", "ユイ", "ショウ", "リク"]
INCOMES = ["年収300万", "年収500万", "年収700万", "年収1000万"]
JOBS = ["倉庫・契約社員", "事務の主任", "設計の係長", "設備会社の部長"]
TOP, BOTTOM = 90, 900          # 絵を置く範囲（下は字幕）


def canvas():
    return bp.canvas()


def heading(d, s, y=120, color=LINE):
    text(d, (960, y), s, 44, fill=color)


def big(d, lines, y=480, size=96, color=WHITE, gap=1.3, amber=()):
    top = y - (len(lines) - 1) * size * gap / 2
    for i, line in enumerate(lines):
        text(d, (960, top + i * size * gap), line, size, fill=AMBER if i in amber else color)


def bldg(d, highlight=None, labels=INCOMES, names=NAMES, x=560, w=520, poses=None, extra=None):
    """画面中央のビル。各階に1人"""
    floors = building(d, x, 240, w, 620, labels=labels, highlight=highlight, label_size=40)
    for i, (a, top, b, bot) in enumerate(floors):
        on = highlight is not None and i in highlight
        person(d, a + 140, bot - 12, h=120, color=AMBER if on else LINE, pose=(poses or ["stand"] * 4)[i], width=4)
        if names:
            text(d, (a + 260, bot - 30), names[i], 28, fill=LINE_DIM)
        if extra:
            extra(d, i, (a, top, b, bot))
    return floors


def room(d, floor, sub=""):
    """1つの階を大きく切り出した部屋。戻り値は部屋の枠"""
    box = (180, 200, 1740, 860)
    d.rectangle(box, outline=AMBER, width=8)
    d.line([(120, box[3]), (1800, box[3])], fill=WHITE, width=6)
    text(d, (box[0], 150), f"{floor + 1}F｜{INCOMES[floor]}｜{NAMES[floor]}{('｜' + sub) if sub else ''}", 44, fill=AMBER, anchor="lm")
    # キープラン
    building(d, 1640, 40, 90, 130, highlight=[floor], roof=False, width=3, side_labels=False)
    return box


def card(head, lines, amber=(), size=84, sub=None):
    def make():
        im, d = canvas()
        heading(d, head)
        big(d, lines, size=size, amber=amber)
        if sub:
            text(d, (960, 820), sub, 34, fill=LINE_DIM)
        return im
    return make


def reason(n, line1, line2):
    def make():
        im, d = canvas()
        d.rectangle([260, 260, 1660, 760], outline=AMBER, width=6)
        text(d, (960, 340), f"理由 {n}", 60, fill=AMBER)
        big(d, [line1, line2], y=560, size=78)
        return im
    return make


def strength(floor, misread, power):
    def make():
        im, d = canvas()
        bldg(d, highlight=[floor], x=220, w=420)
        text(d, (1300, 330), "ほかの階からは", 40, fill=LINE_DIM)
        text(d, (1300, 410), f"「{misread}」", 54, fill=WHITE)
        arrow(d, (1300, 470), (1300, 560), color=AMBER, width=6)
        text(d, (1300, 620), f"{NAMES[floor]}の強み", 40, fill=LINE_DIM)
        text(d, (1300, 700), power, 64, fill=AMBER)
        return im
    return make


def research(title, year, draw):
    def make():
        im, d = canvas()
        text(d, (960, 120), f"研究｜{title}（{year}）", 44, fill=LINE)
        draw(d)
        return im
    return make


def floor_room(floor, sub, draw):
    def make():
        im, d = canvas()
        box = room(d, floor, sub)
        draw(d, box)
        return im
    return make


# ---------------------------------------------------------------- 各場面

def s01a():
    im, d = canvas()
    clock(d, 620, 470, 10, 10, r=230, label=None)
    text(d, (620, 790), "1日 24時間", 48, fill=WHITE)
    cx, cy, r = 1300, 470, 230
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=LINE_DIM, width=4)
    for k in range(0, 360, 45):
        d.pieslice([cx - r, cy - r, cx + r, cy + r], k, k + 12, fill=AMBER)
    text(d, (1300, 790), "自由に使える時間", 48, fill=AMBER)
    return im


def s02a():
    im, d = canvas()
    d.rectangle([360, 230, 1560, 840], outline=WHITE, width=6)
    text(d, (960, 180), "20年前の春・入社式", 44, fill=LINE_DIM)
    for i in range(4):
        person(d, 560 + i * 270, 800, h=430, color=LINE, width=6)
        text(d, (560 + i * 270, 830), NAMES[i], 32, fill=LINE_DIM)
    return im


def envelopes(labels=None, opened=None):
    def make():
        im, d = canvas()
        heading(d, "20年後の自分へ")
        for i in range(4):
            x = 260 + i * 370
            d.rectangle([x, 380, x + 300, 580], outline=AMBER if opened == i else WHITE, width=5)
            d.line([(x, 380), (x + 150, 490), (x + 300, 380)], fill=AMBER if opened == i else WHITE, width=4)
            text(d, (x + 150, 630), NAMES[i], 36, fill=LINE_DIM)
            if labels:
                text(d, (x + 150, 700), labels[i], 30, fill=AMBER)
        return im
    return make


def s02c():
    im, d = canvas()
    bldg(d)
    return im


def s02d():
    im, d = canvas()
    heading(d, "4人とも、同じ24時間")
    for i in range(4):
        x = 340 + i * 410
        clock(d, x, 470, 10, 10, r=130)
        text(d, (x, 680), NAMES[i], 40, fill=WHITE)
        text(d, (x, 740), INCOMES[i], 32, fill=LINE_DIM)
    return im


def s02e():
    im, d = canvas()
    bldg(d, highlight=[0])
    text(d, (1500, 470), "理由を4つ", 56, fill=AMBER)
    text(d, (1500, 550), "1階からのぼる", 40, fill=LINE_DIM)
    arrow(d, (1300, 760), (1300, 330), color=AMBER, width=6)
    return im


def snow(d, box, n=40):
    x0, y0, x1, y1 = box
    for k in range(n):
        x = x0 + 20 + (k * 97) % max(1, (x1 - x0 - 40))
        y = y0 + 20 + (k * 61) % max(1, (y1 - y0 - 40))
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WHITE)


def s03a():
    im, d = canvas()
    snow(d, (100, 100, 1820, 880), 70)
    phone(d, 760, 200, w=400, h=650)
    d.rounded_rectangle([700, 380, 1220, 560], radius=20, fill=NAVY, outline=AMBER, width=5)
    text(d, (960, 430), "明日の朝", 40, fill=WHITE)
    text(d, (960, 500), "大雪のおそれ", 56, fill=AMBER)
    text(d, (960, 160), "1月の金曜 夜9時", 40, fill=LINE_DIM)
    return im


def snow_room(floor, thought, extra=None):
    def draw(d, box):
        window(d, 1300, 280, w=360, h=380)
        snow(d, (1300, 280, 1660, 660), 25)
        person(d, 520, box[3] - 8, h=460, color=AMBER, pose="look_up")
        bubble(d, (600, 250, 1260, 420), thought, 42, tail=(560, 560))
        if extra:
            extra(d, box)
    return floor_room(floor, "大雪の前の夜", draw)


def s03f():
    im, d = canvas()
    times = [(4, 30, "4:30 始発"), (6, 0, "6:00 学童"), (7, 30, "7:30 在宅"), (7, 0, "7:00 タクシー")]

    def extra(d, i, f):
        a, top, b, bot = f
        h, m, lab = times[i]
        clock(d, a + 400, (top + bot) / 2 - 10, h, m, r=52, color=AMBER if i == 0 else LINE)
        text(d, (b + 220, (top + bot) / 2 + 40), lab, 30, fill=AMBER if i == 0 else LINE_DIM)
    bldg(d, highlight=[0], extra=extra)
    return im


def s04a():
    def draw(d, box):
        for k in range(6):
            x = 1000 + (k % 3) * 220
            y = 560 - (k // 3) * 170
            d.rectangle([x, y, x + 190, y + 150], outline=LINE, width=4)
            d.line([(x, y + 75), (x + 190, y + 75)], fill=LINE_DIM, width=2)
        person(d, 600, box[3] - 8, h=460, color=AMBER)
        text(d, (1330, 300), "時給", 44, fill=AMBER)
    return floor_room(0, "倉庫", draw)()


def s04b():
    im, d = canvas()
    d.rectangle([640, 260, 1280, 760], outline=WHITE, width=6)
    text(d, (960, 420), "電気工事士", 72, fill=WHITE)
    text(d, (960, 520), "教科書", 48, fill=LINE_DIM)
    d.rectangle([1230, 260, 1270, 400], fill=AMBER)
    text(d, (1420, 330), "5ページで", 40, fill=AMBER, anchor="lm")
    text(d, (1420, 390), "止まったまま", 40, fill=AMBER, anchor="lm")
    text(d, (960, 840), "（資格の本は、来月から）", 44, fill=LINE_DIM)
    return im


def s04c():
    def draw(d, box):
        desk(d, 700, 760, w=600)
        person(d, 520, box[3] - 8, h=430, pose="sit", color=AMBER)
        for (x0, y0, x1, y1), word, big_ in [((240, 240, 600, 380), "家賃 25日", False), ((640, 230, 1040, 370), "電気代の通知", False),
                                             ((1080, 260, 1500, 420), "あと 4,100円", True), ((780, 420, 1120, 540), "今月", False)]:
            bubble(d, (x0, y0, x1, y1), word, 46 if big_ else 40, color=AMBER if big_ else LINE)
    return floor_room(0, "夜", draw)()


def farmer(d, x, y, h, color=WHITE, full=False):
    head, r = person(d, x, y, h=h, color=color, width=5)
    d.polygon([(head[0] - r * 1.8, head[1] - r * 0.4), (head[0] + r * 1.8, head[1] - r * 0.4), (head[0], head[1] - r * 1.9)],
              outline=color, width=5)
    if full:
        for k, w in enumerate(["借金", "支払い", "お金"]):
            bubble(d, (x - 230 + k * 160, y - h - 200 + (k % 2) * 40, x - 80 + k * 160, y - h - 110 + (k % 2) * 40), w, 30, color=AMBER)


def s04d(d):
    farmer(d, 700, 780, 420, full=True)
    farmer(d, 1250, 780, 420)
    text(d, (700, 830), "収穫前（お金がない）", 38, fill=AMBER)
    text(d, (1250, 830), "収穫後（お金がある）", 38, fill=LINE)


def s04e(d):
    from blueprint import bar_chart
    bar_chart(d, 640, 300, [62, 100], ["収穫前", "収穫後"], h=400, bw=220, gap=200, colors=[AMBER, LINE], size=40)
    text(d, (960, 830), "同じ人のテストの成績（高さはイメージ）", 34, fill=LINE_DIM)


def s04f():
    im, d = canvas()
    head, r = person(d, 960, 880, h=560, color=WHITE, width=6)
    for (x0, y0, x1, y1), w in [((560, 200, 860, 320), "家賃"), ((900, 170, 1200, 290), "電気代"), ((1240, 220, 1500, 340), "今月"),
                                ((620, 340, 920, 450), "あと4,100円"), ((1040, 330, 1360, 440), "支払い")]:
        bubble(d, (x0, y0, x1, y1), w, 36, color=AMBER)
    text(d, (960, 100), "お金の心配が、頭の「空き」を使ってしまう", 44, fill=LINE)
    return im


def stairs_q(floor_from, q1, q2):
    def make():
        im, d = canvas()
        floors = bldg(d, highlight=[floor_from + 1], x=300, w=440)
        a, top, b, bot = floors[floor_from]
        x, y = b - 140, bot
        step = (bot - top) / 5
        for k in range(5):
            d.line([(x, y), (x + 24, y), (x + 24, y - step)], fill=AMBER, width=5)
            x, y = x + 24, y - step
        text(d, (1400, 420), q1, 60, fill=WHITE)
        text(d, (1400, 520), q2, 60, fill=AMBER)
        return im
    return make


def s05a():
    def draw(d, box):
        desk(d, 800, 760, w=560)
        person(d, 600, box[3] - 8, h=430, pose="sit", color=AMBER)
        d.rectangle([900, 560, 1180, 740], outline=LINE, width=4)
        text(d, (1040, 650), "主任", 40, fill=LINE)
        calendar(d, 1380, 280, w=260, h=230)
    return floor_room(1, "事務", draw)()


def s05b():
    im, d = canvas()
    heading(d, "ユイの1日")
    x0, x1, y = 160, 1760, 520
    d.line([(x0, y), (x1, y)], fill=WHITE, width=6)
    marks = [(6, "6:00 起きる・弁当"), (7.5, "7:30 家を出る"), (17, "17:00 学童へ"), (19, "夕飯・宿題"), (22, "22:00〜22:30")]
    for hour, lab in marks:
        x = x0 + (x1 - x0) * (hour - 5) / 19
        d.line([(x, y - 30), (x, y + 30)], fill=LINE, width=4)
        text(d, (x, y + 80 if marks.index((hour, lab)) % 2 == 0 else y - 80), lab, 34, fill=WHITE)
    xa = x0 + (x1 - x0) * (22 - 5) / 19
    xb = x0 + (x1 - x0) * (22.5 - 5) / 19
    d.rectangle([xa, y - 40, xb, y + 40], fill=AMBER)
    text(d, ((xa + xb) / 2, y - 160), "自分の時間 30分", 44, fill=AMBER)
    return im


def s05c():
    def draw(d, box):
        person(d, 520, box[3] - 8, h=380, pose="sit", color=AMBER)
        phone(d, 640, 560, w=120, h=200)
        d.polygon([(690, 620), (690, 700), (745, 660)], fill=AMBER)
        clock(d, 1300, 470, 10, 0, r=170)
        text(d, (1300, 700), "子どもが寝たあとの30分", 40, fill=WHITE)
        bubble(d, (240, 240, 760, 380), "何かしなきゃ", 44, tail=(520, 520))
    return floor_room(1, "夜10時", draw)()


def s05d(d):
    d.rectangle([260, 280, 760, 640], outline=LINE, width=5)
    big_lines = [("余裕がない", 330), ("→ ストレス・不安", 430)]
    for s, y in big_lines:
        text(d, (510, y + 60), s, 44, fill=WHITE)
    arrow(d, (800, 460), (1000, 460), color=AMBER, width=6)
    d.rectangle([1040, 280, 1660, 640], outline=AMBER, width=5)
    text(d, (1350, 390), "今すぐ楽になれるもの", 44, fill=AMBER)
    text(d, (1350, 500), "失敗しない選択", 44, fill=AMBER)
    text(d, (960, 760), "を選びやすくなる", 44, fill=WHITE)


def s05e():
    im, d = canvas()
    head, r = person(d, 960, 880, h=560, color=WHITE, width=6)
    phone(d, 1060, 560, w=140, h=230)
    d.polygon([(1110, 600), (1110, 680), (1170, 640)], fill=AMBER)
    text(d, (960, 120), "だらしないのではない。疲れた頭が「今すぐ楽」を選んでいる", 42, fill=LINE)
    return im


def s05h():
    im, d = canvas()
    bldg(d, highlight=[2], x=300, w=440)
    text(d, (1400, 400), "お金で買っているもの", 54, fill=WHITE)
    text(d, (1400, 500), "それは「物」ではない", 54, fill=AMBER)
    return im


def s06a():
    def draw(d, box):
        desk(d, 800, 760, w=560)
        person(d, 600, box[3] - 8, h=430, pose="sit", color=AMBER)
        d.rectangle([880, 600, 1200, 740], outline=LINE, width=4)
        d.line([(900, 640), (1180, 700)], fill=LINE_DIM, width=3)
        text(d, (1040, 580), "図面", 32, fill=LINE)
    return floor_room(2, "設計", draw)()


def s06b():
    def draw(d, box):
        for k, (lab, x) in enumerate([("食洗機", 420), ("洗濯乾燥機", 820), ("ネットスーパー", 1260)]):
            d.rectangle([x - 150, 380, x + 150, 720], outline=LINE, width=5)
            d.ellipse([x - 80, 460, x + 80, 620], outline=AMBER if k < 2 else LINE, width=5)
            text(d, (x, 780), lab, 38, fill=WHITE)
        text(d, (960, 290), "土曜の朝、家事は機械とお店に", 44, fill=AMBER)
    return floor_room(2, "土曜の朝", draw)()


def s06c():
    def draw(d, box):
        desk(d, 700, 760, w=600)
        person(d, 520, box[3] - 8, h=430, pose="sit", color=AMBER)
        d.rectangle([820, 640, 1060, 740], outline=WHITE, width=4)
        text(d, (940, 690), "技術士", 32, fill=WHITE)
        d.ellipse([1120, 670, 1190, 740], outline=LINE, width=4)
        clock(d, 1450, 420, 8, 0, r=150)
        text(d, (1450, 620), "来年の自分のための1時間", 38, fill=AMBER)
    return floor_room(2, "土曜の朝", draw)()


def s06d():
    im, d = canvas()
    text(d, (960, 140), "ここで、1問", 60, fill=AMBER)
    for k, (lab, sub, x) in enumerate([("A", "お金を払って家事を減らす", 560), ("B", "払わずに自分でやる", 1360)]):
        d.rectangle([x - 340, 280, x + 340, 700], outline=LINE, width=6)
        text(d, (x, 380), lab, 110, fill=WHITE)
        text(d, (x, 560), sub, 44, fill=WHITE)
    text(d, (960, 800), "生活の満足が高いのは、どっち？", 50, fill=AMBER)
    return im


def s06e(d):
    from blueprint import bar_chart
    bar_chart(d, 640, 300, [70, 100], ["物を買う", "時間を買う"], h=380, bw=220, gap=200, colors=[LINE_DIM, AMBER], size=40)
    text(d, (960, 820), "生活の満足（高さはイメージ）", 34, fill=LINE_DIM)


def s06f():
    im, d = canvas()
    for k, (name, a, b, x) in enumerate([("1階 ケンタ", "時間", "お金", 560), ("3階 ショウ", "お金", "時間", 1360)]):
        text(d, (x, 240), name, 52, fill=WHITE)
        text(d, (x - 170, 480), a, 64, fill=LINE)
        arrow(d, (x - 80, 480), (x + 80, 480), color=AMBER, width=8, head=34)
        text(d, (x + 170, 480), b, 64, fill=AMBER)
    text(d, (560, 660), "時間を使ってお金を守る", 40, fill=LINE_DIM)
    text(d, (1360, 660), "お金を使って時間を作る", 40, fill=LINE_DIM)
    return im


def s06i():
    im, d = canvas()
    bldg(d, highlight=[3], x=300, w=440)
    phone(d, 1300, 300, w=200, h=340)
    for k in range(4):
        d.arc([1560, 300 + k * 80, 1640, 360 + k * 80], 200, 340, fill=AMBER, width=5)
    text(d, (1400, 720), "電話の数", 56, fill=AMBER)
    return im


def s07a():
    def draw(d, box):
        desk(d, 800, 760, w=560)
        person(d, 600, box[3] - 8, h=430, pose="sit", color=AMBER)
        window(d, 1300, 260, w=360, h=380)
        text(d, (1040, 700), "部長", 40, fill=LINE)
    return floor_room(3, "部長", draw)()


def s07b():
    def draw(d, box):
        person(d, 420, box[3] - 8, h=440, color=AMBER)
        phone(d, 520, 480, w=110, h=190)
        labels = ["前の会社の後輩", "知り合いの知り合い", "転職の相談", "いい人いない？"]
        for k, lab in enumerate(labels):
            x0 = 760 + (k % 2) * 480
            y0 = 260 + (k // 2) * 220
            bubble(d, (x0, y0, x0 + 440, y0 + 150), lab, 38, color=AMBER if k == 3 else LINE)
    return floor_room(3, "毎週の電話", draw)()


def s07c():
    im, d = canvas()
    d.rectangle([560, 220, 1360, 800], outline=WHITE, width=6)
    text(d, (960, 330), "募集", 80, fill=AMBER)
    text(d, (960, 480), "電気工事士", 80, fill=WHITE)
    text(d, (960, 640), "人が足りません", 48, fill=LINE_DIM)
    return im


def s07d():
    im, d = canvas()
    text(d, (960, 300), "新しい仕事の話は、仲のいい友達から来る？", 56, fill=WHITE)
    text(d, (960, 560), "答えは、逆だった", 96, fill=AMBER)
    return im


def ties(d, cx, cy, n_close, n_far, highlight_far=True, label=None):
    person(d, cx, cy + 70, h=150, color=WHITE, width=4)
    import math
    for k in range(n_close):
        a = 2 * math.pi * k / max(1, n_close)
        x, y = cx + 150 * math.cos(a), cy + 150 * math.sin(a)
        d.line([(cx, cy), (x, y)], fill=LINE, width=5)
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=LINE)
    for k in range(n_far):
        a = 2 * math.pi * k / max(1, n_far) + 0.2
        x, y = cx + 300 * math.cos(a), cy + 280 * math.sin(a)
        dashed(d, (cx, cy), (x, y), color=AMBER if highlight_far else LINE_DIM, width=3)
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=AMBER if highlight_far else LINE_DIM)
    if label:
        text(d, (cx, cy + 340), label, 40, fill=WHITE)


def s07e(d):
    ties(d, 960, 480, 5, 14)
    text(d, (420, 300), "仲のいい友達（実線）", 36, fill=LINE)
    text(d, (1500, 300), "ちょっとした知り合い（点線）", 36, fill=AMBER)


def s07f():
    im, d = canvas()
    ties(d, 960, 460, 5, 14)
    text(d, (960, 120), "仕事につながりやすかったのは「ちょっとした知り合い」", 44, fill=AMBER)
    return im


def s07g():
    im, d = canvas()
    ties(d, 560, 430, 4, 22, label="リク：何百人")
    ties(d, 1400, 430, 3, 3, highlight_far=False, label="ケンタ：数人")
    return im


def s07j():
    im, d = canvas()
    d.rectangle([560, 520, 1360, 560], fill=LINE)
    for k in range(4):
        x = 660 + k * 200
        person(d, x, 780, h=260, color=AMBER if k == 0 else LINE, pose="sit", width=5)
    text(d, (960, 200), "20年ぶりに、同じテーブルへ", 56, fill=WHITE)
    return im


def s08a():
    im, d = canvas()
    phone(d, 760, 160, w=400, h=680)
    d.rounded_rectangle([700, 360, 1220, 560], radius=20, fill=NAVY, outline=LINE, width=5)
    text(d, (960, 410), "同期グループ", 34, fill=LINE_DIM)
    text(d, (960, 490), "送別会のお知らせ", 50, fill=WHITE)
    bubble(d, (1280, 300, 1780, 440), "断ろうかな…", 42, color=LINE_DIM)
    return im


def s08b():
    im, d = canvas()
    phone(d, 760, 160, w=400, h=680)
    d.rounded_rectangle([700, 360, 1220, 600], radius=20, fill=NAVY, outline=AMBER, width=5)
    text(d, (960, 410), "リク", 34, fill=AMBER)
    text(d, (960, 480), "来いよ。", 54, fill=WHITE)
    text(d, (960, 550), "渡したいものがあるって", 34, fill=WHITE)
    return im


def s08f():
    im, d = canvas()
    d.line([(100, 760), (1820, 760)], fill=WHITE, width=6)
    d.rectangle([100, 760, 1820, 800], outline=LINE_DIM, width=3)
    person(d, 760, 750, h=420, color=AMBER, width=6)
    person(d, 1100, 750, h=440, color=LINE, width=6)
    text(d, (760, 260), "ケンタ", 40, fill=AMBER)
    text(d, (1100, 240), "リク", 40, fill=LINE)
    bubble(d, (1180, 220, 1760, 380), "過去問、送るよ", 46, color=LINE, tail=(1120, 330))
    return im


def s09a():
    im, d = canvas()
    phone(d, 500, 200, w=360, h=620)
    text(d, (680, 470), "暗記アプリ", 40, fill=WHITE)
    text(d, (680, 560), "from ユイ", 32, fill=LINE_DIM)
    d.rectangle([1060, 240, 1460, 780], outline=WHITE, width=5)
    for k in range(6):
        d.line([(1100, 320 + k * 70), (1420, 320 + k * 70)], fill=LINE_DIM, width=3)
    text(d, (1260, 820), "過去問の解き方 from ショウ", 32, fill=LINE_DIM)
    return im


def s09b():
    im, d = canvas()
    calendar(d, 260, 260, mark=(2, 3, "7月 試験"), w=520, h=460)
    clock(d, 1200, 400, 12, 15, r=130, label="昼休み 15分")
    clock(d, 1560, 400, 6, 20, r=130, label="帰りの電車 20分")
    text(d, (1380, 720), "「今月」の横に、小さな場所", 44, fill=AMBER)
    return im


def s09c():
    im, d = canvas()
    phone(d, 360, 200, w=380, h=640)
    text(d, (550, 470), "合格", 90, fill=AMBER)
    d.rectangle([980, 280, 1620, 760], outline=WHITE, width=5)
    text(d, (1300, 400), "現場の、頼れる人に", 44, fill=WHITE)
    text(d, (1300, 470), "なっていますか", 44, fill=WHITE)
    text(d, (1300, 640), "今日から、なる。", 60, fill=AMBER)
    return im


def s10b():
    im, d = canvas()
    items = ["お金の心配が、考える時間を奪う", "余裕のなさが、人に「今日」を選ばせる",
             "お金がないと、時間を自分の手で払うしかない", "余裕のある人に、次の道を運ぶ知り合いが増える"]
    for k, s in enumerate(items):
        y = 230 + k * 160
        d.rectangle([220, y - 55, 1700, y + 55], outline=AMBER if k == 0 else LINE, width=4)
        text(d, (300, y), f"理由{k + 1}", 40, fill=AMBER, anchor="lm")
        text(d, (480, y), s, 44, fill=WHITE, anchor="lm")
    return im


def s10c():
    im, d = canvas()
    floors = bldg(d, highlight=[0], x=300, w=440, poses=["look_up", "stand", "stand", "look_down"])
    for i in range(3):
        a, top, b, bot = floors[i]
        x, y = b - 100, bot
        step = (bot - top) / 5
        for k in range(5):
            d.line([(x, y), (x + 20, y), (x + 20, y - step)], fill=AMBER, width=4)
            x, y = x + 20, y - step
    text(d, (1400, 420), "このビルには、階段がある", 56, fill=WHITE)
    text(d, (1400, 540), "あなたは、何階？", 72, fill=AMBER)
    return im


def s11():
    im, d = canvas()
    building(d, 820, 260, 280, 420, highlight=[2], width=5)
    text(d, (960, 780), "人生の断面図", 90, fill=WHITE)
    text(d, (960, 870), "次の図面を描いて、お待ちしています", 40, fill=LINE)
    return im


SCENES = {
    "S01a": s01a,
    "S01b": card("", ["お金がない人ほど、", "時間もない。"], amber=(1,), size=110),
    "S02a": s02a,
    "S02b": envelopes(),
    "S02c": s02c,
    "S02d": s02d,
    "S02e": s02e,
    "S03a": s03a,
    "S03b": snow_room(0, "始発で出よう"),
    "S03c": snow_room(1, "学童の送り、どうしよう"),
    "S03d": snow_room(2, "明日は在宅にしよう"),
    "S03e": snow_room(3, "タクシーを予約しておくか"),
    "S03f": s03f,
    "S04a": s04a,
    "S04b": s04b,
    "S04c": s04c,
    "S04d": research("インドのサトウキビ農家", "2013年", s04d),
    "S04e": research("インドのサトウキビ農家", "2013年", s04e),
    "S04f": s04f,
    "S04g": strength(0, "計画性がない？", "限られた中でやりくりする力"),
    "S04h": reason(1, "お金の心配が、", "考える時間を奪う"),
    "S04i": stairs_q(0, "年収500万なら、", "頭に空きはできる？"),
    "S05a": s05a,
    "S05b": s05b,
    "S05c": s05c,
    "S05d": research("貧しさと心の研究のまとめ", "2014年", s05d),
    "S05e": s05e,
    "S05f": strength(1, "いつも疲れている？", "止めずに回し続ける力"),
    "S05g": reason(2, "余裕のなさが、", "人に「今日」を選ばせる"),
    "S05h": s05h,
    "S06a": s06a,
    "S06b": s06b,
    "S06c": s06c,
    "S06d": s06d,
    "S06e": research("お金で時間を買うと幸せになるか", "2017年", s06e),
    "S06f": s06f,
    "S06g": strength(2, "いちばん普通？", "お金を時間に換える力"),
    "S06h": reason(3, "お金がないと、", "時間を自分の手で払うしかない"),
    "S06i": s06i,
    "S07a": s07a,
    "S07b": s07b,
    "S07c": s07c,
    "S07d": s07d,
    "S07e": research("約2000万人の仕事のSNSでの実験", "2022年", s07e),
    "S07f": s07f,
    "S07g": s07g,
    "S07h": strength(3, "運がよかった？", "人と人をつなぐ力"),
    "S07i": reason(4, "余裕のある人のまわりに、", "次の道を運ぶ知り合いが増える"),
    "S07j": s07j,
    "S08a": s08a,
    "S08b": s08b,
    "S08c": envelopes(),
    "S08d": envelopes(labels=["", "自分の名前で仕事を", "技術士に", "4人とまだ会ってる？"]),
    "S08e": envelopes(opened=0, labels=["現場の、頼れる人に", "", "", ""]),
    "S08f": s08f,
    "S09a": s09a,
    "S09b": s09b,
    "S09c": s09c,
    "S10a": card("", ["それは、誰かが", "怠けているからではない"], amber=(1,), size=90),
    "S10b": s10b,
    "S10c": s10c,
    "S11": s11,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    for key, fn in SCENES.items():
        save_png(fn(), OUT / f"{key}_絵.png")
    print("ok:", len(SCENES), "枚 →", OUT)


if __name__ == "__main__":
    main()

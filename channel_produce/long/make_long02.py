"""長尺第2弾「頼りにされていた人が辞めた職場は、10年後どうなるのか」の場面の絵（1920×1080）。

python channel_produce/long/make_long02.py → channel_produce/long/02_辞めた職場/media/S01a_絵.png …
部品は make_long01.py のものを使い、階のラベルと名前だけ役職に差し替える。
絵のルール（スキル5章）：たとえは言葉で言う／何の絵か分かる目印を入れる／文字は最小36px。
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_long01 as L  # noqa: E402
from make_long01 import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, big, bldg, bubble, building, calendar,  # noqa: E402
                         canvas, card, clock, dashed, desk, floor_room, person, phone, reason, save_png,
                         text, window)

ROLES = ["平社員", "係長", "課長", "部長"]
NAMES = ["ミナト", "アオイ", "タクヤ", "ジュン"]
L.INCOMES, L.NAMES = ROLES, NAMES
OUT = HERE / "02_辞めた職場" / "media"


def b(d, **kw):
    return bldg(d, labels=ROLES, names=NAMES, **kw)


def strength(floor, misread, power):
    def make():
        im, d = canvas()
        b(d, highlight=[floor], x=220, w=420)
        text(d, (1300, 330), "ほかの階からは", 40, fill=LINE_DIM)
        text(d, (1300, 410), f"「{misread}」", 54, fill=WHITE)
        arrow(d, (1300, 470), (1300, 560), color=AMBER, width=6)
        text(d, (1300, 620), f"{NAMES[floor]}の強み", 40, fill=LINE_DIM)
        text(d, (1300, 700), power, 64, fill=AMBER)
        return im
    return make


def floor_room_as(floor, sub, draw, name):
    """部屋の見出しの名前を差し替える（10年後の2階はミナト）"""
    def make():
        old = L.NAMES[floor]
        L.NAMES[floor] = name
        try:
            return floor_room(floor, sub, draw)()
        finally:
            L.NAMES[floor] = old
    return make


def research(title, year, draw):
    def make():
        im, d = canvas()
        text(d, (960, 120), f"研究｜{title}（{year}）", 44, fill=LINE)
        draw(d)
        return im
    return make


def drawing(d, x, y, w=360, h=250, mark=None, color=WHITE):
    """図面1枚（枠・部品の線・寸法線）"""
    d.rectangle([x, y, x + w, y + h], outline=color, width=4)
    d.rectangle([x + 60, y + 70, x + w - 60, y + h - 70], outline=LINE, width=3)
    d.ellipse([x + w / 2 - 30, y + h / 2 - 30, x + w / 2 + 30, y + h / 2 + 30], outline=LINE, width=3)
    d.line([(x + 60, y + h - 35), (x + w - 60, y + h - 35)], fill=LINE_DIM, width=2)
    text(d, (x + w / 2, y + h - 35), "120", 24, fill=LINE_DIM)
    if mark:
        d.ellipse([x + w - 90, y + 10, x + w - 10, y + 90], outline=AMBER, width=5)
        text(d, (x + w - 50, y + 50), mark, 30, fill=AMBER)


def words4(d, y=250):
    """「辞めます」の4文字"""
    for i, ch in enumerate("辞めます"):
        x = 560 + i * 270
        d.rectangle([x - 110, y, x + 110, y + 220], outline=AMBER, width=6)
        text(d, (x, y + 110), ch, 140, fill=WHITE)


# ---------------------------------------------------------------- 場面

def s01a():
    im, d = canvas()
    words4(d)
    text(d, (960, 640), "同じ4文字、4つの重さ", 60, fill=LINE)
    return im


def s01b():
    im, d = canvas()
    d.line([(260, 560), (1660, 560)], fill=WHITE, width=5)
    for k, (x, lab) in enumerate([(300, "言われた日"), (960, "3年後"), (1600, "5年後")]):
        d.ellipse([x - 16, 544, x + 16, 576], fill=AMBER if k == 2 else WHITE)
        text(d, (x, 640), lab, 44, fill=AMBER if k == 2 else WHITE)
    text(d, (1600, 460), "効いてくる", 52, fill=AMBER)
    arrow(d, (1500, 470), (1580, 530), color=AMBER, width=6)
    return im


def s02a():
    im, d = canvas()
    b(d, x=700, w=520)
    text(d, (960, 140), "ある機械メーカーの設計部", 52, fill=WHITE)
    return im


def s02b():
    im, d = canvas()
    b(d, highlight=[0, 1, 2, 3], x=320, w=460)
    for i, (n, r, age) in enumerate(zip(NAMES, ROLES, ["26歳・入社4年目", "38歳", "45歳", "54歳"])):
        y = 790 - i * 155
        text(d, (1180, y), f"{i + 1}階  {r}  {n}", 50, fill=WHITE, anchor="lm")
        text(d, (1180, y + 52), age, 34, fill=LINE_DIM, anchor="lm")
    return im


def s02c():
    im, d = canvas()
    clock(d, 360, 420, 5, 0, r=150, label="10月の金曜 17:00")
    person(d, 960, 820, h=420, color=AMBER, width=6)
    person(d, 1400, 820, h=380, pose="sit", color=LINE, width=6)
    desk(d, 1500, 820, w=320)
    bubble(d, (680, 240, 1280, 400), "来年の3月で、辞めます", 46, tail=(960, 450))
    text(d, (960, 880), "アオイ（係長）", 40, fill=AMBER)
    text(d, (1450, 880), "タクヤ（課長）", 40, fill=LINE)
    return im


def s02d():
    im, d = canvas()
    text(d, (960, 260), "まともな人から、先に辞めていく？", 66, fill=WHITE)
    d.rectangle([420, 420, 900, 700], outline=AMBER, width=6)
    text(d, (660, 520), "半分は", 56, fill=WHITE)
    text(d, (660, 620), "正しい", 64, fill=AMBER)
    d.rectangle([1020, 420, 1500, 700], outline=LINE, width=6)
    text(d, (1260, 520), "半分は", 56, fill=WHITE)
    text(d, (1260, 620), "違う", 64, fill=LINE)
    return im


def s02e():
    im, d = canvas()
    floors = b(d, x=340, w=460)
    for i, (a, top, bb, bot) in enumerate(floors):
        text(d, (bb + 330, (top + bot) / 2), "「辞めます」", 44, fill=AMBER if i == 1 else WHITE)
    text(d, (1500, 160), "1階から、のぼっていく", 48, fill=LINE)
    arrow(d, (1700, 820), (1700, 260), color=AMBER, width=6)
    return im


def mina_desk(d, box, thought=None, with_aoi=True, aoi_gone=False):
    desk(d, 560, box[3] - 6, w=520)
    person(d, 420, box[3] - 6, h=330, pose="sit", color=AMBER)
    drawing(d, 470, 470, w=240, h=160)
    if with_aoi:
        person(d, 1180, box[3] - 6, h=330, pose="sit", color=LINE)
        desk(d, 1300, box[3] - 6, w=420)
        text(d, (1200, 330), "アオイ（係長）", 40, fill=LINE)
    if aoi_gone:
        d.rectangle([1060, 520, 1500, box[3] - 10], outline=LINE_DIM, width=3)
        text(d, (1280, 680), "空いた席", 44, fill=LINE_DIM)
    if thought:
        bubble(d, (240, 250, 860, 400), thought, 44, tail=(420, 470))


def s03a(d, box):
    mina_desk(d, box, "困ったら、隣に聞く")


def s03b(d, box):
    mina_desk(d, box)
    drawing(d, 900, 420, w=300, h=200, mark="OK")
    arrow(d, (720, 540), (890, 520), color=AMBER, width=6)
    arrow(d, (1220, 520), (1560, 520), color=AMBER, width=6)
    text(d, (1640, 520), "工場", 44, fill=WHITE)
    text(d, (1050, 680), "アオイの目を通ってから", 40, fill=AMBER)


def s03c(d, box):
    mina_desk(d, box, "4月から、誰に聞けば？", with_aoi=False, aoi_gone=True)


def quiz():
    im, d = canvas()
    text(d, (960, 200), "1問", 60, fill=AMBER)
    text(d, (960, 330), "辞めやすいのは、どっち？", 66, fill=WHITE)
    for x, lab, col in [(620, "仕事ができる人", LINE), (1300, "できない人", LINE)]:
        d.rectangle([x - 260, 460, x + 260, 760], outline=col, width=6)
        person(d, x, 700, h=200, color=WHITE, width=5)
        text(d, (x, 810), lab, 48, fill=WHITE)
    text(d, (960, 900), "画面を止めて、考えてみてほしい", 40, fill=LINE_DIM)
    return im


def r_mc(d):
    text(d, (960, 215), "24の研究・約7,700人", 48, fill=WHITE)
    for k, (lab, h, col) in enumerate([("成績のいい人", 160, AMBER), ("成績の低い人", 360, LINE)]):
        x = 700 + k * 520
        d.rectangle([x - 110, 820 - h, x + 110, 820], fill=col)
        text(d, (x, 870), lab, 44, fill=WHITE)
    d.line([(480, 820), (1440, 820)], fill=WHITE, width=4)
    text(d, (960, 930), "高さ＝辞める割合（平均の傾向のイメージ）", 36, fill=LINE_DIM)


def r_mc2(d):
    r_mc(d)
    text(d, (960, 310), "成績のいい人ほど、辞めにくかった", 56, fill=AMBER)


def hole():
    im, d = canvas()
    for k in range(5):
        x = 360 + k * 300
        if k == 2:
            d.rectangle([x - 110, 380, x + 110, 760], outline=AMBER, width=6)
            text(d, (x, 570), "？", 120, fill=AMBER)
        else:
            person(d, x, 760, h=360, color=LINE_DIM, width=5)
    text(d, (960, 220), "頼りにされていた人の穴は、目立つ", 56, fill=WHITE)
    return im


def stairs_to(floor, q):
    def make():
        im, d = canvas()
        floors = b(d, highlight=[floor], x=340, w=460)
        a, top, bb, bot = floors[floor]
        text(d, (1480, 470), q, 54, fill=WHITE)
        arrow(d, (bb + 150, (top + bot) / 2), (1090, 470), color=AMBER, width=6)
        return im
    return make


def s05a(d, box):
    person(d, 420, box[3] - 6, h=360, color=AMBER)
    for k, lab in enumerate(["部下の図面", "工場との話", "お客さんの無理"]):
        bubble(d, (720 + k * 330, 330 + (k % 2) * 140, 1020 + k * 330, 450 + (k % 2) * 140), lab, 40)
    text(d, (960, 800), "この設計部で15年", 44, fill=LINE)


def voices():
    im, d = canvas()
    text(d, (960, 140), "「図面を確かめる人を、増やしてください」", 50, fill=WHITE)
    for k, (yr, ans) in enumerate([("3年前", "今は予算がない"), ("2年前", "今は予算がない"), ("去年", "今は予算がない")]):
        x = 420 + k * 540
        text(d, (x, 300), yr, 48, fill=AMBER)
        person(d, x - 90, 640, h=260, color=AMBER, width=5)
        arrow(d, (x - 20, 470), (x + 120, 470), color=AMBER, width=5)
        person(d, x + 170, 640, h=260, color=LINE, width=5)
        text(d, (x + 40, 730), ans, 40, fill=LINE_DIM)
    return im


def r_hir(d):
    person(d, 960, 760, h=300, color=WHITE, width=5)
    text(d, (960, 260), "組織に不満を持った人の、2つの道", 52, fill=WHITE)
    for x, lab, col in [(520, "声を上げる", AMBER), (1400, "去る", LINE)]:
        arrow(d, (960 + (-60 if x < 960 else 60), 560), (x + (215 if x < 960 else -215), 560), color=col, width=8, head=34)
        d.rectangle([x - 200, 500, x + 200, 620], outline=col, width=6)
        text(d, (x, 560), lab, 52, fill=col)


def r_hir2(d):
    text(d, (960, 260), "まず声を上げ、届かないと、去る", 56, fill=WHITE)
    steps = [("声を上げる", AMBER), ("届かない", LINE_DIM), ("去る", LINE)]
    for k, (lab, col) in enumerate(steps):
        x = 420 + k * 540
        d.rectangle([x - 200, 480, x + 200, 620], outline=col, width=6)
        text(d, (x, 550), lab, 52, fill=col)
        if k < 2:
            arrow(d, (x + 210, 550), (x + 330, 550), color=AMBER, width=7)


def s05f():
    im, d = canvas()
    for k in range(3):
        x = 340 + k * 360
        d.rectangle([x - 150, 300, x + 150, 520], outline=LINE_DIM, width=4)
        text(d, (x, 380), ["3年前", "2年前", "去年"][k], 40, fill=LINE_DIM)
        text(d, (x, 460), "人を増やして", 38, fill=WHITE)
        arrow(d, (x + 160, 410), (x + 200, 410), color=LINE_DIM, width=4)
    d.rectangle([1340, 280, 1760, 540], outline=AMBER, width=8)
    text(d, (1550, 410), "辞めます", 72, fill=AMBER)
    text(d, (960, 720), "3年分の声の、最後の形", 60, fill=WHITE)
    return im


def s06a(d, box):
    person(d, 960, box[3] - 6, h=360, color=AMBER)
    arrow(d, (960, 300), (960, 420), color=LINE, width=6)
    text(d, (960, 260), "上から：数字", 44, fill=LINE)
    arrow(d, (960, box[3] + 0), (960, box[3] - 90), color=WHITE, width=6)
    text(d, (1350, 640), "下から：人", 44, fill=WHITE)


def s06b():
    im, d = canvas()
    text(d, (960, 140), "予算の表", 52, fill=WHITE)
    rows = ["新しい機械", "工場の修理", "システム更新", "広告", "設計部の人を1人"]
    for k, r in enumerate(rows):
        y = 260 + k * 110
        d.rectangle([520, y, 1400, y + 90], outline=LINE, width=3)
        text(d, (560, y + 45), r, 44, fill=WHITE if k < 4 else AMBER, anchor="lm")
    d.line([(540, 745), (1380, 745)], fill=AMBER, width=8)
    text(d, (960, 900), "毎年、一番下で消されていた", 48, fill=LINE)
    return im


def s06c(d, box):
    person(d, 360, box[3] - 6, h=330, pose="sit", color=AMBER)
    desk(d, 480, box[3] - 6, w=420)
    for k in range(4):
        drawing(d, 760 + k * 60, 300 + k * 50, w=300, h=200)
    text(d, (1300, 760), "アオイが見ていた図面：月40枚", 44, fill=WHITE)
    bubble(d, (180, 250, 700, 380), "誰に、どう割り振る？", 42, tail=(360, 460))


def s07a(d, box):
    person(d, 360, box[3] - 6, h=360, color=AMBER)
    for k, lab in enumerate(["設計", "工場", "営業", "会社全体"]):
        x = 760 + k * 250
        d.rectangle([x - 100, 380, x + 100, 560], outline=AMBER if k == 3 else LINE, width=5)
        text(d, (x, 470), lab, 40, fill=WHITE)


def s07b():
    im, d = canvas()
    text(d, (960, 160), "4階に届いた「辞めます」", 52, fill=WHITE)
    d.rectangle([520, 300, 1400, 720], outline=LINE, width=4)
    for k, (a, v) in enumerate([("離職", "1人"), ("補充", "来年度の採用で"), ("売り上げ", "変わらず")]):
        y = 380 + k * 120
        text(d, (580, y), a, 48, fill=LINE, anchor="lm")
        text(d, (1340, y), v, 48, fill=AMBER if k == 2 else WHITE, anchor="rm")
    return im


def s07c():
    im, d = canvas()
    for k, (lab, col) in enumerate([("3階から見えるもの：人の顔", WHITE), ("4階から見えるもの：表の数字", AMBER)]):
        y = 340 + k * 300
        text(d, (960, y - 90), lab, 50, fill=col)
        if k == 0:
            for j in range(5):
                person(d, 600 + j * 180, y + 160, h=170, color=LINE, width=4)
        else:
            for j in range(5):
                d.rectangle([560 + j * 170, y, 700 + j * 170, y + 110], outline=AMBER, width=3)
                text(d, (630 + j * 170, y + 55), ["売上", "利益", "原価", "人数", "離職"][j], 34, fill=WHITE)
    return im


def r_hc(d):
    text(d, (960, 220), "48の調査・約2万5000人", 52, fill=WHITE)
    vals = [("売り上げ・利益", 0.03, LINE), ("品質・安全", 0.12, AMBER)]
    for k, (lab, v, col) in enumerate(vals):
        y = 420 + k * 220
        text(d, (520, y), lab, 48, fill=WHITE, anchor="rm")
        d.rectangle([580, y - 40, 580 + v * 8000, y + 40], fill=col)
    text(d, (960, 840), "人が辞めることと、悪くなる数字の結びつきの強さ", 40, fill=LINE_DIM)


def r_hc2(d):
    r_hc(d)
    text(d, (1640, 640), "約4倍", 72, fill=AMBER)


def r_heavey(d):
    text(d, (960, 230), "82の研究のまとめ", 52, fill=WHITE)
    d.line([(520, 800), (1440, 800)], fill=WHITE, width=4)
    d.line([(520, 800), (520, 340)], fill=WHITE, width=4)
    d.line([(560, 400), (1400, 760)], fill=AMBER, width=8)
    text(d, (980, 870), "人が多く辞める →", 44, fill=WHITE)
    text(d, (400, 560), "成果", 44, fill=WHITE)
    text(d, (1250, 560), "下がりやすい", 48, fill=AMBER)


def s08e():
    im, d = canvas()
    d.rectangle([560, 160, 1360, 860], outline=WHITE, width=5)
    for k in range(6):
        y = 200 + k * 110
        d.rectangle([600, y, 1320, y + 80], outline=LINE, width=3)
    text(d, (960, 240), "表の一番上：売り上げ", 40, fill=LINE_DIM)
    d.rectangle([600, 750, 1320, 830], outline=AMBER, width=6)
    text(d, (960, 790), "図面の一番下：品質・安全", 44, fill=AMBER)
    return im


def s09a(d, box):
    mina_desk(d, box, "自分で決めて出す", with_aoi=False, aoi_gone=True)


def s09b():
    im, d = canvas()
    text(d, (960, 140), "2年目の秋　工場から電話", 52, fill=WHITE)
    drawing(d, 300, 330, w=560, h=380)
    text(d, (580, 760), "図面：120.0", 48, fill=WHITE)
    d.rectangle([1100, 360, 1560, 680], outline=AMBER, width=6)
    d.ellipse([1240, 430, 1420, 610], outline=WHITE, width=5)
    text(d, (1330, 760), "部品：入らない", 48, fill=AMBER)
    text(d, (960, 880), "寸法が、1ミリ違っていた", 48, fill=LINE)
    return im


def s09c(d, box):
    person(d, 420, box[3] - 6, h=330, pose="sit", color=AMBER)
    desk(d, 540, box[3] - 6, w=420)
    clock(d, 1300, 500, 10, 0, r=150, label="毎晩 22:00")
    text(d, (960, 300), "3年目：図面の確かめ係", 48, fill=WHITE)


def s09d():
    im, d = canvas()
    text(d, (960, 140), "5年目　作り直しの費用", 52, fill=WHITE)
    for k, (lab, h, col) in enumerate([("4年目", 160, LINE), ("5年目", 480, AMBER)]):
        x = 700 + k * 520
        d.rectangle([x - 120, 820 - h, x + 120, 820], fill=col)
        text(d, (x, 870), lab, 44, fill=WHITE)
    text(d, (1560, 380), "3倍", 90, fill=AMBER)
    d.line([(480, 820), (1440, 820)], fill=WHITE, width=4)
    return im


def s09e():
    im, d = canvas()
    for k in range(5):
        x = 360 + k * 300
        h = 60 + k * 90
        d.rectangle([x - 90, 760 - h, x + 90, 760], outline=AMBER, width=5)
        text(d, (x, 820), f"{k + 1}年目", 40, fill=WHITE)
    text(d, (960, 200), "確かめる人がいない時間が、たまっていく", 52, fill=WHITE)
    return im


def r_heavey2(d):
    text(d, (960, 230), "人が辞めにくい職場にあるもの", 56, fill=WHITE)
    for k, lab in enumerate(["人への投資", "職場とのつながり"]):
        x = 620 + k * 680
        d.rectangle([x - 260, 420, x + 260, 640], outline=AMBER, width=6)
        text(d, (x, 530), lab, 56, fill=AMBER)


def s10b():
    im, d = canvas()
    person(d, 620, 800, h=380, color=AMBER, width=6)
    bubble(d, (300, 240, 1000, 400), "人を増やしてください", 48, tail=(620, 440))
    arrow(d, (1000, 600), (1280, 600), color=AMBER, width=8)
    person(d, 1400, 800, h=380, color=LINE, width=6)
    text(d, (1400, 880), "届く", 52, fill=AMBER)
    return im


def s10c(d, box):
    desk(d, 560, box[3] - 6, w=520)
    person(d, 420, box[3] - 6, h=330, pose="sit", color=LINE)
    person(d, 1180, box[3] - 6, h=330, pose="sit", color=AMBER)
    desk(d, 1300, box[3] - 6, w=420)
    text(d, (420, 300), "新人", 44, fill=LINE)
    text(d, (1180, 300), "係長ミナト", 44, fill=AMBER)
    bubble(d, (240, 340, 880, 470), "この寸法、大丈夫ですか", 42, tail=(420, 520))


def s10d(d, box):
    s10c(d, box)
    drawing(d, 760, 560, w=300, h=200, mark="OK")


def s10e():
    im, d = canvas()
    text(d, (960, 140), "10年後の予算の表", 52, fill=WHITE)
    rows = ["新しい機械", "工場の修理", "システム更新", "広告", "設計部の人を1人"]
    for k, r in enumerate(rows):
        y = 260 + k * 110
        d.rectangle([520, y, 1400, y + 90], outline=AMBER if k == 4 else LINE, width=6 if k == 4 else 3)
        text(d, (560, y + 45), r, 44, fill=AMBER if k == 4 else WHITE, anchor="lm")
    text(d, (1460, 705), "消されなかった", 48, fill=AMBER, anchor="lm")
    return im


def s11b():
    im, d = canvas()
    floors = b(d, highlight=[1], x=340, w=460)
    a, top, bb, bot = floors[1]
    bubble(d, (1000, 300, 1760, 460), "人を増やしてください", 48, tail=(bb + 20, (top + bot) / 2))
    text(d, (1380, 620), "最後に言ったのは、誰？", 56, fill=WHITE)
    return im


def s11c():
    im, d = canvas()
    b(d, x=340, w=460, poses=["look_up", "stand", "stand", "look_down"])
    text(d, (1380, 460), "あなたは、何階の窓から", 56, fill=WHITE)
    text(d, (1380, 570), "その声を聞いている？", 56, fill=AMBER)
    return im


SCENES = {
    "S01a": s01a,
    "S01b": s01b,
    "S02a": s02a,
    "S02b": s02b,
    "S02c": s02c,
    "S02d": s02d,
    "S02e": s02e,
    "S03a": floor_room(0, "設計部", s03a),
    "S03b": floor_room(0, "設計部", s03b),
    "S03c": floor_room(0, "10月の金曜", s03c),
    "S03d": strength(0, "まだ何もできない？", "素直に聞ける力"),
    "S03e": quiz,
    "S04a": research("成績と、会社を辞めること", "1987年", r_mc),
    "S04b": research("成績と、会社を辞めること", "1987年", r_mc2),
    "S04c": hole,
    "S04d": stairs_to(1, "なぜ、アオイは辞めるのか"),
    "S05a": floor_room(1, "15年", s05a),
    "S05b": voices,
    "S05c": voices,
    "S05d": research("離脱・発言・忠誠（ハーシュマン）", "1970年", r_hir),
    "S05e": research("離脱・発言・忠誠（ハーシュマン）", "1970年", r_hir2),
    "S05f": s05f,
    "S05g": strength(1, "会社を見捨てた？", "黙らずに言い続ける力"),
    "S05h": stairs_to(2, "その声を受け取った3階では？"),
    "S06a": floor_room(2, "板挟み", s06a),
    "S06b": s06b,
    "S06c": floor_room(2, "来年の予定表", s06c),
    "S06d": strength(2, "部下を守れなかった？", "板挟みでも、つなぎ続ける力"),
    "S07a": floor_room(3, "会社全体", s07a),
    "S07b": s07b,
    "S07c": s07c,
    "S07d": strength(3, "現場を見ていない？", "全体を見渡す力"),
    "S07e": card("", ["1人辞めても、", "会社は変わらない？"], amber=(1,), size=96),
    "S08a": research("社員が辞めることと、会社の成績", "2013年", r_hc),
    "S08b": research("社員が辞めることと、会社の成績", "2013年", r_hc),
    "S08c": research("社員が辞めることと、会社の成績", "2013年", r_hc2),
    "S08d": research("人が多く辞める職場の研究のまとめ", "2013年", r_heavey),
    "S08e": s08e,
    "S09a": floor_room(0, "4月", s09a),
    "S09b": s09b,
    "S09c": floor_room(2, "3年目", s09c),
    "S09d": s09d,
    "S09e": s09e,
    "S10a": research("人が多く辞める職場の研究のまとめ", "2013年", r_heavey2),
    "S10b": s10b,
    "S10c": floor_room_as(1, "10年後", s10c, "ミナト"),
    "S10d": floor_room_as(1, "10年後", s10d, "ミナト"),
    "S10e": s10e,
    "S11a": card("", ["変わるのは、", "5年後の品質と安全"], amber=(1,), size=96),
    "S11b": s11b,
    "S11c": s11c,
    "S12": L.s11,
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

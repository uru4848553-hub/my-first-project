"""ショート6〜10：長尺第1弾「なぜお金がない人ほど、時間もないのか」から切り出した5本。

python channel_produce/shorts/make_shorts_6to10.py      → 5本とも
python channel_produce/shorts/make_shorts_6to10.py 8    → 8本目だけ

どの回も、最初の1秒は「動き＋音＋短い言葉」。最後は本編（長尺）への入口にする。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blueprint import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, bubble, building_scene, calendar, canvas,  # noqa: E402
                       clock, dashed, desk, ease, intro_stack, loop_end, person, phone, room, sky, text, window)
from make_shorts_2to5 import write_folder  # noqa: E402

LABELS = ["年収 300万", "年収 500万", "年収 700万", "年収 1000万"]
NAMES = ["ケンタ", "ユイ", "ショウ", "リク"]
TAIL = "本編で、4人の20年をたどる。あなたは、何階でした？"


def snow(d, box, n=30, phase=0):
    x0, y0, x1, y1 = box
    for k in range(n):
        x = x0 + 20 + (k * 97) % max(1, int(x1 - x0 - 40))
        y = y0 + 20 + ((k * 61) + phase * 12) % max(1, int(y1 - y0 - 40))
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=WHITE)


def notify(title, body, color=AMBER, snowy=False):
    """スマホに通知がスッと降りてくる（約1.1秒）"""
    def make():
        frames = []
        for f in range(34):
            im, d = canvas()
            t = f / 30
            if snowy:
                snow(d, (60, 640, 1020, 1560), 60, phase=f)
            phone(d, 340, 700, w=400, h=760)
            y = 700 + 260 * ease(min(1, t / 0.3)) - 120
            d.rounded_rectangle([290, y, 790, y + 200], radius=24, fill=NAVY, outline=color, width=6)
            text(d, (540, y + 60), title, 36, fill=LINE_DIM)
            text(d, (540, y + 135), body, 52, fill=color)
            frames.append(im)
        return frames
    return make


def floor_room(floor, sub, draw):
    def make():
        im, d = canvas()
        box = room(d, floor, f"{floor + 1}F｜{LABELS[floor].replace(' ', '')}｜{NAMES[floor]}{('｜' + sub) if sub else ''}", title_size=40)
        draw(d, box)
        return im
    return make


def thought_room(floor, sub, thought, extra=None):
    def draw(d, box):
        person(d, 300, box[3] - 6, h=380, color=AMBER)
        bubble(d, (110, 800, 560, 940), thought, 40, tail=(300, 1040))
        if extra:
            extra(d, box)
    return floor_room(floor, sub, draw)


def clocks_building(times):
    def make():
        im, d = canvas()
        floors = building_scene(d, LABELS, NAMES, label_size=40)
        for i, (a, top, b, bot) in enumerate(floors):
            h, m, lab = times[i]
            # 時刻は時計の右に40pxで（小さな注記に意味を持たせない）
            clock(d, a + 330, (top + bot) / 2, h, m, r=55, color=AMBER if i == 0 else LINE)
            text(d, (a + 400, (top + bot) / 2), lab.split()[0], 40, fill=AMBER if i == 0 else WHITE, anchor="lm")
        return im
    return make


def big_card(lines, amber=(), head=None):
    def make():
        im, d = canvas()
        if head:
            text(d, (540, 700), head, 40, fill=LINE)
        top = 1000 - (len(lines) - 1) * 60
        for i, s in enumerate(lines):
            text(d, (540, top + i * 120), s, 68, fill=AMBER if i in amber else WHITE)
        return im
    return make


def research_card(title, draw):
    def make():
        im, d = canvas()
        text(d, (540, 690), title, 40, fill=LINE_DIM)
        draw(d)
        return im
    return make


# ======================================================== 6. 大雪の朝
S6 = """# 同じ雪、4つの朝（年収別）
// 長尺第1弾の切り出し。研究なし、本編への入口

## S01
テロップ：明日の朝 大雪
効果音：K01 +0.1
明日の朝、大雪のおそれ。

## S02
テロップ：同期4人 年収別 視えている朝
{TON}
同じ年に入社した、同期の4人。同じ雪が、まったく違う長さの朝に見えていた。

## S03
テロップ：1F 300万「始発で出よう」
300万のケンタは思う。遅れたら、1日分の給料がなくなる。始発で出よう。

## S04
テロップ：2F 500万「学童の送り、どうしよう」
500万のユイは思う。学童の送り、どうしよう。

## S05
テロップ：3F 700万「明日は在宅にしよう」
700万のショウは思う。明日は、在宅にしよう。

## S06
テロップ：4F 1000万「タクシーを予約しておくか」
1000万のリクは思う。タクシーを、予約しておくか。

## S07
テロップ：お金がない人ほど、時間もない
同じ雪でも、起きる時間が、こんなに違う。お金がない人ほど、時間もなくなっていく。

## S08
テロップ：理由は4つ。本編で
その理由は、4つある。本編で、4人の20年をたどる。あなたの朝は、何時でした？
"""


def s6_room(floor, thought, sub):
    def extra(d, box):
        window(d, 600, 840, w=260, h=280)
        snow(d, (600, 840, 860, 1120), 18)
    return thought_room(floor, sub, thought, extra)


# ======================================================== 7. 自分の時間は30分
S7 = """# 自分の時間は、1日30分（2階の部屋）
// 長尺第1弾の切り出し。研究：Haushofer & Fehr 2014（Science）

## S01
テロップ：自分の時間 30分
効果音：K01 +0.15
自分の時間は、1日30分。

## S02
テロップ：2F 年収500万 ユイの1日
{TON}
年収500万、事務の主任のユイ。朝6時に起きて、弁当を2つ作り、7時半に家を出る。

## S03
テロップ：夕方5時から 学童・夕飯・宿題
夕方5時に会社を出て、学童に迎えに行き、夕飯を作り、宿題を見る。

## S04
テロップ：子どもが寝たあとの30分
自分のために使えるのは、子どもが寝たあとの30分だけ。

## S05
テロップ：開くのは、いつもスマホの動画
この30分で、何かしなきゃ。でも、開くのは、いつもスマホの動画だ。

## S06
テロップ：余裕がないと「今すぐ楽」を選ぶ（研究のまとめ）
貧しさと心の研究をまとめた論文では、余裕がないとストレスが増え、人は今すぐ楽になれるものを選びやすくなる。

## S07
テロップ：だらしないのではない
だらしないのではない。疲れた頭が、今すぐ楽になれるものを、選んでいるのだ。

## S08
テロップ：ユイの強みは、止めずに回し続ける力
家と会社を、1日も止めずに回しているのは、ユイだ。本編で、4人の20年をたどる。あなたは、何階でした？
"""


def s7_day():
    im, d = canvas()
    text(d, (540, 690), "ユイの1日", 44, fill=LINE)
    x, y0, y1 = 300, 780, 1520
    d.line([(x, y0), (x, y1)], fill=WHITE, width=6)
    marks = [(6, "6:00 起きる・弁当2つ"), (7.5, "7:30 家を出る"), (17, "17:00 学童へ"), (19, "19:00 夕飯・宿題"), (22, "22:00 子どもが寝る")]
    for hour, lab in marks:
        y = y0 + (y1 - y0) * (hour - 5) / 19
        d.line([(x - 25, y), (x + 25, y)], fill=LINE, width=4)
        text(d, (x + 60, y), lab, 40, fill=WHITE, anchor="lm")
    ya = y0 + (y1 - y0) * (22 - 5) / 19
    yb = y0 + (y1 - y0) * (22.5 - 5) / 19
    d.rectangle([x - 40, ya, x + 40, yb + 6], fill=AMBER)
    text(d, (x + 60, yb + 50), "自分の時間 30分", 46, fill=AMBER, anchor="lm")
    return im


def s7_s01():
    """時計の針が夜10時に進み、30分だけアンバーになる（約1秒）"""
    frames = []
    for f in range(32):
        im, d = canvas()
        t = min(1, f / 18)
        minute = int(60 * 22 * ease(t)) % 720
        clock(d, 540, 1080, minute // 60, minute % 60, r=300)
        if f >= 18:
            d.pieslice([240, 780, 840, 1380], -90, 90 - 180 + 0, fill=None, outline=AMBER, width=14)
            d.pieslice([240, 780, 840, 1380], 270, 450 - 180, outline=AMBER, width=0)
            text(d, (540, 1460), "30分", 90, fill=AMBER)
        frames.append(im)
    return frames


# ======================================================== 8. お金で時間を買う
S8 = """# お金で「時間」を買う人（3階の部屋）
// 長尺第1弾の切り出し。研究：Whillans ほか2017（PNAS）

## S01
テロップ：どっちが満足？
効果音：K01 +0.1
家事にお金を払う人と、払わない人。

## S02
テロップ：お金を払って家事を減らす人 と 自分でやる人
{TON}
生活の満足が高いのは、どっちだろう。

## S03
テロップ：3F 年収700万 ショウの土曜の朝
年収700万、設計の係長のショウ。土曜の朝、食洗機と乾燥まで終わる洗濯機が、同時に回っている。

## S04
テロップ：浮いた1時間で、技術士の勉強
その間に、コーヒーを淹れて仕事の本を開く。去年、その1時間で、技術士の勉強を始めた。

## S05
テロップ：時間を買う人ほど、満足が高い（2017年の研究）
お金で時間を買う研究では、家事を人に頼んだり、時間を減らす家電を買ったりする人ほど、生活の満足が高い傾向があった。

## S06
テロップ：ケンタは時間でお金を守る ショウはお金で時間を作る
1階のケンタは、時間を使ってお金を守っている。3階のショウは、お金を使って時間を作っている。

## S07
テロップ：お金がないと、時間を自分の手で払う
お金がないと、時間を、自分の手で払うしかない。本編で、4人の20年をたどる。あなたは、何階でした？
"""


def s8_s01():
    """A と B の札が左右から滑り込む（約1秒）"""
    frames = []
    for f in range(32):
        im, d = canvas()
        t = ease(min(1, f / 12))
        for k, (lab, sub, cx) in enumerate([("A", "払って減らす", 290), ("B", "自分でやる", 790)]):
            off = (1 - t) * (-500 if k == 0 else 500)
            d.rectangle([cx - 210 + off, 820, cx + 210 + off, 1320], outline=AMBER if k == 0 else LINE, width=8)
            text(d, (cx + off, 960), lab, 160, fill=WHITE)
            text(d, (cx + off, 1200), sub, 44, fill=WHITE)
        if f >= 14:
            text(d, (540, 1460), "どっちが満足？", 72, fill=AMBER)
        frames.append(im)
    return frames


# ======================================================== 9. ちょっとした知り合い
S9 = """# 仕事を運んでくるのは「ちょっとした知り合い」（4階の部屋）
// 長尺第1弾の切り出し。研究：Rajkumar ほか2022（Science）

## S01
テロップ：知らない番号から、電話
効果音：K01 +0.1
知らない番号から、電話。

## S02
テロップ：4F 年収1000万 リクのスマホ
{TON}
年収1000万、部長のリク。スマホには、毎週、知らない番号から電話がかかってくる。

## S03
テロップ：前の会社の後輩 知り合いの知り合い 転職の相談
前の会社の後輩。取引先の、知り合いの知り合い。転職の相談。

## S04
テロップ：仕事の話は、仲のいい友達から？
新しい仕事の話は、仲のいい友達から来る。そう思いやすい。答えは、逆だった。

## S05
テロップ：約2000万人の実験（2022年）
仕事のSNSで、約2000万人を対象にした実験では、仕事につながりやすかったのは、ちょっとした知り合いだった。

## S06
テロップ：リク：何百人 ケンタ：数人
リクには、ちょっとした知り合いが何百人もいる。1階のケンタは、倉庫の同じシフトの、数人だ。

## S07
テロップ：余裕がある人に、次の道が集まる
時間に余裕がある人のまわりに、次の道を運んでくる知り合いが増えていく。本編で、4人の20年をたどる。あなたは、何階でした？
"""


def s9_s01():
    """スマホが震えて、着信の波が広がる（約1秒）"""
    frames = []
    for f in range(32):
        im, d = canvas()
        shake = (8 if f % 2 else -8) if f < 20 else 0
        phone(d, 340 + shake, 700, w=400, h=760)
        text(d, (540 + shake, 960), "着信", 60, fill=AMBER)
        text(d, (540 + shake, 1060), "知らない番号", 44, fill=WHITE)
        for k in range(3):
            r = 60 + ((f * 12 + k * 60) % 180)
            d.arc([540 - 260 - r, 1080 - r, 540 - 260 + r, 1080 + r], 120, 240, fill=AMBER, width=6)
            d.arc([540 + 260 - r, 1080 - r, 540 + 260 + r, 1080 + r], -60, 60, fill=AMBER, width=6)
        frames.append(im)
    return frames


def ties(d, cx, cy, n_close, n_far, far_on=True, label=None, scale=1.0):
    import math
    person(d, cx, cy + 60 * scale, h=130 * scale, color=WHITE, width=4)
    for k in range(n_close):
        a = 2 * math.pi * k / max(1, n_close)
        x, y = cx + 110 * scale * math.cos(a), cy + 110 * scale * math.sin(a)
        d.line([(cx, cy), (x, y)], fill=LINE, width=5)
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=LINE)
    for k in range(n_far):
        a = 2 * math.pi * k / max(1, n_far) + 0.2
        x, y = cx + 220 * scale * math.cos(a), cy + 220 * scale * math.sin(a)
        dashed(d, (cx, cy), (x, y), color=AMBER if far_on else LINE_DIM, width=3)
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=AMBER if far_on else LINE_DIM)
    if label:
        text(d, (cx, cy + 290 * scale), label, 44, fill=WHITE)


# ======================================================== 10. 20年後の手紙
S10 = """# 20年前の自分から、手紙が届いた
// 長尺第1弾の切り出し（物語の結末側）。本編への入口

## S01
テロップ：20年前の自分から
効果音：K01 +0.2
20年前の自分から、手紙が届いた。

## S02
テロップ：同期4人の 20年後への手紙
{TON}
入社式で隣に並んだ、同期の4人。研修の最後の日、20年後の自分に手紙を書いた。

## S03
テロップ：45歳 年収は 300万〜1000万
45歳。4人の年収は、300万、500万、700万、1000万になっていた。

## S04
テロップ：「同期の4人とは、まだ会っていますか」
リクの手紙には、同期の4人とは、まだ会っていますか。

## S05
テロップ：「現場の、頼れる人になっていますか」
ケンタは、自分の封筒を、なかなか開けなかった。現場の、頼れる人になっていますか。

## S06
テロップ：「過去問、送るよ」
帰りの駅で、リクが言った。うちの会社、電気工事士が足りないんだ。古い過去問、送るよ。

## S07
テロップ：今日から、なる
7月。ケンタのスマホに、合格の通知が届いた。今日から、なる。

## S08
テロップ：お金がない人ほど、時間もない 理由は本編で
お金がない人ほど、時間もない。その理由と、4人の20年は、本編で。あなたは、何階でした？
"""


def letter_open():
    """封筒のふたが開く（約1秒）"""
    frames = []
    for f in range(32):
        im, d = canvas()
        t = ease(min(1, f / 18))
        x0, y0, x1, y1 = 190, 880, 890, 1320
        d.rectangle([x0, y0, x1, y1], outline=WHITE, width=8)
        tip = y0 + 260 * (1 - t) - 200 * t
        d.line([(x0, y0), (540, tip), (x1, y0)], fill=AMBER, width=8)
        if f >= 18:
            d.rectangle([260, 700, 820, 980], fill=NAVY, outline=WHITE, width=5)
            text(d, (540, 790), "20年後の自分へ", 48, fill=AMBER)
            text(d, (540, 880), "入社式の日に", 36, fill=LINE_DIM)
        frames.append(im)
    return frames


def envelopes(highlight=None, labels=None):
    def make():
        im, d = canvas()
        for i in range(4):
            x, y = 90 + (i % 2) * 470, 780 + (i // 2) * 380
            col = AMBER if highlight == i else WHITE
            d.rectangle([x, y, x + 430, y + 260], outline=col, width=6)
            d.line([(x, y), (x + 215, y + 150), (x + 430, y)], fill=col, width=5)
            text(d, (x + 215, y + 300), NAMES[i], 36, fill=LINE_DIM)
            if labels and labels[i]:
                text(d, (x + 215, y + 200), labels[i], 30, fill=AMBER)
        return im
    return make


def station():
    im, d = canvas()
    d.line([(60, 1400), (1020, 1400)], fill=WHITE, width=6)
    person(d, 380, 1390, h=520, color=AMBER, width=6)
    person(d, 720, 1390, h=560, color=LINE, width=6)
    text(d, (380, 1450), "ケンタ", 40, fill=AMBER)
    text(d, (720, 1450), "リク", 40, fill=LINE)
    bubble(d, (480, 560, 1010, 700), "過去問、送るよ", 42, tail=(720, 800))
    return im


def passed():
    im, d = canvas()
    phone(d, 290, 720, w=500, h=760)
    text(d, (540, 1000), "合格", 130, fill=AMBER)
    text(d, (540, 1180), "今日から、なる。", 56, fill=WHITE)
    return im


def make_6():
    write_folder("06_大雪の朝", S6, "ピロン", [
        ("S01_通知_大雪", notify("1月の金曜 夜9時", "明日の朝 大雪", snowy=True), "mp4"),
        ("S02_同期4人が各階へ", lambda: intro_stack(LABELS, NAMES, "入社式", label_size=40), "mp4"),
        ("S03_1F_始発", s6_room(0, "始発で出よう", "大雪の前の夜"), "png"),
        ("S04_2F_学童", s6_room(1, "送り、どうしよう", "大雪の前の夜"), "png"),
        ("S05_3F_在宅", s6_room(2, "在宅にしよう", "大雪の前の夜"), "png"),
        ("S06_4F_タクシー", s6_room(3, "タクシー予約", "大雪の前の夜"), "png"),
        ("S07_起きる時間", clocks_building([(4, 30, "4:30 始発"), (6, 0, "6:00"), (7, 30, "7:30 在宅"), (7, 0, "7:00 タクシー")]), "png"),
        ("S08_本編へ", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
    ])


def make_7():
    def s04(d, box):
        person(d, 300, box[3] - 6, h=340, pose="sit", color=AMBER)
        clock(d, 680, 1000, 10, 0, r=170)
        text(d, (680, 1230), "子どもが寝たあと", 34, fill=WHITE)

    def s05(d, box):
        person(d, 300, box[3] - 6, h=340, pose="sit", color=AMBER)
        phone(d, 420, 1150, w=120, h=200)
        d.polygon([(465, 1215), (465, 1290), (520, 1252)], fill=AMBER)
        bubble(d, (520, 820, 880, 960), "何かしなきゃ", 40, tail=(360, 1050))

    def s06(d):
        d.rectangle([140, 800, 940, 1020], outline=LINE, width=5)
        text(d, (540, 870), "余裕がない", 50, fill=WHITE)
        text(d, (540, 960), "→ ストレス・不安", 44, fill=WHITE)
        arrow(d, (540, 1040), (540, 1150), color=AMBER, width=8)
        d.rectangle([140, 1170, 940, 1400], outline=AMBER, width=5)
        text(d, (540, 1240), "今すぐ楽になれるもの", 46, fill=AMBER)
        text(d, (540, 1330), "を選びやすくなる", 40, fill=WHITE)

    write_folder("07_自分の時間30分", S7, "ピコン", [
        ("S01_時計_30分", s7_s01, "mp4"),
        ("S02_ユイ", lambda: intro_stack(LABELS, NAMES, "入社式", label_size=40), "mp4"),
        ("S03_ユイの1日", s7_day, "png"),
        ("S04_30分", floor_room(1, "夜10時", s04), "png"),
        ("S05_スマホの動画", floor_room(1, "夜10時", s05), "png"),
        ("S06_研究", research_card("研究のまとめ（2014年）", s06), "png"),
        ("S07_疲れた頭", big_card(["だらしない", "のではない"], amber=(1,), head="疲れた頭が「今すぐ楽」を選ぶ"), "png"),
        ("S08_本編へ", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
    ])


def make_8():
    def s03(d, box):
        for k, (lab, x) in enumerate([("食洗機", 250), ("洗濯乾燥機", 560)]):
            d.rectangle([x - 120, 860, x + 120, 1160], outline=LINE, width=5)
            d.ellipse([x - 70, 930, x + 70, 1070], outline=AMBER, width=5)
            text(d, (x, 1200), lab, 34, fill=WHITE)
        person(d, 790, box[3] - 6, h=330, color=AMBER)

    def s04(d, box):
        desk(d, 380, 1300, w=420)
        person(d, 300, box[3] - 6, h=330, pose="sit", color=AMBER)
        d.rectangle([460, 1200, 660, 1290], outline=WHITE, width=4)
        text(d, (560, 1245), "技術士", 30, fill=WHITE)
        clock(d, 700, 960, 8, 0, r=120, label="1時間")

    def s05(d):
        from blueprint import bar_chart
        text(d, (540, 800), "生活の満足", 52, fill=WHITE)
        bar_chart(d, 230, 900, [70, 100], ["物を買う", "時間を買う"], h=440, bw=220, gap=180, colors=[LINE_DIM, AMBER], size=46)
        text(d, (540, 1480), "時間を買う人ほど、満足が高い", 44, fill=AMBER)

    def s06():
        im, d = canvas()
        for k, (name, a, b, y) in enumerate([("1階 ケンタ", "時間", "お金", 900), ("3階 ショウ", "お金", "時間", 1250)]):
            text(d, (540, y - 110), name, 50, fill=WHITE)
            text(d, (330, y), a, 70, fill=LINE)
            arrow(d, (440, y), (640, y), color=AMBER, width=8, head=36)
            text(d, (760, y), b, 70, fill=AMBER)
        return im

    write_folder("08_時間を買う", S8, "ピコン", [
        ("S01_AかBか", s8_s01, "mp4"),
        ("S02_4人が各階へ", lambda: intro_stack(LABELS, NAMES, "入社式", label_size=40), "mp4"),
        ("S03_土曜の朝", floor_room(2, "土曜の朝", s03), "png"),
        ("S04_浮いた1時間", floor_room(2, "土曜の朝", s04), "png"),
        ("S05_研究", research_card("お金で時間を買う研究（2017年）", s05), "png"),
        ("S06_時間とお金", s06, "png"),
        ("S07_本編へ", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
    ])


def make_9():
    def s03(d, box):
        person(d, 260, box[3] - 6, h=380, color=AMBER)
        labels = ["前の会社の後輩", "知り合いの知り合い", "転職の相談"]
        for k, lab in enumerate(labels):
            bubble(d, (400, 820 + k * 170, 880, 950 + k * 170), lab, 36, color=AMBER if k == 1 else LINE)

    def s05(d):
        # 左：仲のいい友達（実線・少ない）、右：ちょっとした知り合い（点線・多い）。仕事の話は右から届く
        import math
        text(d, (540, 780), "仕事の話は、どこから来た？", 48, fill=WHITE)
        for cx, n, dash, lab, col in [(280, 3, False, "仲のいい友達", LINE), (800, 9, True, "ちょっとした知り合い", AMBER)]:
            person(d, cx, 1180, h=150, color=WHITE, width=4)
            for k in range(n):
                a = math.pi * (0.15 + 0.7 * k / max(1, n - 1)) + math.pi
                x, y = cx + 190 * math.cos(a), 1060 + 190 * math.sin(a)
                if dash:
                    dashed(d, (cx, 1060), (x, y), color=col, width=4)
                else:
                    d.line([(cx, 1060), (x, y)], fill=col, width=6)
                d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col)
            text(d, (cx, 1260), lab, 42, fill=col)
        # 知り合いの1人から「仕事の話」の封筒
        d.rectangle([700, 1330, 900, 1450], outline=AMBER, width=5)
        d.line([(700, 1330), (800, 1400), (900, 1330)], fill=AMBER, width=5)
        text(d, (800, 1500), "仕事の話", 44, fill=AMBER)

    def s06():
        im, d = canvas()
        ties(d, 540, 940, 4, 22, label="リク：何百人", scale=0.8)
        ties(d, 540, 1380, 3, 3, far_on=False, label="ケンタ：数人", scale=0.6)
        text(d, (540, 700), "点線＝ちょっとした知り合い", 44, fill=AMBER)
        return im

    write_folder("09_ちょっとした知り合い", S9, "ピロン", [
        ("S01_着信", s9_s01, "mp4"),
        ("S02_4人が各階へ", lambda: intro_stack(LABELS, NAMES, "入社式", label_size=40), "mp4"),
        ("S03_電話の相手", floor_room(3, "毎週の電話", s03), "png"),
        ("S04_逆だった", big_card(["答えは、", "逆だった"], amber=(1,), head="仕事の話は、仲のいい友達から？"), "png"),
        ("S05_研究", research_card("約2000万人の実験（2022年）", s05), "png"),
        ("S06_知り合いの数", s06, "png"),
        ("S07_本編へ", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
    ])


def make_10():
    write_folder("10_20年後の手紙", S10, "シャッ", [
        ("S01_封筒が開く", letter_open, "mp4"),
        ("S02_4人が各階へ", lambda: intro_stack(LABELS, NAMES, "入社式", label_size=40), "mp4"),
        ("S03_45歳の4人", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
        ("S04_リクの手紙", envelopes(highlight=3, labels=["", "", "", "まだ会ってる？"]), "png"),
        ("S05_ケンタの手紙", envelopes(highlight=0, labels=["頼れる人に？", "", "", ""]), "png"),
        ("S06_駅", station, "png"),
        ("S07_合格", passed, "png"),
        ("S08_本編へ", lambda: loop_end(LABELS, NAMES, label_size=40), "png"),
    ])


MAKERS = {6: make_6, 7: make_7, 8: make_8, 9: make_9, 10: make_10}

if __name__ == "__main__":
    for n in ([int(a) for a in sys.argv[1:]] or sorted(MAKERS)):
        MAKERS[n]()

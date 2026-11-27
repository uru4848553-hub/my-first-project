"""ショート2〜5の動画フォルダを作る（世代・IQ・AIの使い方・会社の大きさ）。

python channel_produce/shorts/make_shorts_2to5.py        → 4本とも作る
python channel_produce/shorts/make_shorts_2to5.py 3      → 3本目だけ

どの回も同じ型：
- S01（0〜1秒）：誰でも分かる出来事を「動き＋音」で見せる。声は1秒以内に言い切る
- S02：4人の写真が割れて、ビルの4つの階に分かれる（「トン」×4）
- S03〜S06：1階から順に、各階の部屋と心の声
- S07：ビル全体で「見えているものが違う」
- S08：研究（[a]説明 [b]意味）
- S09：救い・強み → 最後の絵は S02 の終わりと同じ（ループ）
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sfx  # noqa: E402
from blueprint import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, bar_chart, bubble, building, building_scene,  # noqa: E402
                       canvas, clock, dashed, desk, ease, intro_stack, loop_end, person, phone, room, save_mp4,
                       save_png, sky, text, window)

TON = "効果音：K02 +0.4\n効果音：K02 +0.6\n効果音：K02 +0.8\n効果音：K02 +1.0"


def write_folder(folder, script, k01, scenes):
    """動画フォルダ一式を書き出す。scenes は [(ファイル名, 作る関数, "mp4" か "png")]"""
    out = HERE / folder
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    for old in media.glob("*"):
        if old.is_file():
            old.unlink()
    (out / "audio").mkdir(exist_ok=True)
    (out / "audio" / "ここにナレーション（mp3など1本）を入れる.txt").write_text(
        "script.md の本文（「テロップ：」「効果音：」と「//」の行を除く）を読み上げた音声を、このフォルダに1本だけ入れてください。\n",
        encoding="utf-8")
    se = out / "se"
    se.mkdir(exist_ok=True)
    for old in se.glob("*.wav"):
        old.unlink()
    sfx.make(k01, se / f"K01_{k01}.wav")
    sfx.make("トン", se / "K02_トン.wav")
    (out / "script.md").write_text(script.replace("{TON}", TON), encoding="utf-8")
    for name, fn, kind in scenes:
        result = fn()
        if kind == "mp4":
            save_mp4(result, media / f"{name}.mp4")
        else:
            save_png(result, media / f"{name}.png")
    print("ok:", out)


# =====================================================================
# 2. 世代：同じニュース、4つの重さ
# =====================================================================
G_LABELS = ["Z世代", "ゆとり世代", "氷河期世代", "バブル世代"]
G_NAMES = ["新人", "主任", "課長", "部長"]

G_SCRIPT = """# 同じニュース、4つの重さ（世代別）
// 人生の断面図 ショート2。人物は「同じ部署の4人」（この回だけ）

## S01
テロップ：株価 史上最高値
効果音：K01 +0.1
株価、史上最高値。

## S02
テロップ：同じ部署の4人 世代別 視えている世界
{TON}
同じ部署の4人。同じニュースが、まったく違って聞こえた。

## S03
テロップ：Z世代「今からでも遅くない？」
Z世代の新人は思う。今から始めても、遅くないかな。

## S04
テロップ：ゆとり世代「続けててよかった」
ゆとり世代の主任は思う。積み立て、続けててよかった。

## S05
テロップ：氷河期世代「どうせまた下がる」
氷河期世代の課長は思う。どうせ、また下がる。

## S06
テロップ：バブル世代「またあの頃が来る」
バブル世代の部長は思う。またあの頃が、来るぞ。

## S07
テロップ：若いころに見た空がちがう
同じニュースでも、若いころに見た空が、ちがう。

## S08
テロップ：若いころの暴落は、何十年も残る（アメリカの研究）
[a] アメリカの研究では、若いころに株の暴落を見た人は、何十年たっても、投資に慎重だった。
[b] 最初に見た空が、一生の当たり前になる。

## S09
テロップ：性格じゃない。見てきた空がちがうだけ
[a] すれ違うのは、性格じゃない。挑む力も、備える力も、その世代の強みだ。
[b] あなたは、何世代でした？
"""


def g_s01():
    """テレビに速報が流れ、株価の線が跳ね上がる（約1.2秒）"""
    frames = []
    for f in range(36):
        im, d = canvas()
        t = f / 30
        d.rectangle([110, 780, 970, 1380], outline=WHITE, width=8)          # テレビ
        d.line([(440, 1380), (400, 1450)], fill=WHITE, width=6)
        d.line([(640, 1380), (680, 1450)], fill=WHITE, width=6)
        # 株価の線（左から右へ伸び、最後に跳ね上がる）
        pts = [(160, 1150), (260, 1180), (360, 1120), (460, 1160), (560, 1080), (660, 1110), (760, 990), (920, 830)]
        n = 2 + int(ease(min(1, t / 0.8)) * (len(pts) - 2))
        d.line(pts[:n], fill=AMBER if n == len(pts) else LINE, width=8)
        if n == len(pts):
            arrow(d, pts[-2], pts[-1], color=AMBER, width=8, head=40)
        # 速報の帯：右から滑り込む
        bx = 1080 - 960 * ease(min(1, t / 0.25))
        d.rectangle([bx, 1250, bx + 860, 1340], fill=AMBER)
        text(d, (bx + 30, 1295), "速報  株価 史上最高値", 48, fill=NAVY, anchor="lm")
        frames.append(im)
    return frames


def g_room(floor, title, sky_kind, bubble_text, extra=None):
    def make():
        im, d = canvas()
        box = room(d, floor, title)
        window(d, 560, 820, w=290, h=300)
        sky(d, (560, 820, 850, 1120), sky_kind)
        person(d, 300, box[3] - 6, h=380, color=AMBER, pose="look_up" if floor == 3 else "stand")
        bubble(d, (130, 820, 500, 960), bubble_text, 40, tail=(310, 1060))
        if extra:
            extra(d)
        return im
    return make


def g_phone_chart(d):
    phone(d, 420, 1180, w=110, h=190)
    d.line([(440, 1330), (470, 1300), (495, 1310), (515, 1260)], fill=AMBER, width=4)


def g_umbrella(d):
    d.pieslice([600, 1180, 840, 1330], 180, 360, outline=LINE, width=5)
    d.line([(720, 1255), (720, 1420)], fill=LINE, width=5)
    d.arc([700, 1400, 740, 1440], 0, 180, fill=LINE, width=5)


def g_s07():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=G_LABELS, label_size=44)
    kinds = ["sunrise", "cloudy", "rain", "fireworks"]
    for i, (a, top, b, bot) in enumerate(floors):
        person(d, a + 110, bot - 14, h=140, color=LINE, width=4)
        wb = (a + 250, top + 30, a + 470, bot - 25)
        d.rectangle(wb, outline=LINE, width=4)
        sky(d, wb, kinds[i])
    return im


def g_s08a():
    im, d = canvas()
    text(d, (540, 690), "アメリカの研究（若いころの株価と、その後の投資）", 32, fill=LINE_DIM)
    # 時間の矢印：20代に暴落 → 60代まで傘をさしたまま
    d.line([(120, 1400), (960, 1400)], fill=WHITE, width=5)
    for k, age in enumerate(["20代", "30代", "40代", "50代", "60代"]):
        x = 170 + k * 190
        text(d, (x, 1450), age, 32, fill=LINE_DIM)
        person(d, x, 1380, h=200, color=AMBER if k == 0 else LINE, width=4)
        d.pieslice([x - 60, 1150, x + 60, 1230], 180, 360, outline=AMBER, width=4)   # 開いたままの傘
    pts = [(120, 880), (230, 830), (300, 1050), (360, 1010)]
    d.line(pts, fill=AMBER, width=6)
    text(d, (300, 1100), "暴落", 34, fill=AMBER)
    return im


def g_s08b():
    im, d = canvas()
    head, r = person(d, 540, 1500, h=620, color=WHITE, width=6)
    d.pieslice([300, 760, 780, 1000], 180, 360, outline=AMBER, width=8)
    d.line([(540, 880), (540, 1040)], fill=AMBER, width=6)
    text(d, (540, 700), "最初に見た空が、当たり前になる", 40, fill=LINE_DIM)
    return im


def g_s09a():
    im, d = canvas()
    floors = building_scene(d, G_LABELS, G_NAMES, label_size=44)
    strengths = ["選ぶ力", "続ける力", "備える力", "挑む力"]
    for i, (a, top, b, bot) in enumerate(floors):
        text(d, (a + 320, top + 60), strengths[i], 38, fill=AMBER)
    return im


def make_generation():
    write_folder("02_世代_同じニュース", G_SCRIPT, "ピロン", [
        ("S01_速報_株価最高値", g_s01, "mp4"),
        ("S02_同じ部署の4人が各階へ", lambda: intro_stack(G_LABELS, G_NAMES, "同じ部署", label_size=44), "mp4"),
        ("S03_1F_Z世代", g_room(0, "1F｜Z世代｜新人", "sunrise", "今からでも？", g_phone_chart), "png"),
        ("S04_2F_ゆとり世代", g_room(1, "2F｜ゆとり世代｜主任", "cloudy", "続けてて良かった", g_phone_chart), "png"),
        ("S05_3F_氷河期世代", g_room(2, "3F｜氷河期世代｜課長", "rain", "どうせ…", g_umbrella), "png"),
        ("S06_4F_バブル世代", g_room(3, "4F｜バブル世代｜部長", "fireworks", "あの頃が来る"), "png"),
        ("S07_見てきた空", g_s07, "png"),
        ("S08a_研究_暴落", g_s08a, "png"),
        ("S08b_最初に見た空", g_s08b, "png"),
        ("S09a_世代の強み", g_s09a, "png"),
        ("S09b_あなたは何世代", lambda: loop_end(G_LABELS, G_NAMES, label_size=44), "png"),
    ])


# =====================================================================
# 3. IQ：同じ迷路、4つの景色
# =====================================================================
I_LABELS = ["IQ 80", "IQ 100", "IQ 120", "IQ 140"]

I_SCRIPT = """# 同じ迷路、4つの景色（IQ別）
// 人生の断面図 ショート3。研究：学校に通う年数とIQ（Ritchie & Tucker-Drob 2018, Psychological Science）。数字は投稿前に論文で確認

## S01
テロップ：同じ迷路
効果音：K01 +0.0
同じ迷路。

## S02
テロップ：IQ別 視えている世界
{TON}
IQのちがう4人には、まったく違う迷路に見えていた。

## S03
テロップ：IQ80「とにかく進む」
IQ80の人は思う。とにかく、壁に手をついて進もう。

## S04
テロップ：IQ100「前の人について行く」
IQ100の人は思う。前の人に、ついて行こう。

## S05
テロップ：IQ120「この先は行き止まり」
IQ120の人は思う。この先は、たぶん行き止まりだ。

## S06
テロップ：IQ140「なんでみんな迷うんだろう」
IQ140の人は思う。出口まで、もう見えてる。なんで、みんな迷うんだろう。

## S07
テロップ：見える高さがちがうだけ
同じ迷路でも、見える高さが、ちがう。

## S08
テロップ：学校に通った1年で、IQは上がる（研究のまとめ）
[a] 60万人以上のデータをまとめた研究では、学校に通う年数が1年増えるごとに、IQが1から5ポイント上がっていた。
[b] 見える高さは、生まれつきだけでは、決まらない。

## S09
テロップ：学んだ1年が、1階分の階段
[a] 1階の人には、壁にぶつかっても進み続ける強さがある。そして、学んだ1年が、1階分の階段になる。
[b] あなたは、何階から見ていますか？
"""

MAZE = [  # 迷路の壁（0〜1の座標）
    ((0.0, 0.0), (1.0, 0.0)), ((0.0, 0.0), (0.0, 1.0)), ((1.0, 0.0), (1.0, 0.8)), ((0.0, 1.0), (0.8, 1.0)),
    ((0.2, 0.0), (0.2, 0.6)), ((0.2, 0.8), (0.6, 0.8)), ((0.4, 0.2), (0.4, 0.8)), ((0.4, 0.2), (0.8, 0.2)),
    ((0.6, 0.4), (1.0, 0.4)), ((0.6, 0.4), (0.6, 0.6)), ((0.8, 0.6), (0.8, 1.0)), ((0.2, 0.6), (0.0, 0.6)),
]


def draw_maze(d, box, upto=1.0, color=LINE, width=6):
    x0, y0, x1, y1 = box
    n = len(MAZE)
    for k, ((ax, ay), (bx, by)) in enumerate(MAZE):
        t = min(1, max(0, upto * n - k))
        if t <= 0:
            break
        p0 = (x0 + (x1 - x0) * ax, y0 + (y1 - y0) * ay)
        p1 = (x0 + (x1 - x0) * bx, y0 + (y1 - y0) * by)
        d.line([p0, (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)], fill=color, width=width)


def i_s01():
    """ペンが一気に迷路を描く（約1秒）→ 入口と出口に印"""
    frames = []
    box = (160, 760, 920, 1520)
    for f in range(32):
        im, d = canvas()
        t = f / 30
        u = ease(min(1, t / 0.7))
        draw_maze(d, box, upto=u, color=LINE, width=8)
        # ペン先
        k = min(len(MAZE) - 1, int(u * len(MAZE)))
        (ax, ay), (bx, by) = MAZE[k]
        px = box[0] + (box[2] - box[0]) * bx
        py = box[1] + (box[3] - box[1]) * by
        if u < 1:
            d.polygon([(px, py), (px + 22, py - 60), (px + 44, py - 50)], fill=AMBER)
        else:
            text(d, (box[0] + 40, box[3] + 40), "入口", 34, fill=AMBER)
            text(d, (box[2] - 10, box[3] - 120), "出口", 34, fill=AMBER, anchor="lm")
        frames.append(im)
    return frames


def i_room(floor, title, visible, bubble_text, pose="stand"):
    """visible：その階から見える迷路の割合（上の階ほど広く見える）"""
    def make():
        im, d = canvas()
        box = room(d, floor, title)
        mb = (430, 830, 860, 1260)
        draw_maze(d, mb, upto=visible, color=LINE, width=5)
        if visible < 1:
            d.rectangle([mb[0] - 10, mb[1] - 10, mb[2] + 10, mb[3] + 10], outline=LINE_DIM, width=2)
            text(d, ((mb[0] + mb[2]) / 2, mb[3] + 40), "見えているのは、ここまで", 28, fill=LINE_DIM)
        else:
            text(d, ((mb[0] + mb[2]) / 2, mb[3] + 40), "出口まで全部", 28, fill=AMBER)
        person(d, 250, box[3] - 6, h=380, color=AMBER, pose=pose)
        bubble(d, (110, 820, 410, 950), bubble_text, 36, tail=(260, 1060))
        return im
    return make


def i_s07():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=I_LABELS, label_size=46)
    for i, (a, top, b, bot) in enumerate(floors):
        person(d, a + 110, bot - 14, h=140, color=LINE, width=4)
        mb = (a + 250, top + 25, a + 470, bot - 20)
        draw_maze(d, mb, upto=[0.25, 0.45, 0.7, 1.0][i], color=AMBER if i == 3 else LINE, width=3)
    arrow(d, (95, 1450), (95, 830), color=AMBER, width=5)
    return im


def i_s08a():
    im, d = canvas()
    text(d, (540, 650), "60万人以上のデータをまとめた研究（2018年）", 32, fill=LINE_DIM)
    # 階段：学校の1年ごとに1段
    x, y = 150, 1480
    for k in range(5):
        d.line([(x, y), (x + 150, y), (x + 150, y - 110)], fill=LINE, width=6)
        text(d, (x + 75, y + 36), f"+1年", 30, fill=LINE_DIM)
        x, y = x + 150, y - 110
    person(d, 840, 1480 - 5 * 110 + 10, h=170, color=AMBER, width=5)
    text(d, (540, 1560), "学校に通う年数が1年増えるごとに、IQが上がる", 32, fill=AMBER)
    return im


def i_s08b():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=I_LABELS, label_size=46)
    a, top, b, bot = floors[0]
    a2, top2, b2, bot2 = floors[1]
    # 1階から2階への階段
    x, y = a + 330, bot
    for k in range(5):
        d.line([(x, y), (x + 30, y), (x + 30, y - fh_step())], fill=AMBER, width=5)
        x, y = x + 30, y - fh_step()
    person(d, a + 200, bot - 14, h=150, color=AMBER, pose="look_up", width=4)
    text(d, (BX_TEXT, 1600), "見える高さは、生まれつきだけで決まらない", 32, fill=LINE_DIM)
    return im


BX_TEXT = 540


def fh_step():
    return 780 / 4 / 5


def i_s09a():
    im, d = canvas()
    floors = building_scene(d, I_LABELS, None, poses=["look_up", "stand", "stand", "look_down"], label_size=46)
    strengths = ["進み続ける力", "合わせる力", "先を読む力", "全体を見る力"]
    for i, (a, top, b, bot) in enumerate(floors):
        text(d, (a + 340, top + 60), strengths[i], 34, fill=AMBER)
    return im


def make_iq():
    write_folder("03_IQ_同じ迷路", I_SCRIPT, "シャッ", [
        ("S01_迷路を描く", i_s01, "mp4"),
        ("S02_4人が各階へ", lambda: intro_stack(I_LABELS, None, "同じ迷路の入口", label_size=46), "mp4"),
        ("S03_1F_IQ80", i_room(0, "1F｜IQ80", 0.25, "とにかく進む"), "png"),
        ("S04_2F_IQ100", i_room(1, "2F｜IQ100", 0.45, "ついて行こう"), "png"),
        ("S05_3F_IQ120", i_room(2, "3F｜IQ120", 0.7, "行き止まり？"), "png"),
        ("S06_4F_IQ140", i_room(3, "4F｜IQ140", 1.0, "なんで迷う？", pose="look_down"), "png"),
        ("S07_見える高さ", i_s07, "png"),
        ("S08a_研究_学校の年数", i_s08a, "png"),
        ("S08b_階段", i_s08b, "png"),
        ("S09a_それぞれの強み", i_s09a, "png"),
        ("S09b_あなたは何階", lambda: loop_end(I_LABELS, None, label_size=46), "png"),
    ])


# =====================================================================
# 4. AIの使い方：同じ「明日までに」、4つの重さ
# =====================================================================
A_LABELS = ["使わない", "調べる", "相談する", "任せる"]
A_NAMES = ["ケンタ", "ユイ", "ショウ", "リク"]

A_SCRIPT = """# 同じ「明日までに」、4つの重さ（AIの使い方別）
// 人生の断面図 ショート4。研究：Dell'Acqua ほか（2023、ハーバード・ビジネス・スクール ワーキングペーパー）。数字は投稿前に確認

## S01
テロップ：明日までに。
効果音：K01 +0.3
この資料、明日までに。

## S02
テロップ：同期4人 AIの使い方別 視えている世界
{TON}
同じ年に入社した、同期の4人。同じ「明日までに」が、まったく違う重さだった。

## S03
テロップ：使わない「今夜は徹夜」
AIを使わないケンタは思う。今夜は、徹夜だ。

## S04
テロップ：調べる「終電には帰れる」
調べ物にだけ使うユイは思う。終電には、帰れるかな。

## S05
テロップ：相談する「夕方には形になる」
相談相手にするショウは思う。夕方には、形になる。

## S06
テロップ：任せる「ケンタを手伝うか」
作業を任せるリクは思う。1時間で終わった。ケンタを、手伝うか。

## S07
テロップ：見えている時間がちがう
同じ仕事でも、見えている時間が、ちがう。

## S08
テロップ：成績が低かった人ほど、大きく伸びた（2023年の実験）
[a] 大手コンサル会社の実験では、AIを使うと、仕事の速さも、質も上がった。
[b] しかも、もともと成績が低かった人ほど、大きく伸びていた。

## S09
テロップ：差は才能じゃなく、任せ方
[a] だから今、いちばん下の階の人が、いちばん上がりやすい。差は、才能じゃなく、任せ方。
[b] あなたは今、何階でした？
"""


def a_s01():
    """資料の束が机に落ちる（約1.1秒）→ 付箋「明日まで」"""
    frames = []
    for f in range(34):
        im, d = canvas()
        t = f / 30
        y = 600 + (1110 - 600) * ease(min(1, t / 0.3))
        bounce = -18 if 0.3 <= t < 0.38 else 0
        d.line([(120, 1300), (960, 1300)], fill=LINE, width=8)        # 机
        d.line([(170, 1300), (170, 1520)], fill=LINE, width=6)
        d.line([(910, 1300), (910, 1520)], fill=LINE, width=6)
        for k in range(7):                                            # 紙の束
            yy = y + bounce + k * 26
            d.rectangle([300 + (k % 2) * 8, yy, 780 + (k % 2) * 8, yy + 22], outline=WHITE, fill=NAVY, width=3)
        if t >= 0.3:
            for k in (-1, 1):
                d.line([(540 + k * 280, 1290), (540 + k * 350, 1250)], fill=AMBER, width=5)
        if t >= 0.55:
            d.rectangle([620, 1010, 860, 1110], fill=AMBER)
            text(d, (740, 1060), "明日まで", 44, fill=NAVY)
        frames.append(im)
    return frames


def a_room(floor, title, hour, minute, label, bubble_text, window_kind, extra=None):
    def make():
        im, d = canvas()
        box = room(d, floor, title)
        window(d, 640, 830, w=220, h=230)
        sky(d, (640, 830, 860, 1060), window_kind)
        clock(d, 520, 930, hour, minute, r=80, label=label)
        desk(d, 380, 1300, w=420)
        person(d, 300, box[3] - 6, h=330, pose="sit", color=AMBER)
        bubble(d, (110, 820, 400, 940), bubble_text, 36, tail=(280, 1060))
        if extra:
            extra(d)
        return im
    return make


def a_papers(d):
    for k in range(6):
        d.rectangle([520 + (k % 2) * 6, 1240 - k * 18, 740 + (k % 2) * 6, 1256 - k * 18], outline=WHITE, fill=NAVY, width=2)


def a_chat(d):
    d.rounded_rectangle([520, 1150, 780, 1290], radius=16, outline=LINE, width=4)
    for k, w in enumerate([200, 150, 180]):
        d.line([(540, 1180 + k * 35), (540 + w, 1180 + k * 35)], fill=AMBER if k % 2 else LINE, width=5)


def a_auto(d):
    # AI が資料を作り続けている（四角の中で書類が流れる）
    d.rounded_rectangle([520, 1130, 780, 1290], radius=16, outline=AMBER, width=5)
    text(d, (650, 1160), "AI", 34, fill=AMBER)
    for k in range(3):
        d.rectangle([550 + k * 70, 1200, 600 + k * 70, 1270], outline=WHITE, width=3)
    d.ellipse([200, 1170, 250, 1220], outline=LINE, width=4)     # コーヒー


def a_s07():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=A_LABELS, label_size=44)
    times = [(2, 0, "夜中2時"), (11, 30, "終電"), (5, 0, "夕方5時"), (3, 0, "午後3時")]
    for i, (a, top, b, bot) in enumerate(floors):
        person(d, a + 110, bot - 14, h=140, color=LINE, width=4)
        h, m, lab = times[i]
        clock(d, a + 360, (top + bot) / 2 - 12, h, m, r=58, color=AMBER if i == 0 else LINE)
        text(d, (a + 360, bot - 20), lab, 26, fill=LINE_DIM)
    return im


def a_s08a():
    im, d = canvas()
    text(d, (540, 690), "大手コンサル会社の実験（2023年）", 34, fill=LINE_DIM)
    bar_chart(d, 250, 900, [55, 80], ["AIなし", "AIあり"], h=420, bw=180, gap=160, colors=[LINE_DIM, AMBER], size=36)
    text(d, (540, 1560), "仕事の速さも質も上がった（高さはイメージ）", 30, fill=LINE_DIM)
    return im


def a_s08b():
    im, d = canvas()
    text(d, (540, 690), "伸び幅（高さはイメージ）", 34, fill=LINE_DIM)
    # 成績が低かった人／高かった人：AIなし→あり
    for k, (label, before, after) in enumerate([("成績が低かった人", 35, 80), ("成績が高かった人", 70, 88)]):
        x = 160 + k * 420
        h0, h1 = 500 * before / 100, 500 * after / 100
        d.rectangle([x, 1450 - h0, x + 130, 1450], fill=LINE_DIM)
        d.rectangle([x + 150, 1450 - h1, x + 280, 1450], fill=AMBER)
        arrow(d, (x + 65, 1450 - h0 - 20), (x + 215, 1450 - h1 - 20), color=AMBER if k == 0 else LINE, width=5)
        text(d, (x + 140, 1500), label, 32, fill=AMBER if k == 0 else WHITE)
    d.line([(120, 1450), (960, 1450)], fill=WHITE, width=4)
    return im


def a_s09a():
    im, d = canvas()
    floors = building_scene(d, A_LABELS, A_NAMES, poses=["look_up", "stand", "stand", "stand"], label_size=44)
    a, top, b, bot = floors[0]
    x, y = a + 330, bot
    step = 780 / 4 / 5
    for k in range(5):
        d.line([(x, y), (x + 30, y), (x + 30, y - step)], fill=AMBER, width=5)
        x, y = x + 30, y - step
    text(d, (a + 420, bot - 30), "任せ方", 30, fill=AMBER)
    return im


def make_ai():
    write_folder("04_AI_同じ明日までに", A_SCRIPT, "ドサッ", [
        ("S01_資料が落ちる", a_s01, "mp4"),
        ("S02_同期4人が各階へ", lambda: intro_stack(A_LABELS, A_NAMES, "入社式", label_size=44), "mp4"),
        ("S03_1F_使わない", a_room(0, "1F｜使わない｜ケンタ", 2, 0, "夜中2時", "今夜は徹夜", "moon", a_papers), "png"),
        ("S04_2F_調べる", a_room(1, "2F｜調べる｜ユイ", 11, 30, "終電", "終電までに", "moon", a_papers), "png"),
        ("S05_3F_相談する", a_room(2, "3F｜相談する｜ショウ", 5, 0, "夕方5時", "形になる", "sunrise", a_chat), "png"),
        ("S06_4F_任せる", a_room(3, "4F｜任せる｜リク", 3, 0, "午後3時", "手伝うか", "cloudy", a_auto), "png"),
        ("S07_見えている時間", a_s07, "png"),
        ("S08a_研究_AIあり", a_s08a, "png"),
        ("S08b_低かった人ほど伸びた", a_s08b, "png"),
        ("S09a_任せ方の階段", a_s09a, "png"),
        ("S09b_あなたは何階", lambda: loop_end(A_LABELS, A_NAMES, label_size=44), "png"),
    ])


# =====================================================================
# 5. 会社の大きさ：同じアイデア、4つの道のり
# =====================================================================
C_LABELS = ["社員 10人", "社員 100人", "社員 1000人", "社員 3万人"]
C_NAMES = ["アキラ", "ナオ", "ケイ", "ソウ"]

C_SCRIPT = """# 同じアイデア、4つの道のり（会社の大きさ別）
// 人生の断面図 ショート5。研究：Wheatley（2017, Work and Occupations）仕事の自律性と満足（イギリス）。投稿前に確認

## S01
テロップ：いいアイデア、思いついた
効果音：K01 +0.35
いいアイデアを、思いついた。

## S02
テロップ：同じ年に就活した4人 会社の大きさ別 視えている世界
{TON}
同じ年に就活した、4人。同じアイデアが、まったく違う道のりになった。

## S03
テロップ：社員10人「社長に言えば明日から」
社員10人の会社のアキラは思う。社長に言えば、明日から始められる。

## S04
テロップ：社員100人「部長に通せば来月」
社員100人の会社のナオは思う。部長に通せば、来月には動ける。

## S05
テロップ：社員1000人「稟議が通るまで3か月」
社員1000人の会社のケイは思う。稟議が通るまで、3か月か。

## S06
テロップ：社員3万人「予算は大きい。でも判子は7つ」
社員3万人の会社のソウは思う。通れば、予算は大きい。でも、判子は7つ。

## S07
テロップ：決めるまでの距離がちがう
同じアイデアでも、決めるまでの距離が、ちがう。

## S08
テロップ：自分で決められる人ほど、満足が高い（イギリスの研究）
[a] イギリスで、たくさんの働く人を調べた研究がある。仕事のやり方や順番を、自分で決められる人ほど、仕事への満足が高かった。
[b] 給料だけでなく、自分で決められる幅も、毎日の満足を左右していた。

## S09
テロップ：どの階にも、自分で決められる場所は作れる
[a] 大きな会社には、大きな予算がある。小さな会社には、決める速さがある。どの階にも、自分で決められる場所は、作れる。
[b] あなたの会社は、何階でした？
"""


def lightbulb(d, cx, cy, s=1.0, lit=False, draw_t=1.0):
    r = 110 * s
    col = AMBER if lit else LINE
    if draw_t > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], 135, 135 + 270 * draw_t, fill=col, width=int(8 * s))
    if draw_t >= 1:
        d.rectangle([cx - 50 * s, cy + r * 0.75, cx + 50 * s, cy + r * 1.35], outline=col, width=int(7 * s))
        d.line([(cx - 50 * s, cy + r * 1.05), (cx + 50 * s, cy + r * 1.05)], fill=col, width=int(5 * s))
        d.line([(cx - 25 * s, cy + 30 * s), (cx, cy - 20 * s), (cx + 25 * s, cy + 30 * s)], fill=col, width=int(5 * s))
    if lit:
        for k in range(8):
            a = math.radians(-90 + (k - 3.5) * 28)
            d.line([(cx + math.cos(a) * r * 1.25, cy + math.sin(a) * r * 1.25),
                    (cx + math.cos(a) * r * 1.6, cy + math.sin(a) * r * 1.6)], fill=AMBER, width=int(7 * s))


def c_s01():
    """電球が描かれて、パッと光る（約1.1秒）"""
    frames = []
    for f in range(34):
        im, d = canvas()
        t = f / 30
        draw_t = ease(min(1, t / 0.3))
        lit = t >= 0.35
        lightbulb(d, 540, 1000, s=1.6, lit=lit, draw_t=draw_t)
        frames.append(im)
    return frames


def c_room(floor, title, steps, bubble_text, extra=None):
    """steps：アイデアが通るまでの判子（はんこ）の数"""
    def make():
        im, d = canvas()
        box = room(d, floor, title)
        lightbulb(d, 300, 900, s=0.45, lit=True)
        person(d, 300, box[3] - 6, h=360, color=AMBER)
        # 道のり：判子の丸が並ぶ
        for k in range(steps):
            cx = 480 + (k % 4) * 100
            cy = 900 + (k // 4) * 110
            d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], outline=RED_STAMP, width=5)
            text(d, (cx, cy), "承認", 22, fill=RED_STAMP)
        bubble(d, (440, 1200, 860, 1330), bubble_text, 36, tail=(360, 1170))
        if extra:
            extra(d)
        return im
    return make


RED_STAMP = (255, 120, 110)


def c_s07():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=C_LABELS, label_size=40)
    lengths = [60, 140, 230, 300]
    for i, (a, top, b, bot) in enumerate(floors):
        person(d, a + 110, bot - 14, h=140, color=LINE, width=4)
        y = (top + bot) / 2
        lightbulb(d, a + 185, y - 40, s=0.18, lit=True)
        arrow(d, (a + 200, y + 10), (a + 200 + lengths[i], y + 10), color=AMBER if i == 0 else LINE, width=5, head=18)
    return im


def c_s08a():
    im, d = canvas()
    text(d, (540, 690), "イギリスの研究（仕事を自分で決められる幅と満足）", 32, fill=LINE_DIM)
    items = ["やり方", "順番", "ペース", "働く時間"]
    for k, it in enumerate(items):
        y = 840 + k * 120
        d.rectangle([180, y, 240, y + 60], outline=AMBER, width=5)
        d.line([(192, y + 30), (208, y + 48), (232, y + 12)], fill=AMBER, width=6)
        text(d, (280, y + 30), f"{it}を自分で決められる", 40, fill=WHITE, anchor="lm")
    arrow(d, (540, 1340), (540, 1420), color=AMBER, width=6)
    text(d, (540, 1480), "仕事への満足が高い", 48, fill=AMBER)
    return im


def c_s08b():
    im, d = canvas()
    # 天びん：給料と、決められる幅
    d.line([(540, 900), (540, 1450)], fill=WHITE, width=6)
    d.line([(240, 1000), (840, 1000)], fill=WHITE, width=6)
    for x, lab in [(240, "給料"), (840, "決められる幅")]:
        d.line([(x, 1000), (x - 80, 1150)], fill=LINE, width=4)
        d.line([(x, 1000), (x + 80, 1150)], fill=LINE, width=4)
        d.arc([x - 110, 1110, x + 110, 1200], 0, 180, fill=LINE, width=5)
        text(d, (x, 1250), lab, 40, fill=AMBER if lab != "給料" else WHITE)
    d.polygon([(500, 1450), (580, 1450), (540, 1400)], outline=WHITE, width=5)
    text(d, (540, 760), "毎日の満足を左右するもの", 38, fill=LINE_DIM)
    return im


def c_s09a():
    im, d = canvas()
    floors = building_scene(d, C_LABELS, C_NAMES, label_size=40)
    strengths = ["決める速さ", "現場との近さ", "仕組みの強さ", "予算の大きさ"]
    for i, (a, top, b, bot) in enumerate(floors):
        text(d, (a + 330, top + 60), strengths[i], 34, fill=AMBER)
    return im


def make_company():
    write_folder("05_会社の大きさ_同じアイデア", C_SCRIPT, "ピコン", [
        ("S01_ひらめき", c_s01, "mp4"),
        ("S02_4人が各階へ", lambda: intro_stack(C_LABELS, C_NAMES, "就活のころ", label_size=40), "mp4"),
        ("S03_1F_社員10人", c_room(0, "1F｜社員10人｜アキラ", 1, "明日から"), "png"),
        ("S04_2F_社員100人", c_room(1, "2F｜社員100人｜ナオ", 2, "来月には"), "png"),
        ("S05_3F_社員1000人", c_room(2, "3F｜社員1000人｜ケイ", 4, "3か月か"), "png"),
        ("S06_4F_社員3万人", c_room(3, "4F｜社員3万人｜ソウ", 7, "判子は7つ"), "png"),
        ("S07_決めるまでの距離", c_s07, "png"),
        ("S08a_研究_決められる幅", c_s08a, "png"),
        ("S08b_給料と決められる幅", c_s08b, "png"),
        ("S09a_それぞれの強み", c_s09a, "png"),
        ("S09b_あなたの会社は何階", lambda: loop_end(C_LABELS, C_NAMES, label_size=40), "png"),
    ])


MAKERS = {2: make_generation, 3: make_iq, 4: make_ai, 5: make_company}

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:]] or sorted(MAKERS)
    for n in which:
        MAKERS[n]()

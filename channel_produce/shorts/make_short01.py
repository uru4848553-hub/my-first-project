"""ショート1「同じ3万円、4つの重さ」（年収別）の動画フォルダを作る。

python channel_produce/shorts/make_short01.py
→ channel_produce/shorts/01_年収_同じ3万円/（script.md、media/、audio/）
audio/ にナレーション（mp3 など1本）を入れて、自動配置ツールで組み上げる。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, bar_chart, bill, bubble, building, calendar,  # noqa: E402
                       canvas, dashed, desk, ease, person, phone, room, save_mp4, save_png, text, window)

OUT = Path(__file__).resolve().parent / "01_年収_同じ3万円"
MEDIA = OUT / "media"
LABELS = ["年収 300万", "年収 500万", "年収 700万", "年収 1000万"]
NAMES = ["ケンタ", "ユイ", "ショウ", "リク"]

SCRIPT = """# 同じ3万円、4つの重さ（年収別）
// 人生の断面図 ショート1。ナレーションは audio/ に1本（ElevenLabs などで、この本文を読ませる）
// 「テロップ：」の行は読まない。自動配置ツールが画面の上に出す

## S01
テロップ：修理代 3万円
効果音：K01 +0.35
スマホが割れた。

## S02
テロップ：同期4人 年収別 視えている世界
効果音：K02 +0.4
効果音：K02 +0.6
効果音：K02 +0.8
効果音：K02 +1.0
同じ年に入社した、同期の4人。同じ3万円が、まったく違う重さだった。

## S03
テロップ：1F 300万「割れたまま使う」
300万のケンタは思う。割れたまま、使うしかない。

## S04
テロップ：2F 500万「ボーナスまで我慢」
500万のユイは思う。ボーナスまで、我慢しよう。

## S05
テロップ：3F 700万「買い替えるか」
700万のショウは思う。ちょうどいい、買い替えるか。

## S06
テロップ：4F 1000万「ケンタ元気かな」
1000万のリクは思う。そういえば、ケンタ、元気かな。

## S07
テロップ：頭の中で占める大きさが違う
同じ3万円が、頭の中で占める大きさが、違う。

## S08
テロップ：同じ人でも、お金がない時は成績が下がる
[a] インドの農家を調べた研究があります。同じ人なのに、お金がない収穫前は、収穫後より、テストの成績が下がっていた。
[b] お金の心配が、頭の空きを奪っていたんです。

## S09
テロップ：差は「頭の空き」
[a] 差は、頭の良さじゃない。頭の空きの差。悩みを1つ減らすだけで、判断は変わる。
[b] あなたは、何階でした？
"""


def s01_crack():
    """スマホが落ちて割れる（約1.2秒）。最後の絵のまま止まり、残りの尺は自動配置ツールが静止で埋める"""
    frames = []
    for f in range(36):
        im, d = canvas()
        t = f / 30
        y = 420 + (1000 - 420) * ease(min(1, t / 0.35))
        hit = t >= 0.35
        shake = (10 if f % 2 else -10) if 0.35 <= t < 0.55 else 0
        crack = max(0.0, (t - 0.35) / 0.35)
        d.line([(160, 1370), (920, 1370)], fill=LINE_DIM, width=4)   # 床
        if hit:
            for k in (-2, -1, 1, 2):   # 衝撃の線
                d.line([(540 + k * 150, 1395), (540 + k * 215, 1450)], fill=AMBER, width=5)
        phone(d, 440 + shake, y, w=200, h=360, cracked=hit, crack_t=crack)
        if crack > 0.6:
            text(d, (540, 1500), "¥30,000", 64, fill=AMBER)
        frames.append(im)
    return frames


def building_scene(d, highlight=None, people=True, bubbles=None):
    floors = building(d, 150, 760, 520, 780, labels=LABELS, highlight=highlight, label_size=46)
    if people:
        for i, (a, top, b, bot) in enumerate(floors):
            person(d, a + 170, bot - 14, h=150, color=AMBER if highlight and i in highlight else LINE, width=4)
            text(d, (a + 300, bot - 40), NAMES[i], 30, fill=LINE_DIM)
    return floors


def s02_split():
    """入社式の写真（4人並び）が割れて、ビルの4つの階に1人ずつ積み上がる（約1.6秒）"""
    frames = []
    x0, y0, w, h = 150, 760, 520, 780
    fh = h / 4
    for f in range(48):
        im, d = canvas()
        t = f / 30
        if t < 0.4:
            d.rectangle([120, 820, 960, 1300], outline=WHITE, width=6)
            text(d, (540, 780), "入社式", 40, fill=LINE_DIM)
            for i in range(4):
                person(d, 230 + i * 205, 1250, h=320, color=LINE, width=5)
            if t > 0.27:   # ひびが入る
                for i in range(1, 4):
                    x = 120 + i * 210
                    d.line([(x, 820), (x + 12, 1060), (x - 8, 1300)], fill=AMBER, width=6)
        else:
            k = (t - 0.4) / 0.2      # 0.2秒ごとに1階ずつ積み上がる
            shown = min(4, int(k) + 1)
            for i in range(shown):
                top, bot = y0 + h - (i + 1) * fh, y0 + h - i * fh
                drop = (1 - ease(min(1, (k - i) * 1.6))) if i == shown - 1 and k < 4 else 0
                off = -140 * drop
                d.rectangle([x0, top + off, x0 + w, bot + off], outline=LINE, width=6)
                text(d, (x0 + 18, top + off + 16), f"{i + 1}F", 30, fill=LINE, anchor="lt")
                person(d, x0 + 170, bot - 14 + off, h=150, color=LINE, width=4)
                text(d, (x0 + 300, bot - 40 + off), NAMES[i], 30, fill=LINE_DIM)
                text(d, (x0 + w + 22, (top + bot) / 2 + off), LABELS[i], 46, fill=WHITE, anchor="lm")
            d.line([(x0 - 60, y0 + h), (x0 + w + 60, y0 + h)], fill=WHITE, width=6)
        frames.append(im)
    # 積み上がったあと、1階から順に1つずつ光る（0.4秒ずつ）→ 最後は全部ふつうに戻る
    for i in range(4):
        im, d = canvas()
        building_scene(d, highlight=[i])
        frames += [im] * 12
    im, d = canvas()
    building_scene(d)
    frames += [im] * 12
    return frames


def s03_kenta():
    im, d = canvas()
    box = room(d, 0, "1F｜年収300万｜ケンタ")
    desk(d, 380, 1300, w=420)
    person(d, 300, box[3] - 6, h=330, pose="sit", color=AMBER)
    phone(d, 600, 1170, w=80, h=130, cracked=True)
    bubble(d, (130, 800, 380, 930), "家賃", 44, color=AMBER, tail=(300, 1080))
    bubble(d, (390, 790, 640, 910), "電気代", 40)
    bubble(d, (620, 900, 870, 1030), "3万", 52, color=AMBER)
    bubble(d, (420, 940, 610, 1050), "今月", 40)
    bubble(d, (140, 960, 390, 1060), "あと4,100円", 32)
    bill(d, 690, 1180, "請求書", w=150)
    return im


def s04_yui():
    im, d = canvas()
    box = room(d, 1, "2F｜年収500万｜ユイ")
    calendar(d, 560, 830, mark=(3, 4, "ボーナス"))
    person(d, 330, box[3] - 6, h=380, color=AMBER)
    phone(d, 405, 1160, w=60, h=100, cracked=True)
    bubble(d, (150, 820, 470, 960), "あと〇日", 44, tail=(330, 1050))
    return im


def s05_sho():
    im, d = canvas()
    box = room(d, 2, "3F｜年収700万｜ショウ")
    window(d, 600, 840, w=230, h=250)
    desk(d, 380, 1300, w=400)
    person(d, 300, box[3] - 6, h=330, pose="sit", color=AMBER)
    d.rectangle([520, 1150, 700, 1290], outline=LINE, width=4)   # カタログ
    for k in range(3):
        d.rounded_rectangle([540 + k * 54, 1175, 576 + k * 54, 1240], radius=6, outline=AMBER, width=3)
    text(d, (610, 1265), "NEW", 22, fill=AMBER)
    bubble(d, (150, 880, 360, 980), "新しいの", 36, tail=(290, 1080))
    return im


def s06_riku():
    im, d = canvas()
    box = room(d, 3, "4F｜年収1000万｜リク")
    window(d, 440, 830, w=330, h=360)
    person(d, 300, box[3] - 6, h=380, pose="look_down", color=AMBER)
    phone(d, 140, 1300, w=70, h=110)   # 机に置いたスマホ（割れていない）
    bubble(d, (420, 1230, 760, 1340), "ケンタ？", 40, tail=(360, 1130))
    # キープランの4階→1階へ点線
    dashed(d, (860, 580), (860, 690), color=AMBER, width=4)
    return im


def s07_sizes():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=LABELS)
    sizes = [(230, 150), (170, 110), (120, 80), (70, 50)]
    for i, (a, top, b, bot) in enumerate(floors):
        person(d, a + 110, bot - 14, h=140, color=LINE, width=4)
        w, h = sizes[i]
        cx, cy = a + 330, (top + bot) / 2 - 10
        bubble(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), "3万", int(h * 0.38) + 10,
               color=AMBER if i == 0 else LINE)
    arrow(d, (95, 1450), (95, 830), color=AMBER, width=5)   # 下の階ほど大きい
    return im


def s08_research():
    im, d = canvas()
    text(d, (540, 690), "インドのサトウキビ農家（2013年の研究）", 38, fill=LINE_DIM)
    for k, (label, full) in enumerate([("収穫前（お金がない）", True), ("収穫後（お金がある）", False)]):
        x = 110 + k * 450
        d.rectangle([x, 750, x + 410, 1180], outline=AMBER if full else LINE, width=5)
        text(d, (x + 205, 1220), label, 34, fill=AMBER if full else LINE)
        head, r = person(d, x + 200, 1160, h=250, color=WHITE, width=4)
        d.polygon([(head[0] - r * 1.8, head[1] - r * 0.4), (head[0] + r * 1.8, head[1] - r * 0.4), (head[0], head[1] - r * 1.9)],
                  outline=WHITE, width=4)   # 麦わら帽子
        if full:
            for j, bx in enumerate([(130, 780, 260, 860), (250, 770, 380, 850), (180, 840, 330, 920)]):
                bubble(d, (bx[0] + x - 110, bx[1], bx[2] + x - 110, bx[3]), ["借金", "支払い", "お金"][j], 30, color=AMBER)
        else:
            bubble(d, (x + 140, 790, x + 270, 870), "", 20, color=LINE_DIM)
    bar_chart(d, 330, 1290, [62, 100], ["収穫前", "収穫後"], h=200, bw=150, gap=120, colors=[AMBER, LINE], size=32)
    text(d, (540, 1610), "同じ人のテストの成績（高さはイメージ）", 30, fill=LINE_DIM)
    return im


def s08b_bandwidth():
    """収穫前の人の頭の中：心配の吹き出しが、考えるための場所を埋めている"""
    im, d = canvas()
    text(d, (540, 690), "収穫前（お金がない）", 40, fill=AMBER)
    head, r = person(d, 540, 1500, h=640, color=WHITE, width=6)
    d.polygon([(head[0] - r * 1.8, head[1] - r * 0.4), (head[0] + r * 1.8, head[1] - r * 0.4), (head[0], head[1] - r * 1.9)],
              outline=WHITE, width=6)
    for (x0, y0, x1, y1), word in [((120, 760, 380, 880), "借金"), ((400, 740, 680, 860), "支払い"),
                                   ((700, 770, 930, 890), "お金"), ((200, 880, 470, 990), "来月"),
                                   ((560, 880, 860, 990), "家族の食費")]:
        bubble(d, (x0, y0, x1, y1), word, 40, color=AMBER)
    dashed(d, (120, 1010), (930, 1010), color=LINE_DIM)
    text(d, (540, 1040), "考えるための場所が、心配で埋まる", 34, fill=LINE_DIM)
    return im


def s09b_loop():
    """最後の絵＝S02 の最後の絵（ループで冒頭に戻ったとき、つなぎ目が目立たないように）"""
    im, d = canvas()
    building_scene(d)
    return im


def s09_space():
    im, d = canvas()
    floors = building(d, 150, 760, 520, 780, labels=LABELS, highlight=[0])
    for i, (a, top, b, bot) in enumerate(floors):
        pose = "look_up" if i == 0 else ("look_down" if i == 3 else "stand")
        person(d, a + 170, bot - 14, h=150, color=AMBER if i == 0 else LINE, pose=pose, width=4)
        text(d, (a + 300, bot - 40), NAMES[i], 30, fill=LINE_DIM)
    a, top, b, bot = floors[0]
    dashed(d, (a + 260, top + 30), (a + 420, top + 30), color=LINE_DIM)       # 消えた吹き出しの跡
    dashed(d, (a + 260, top + 90), (a + 420, top + 90), color=LINE_DIM)
    a4, top4, b4, bot4 = floors[3]
    arrow(d, (a4 + 420, top4 + 60), (a + 420, bot - 120), color=AMBER, width=4)   # 4階から1階へのメッセージ
    text(d, (a4 + 445, (top4 + bot) / 2), "✉", 48, fill=AMBER)
    return im


def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    for old in MEDIA.glob("*"):          # 名前を変えた素材が残らないよう、作り直す前に消す
        if old.is_file():
            old.unlink()
    (OUT / "audio").mkdir(exist_ok=True)
    (OUT / "audio" / "ここにナレーション（mp3など1本）を入れる.txt").write_text(
        "script.md の本文（「テロップ：」「効果音：」と「//」の行を除く）を読み上げた音声を、このフォルダに1本だけ入れてください。\n",
        encoding="utf-8")
    (OUT / "script.md").write_text(SCRIPT, encoding="utf-8")
    import sfx
    se = OUT / "se"
    se.mkdir(exist_ok=True)
    sfx.make("ガシャッ", se / "K01_ガシャッ.wav")
    sfx.make("トン", se / "K02_トン.wav")
    save_mp4(s01_crack(), MEDIA / "S01_スマホが割れる.mp4")
    save_mp4(s02_split(), MEDIA / "S02_同期4人が各階へ.mp4")
    for name, fn in [("S03_1F_ケンタ", s03_kenta), ("S04_2F_ユイ", s04_yui), ("S05_3F_ショウ", s05_sho),
                     ("S06_4F_リク", s06_riku), ("S07_頭の中の大きさ", s07_sizes), ("S08a_研究_農家", s08_research),
                     ("S08b_頭の空きを奪う", s08b_bandwidth), ("S09a_頭の空き", s09_space), ("S09b_あなたは何階", s09b_loop)]:
        save_png(fn(), MEDIA / f"{name}.png")
    print("ok:", OUT)


if __name__ == "__main__":
    main()

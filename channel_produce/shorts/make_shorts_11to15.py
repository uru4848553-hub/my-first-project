"""ショート11〜15（2026-11-27 企画。research/1127_企画決定.md）。

python channel_produce/shorts/make_shorts_11to15.py      → 5本とも
python channel_produce/shorts/make_shorts_11to15.py 12   → 12本目だけ

11は長尺第2弾「頼りにされていた人が辞めた職場は、10年後どうなるのか」の予告（長尺につなげる1本）。
会社の回は「同じ設計部の4人」：1階 平社員ミナト／2階 係長アオイ／3階 課長タクヤ／4階 部長ジュン。
ボーナスの回だけ年収別の同期4人（ケンタ・ユイ・ショウ・リク）。
絵のルール（スキル5章）：たとえは言葉で言う／目印を入れる／文字は最小40px。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blueprint import (AMBER, LINE, LINE_DIM, NAVY, WHITE, arrow, bubble, canvas, clock, desk,  # noqa: E402
                       ease, intro_stack, loop_end, person, phone, room, text)
from make_shorts_2to5 import write_folder  # noqa: E402

ROLES = ["平社員", "係長", "課長", "部長"]
STAFF = ["ミナト", "アオイ", "タクヤ", "ジュン"]
INCOMES = ["年収 300万", "年収 500万", "年収 700万", "年収 1000万"]
DOUKI = ["ケンタ", "ユイ", "ショウ", "リク"]
GO_LONG = "続きは本編で。辞めた職場の10年後を、図面にした。"


def stack(labels, names):
    return lambda: intro_stack(labels, names, "同じ部署" if labels is ROLES else "入社式", label_size=40)


def end(labels, names):
    return lambda: loop_end(labels, names, label_size=40)


def floor_room(floor, sub, draw, labels=ROLES, names=STAFF):
    def make():
        im, d = canvas()
        box = room(d, floor, f"{floor + 1}F｜{labels[floor].replace(' ', '')}｜{names[floor]}｜{sub}", title_size=40)
        draw(d, box)
        return im
    return make


def thought(floor, sub, s, labels=ROLES, names=STAFF, extra=None):
    def draw(d, box):
        person(d, 300, box[3] - 6, h=380, color=AMBER)
        bubble(d, (90, 790, 990, 950), s, 44, tail=(300, 1040))
        if extra:
            extra(d, box)
    return floor_room(floor, sub, draw, labels, names)


def card(lines, amber=(), head=None, size=72):
    def make():
        im, d = canvas()
        if head:
            text(d, (540, 700), head, 44, fill=LINE)
        top = 1000 - (len(lines) - 1) * 65
        for i, s in enumerate(lines):
            text(d, (540, top + i * 130), s, size, fill=AMBER if i in amber else WHITE)
        return im
    return make


def research(title, draw):
    def make():
        im, d = canvas()
        text(d, (540, 690), title, 40, fill=LINE_DIM)
        draw(d)
        return im
    return make


def speech_pop(s, sub=None, color=AMBER):
    """吹き出しの言葉がポンと出る（約1秒）"""
    def make():
        frames = []
        for f in range(32):
            im, d = canvas()
            t = ease(min(1, f / 8))
            w = 440 * t + 40
            d.rounded_rectangle([540 - w, 860 - 120 * t, 540 + w, 860 + 120 * t], radius=40, outline=color, width=8)
            if f >= 6:
                text(d, (540, 860), s, 96, fill=WHITE)
            if sub and f >= 14:
                text(d, (540, 1060), sub, 48, fill=LINE)
            frames.append(im)
        return frames
    return make


# ======================================================== 11. 「辞めます」（長尺の予告）
S11 = """# 「辞めます」、4つの階でどう聞こえる？（長尺第2弾の予告）
// 研究：Hancock ほか 2013（Journal of Management）。本編へつなげる

## S01
テロップ：辞めます
効果音：K01 +0.1
来年の3月で、辞めます。

## S02
テロップ：同じ部署の4人 役職別
{TON}
係長の、たった4文字。同じ部署の4人には、まったく違う重さで聞こえた。

## S03
テロップ：平社員「誰に聞けばいい？」
平社員は思う。来年から、誰に聞けばいいんだろう。

## S04
テロップ：係長「3年、言い続けた」
言った本人は思う。人を増やしてと、3年、言い続けた。

## S05
テロップ：課長「この仕事、誰に振る？」
課長は思う。この仕事を、誰に振ろう。

## S06
テロップ：部長「来年度の採用で考えよう」
部長は思う。来年度の採用で、考えよう。

## S07
テロップ：品質と安全では、およそ4倍
48の調査をまとめた研究では、人が辞めることと売り上げの関係は小さかった。ところが品質と安全では、およそ4倍、強く結びついていた。

## S08
テロップ：効いてくるのは、5年後
1人の「辞めます」が効いてくるのは、言われた日ではない。5年後だ。続きは本編で。辞めた職場の10年後を、図面にした。
"""


def s11_s07(d):
    text(d, (540, 800), "人が辞めることとの結びつき", 44, fill=WHITE)
    for k, (lab, v, col) in enumerate([("売り上げ", 0.03, LINE), ("品質・安全", 0.12, AMBER)]):
        x = 330 + k * 420
        h = v * 3300
        d.rectangle([x - 110, 1380 - h, x + 110, 1380], fill=col)
        text(d, (x, 1440), lab, 46, fill=WHITE)
    d.line([(150, 1380), (930, 1380)], fill=WHITE, width=4)
    text(d, (750, 1380 - 0.12 * 3300 - 60), "約4倍", 64, fill=AMBER)


def s11_s08():
    im, d = canvas()
    d.line([(140, 1000), (940, 1000)], fill=WHITE, width=5)
    for k, (x, lab) in enumerate([(180, "言われた日"), (540, "3年後"), (900, "5年後")]):
        d.ellipse([x - 18, 982, x + 18, 1018], fill=AMBER if k == 2 else WHITE)
        text(d, (x, 1080), lab, 44, fill=AMBER if k == 2 else WHITE)
    text(d, (540, 760), "効いてくるのは", 56, fill=WHITE)
    text(d, (900, 880), "ここ", 56, fill=AMBER)
    text(d, (540, 1300), "本編：辞めた職場の10年後", 48, fill=AMBER)
    return im


def s11_extra_empty(d, box):
    d.rectangle([620, 1150, 960, box[3] - 10], outline=LINE_DIM, width=3)
    text(d, (790, 1270), "空く席", 44, fill=LINE_DIM)


def s11_voices(d, box):
    for k, yr in enumerate(["3年前", "2年前", "去年"]):
        text(d, (780, 1130 + k * 90), f"{yr}「人を増やして」", 40, fill=LINE)


def s11_tasks(d, box):
    for k in range(3):
        d.rectangle([620 + k * 40, 1120 + k * 40, 900 + k * 40, 1300 + k * 40], outline=WHITE, width=4)
    text(d, (800, 1440), "アオイの仕事", 40, fill=WHITE)


def s11_table(d, box):
    d.rectangle([600, 1120, 980, 1400], outline=LINE, width=4)
    for k, (a, v) in enumerate([("離職", "1人"), ("補充", "来年度")]):
        text(d, (630, 1190 + k * 110), a, 40, fill=LINE, anchor="lm")
        text(d, (950, 1190 + k * 110), v, 40, fill=WHITE, anchor="rm")


# ======================================================== 12. 同じ会議
S12 = """# 同じ会議、役職別に見えている世界
// 研究：Edmondson 1999（Administrative Science Quarterly）心理的安全性。51のチーム

## S01
テロップ：何か意見ある人？
効果音：K01 +0.1
何か、意見ある人？

## S02
テロップ：同じ会議 役職別
{TON}
同じ会議の、同じひと言。4つの席からは、まったく違って見えていた。

## S03
テロップ：平社員「言ったら、自分の仕事が増える」
平社員は思う。言ったら、自分の仕事が増える。

## S04
テロップ：係長「現場の問題、言うなら今だ」
係長は思う。現場の問題を言うなら、今だ。

## S05
テロップ：課長「部長の前で、もめたくない」
課長は思う。部長の前で、もめたくない。

## S06
テロップ：部長「みんな賛成。いい会議だ」
部長は思う。誰も何も言わない。みんな賛成だ。いい会議だった。

## S07
テロップ：言っても大丈夫なチームほど、成果が高い
51のチームを調べた研究では、ここでは失敗や反対を言っても大丈夫、と感じているチームほど、質問や相談が多く、成果も高かった。

## S08
テロップ：沈黙は、賛成ではない
会議の沈黙は、賛成ではない。4階から見えるのは、手が挙がらなかったことだけだ。あなたは、何階の席にいましたか？
"""


def table_scene(d, highlight=None, speak=None):
    """会議の机を横から：左から平社員・係長・課長、右端に部長"""
    d.rectangle([120, 1180, 960, 1210], fill=LINE)
    for k, (x, r) in enumerate(zip([210, 410, 610, 850], ROLES)):
        on = highlight == k
        person(d, x, 1180, h=260, pose="sit", color=AMBER if on else LINE, width=5)
        text(d, (x, 1270), r, 40, fill=AMBER if on else WHITE)
    if speak is not None:
        bubble(d, (420, 720, 1000, 860), speak, 44, tail=(850, 920))


def s12_s01():
    frames = []
    for f in range(32):
        im, d = canvas()
        table_scene(d)
        if f >= 4:
            bubble(d, (300, 700, 1000, 850), "何か意見ある人？", 52, tail=(850, 920))
        frames.append(im)
    return frames


def s12_room(k, s):
    def make():
        im, d = canvas()
        table_scene(d, highlight=k)
        text(d, (540, 640), f"{k + 1}階｜{ROLES[k]}の席から", 44, fill=AMBER)
        x = [210, 410, 610, 850][k]
        bubble(d, (90, 760, 990, 920), s, 44, tail=(x, 1000))
        return im
    return make


def s12_research(d):
    text(d, (540, 790), "51のチーム", 52, fill=WHITE)
    for k, (lab, h, col) in enumerate([("言いにくい", 180, LINE), ("言っても大丈夫", 420, AMBER)]):
        x = 320 + k * 440
        d.rectangle([x - 120, 1400 - h, x + 120, 1400], fill=col)
        text(d, (x, 1460), lab, 44, fill=WHITE)
    d.line([(140, 1400), (940, 1400)], fill=WHITE, width=4)
    text(d, (540, 900), "質問・相談・失敗の報告", 44, fill=LINE)
    text(d, (540, 1580), "→ 成果も高かった", 48, fill=AMBER)


def s12_s08():
    im, d = canvas()
    table_scene(d)
    for k, x in enumerate([210, 410, 610]):
        d.ellipse([x - 40, 820, x + 40, 900], outline=LINE_DIM, width=4)
        text(d, (x, 860), "…", 44, fill=LINE_DIM)
    text(d, (540, 650), "沈黙 ≠ 賛成", 84, fill=AMBER)
    return im


# ======================================================== 13. 同じ残業指示
S13 = """# 同じ残業指示、4つの階
// 研究：Karasek 1979（Administrative Science Quarterly）仕事の要求度と裁量

## S01
テロップ：今日中にお願い
効果音：K01 +0.1
これ、今日中にお願い。

## S02
テロップ：同じ「今日中」 役職別
{TON}
夕方5時の、同じ「今日中に」。4つの階では、重さがまったく違った。

## S03
テロップ：平社員「断れない。やり方も選べない」
平社員は思う。断れない。やり方も、選べない。

## S04
テロップ：係長「部下に頼むか、自分でやるか」
係長は思う。部下に頼むか、自分でやるか。

## S05
テロップ：課長「明日の朝でもいいと言える」
課長は思う。明日の朝でもいいと、言える。

## S06
テロップ：部長「頼んだことを、もう忘れている」
部長は、頼んだことを、もう忘れている。

## S07
テロップ：つらいのは「忙しい×選べない」
アメリカとスウェーデンの働く人を調べた研究では、一番心がすり減っていたのは、仕事が多い人ではなく、仕事が多くて、しかも自分で決められない人だった。

## S08
テロップ：同じ量でも、選べるかで重さが変わる
同じ量の仕事でも、選べるかどうかで、重さが変わる。あなたは、何階で、その「今日中」を聞きましたか？
"""


def s13_s01():
    frames = []
    for f in range(32):
        im, d = canvas()
        clock(d, 540, 760, 5, 0, r=150, label="17:00")
        t = ease(min(1, f / 10))
        y = 1500 - 300 * t
        d.rectangle([300, y, 780, y + 280], outline=AMBER, width=6)
        for k in range(4):
            d.line([(340, y + 60 + k * 50), (740, y + 60 + k * 50)], fill=LINE, width=3)
        if f >= 10:
            text(d, (540, 1000), "今日中にお願い", 72, fill=WHITE)
        frames.append(im)
    return frames


def s13_research(d):
    text(d, (540, 790), "一番すり減っていたのは？", 50, fill=WHITE)
    cells = [("仕事が少ない\n決められる", LINE_DIM), ("仕事が多い\n決められる", LINE),
             ("仕事が少ない\n決められない", LINE_DIM), ("仕事が多い\n決められない", AMBER)]
    for k, (lab, col) in enumerate(cells):
        x, y = 290 + (k % 2) * 500, 1000 + (k // 2) * 330
        d.rectangle([x - 230, y - 140, x + 230, y + 140], outline=col, width=8 if col == AMBER else 4)
        for j, line in enumerate(lab.split("\n")):
            text(d, (x, y - 30 + j * 64), line, 42, fill=AMBER if col == AMBER else WHITE)


# ======================================================== 14. 同じボーナス
S14 = """# 同じボーナス、4つの使い道（年収別）
// 研究：Thaler 1999（Journal of Behavioral Decision Making）心の会計

## S01
テロップ：ボーナス 振り込み
効果音：K01 +0.1
ボーナスが、振り込まれた。

## S02
テロップ：同期4人 年収別
{TON}
同じ日に入社した、同期の4人。同じ「ボーナス」が、まったく違う財布に入った。

## S03
テロップ：300万「カードの支払いで消える」
300万のケンタは思う。先月のカードの支払いで、ほとんど消える。

## S04
テロップ：500万「子どもの塾代に取っておく」
500万のユイは思う。来年の、子どもの塾代に取っておこう。

## S05
テロップ：700万「半分は、自分へのご褒美」
700万のショウは思う。半分は、自分へのご褒美にしよう。

## S06
テロップ：1000万「そのまま投資の口座へ」
1000万のリクは、何も考えずに、そのまま投資の口座へ移す。

## S07
テロップ：お金に「心の財布」を付けて使う
行動経済学者のセイラーは、人はお金に、心の中で名前を付けて、別々の財布に分けて使う、と考えた。同じ1万円でも、どの財布に入ったかで、使い方が変わる。

## S08
テロップ：ボーナスが入る財布が、違うだけ
ケンタがだらしないのではない。ボーナスが入る財布が、最初から違うだけだ。あなたのボーナスは、どの財布に入りましたか？
"""


def s14_s01():
    frames = []
    for f in range(32):
        im, d = canvas()
        phone(d, 340, 700, w=400, h=760)
        t = ease(min(1, f / 9))
        y = 760 + 120 * t
        d.rounded_rectangle([290, y, 790, y + 200], radius=24, fill=NAVY, outline=AMBER, width=6)
        text(d, (540, y + 60), "振り込みがありました", 36, fill=LINE_DIM)
        text(d, (540, y + 135), "ボーナス", 60, fill=AMBER)
        frames.append(im)
    return frames


def wallet(d, x, y, label, col=AMBER, w=300):
    d.rounded_rectangle([x - w / 2, y, x + w / 2, y + 180], radius=20, outline=col, width=6)
    d.line([(x - w / 2, y + 60), (x + w / 2, y + 60)], fill=col, width=4)
    text(d, (x, y + 120), label, 40, fill=WHITE)


def s14_extra(label):
    def ex(d, box):
        wallet(d, 760, 1150, label, w=320)
    return ex


def s14_research(d):
    text(d, (540, 800), "同じ1万円でも", 52, fill=WHITE)
    for k, lab in enumerate(["生活費", "貯金", "ご褒美", "投資"]):
        wallet(d, 290 + (k % 2) * 500, 950 + (k // 2) * 300, lab, col=AMBER if k == 2 else LINE)
    text(d, (540, 1600), "入った財布で、使い方が変わる", 46, fill=AMBER)


# ======================================================== 15. 同じ「反対です」
S15 = """# 同じ「反対です」、4つの階でどう聞こえる？
// 研究：Hirschman 1970『離脱・発言・忠誠』

## S01
テロップ：反対です
効果音：K01 +0.1
その案には、反対です。

## S02
テロップ：同じ部署の4人 役職別
{TON}
係長のひと言。同じ部署の4人には、まったく違う意味に聞こえた。

## S03
テロップ：平社員「言っていいんだ」
平社員は思う。言っていいんだ。

## S04
テロップ：係長「黙ったら、現場が困る」
言った本人は思う。ここで黙ったら、来月、現場が困る。

## S05
テロップ：課長「また面倒なことを」
課長は思う。また、面倒なことを。

## S06
テロップ：部長「やる気がある証拠だ」
部長は思う。反対が出るのは、やる気がある証拠だ。

## S07
テロップ：まず声を上げ、届かないと去る
経済学者のハーシュマンは、組織に不満を持った人には、声を上げるか、去るか、の2つの道があると考えた。声が届かないと感じたとき、人は去ることを選びやすくなる。

## S08
テロップ：「反対です」は、まだ辞めていない証拠
「反対です」は、まだ辞めていない人の声だ。あなたの職場で、最後に反対したのは、誰ですか？
"""


def s15_research(d):
    text(d, (540, 800), "組織に不満を持った人の道", 48, fill=WHITE)
    for k, (lab, col) in enumerate([("声を上げる", AMBER), ("届かない", LINE_DIM), ("去る", LINE)]):
        y = 960 + k * 230
        d.rectangle([290, y, 790, y + 150], outline=col, width=6)
        text(d, (540, y + 75), lab, 56, fill=col)
        if k < 2:
            arrow(d, (540, y + 160), (540, y + 222), color=AMBER, width=6)


def make_11():
    write_folder("11_辞めます", S11, "ドサッ", [
        ("S01_辞めます", speech_pop("辞めます", "来年の3月で"), "mp4"),
        ("S02_同じ部署の4人", stack(ROLES, STAFF), "mp4"),
        ("S03_平社員", thought(0, "辞めます", "誰に聞けばいい？", extra=s11_extra_empty), "png"),
        ("S04_係長", thought(1, "言った本人", "3年、言い続けた", extra=s11_voices), "png"),
        ("S05_課長", thought(2, "辞めます", "誰に振ろう？", extra=s11_tasks), "png"),
        ("S06_部長", thought(3, "辞めます", "来年度の採用で", extra=s11_table), "png"),
        ("S07_研究", research("48の調査のまとめ（2013年）", s11_s07), "png"),
        ("S08_本編へ", s11_s08, "png"),
    ])


def make_12():
    write_folder("12_同じ会議", S12, "ピロン", [
        ("S01_意見ある人", s12_s01, "mp4"),
        ("S02_4人が各階へ", stack(ROLES, STAFF), "mp4"),
        ("S03_平社員", s12_room(0, "言ったら仕事が増える"), "png"),
        ("S04_係長", s12_room(1, "言うなら今だ"), "png"),
        ("S05_課長", s12_room(2, "部長の前でもめたくない"), "png"),
        ("S06_部長", s12_room(3, "みんな賛成。いい会議"), "png"),
        ("S07_研究", research("51のチームの研究（1999年）", s12_research), "png"),
        ("S08_沈黙", s12_s08, "png"),
    ])


def make_13():
    write_folder("13_今日中に", S13, "ドサッ", [
        ("S01_今日中", s13_s01, "mp4"),
        ("S02_4人が各階へ", stack(ROLES, STAFF), "mp4"),
        ("S03_平社員", thought(0, "17:00", "断れない。選べない"), "png"),
        ("S04_係長", thought(1, "17:00", "頼むか、自分でやるか"), "png"),
        ("S05_課長", thought(2, "17:00", "明日の朝でもいい"), "png"),
        ("S06_部長", thought(3, "17:00", "（もう忘れている）"), "png"),
        ("S07_研究", research("仕事の量と、決められる幅（1979年）", s13_research), "png"),
        ("S08_最後", end(ROLES, STAFF), "png"),
    ])


def make_14():
    write_folder("14_同じボーナス", S14, "ピロン", [
        ("S01_振り込み", s14_s01, "mp4"),
        ("S02_同期4人", stack(INCOMES, DOUKI), "mp4"),
        ("S03_300万", thought(0, "ボーナスの日", "支払いで消える", INCOMES, DOUKI, s14_extra("カード払い")), "png"),
        ("S04_500万", thought(1, "ボーナスの日", "塾代に取っておく", INCOMES, DOUKI, s14_extra("塾代")), "png"),
        ("S05_700万", thought(2, "ボーナスの日", "半分はご褒美", INCOMES, DOUKI, s14_extra("ご褒美")), "png"),
        ("S06_1000万", thought(3, "ボーナスの日", "そのまま投資へ", INCOMES, DOUKI, s14_extra("投資")), "png"),
        ("S07_研究", research("心の会計（行動経済学）", s14_research), "png"),
        ("S08_最後", end(INCOMES, DOUKI), "png"),
    ])


def make_15():
    write_folder("15_反対です", S15, "ドサッ", [
        ("S01_反対です", speech_pop("反対です", "その案には"), "mp4"),
        ("S02_4人が各階へ", stack(ROLES, STAFF), "mp4"),
        ("S03_平社員", thought(0, "会議のあと", "言っていいんだ"), "png"),
        ("S04_係長", thought(1, "言った本人", "黙ったら現場が困る"), "png"),
        ("S05_課長", thought(2, "会議のあと", "また面倒なことを"), "png"),
        ("S06_部長", thought(3, "会議のあと", "やる気がある証拠だ"), "png"),
        ("S07_研究", research("離脱・発言・忠誠（1970年）", s15_research), "png"),
        ("S08_最後", end(ROLES, STAFF), "png"),
    ])


MAKERS = {11: make_11, 12: make_12, 13: make_13, 14: make_14, 15: make_15}

if __name__ == "__main__":
    for n in ([int(a) for a in sys.argv[1:]] or sorted(MAKERS)):
        MAKERS[n]()

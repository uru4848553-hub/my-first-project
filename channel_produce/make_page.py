"""channel_produce/ の資料（.md と画像）を、スマホでも読める1枚のページにまとめる。

python channel_produce/make_page.py  →  channel_produce/人生の断面図_資料.html
（markdown パッケージが必要：pip install markdown）
"""
import base64
import html
import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
OUT = HERE / "人生の断面図_資料.html"

DOCS = [
    ("rivals", "競合5チャンネル分析", "06_競合5チャンネル分析.md"),
    ("rules", "TTP分析と法則", "01_TTP分析と法則.md"),
    ("design", "チャンネル設計", "02_新チャンネル設計.md"),
    ("meta", "ショートのタイトル・説明欄・サムネ", "shorts/タイトル_説明欄_サムネ.md"),
    ("shorts5", "ショート5本の使い方", "shorts/README.md"),
    ("shorts", "ショート台本（初期案）", "04_ショート台本.md"),
    ("long", "長尺台本", "05_長尺台本_年収と時間.md"),
    ("data", "再生数データ", "03_再生数データ記入表.md"),
]


def img(name):
    return "data:image/png;base64," + base64.b64encode((HERE / name).read_bytes()).decode()


def convert(md_text):
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    # 見出しを1段下げる（ページの h1 はひとつだけにする）
    body = re.sub(r"<(/?)h([1-5])>", lambda m: f"<{m.group(1)}h{int(m.group(2)) + 1}>", body)
    body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    return body


STYLE = """
/* 設計図の紙：紺の線とアンバーの「差」。本文は読みやすさ優先の1カラム */
:root {
  --bg: #f5f7fb; --paper: #ffffff; --fg: #18223a; --muted: #5a6680;
  --line: #d8dfec; --accent: #1f4f9c; --gap: #c27c00; --gap-soft: #fff3dc; --code: #eef2f9;
  --display: "Zen Kaku Gothic New", "Hiragino Sans", "Noto Sans JP", sans-serif;
  --body: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0b1430; --paper: #111d3f; --fg: #e8edf8; --muted: #9fb0d0;
  --line: #24365f; --accent: #7cc4ff; --gap: #ffb020; --gap-soft: #2a2410; --code: #172650; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0b1430; --paper: #111d3f; --fg: #e8edf8; --muted: #9fb0d0;
  --line: #24365f; --accent: #7cc4ff; --gap: #ffb020; --gap-soft: #2a2410; --code: #172650; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15.5px; line-height: 1.8; }
.wrap { max-width: 860px; margin: 0 auto; padding-block: 24px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1, h2, h3, h4 { font-family: var(--display); text-wrap: balance; line-height: 1.4; }
h1 { font-size: 1.9rem; margin: 0; }
h2 { font-size: 1.45rem; margin: 2.2em 0 .6em; padding-bottom: .3em; border-bottom: 2px solid var(--accent); }
h3 { font-size: 1.2rem; margin: 1.8em 0 .5em; color: var(--accent); }
h4, h5, h6 { font-size: 1.05rem; margin: 1.4em 0 .4em; }
a { color: var(--accent); }
.lead { color: var(--muted); margin: .4em 0 0; }
.brand { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 16px; align-items: center; margin-top: 20px; }
.brand img.icon { width: 120px; height: 120px; border-radius: 50%; }
.banner { width: 100%; border-radius: 10px; margin-top: 16px; border: 1px solid var(--line); }
.summary { background: var(--paper); border: 1px solid var(--line); border-left: 5px solid var(--gap);
  border-radius: 10px; padding: 14px 18px; margin-top: 20px; }
.summary h2 { border: 0; margin: 0 0 .3em; font-size: 1.15rem; padding: 0; }
.summary ul { margin: 0; padding-left: 1.2em; }
.summary b { color: var(--gap); }
nav { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--bg);
  display: flex; gap: 8px; overflow-x: auto; padding: 10px 0; margin-top: 20px; border-bottom: 1px solid var(--line); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--bg); }
nav a { flex: none; text-decoration: none; padding: 6px 14px; border-radius: 999px; border: 1px solid var(--line);
  background: var(--paper); color: var(--fg); font-size: .9rem; }
nav a:focus-visible { outline: 2px solid var(--accent); }
section.doc { scroll-margin-top: 64px; }
section.doc > h2:first-child { margin-top: 1.6em; }
.tw { overflow-x: auto; margin: 1em 0; border: 1px solid var(--line); border-radius: 8px; background: var(--paper); }
table { border-collapse: collapse; width: 100%; font-size: .9rem; line-height: 1.6; }
th, td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; min-width: 5em; }
th { background: var(--code); font-weight: 700; white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
td { font-variant-numeric: tabular-nums; }
pre { background: var(--code); padding: 12px 14px; border-radius: 8px; overflow-x: auto; font-size: .85rem; line-height: 1.6; }
code { font-family: ui-monospace, Menlo, Consolas, monospace; }
:not(pre) > code { background: var(--code); padding: 1px 5px; border-radius: 4px; font-size: .9em; }
blockquote { margin: 1em 0; padding: 8px 16px; border-left: 4px solid var(--accent); background: var(--paper); border-radius: 0 8px 8px 0; }
strong { color: var(--fg); background: linear-gradient(transparent 62%, var(--gap-soft) 62%); }
.alts { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
.alts figure { margin: 0; } .alts img { width: 100%; border-radius: 8px; border: 1px solid var(--line); }
.alts figcaption { color: var(--muted); font-size: .85rem; }
.copywrap { position: relative; }
.copybtn { position: absolute; top: 6px; right: 6px; font: inherit; font-size: .8rem; padding: 4px 10px;
  border-radius: 6px; border: 1px solid var(--line); background: var(--paper); color: var(--fg); cursor: pointer; }
.copybtn:focus-visible { outline: 2px solid var(--accent); }
"""


SCRIPT_JS = """<script>
document.querySelectorAll("pre").forEach(function (pre) {
  var wrap = document.createElement("div");
  wrap.className = "copywrap";
  pre.parentNode.insertBefore(wrap, pre);
  wrap.appendChild(pre);
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "copybtn";
  btn.textContent = "コピー";
  btn.addEventListener("click", function () {
    var t = pre.innerText;
    var done = function () { btn.textContent = "コピーしました"; setTimeout(function () { btn.textContent = "コピー"; }, 1500); };
    try {
      navigator.clipboard.writeText(t).then(done, function () { select(); });
    } catch (e) { select(); }
    function select() {
      var r = document.createRange(); r.selectNodeContents(pre);
      var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      btn.textContent = "選択しました（Ctrl+C）";
    }
  });
  wrap.appendChild(btn);
});
</script>
"""


def build():
    nav = "".join(f'<a href="#{key}">{html.escape(label)}</a>' for key, label, _ in DOCS)
    sections = []
    for key, label, name in DOCS:
        body = convert((HERE / name).read_text(encoding="utf-8"))
        sections.append(f'<section class="doc" id="{key}">{body}</section>')
        if key == "design":
            sections.append(
                '<div class="alts">'
                f'<figure><img src="{img("banner_safe_preview.png")}" alt="バナーのスマホ表示範囲（赤枠）">'
                '<figcaption>バナー：赤枠の中がスマホでも見える範囲</figcaption></figure>'
                f'<figure><img src="{img("icon_alt.png")}" alt="予備案のアイコン">'
                '<figcaption>予備案「差の設計図」のアイコン</figcaption></figure></div>')
    page = f"""<title>人生の断面図 企画書</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Zen+Kaku+Gothic+New:wght@700&display=swap">
<style>{STYLE}</style>
<div class="wrap">
  <header>
    <div class="brand">
      <img class="icon" src="{img("icon.png")}" alt="人生の断面図のアイコン">
      <div>
        <h1>人生の断面図</h1>
        <p class="lead">夜ふかし解剖室（@yofukashi_kaibou）の TTP 分析から作った、新チャンネルの企画書・台本一式</p>
      </div>
    </div>
    <img class="banner" src="{img("banner.png")}" alt="人生の断面図のバナー">
    <div class="summary">
      <h2>結論（要点）</h2>
      <ul>
        <li>元チャンネルは<b>開設46日・35本で総再生288万回</b>。1本目から20万回。型とテーマの力で伸びている＝<b>再現しやすい</b></li>
        <li>型は<b>「〇〇別 視えている世界」</b>。年収・世代・IQなど<b>順位がはっきりした軸</b>を<b>3〜4段</b>に分ける。心理・性格の軸と2段の比較は外れやすい</li>
        <li>中身は<b>4人の登場人物の物語</b>（こちらは同期4人）＋<b>意外な研究</b>＋<b>最後に救い</b>。冒頭は「数字2つ→言い切り→同じスタートの4人」</li>
        <li>当たりは<b>約4本に1本</b>。課題は本数 → 長尺1本からショート4本を切り出す</li>
        <li>次にやること：4人のキャラクターと空のビルの断面図を作る → 長尺第1弾（年収）を制作</li>
      </ul>
    </div>
  </header>
  <nav aria-label="資料の目次">{nav}</nav>
  {"".join(sections)}
</div>
{SCRIPT_JS}
"""
    OUT.write_text(page, encoding="utf-8")
    print("ok:", OUT, f"{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    build()

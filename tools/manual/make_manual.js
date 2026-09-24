// Resolve 自動配置ツール 取扱説明書（PowerPoint）を作る
// 使い方: npm install pptxgenjs のあと  node tools/manual/make_manual.js  → 取扱説明書.pptx
const pptxgen = require("pptxgenjs");
const path = require("path");

const SP = __dirname;
const REPO = path.join(__dirname, "..", "..");
const OUT = process.argv[2] || path.join(REPO, "取扱説明書.pptx");
const IMG = (n) => path.join(SP, "shots", n);

const C = {
  dark: "161B26", ink: "1F2937", muted: "5B6472", light: "F2F4F8", line: "D5DAE3",
  orange: "F28C28", orangeSoft: "FDEBD7", white: "FFFFFF",
  video: "3B82F6", telop: "F28C28", narr: "22A06B", bgm: "8B5CF6", se: "E5484D",
};
const F = "Meiryo";
const MONO = "Consolas";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Resolve 自動配置ツール 取扱説明書";

// ---------- 部品 ----------
function title(s, text, sub) {
  s.addText(text, { x: 0.6, y: 0.4, w: 12.1, h: 0.75, fontFace: F, fontSize: 30, bold: true, color: C.ink, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: 0.6, y: 1.12, w: 12.1, h: 0.4, fontFace: F, fontSize: 14, color: C.muted, margin: 0, isTextBox: true });
}
function num(s, x, y, n, d = 0.5, fill = C.orange) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: F, fontSize: d * 34, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function card(s, x, y, w, h, fill = C.light) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill } });
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(t, Object.assign({ x, y, w, h, fontFace: F, fontSize: 14, color: C.ink, margin: 0, valign: "top", isTextBox: true }, o));
}
function code(s, t, x, y, w, h, size = 12) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: "1E2430" }, line: { color: "1E2430" } });
  s.addText(t, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: h - 0.24, fontFace: MONO, fontSize: size, color: "E6EDF3", margin: 0, valign: "top", isTextBox: true });
}
function shot(s, file, x, y, w, h) {
  s.addImage({ path: IMG(file), x, y, w, h, shadow: { type: "outer", color: "000000", opacity: 0.25, blur: 8, offset: 3, angle: 90 } });
}
function bullets(items, size = 14) {
  return items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6, fontSize: size } }));
}
function note(s, t, x, y, w, h) {
  card(s, x, y, w, h, C.orangeSoft);
  text(s, t, x + 0.2, y + 0.12, w - 0.4, h - 0.24, { fontSize: 13, valign: "middle" });
}
// タイムラインの図（トラックごとのブロック）
function timeline(s, x, y, w, rowH = 0.46, labelW = 1.5) {
  const rows = [
    ["V2 テロップ", C.telop, [[0, 0.24], [0.24, 0.47], [0.47, 0.72], [0.72, 1]]],
    ["V1 動画・画像", C.video, [[0, 0.24], [0.24, 0.47], [0.47, 0.6], [0.6, 0.72], [0.72, 1]]],
    ["A1 ナレーション", C.narr, [[0, 1]]],
    ["A2 BGM", C.bgm, [[0, 1]]],
    ["A3 効果音", C.se, [[0, 0.05], [0.66, 0.72]]],
  ];
  const bw = w - labelW;
  rows.forEach(([label, color, blocks], i) => {
    const ry = y + i * (rowH + 0.12);
    text(s, label, x, ry, labelW - 0.1, rowH, { fontSize: 12, bold: true, valign: "middle", color: C.ink });
    s.addShape(pres.shapes.RECTANGLE, { x: x + labelW, y: ry, w: bw, h: rowH, fill: { color: "E7EBF1" }, line: { color: "E7EBF1" } });
    blocks.forEach(([a, b]) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + labelW + bw * a + 0.02, y: ry + 0.05, w: Math.max(bw * (b - a) - 0.04, 0.12), h: rowH - 0.1, rectRadius: 0.05, fill: { color }, line: { color } });
    });
  });
  // シーンの頭のマーカー
  [0, 0.24, 0.47, 0.72].forEach((a, i) => {
    s.addShape(pres.shapes.OVAL, { x: x + labelW + bw * a + 0.02, y: y - 0.3, w: 0.2, h: 0.2, fill: { color: "2563EB" }, line: { color: "2563EB" } });
    text(s, `S0${i + 1}`, x + labelW + bw * a + 0.26, y - 0.33, 0.6, 0.26, { fontSize: 10, color: C.muted, valign: "middle" });
  });
}

// ---------- 1. 表紙 ----------
{
  const s = pres.addSlide(); s.background = { color: C.dark };
  s.addImage({ path: path.join(REPO, "assets", "app.png"), x: 0.8, y: 1.0, w: 1.3, h: 1.3 });
  text(s, "Resolve 自動配置ツール", 0.8, 2.6, 7.2, 1.0, { fontSize: 40, bold: true, color: C.white });
  text(s, "取扱説明書", 0.8, 3.55, 7, 0.7, { fontSize: 28, color: C.orange, bold: true });
  text(s, "絵コンテ → 台本 → 素材を入れて「スタート」\nDaVinci Resolve にタイムラインが自動でできあがります", 0.8, 4.5, 7, 1.0, { fontSize: 16, color: "C9D1DD" });
  text(s, "2026年9月版", 0.8, 6.6, 4, 0.4, { fontSize: 12, color: "8A94A6" });
  s.addImage({ path: IMG("storyboard.jpg"), x: 7.9, y: 0.9, w: 4.9, h: 2.99, shadow: { type: "outer", color: "000000", opacity: 0.5, blur: 12, offset: 4, angle: 90 } });
  s.addImage({ path: IMG("telop_example.png"), x: 10.85, y: 4.15, w: 1.75, h: 3.11, shadow: { type: "outer", color: "000000", opacity: 0.5, blur: 12, offset: 4, angle: 90 } });
}

// ---------- 2. できること ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "このツールでできること", "台本のシーン順に、素材・テロップ・音をタイムラインへ自動で並べます");
  card(s, 0.6, 1.8, 7.6, 4.05);
  text(s, "できあがるタイムライン（イメージ）", 0.85, 1.95, 7, 0.35, { fontSize: 13, bold: true, color: C.muted });
  timeline(s, 0.85, 2.75, 7.1);
  text(s, "● はシーンの頭に付くマーカー（名前＝シーン番号）", 0.85, 5.55, 7, 0.28, { fontSize: 11, color: C.muted });

  text(s, "自動でやること", 8.7, 1.8, 4.1, 0.4, { fontSize: 18, bold: true, color: C.narr });
  s.addText(bullets([
    "読み上げに合わせてシーンを切り替え",
    "動画が短いときは最後の画面で埋める",
    "テロップを作って V2 に置く",
    "BGM・効果音を置く",
    "縦長 1080×1920・30fps で作る",
  ], 13), { x: 8.7, y: 2.25, w: 4.1, h: 2.3, fontFace: F, color: C.ink, margin: 0, valign: "top", isTextBox: true });
  text(s, "人がやること", 8.7, 4.65, 4.1, 0.4, { fontSize: 18, bold: true, color: C.se });
  s.addText(bullets([
    "最後の確認（再生して見る）",
    "音量の調整・テロップの色分けなどの仕上げ",
  ], 13), { x: 8.7, y: 5.1, w: 4.1, h: 1.0, fontFace: F, color: C.ink, margin: 0, valign: "top", isTextBox: true });
  note(s, "既存のタイムラインは変更しません。実行するたびに「動画名_日付_時刻」の新しいタイムラインが増えます。", 0.6, 6.1, 12.2, 0.75);
}

// ---------- 3. 全体の流れ ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "動画ができるまでの流れ", "毎回この5ステップ。②〜④はアプリの中で進めます");
  const steps = [
    ["絵コンテを作る", "今までどおり PNG で作成。ナレーション・テロップ・素材名を書く", "p.6"],
    ["台本に変換", "アプリの「絵コンテ画像から作る」で PNG を読み込み、文字を確認", "p.7"],
    ["ナレーション音声", "台本の文章を ElevenLabs などで読み上げて1本の音声に", "p.9"],
    ["素材を入れてスタート", "動画・画像・BGM・効果音を入れて「▶ スタート」", "p.10-12"],
    ["Resolve で確認", "再生してチェック。音量などを仕上げて完成", "p.13"],
  ];
  const w = 2.3, gap = 0.18, y = 2.1;
  steps.forEach(([h, d, p], i) => {
    const x = 0.6 + i * (w + gap);
    card(s, x, y, w, 3.6, i === 1 ? C.orangeSoft : C.light);
    num(s, x + 0.25, y + 0.3, i + 1, 0.6);
    text(s, h, x + 0.25, y + 1.1, w - 0.4, 0.8, { fontSize: 17, bold: true });
    text(s, d, x + 0.25, y + 1.9, w - 0.45, 1.3, { fontSize: 12.5, color: C.muted });
    text(s, `→ ${p}`, x + 0.25, y + 3.15, w - 0.4, 0.3, { fontSize: 11, color: C.orange, bold: true });
    if (i < steps.length - 1) text(s, "▶", x + w - 0.02, y + 1.6, gap + 0.05, 0.4, { fontSize: 12, color: C.line, align: "center" });
  });
  note(s, "時間のめやす：準備 10分 ＋ 処理（音声1分あたり約2分）。処理中は待つだけです。", 0.6, 6.1, 12.2, 0.7);
}

// ---------- 4. 最初の準備 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "最初の準備（1回だけ）", "新しいパソコンや更新のあとに行います");
  const colW = 3.9, y = 1.9;
  [
    ["最新版と部品を入れる", "PowerShell で1行ずつ貼り付けて Enter"],
    ["デスクトップにアイコン", "フォルダの「ショートカット作成.bat」をダブルクリック"],
    ["API キーを用意", "絵コンテ画像の読み取りに使う（次のページ）"],
  ].forEach(([h, d], i) => {
    const x = 0.6 + i * (colW + 0.25);
    card(s, x, y, colW, 4.6);
    num(s, x + 0.25, y + 0.25, i + 1);
    text(s, h, x + 0.9, y + 0.28, colW - 1.1, 0.5, { fontSize: 17, bold: true, valign: "middle" });
    text(s, d, x + 0.25, y + 0.95, colW - 0.5, 0.6, { fontSize: 12.5, color: C.muted });
  });
  code(s, 'cd "G:\\@Auto_Davinch-Cloude"\ngit pull origin claude/claude-md-phase-0-qxn5wu\n.\\run.bat -m pip install -r requirements.txt', 0.8, 3.6, 3.5, 1.6, 9);
  text(s, "最後に「Successfully installed」か「already satisfied」と出れば OK", 0.85, 5.4, 3.4, 0.8, { fontSize: 11.5, color: C.muted });
  s.addImage({ path: path.join(REPO, "assets", "app.png"), x: 5.9, y: 3.5, w: 1.2, h: 1.2 });
  text(s, "Resolve自動配置", 5.2, 4.75, 2.6, 0.35, { fontSize: 13, bold: true, align: "center" });
  text(s, "次からはこのアイコンを\nダブルクリックするだけ", 4.95, 5.25, 3.1, 0.8, { fontSize: 12, color: C.muted, align: "center" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.2, y: 3.55, w: 3.3, h: 0.7, rectRadius: 0.1, fill: { color: C.white }, line: { color: C.line } });
  text(s, "sk-ant-api03-••••••••", 9.35, 3.55, 3.0, 0.7, { fontFace: MONO, fontSize: 13, valign: "middle", color: C.ink });
  text(s, "キーは初回の読み取り時にアプリが聞いてきます。一度入れれば覚えています", 9.0, 4.45, 3.5, 1.2, { fontSize: 12, color: C.muted });
}

// ---------- 5. API キー ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "API キーの作り方", "絵コンテ画像の読み取り（AI）に使います。1回 数円〜十数円程度");
  const steps = [
    ["console.anthropic.com を開く", "アカウントがなければ作成してログイン"],
    ["クレジットを購入", "「Billing」から。最低 5 ドル程度で十分"],
    ["キーを作る", "「API Keys」→「Create Key」。名前は自由（例: resolve）"],
    ["キーをコピー", "sk-ant- で始まる文字。画面を閉じると二度と見られないので注意"],
    ["アプリに貼る", "「絵コンテ画像から作る…」を初めて押したときの画面に貼り付けて OK"],
  ];
  steps.forEach(([h, d], i) => {
    const y = 1.85 + i * 0.95;
    num(s, 0.6, y, i + 1, 0.55);
    text(s, h, 1.35, y - 0.03, 5.2, 0.4, { fontSize: 16, bold: true });
    text(s, d, 1.35, y + 0.37, 5.3, 0.45, { fontSize: 12.5, color: C.muted });
  });
  shot(s, "app_apikey.png", 7.0, 1.75, 5.7, 5.24);
  note(s, "キーはパスワードと同じ。人に見せたり、SNS に載せたりしないでください", 0.6, 6.65, 6.1, 0.55);
}

// ---------- 6. 絵コンテのルール ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "絵コンテの書き方のルール", "各カットに「素材ファイル名」の欄を作り、下の名前で書きます");
  s.addImage({ path: IMG("storyboard.jpg"), x: 0.6, y: 1.8, w: 6.6, h: 4.03 });
  text(s, "例：samples\\絵コンテ_iPhone\\絵コンテ_修正版.png", 0.6, 5.9, 6.6, 0.3, { fontSize: 11, color: C.muted });
  const hdr = { bold: true, color: C.white, fill: { color: C.dark }, fontFace: F, fontSize: 13 };
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontFace: F, fontSize: 13, color: C.ink }, o) });
  s.addTable([
    [{ text: "項目", options: hdr }, { text: "名前", options: hdr }, { text: "ポイント", options: hdr }],
    [cell("動画・画像"), cell("M01, M02 …", { bold: true }), cell("カット番号と同じ数字")],
    [cell("1カットに複数"), cell("M03_1, M03_2", { bold: true }), cell("ナレーションを [1][2] で分ける")],
    [cell("テロップ"), cell("S01, S02 …", { bold: true }), cell("画面の見出し文字")],
    [cell("効果音"), cell("K01, K02 …", { bold: true }), cell("使うカットにだけ書く")],
    [cell("BGM"), cell("BGM1", { bold: true }), cell("動画全体で1曲")],
  ], { x: 7.5, y: 1.8, w: 5.25, colW: [1.45, 1.6, 2.2], rowH: 0.5, border: { type: "solid", color: C.line, pt: 1 }, fill: { color: C.white } });
  note(s, "ナレーション欄は「読み上げる文章そのもの」を書きます。この文章が台本になり、音声とも一致させます。", 7.5, 5.1, 5.25, 1.1);
}

// ---------- 7. 絵コンテ画像から台本を作る ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "絵コンテ画像から台本を作る", "PNG を選ぶだけで、AI が台本の文字に変換します");
  shot(s, "app_storyboard.png", 0.6, 1.75, 5.8, 5.34);
  const steps = [
    ["「絵コンテ画像から作る…」を押す", "アプリの ② 台本 の欄にあるボタン"],
    ["絵コンテの PNG を選ぶ", "複数ページなら Ctrl を押しながら全部選ぶ（名前順に読みます）"],
    ["30秒〜1分待つ", "② の欄に台本が入ります"],
    ["「直した箇所」を確認", "崩れた文字を AI が直した所が一覧で出ます。違っていれば ② で直接修正"],
  ];
  steps.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.02;
    num(s, 6.9, y, i + 1, 0.55);
    text(s, h, 7.65, y - 0.03, 5.1, 0.4, { fontSize: 16, bold: true });
    text(s, d, 7.65, y + 0.38, 5.1, 0.55, { fontSize: 12.5, color: C.muted });
  });
  note(s, "AI の変換は完璧ではありません。特にナレーションの文章は必ず目で確認してください（音声と合わないと、切り替え位置がずれます）", 6.9, 6.0, 5.85, 1.0);
}

// ---------- 8. 台本の書き方 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "台本の書き方（自分で直すとき）", "② の欄に書く文字のルール。AI で作った台本もこの形になっています");
  code(s, [
    "## S01",
    "// 動画：M01",
    "テロップ：ついに、想像を超えた",
    "テロップ：iPhoneが来る。",
    "効果音：K01",
    "ついに、私たちの想像を超えたiPhoneがやって来ます。",
    "",
    "## S03",
    "テロップ：シーン全体に出す文字",
    "[1] 最初の部分のナレーション。",
    "効果音：K02 +1.5",
    "[2] 次の部分のナレーション。",
  ].join("\n"), 0.6, 1.8, 6.4, 4.9, 13);
  const rows = [
    ["## S01", "シーンの区切り（必須）。S＋2桁"],
    ["テロップ：文字", "1行＝画面の1行。見出しの直後ならシーン全体に出る"],
    ["効果音：K01", "シーンの頭で鳴らす。「+1.5」で1.5秒後"],
    ["[1] [2]", "1シーンで素材を切り替える位置（M03_1・M03_2 と対応）"],
    ["// メモ", "読み上げない。カメラの指示などを残せる"],
    ["それ以外の行", "ナレーション（音声と同じ文章に）"],
  ];
  rows.forEach(([k, d], i) => {
    const y = 1.85 + i * 0.8;
    card(s, 7.3, y, 5.45, 0.68);
    text(s, k, 7.45, y, 1.9, 0.68, { fontFace: MONO, fontSize: 13, bold: true, color: C.orange, valign: "middle" });
    text(s, d, 9.35, y, 3.3, 0.68, { fontSize: 12, valign: "middle" });
  });
}

// ---------- 9. ナレーション音声 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "ナレーション音声を作る", "切り替え位置は「台本の文章」と「音声」を突き合わせて決まります");
  const cards = [
    ["台本の文章をそのまま読ませる", "② の台本から、ナレーションの行だけをコピーして ElevenLabs などに入れる。テロップ・// の行は入れない"],
    ["音声ファイルは1本", "全シーン分を1本にまとめる。形式は mp3 / wav / m4a。ファイル名は自由"],
    ["台本を直したら音声も作り直す", "文章が違うと切り替え位置がずれ、レポートに「信頼度が低い」と警告が出ます"],
  ];
  cards.forEach(([h, d], i) => {
    const x = 0.6 + i * 4.15;
    card(s, x, 1.9, 3.9, 3.3);
    num(s, x + 0.3, 2.2, i + 1, 0.6, [C.narr, C.video, C.se][i]);
    text(s, h, x + 0.3, 3.0, 3.3, 0.8, { fontSize: 17, bold: true });
    text(s, d, x + 0.3, 3.8, 3.3, 1.3, { fontSize: 12.5, color: C.muted });
  });
  // 波形のイメージ
  const wy = 5.75;
  for (let i = 0; i < 60; i++) {
    const h = 0.15 + Math.abs(Math.sin(i * 0.7) * Math.cos(i * 0.23)) * 0.75;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + i * 0.205, y: wy + (0.9 - h) / 2, w: 0.1, h, fill: { color: C.narr }, line: { color: C.narr } });
  }
  text(s, "例：iPhone の台本（8シーン）→ 約43秒の音声1本", 0.6, 6.8, 12, 0.35, { fontSize: 12, color: C.muted });
}

// ---------- 10. アプリ画面の見方 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "アプリ画面の見方", "上から順に ①〜⑤ を埋めて「▶ スタート」");
  const sx = 0.95, sy = 1.7, sh = 5.55, sc = sh / 920, sw = 1000 * sc;
  shot(s, "app_filled.png", sx, sy, sw, sh);
  [[22, 1], [160, 2], [340, 3], [462, 4], [672, 5]].forEach(([py, n]) => num(s, sx - 0.42, sy + py * sc - 0.17, n, 0.36));
  const items = [
    ["動画の名前と保存先", "名前がタイムライン名に。保存先に作業フォルダができる"],
    ["台本", "絵コンテ画像から作る／貼り付ける／ファイルから読み込む"],
    ["ナレーションと BGM", "ナレーションは必須。BGM はなくても OK"],
    ["素材と効果音", "シーンごとに動画・画像を。効果音の行は台本から自動で出る"],
    ["Resolve に並べる", "プロジェクト名（なければ作る）→「▶ スタート」"],
  ];
  items.forEach(([h, d], i) => {
    const y = 1.75 + i * 1.08;
    num(s, 7.35, y, i + 1, 0.45);
    text(s, h, 7.95, y - 0.02, 4.8, 0.4, { fontSize: 15, bold: true });
    text(s, d, 7.95, y + 0.38, 4.8, 0.6, { fontSize: 12, color: C.muted });
  });
}

// ---------- 11. 素材の入れ方 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "④ 素材・効果音の入れ方", "「まとめて追加」なら、ファイル名を見て自動で振り分けます");
  const hdr = { bold: true, color: C.white, fill: { color: C.dark }, fontFace: F, fontSize: 13 };
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontFace: F, fontSize: 13, color: C.ink }, o) });
  s.addTable([
    [{ text: "ファイル名", options: hdr }, { text: "入る場所", options: hdr }],
    [cell("M01.mp4 / M01_オープニング.mp4", { fontFace: MONO }), cell("S01")],
    [cell("M03_1.mp4 / M03_2.png", { fontFace: MONO }), cell("S03 の [1] / [2]")],
    [cell("K01_ポン.wav", { fontFace: MONO }), cell("効果音 K01 の行")],
    [cell("それ以外の名前", {}), cell("空いている行に、名前の順で上から")],
  ], { x: 0.6, y: 1.8, w: 6.6, colW: [3.9, 2.7], rowH: 0.55, border: { type: "solid", color: C.line, pt: 1 } });
  const tips = [
    ["1つずつ選ぶ", "表の行をダブルクリック → ファイルを選ぶ"],
    ["同じ素材を何シーンにも", "Shift を押しながら行を選び「選んだ行のファイルを選ぶ…」"],
    ["入れ直す", "行を選んで「選んだ行から外す」"],
  ];
  tips.forEach(([h, d], i) => {
    const y = 1.8 + i * 1.25;
    card(s, 7.6, y, 5.15, 1.05);
    text(s, h, 7.85, y + 0.12, 4.7, 0.4, { fontSize: 15, bold: true });
    text(s, d, 7.85, y + 0.52, 4.7, 0.45, { fontSize: 12, color: C.muted });
  });
  note(s, "赤い「（未選択）」が残っているとスタートできません。画面下に「準備ができました」と出たら OK", 0.6, 5.0, 6.6, 0.95);
  text(s, "使える形式　動画：mp4 / mov　画像：png / jpg　音声：mp3 / wav / m4a", 0.6, 6.25, 12, 0.4, { fontSize: 12.5, color: C.muted });
}

// ---------- 12. スタート〜完了 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "「▶ スタート」から完了まで", "あとは待つだけ。進み具合は画面下の黒い欄に出ます");
  shot(s, "app_done.png", 0.6, 1.75, 5.8, 5.34);
  const flow = [
    ["素材をフォルダにコピー", "数秒"],
    ["Resolve を起動・プロジェクトを開く", "〜1分"],
    ["読み上げとシーンの対応をとる", "音声1分あたり約2分"],
    ["テロップ・静止画の動画を作る", "数十秒"],
    ["Resolve に並べる", "数十秒"],
  ];
  flow.forEach(([h, t], i) => {
    const y = 1.85 + i * 0.86;
    num(s, 6.9, y, i + 1, 0.5, C.dark);
    text(s, h, 7.6, y, 3.3, 0.5, { fontSize: 14.5, bold: true, valign: "middle" });
    text(s, t, 10.6, y, 2.15, 0.5, { fontSize: 12.5, color: C.orange, bold: true, valign: "middle", align: "right" });
  });
  note(s, "「完了しました」と出たら Resolve へ。エラーで止まったら「レポートを開く」で理由を確認（p.15）", 6.9, 6.25, 5.85, 0.85);
}

// ---------- 13. Resolve で確認 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "Resolve で確認・仕上げ", "新しくできたタイムラインを再生してチェック");
  const checks = [
    ["切り替え位置", "映像がナレーションと合っているか"],
    ["テロップの文字", "誤字がないか。直すときは台本を直して再スタート"],
    ["テロップの周り", "黒くなっていたら：クリップを右クリック → クリップ属性 → アルファモード「ストレート」"],
    ["音量", "BGM・効果音は自動で下げないので、Resolve で調整"],
    ["レポート", "アプリの「レポートを開く」で警告を確認"],
  ];
  checks.forEach(([h, d], i) => {
    const y = 1.8 + i * 1.0;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: y + 0.05, w: 0.38, h: 0.38, rectRadius: 0.06, fill: { color: C.white }, line: { color: C.narr, width: 2 } });
    text(s, "✓", 0.6, y + 0.02, 0.38, 0.42, { fontSize: 16, bold: true, color: C.narr, align: "center", valign: "middle" });
    text(s, h, 1.2, y - 0.17, 2.1, 0.8, { fontSize: 16, bold: true, valign: "middle" });
    text(s, d, 3.4, y - 0.17, 5.4, 0.8, { fontSize: 12.5, color: C.muted, valign: "middle" });
  });
  s.addImage({ path: IMG("telop_example.png"), x: 9.6, y: 1.7, w: 3.0, h: 5.33, shadow: { type: "outer", color: "000000", opacity: 0.3, blur: 8, offset: 3, angle: 90 } });
  text(s, "テロップの見本（白文字・黒縁・上から4分の1）", 9.2, 7.07, 3.8, 0.3, { fontSize: 10.5, color: C.muted, align: "center" });
}

// ---------- 14. 見た目の調整 ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "テロップの見た目を変える", "フォルダの config.json をメモ帳で開いて数字を変え、保存します");
  const hdr = { bold: true, color: C.white, fill: { color: C.dark }, fontFace: F, fontSize: 13 };
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontFace: F, fontSize: 12.5, color: C.ink }, o) });
  s.addTable([
    [{ text: "項目", options: hdr }, { text: "意味", options: hdr }, { text: "最初の値", options: hdr }],
    [cell("telop_size", { fontFace: MONO, bold: true }), cell("文字の大きさ"), cell("80")],
    [cell("telop_y", { fontFace: MONO, bold: true }), cell("縦の位置（上 0 〜 下 1）"), cell("0.25")],
    [cell("telop_color", { fontFace: MONO, bold: true }), cell("文字の色"), cell("#FFFFFF（白）")],
    [cell("telop_stroke_color", { fontFace: MONO, bold: true }), cell("縁取りの色"), cell("#000000（黒）")],
    [cell("telop_stroke_width", { fontFace: MONO, bold: true }), cell("縁取りの太さ"), cell("8")],
    [cell("telop_font", { fontFace: MONO, bold: true }), cell("フォントファイル（空ならメイリオ）"), cell("\"\"")],
  ], { x: 0.6, y: 1.8, w: 7.4, colW: [2.6, 3.0, 1.8], rowH: 0.52, border: { type: "solid", color: C.line, pt: 1 } });
  code(s, '{\n  "fps": 30,\n  "width": 1080,\n  "height": 1920,\n  "telop_size": 70,\n  "telop_y": 0.7,\n  ...\n}', 8.4, 1.8, 4.35, 3.1, 13);
  text(s, "↑ 例：少し小さく、画面の下のほうに", 8.4, 5.0, 4.35, 0.4, { fontSize: 12, color: C.muted });
  note(s, "数字を変えて再スタートすると、新しい見た目のテロップが作られます。わからなければ「もう少し小さく」などと Claude に頼んでも OK", 0.6, 5.75, 12.15, 0.95);
}

// ---------- 15. 困ったとき ----------
{
  const s = pres.addSlide(); s.background = { color: C.white };
  title(s, "困ったとき", "エラーは Resolve に置く前に止まり、画面とレポートに理由が出ます");
  const hdr = { bold: true, color: C.white, fill: { color: C.dark }, fontFace: F, fontSize: 13 };
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontFace: F, fontSize: 12, color: C.ink, valign: "middle" }, o) });
  s.addTable([
    [{ text: "表示", options: hdr }, { text: "直し方", options: hdr }],
    [cell("ナレーションの音声ファイルを選んでください"), cell("③ でナレーションを選ぶ")],
    [cell("素材が選ばれていないシーンがあります"), cell("④ の赤い行に素材を選ぶ（同じ素材を使い回しても OK）")],
    [cell("台本の効果音 K02 のファイルがありません"), cell("④ の「効果音 K02」の行に音声を選ぶ")],
    [cell("API キーが正しくありません"), cell("キーを貼り直す（p.5）。残高がないときも失敗します")],
    [cell("アライメント信頼度が低い（警告）"), cell("台本と音声の文章が違う。どちらかを直す")],
    [cell("Resolve に接続できません"), cell("Resolve の 環境設定 → システム → 一般 →「外部スクリプトに使用」を「ローカル」に")],
    [cell("テロップを作るには Pillow が必要です"), cell("p.4 の準備（pip install）をもう一度")],
  ], { x: 0.6, y: 1.8, w: 12.15, colW: [5.0, 7.15], rowH: 0.56, border: { type: "solid", color: C.line, pt: 1 } });
  note(s, "わからないときは、アプリ画面（黒い欄が見えるように）を撮って Claude に送ってください", 0.6, 6.45, 12.15, 0.6);
}

// ---------- 16. まとめ ----------
{
  const s = pres.addSlide(); s.background = { color: C.dark };
  text(s, "毎回の作業まとめ", 0.8, 0.8, 11, 0.8, { fontSize: 32, bold: true, color: C.white });
  const steps = ["絵コンテを PNG で作る", "「絵コンテ画像から作る…」で台本に", "台本の文章でナレーション音声を作る", "素材・BGM・効果音を入れて ▶ スタート", "Resolve で確認・仕上げ"];
  steps.forEach((t, i) => {
    const y = 1.9 + i * 0.78;
    num(s, 0.8, y, i + 1, 0.52);
    text(s, t, 1.55, y, 6.5, 0.52, { fontSize: 18, color: C.white, valign: "middle" });
  });
  text(s, "ツールの更新", 8.6, 1.9, 4.2, 0.45, { fontSize: 18, bold: true, color: C.orange });
  code(s, 'cd "G:\\@Auto_Davinch-Cloude"\ngit pull origin claude/claude-md-phase-0-qxn5wu', 8.6, 2.45, 4.2, 1.0, 9);
  text(s, "詳しい文章の説明：取扱説明書.md\n絵コンテと台本の見本：samples\\絵コンテ_iPhone", 8.6, 3.75, 4.2, 1.0, { fontSize: 12, color: "C9D1DD" });
  s.addImage({ path: path.join(REPO, "assets", "app.png"), x: 10.0, y: 5.2, w: 1.4, h: 1.4 });
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("written:", f));

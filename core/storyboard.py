"""絵コンテの画像（PNG など）から、台本テキスト（## S01 …）を作る。

画像の文字を読むのに Claude API を使う（インターネット接続と API キーが必要。1回数円〜十数円程度）。
AI で作った絵コンテ画像は文字が崩れていることがあるので、自然な日本語に直させ、直した箇所を一覧で返させる。
結果は必ず人が確認する（ナレーション音声は、確認した台本の文章で作る）。
"""
import base64
import io
import json
import os

from core.script import parse_script

MODEL = "claude-opus-5"
MAX_EDGE = 2400                 # 送る画像の長辺の上限（小さな文字が読めるよう大きめ）
MAX_BYTES = 4_500_000           # 1枚あたりの上限（API の上限 5MB より少し小さく）
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

SYSTEM = """\
あなたは動画編集の補助をします。渡された絵コンテ画像（1枚または複数枚。複数ならその順につながる）を読み、
動画編集ツール用の台本テキストに変換してください。

【台本テキストの形式】
- カット番号ごとに「## S01」「## S02」…の見出し（S＋2桁）。カット番号の順に並べる
- 見出しの次の行に「// 動画：M01」のように、そのカットの素材ファイル名（絵コンテに書かれていれば）
- 画像に大きく載っている見出し文字（テロップ）は「テロップ：文字」。画像内で改行されていれば、行ごとに「テロップ：」を分ける
- 効果音が指定されていれば（K01 など）「効果音：K01」。「－」やなしなら書かない
- ナレーション欄の文章は、見出しの下にそのまま1行で書く（「ナレーション」などの項目名は付けない）
- 1カットに動画が複数（M03_1、M03_2 など）のときは、ナレーションを文の切れ目で分け、行頭に「[1]」「[2]」を付ける
- カメラ・構図などの指示は、行頭に「// 」を付けて残す
- 時間（00:00-00:04 など）は書かない
- BGM の指定があれば、先頭に「// BGM：BGM1」のようにメモで書く

【注意】
- 画像の文字が崩れている・誤字・不自然な所は、前後の文脈から自然な日本語に直す。直した所は corrections に
  「S04 ナレーション：「予定を移動も」→「予定も移動も」」のように1件ずつ書く
- 読めない・判断できない所は推測で埋め、corrections に「S05 ナレーション：一部が読めないため推測（要確認）」のように書く
- ナレーションを [1] [2] で分けたときは、分けた位置を corrections に書く（要確認）
- 絵コンテにない内容を足さない
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "script": {"type": "string", "description": "台本テキスト全体"},
        "corrections": {"type": "array", "items": {"type": "string"},
                        "description": "直した箇所・推測した箇所・要確認の箇所"},
    },
    "required": ["script", "corrections"],
    "additionalProperties": False,
}


class StoryboardError(RuntimeError):
    pass


def _encode(path):
    """画像を API に送れる形（base64）にする。大きすぎれば縮小し、それでも大きければ JPEG にする"""
    try:
        from PIL import Image
    except ImportError as e:
        raise StoryboardError("画像を扱うには Pillow が必要です。  .\\run.bat -m pip install pillow  を実行してください") from e
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            if max(im.size) > MAX_EDGE:
                scale = MAX_EDGE / max(im.size)
                im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            media_type = "image/png"
            if buf.tell() > MAX_BYTES:
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=90)
                media_type = "image/jpeg"
    except OSError as e:
        raise StoryboardError(f"画像を読めません: {os.path.basename(path)}") from e
    return media_type, base64.standard_b64encode(buf.getvalue()).decode("ascii")


def build_content(paths):
    content = []
    for i, path in enumerate(paths, 1):
        media_type, data = _encode(path)
        if len(paths) > 1:
            content.append({"type": "text", "text": f"{i}枚目: {os.path.basename(path)}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}})
    content.append({"type": "text", "text": "この絵コンテを台本テキストに変換してください。"})
    return content


def convert(paths, api_key=None, client=None):
    """絵コンテ画像 → (台本テキスト, 直した箇所のリスト, 台本の問題のリスト)

    client: テスト用に差し替える（省略時は anthropic.Anthropic）
    """
    if not paths:
        raise StoryboardError("画像が選ばれていません")
    for p in paths:
        if os.path.splitext(p)[1].lower() not in IMAGE_EXTS:
            raise StoryboardError(f"png / jpg / webp の画像を選んでください（{os.path.basename(p)}）")
    content = build_content(paths)

    anthropic = None
    if client is None:
        try:
            import anthropic
        except ImportError as e:
            raise StoryboardError("画像から台本を作るには anthropic が必要です。"
                                  "  .\\run.bat -m pip install anthropic  を実行してください") from e

    try:
        if client is None:
            client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            # 安全のための自動判定で断られたときは、別のモデルで自動的にやり直す
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except Exception as e:  # 通信・認証・料金などの失敗は、画面に分かる言葉で出す
        raise StoryboardError(_api_error_message(e, anthropic)) from e

    if response.stop_reason == "refusal":
        raise StoryboardError("AI がこの画像の処理を断りました。別の画像で試すか、手で台本を書いてください")
    if response.stop_reason == "max_tokens":
        raise StoryboardError("絵コンテが長すぎて、途中までしか変換できませんでした。画像を分けて試してください")
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
        script, corrections = data["script"], list(data["corrections"])
    except (ValueError, KeyError, TypeError) as e:
        raise StoryboardError("AI の返事を読み取れませんでした。もう一度試してください") from e

    script = script.strip() + "\n"
    problems = parse_script(script).errors
    return script, corrections, problems


def _api_error_message(e, anthropic):
    if anthropic is not None:
        if isinstance(e, anthropic.AuthenticationError):
            return "API キーが正しくありません。キーを確認してください"
        if isinstance(e, anthropic.PermissionDeniedError):
            return "この API キーでは使えません（権限・残高を確認してください）"
        if isinstance(e, anthropic.RateLimitError):
            return "混み合っています。少し待ってからもう一度試してください"
        if isinstance(e, anthropic.BadRequestError):
            return f"AI への依頼が受け付けられませんでした（残高不足・画像が大きすぎるなど）: {e.message}"
        if isinstance(e, anthropic.APIStatusError):
            return f"AI のサーバーでエラーが起きました（{e.status_code}）。少し待ってからもう一度試してください"
        if isinstance(e, anthropic.APIConnectionError):
            return "インターネットに接続できません。接続を確認してください"
    msg = str(e)
    if "api_key" in msg or "authentication" in msg.lower():
        return "API キーが設定されていません。キーを入力してください"
    return f"AI での変換に失敗しました: {msg}"

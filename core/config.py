"""config.json の読み込み。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULTS = {
    "fps": 30,
    "width": 1080,
    "height": 1920,
    "sizing": "fit",
    "whisper_model": "large-v3",
    # セクション内の単語の平均確率がこれ未満なら「信頼度が低い」と警告する
    "low_confidence": 0.5,
    # テロップ（台本の「テロップ：〜」）
    # "text"：Resolve のメディアプールのひな形（Text+）を置いて文字を入れる（Resolve で直せる）
    # "video"：文字を描いた透明付きの動画を置く（以前の方式。下の telop_font 〜 telop_max_width はこのときの見た目）
    "telop_mode": "text",
    "telop_template": "テロップ",  # "text" のときに使う、メディアプールのひな形の名前
    "telop_line_chars": 0,         # "text" のときの1行の文字数（全角）。0 ならひな形の文字の大きさから自動
    "telop_font": "",              # 空ならメイリオ Bold など見つかったもの
    "telop_size": 80,              # 文字の大きさ（ピクセル）
    "telop_y": 0.25,               # 文字の縦位置（画面の上端 0 〜 下端 1。テロップのまとまりの中心）
    "telop_color": "#FFFFFF",
    "telop_stroke_color": "#000000",
    "telop_stroke_width": 8,       # 縁取りの太さ（ピクセル）
    "telop_max_width": 0.9,        # 1行の最大幅（画面の幅に対する割合。超えたら折り返す）
}


class ConfigError(ValueError):
    pass


def load_config(path=None):
    path = path or os.path.join(ROOT, "config.json")
    config = dict(DEFAULTS)
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as fp:
            try:
                config.update(json.load(fp))
            except json.JSONDecodeError as e:
                raise ConfigError(f"config.json の書式が正しくありません: {e}") from e

    for key in ("fps", "width", "height"):
        if not isinstance(config[key], int) or config[key] <= 0:
            raise ConfigError(f"config.json の {key} は正の整数にしてください（現在: {config[key]!r}）")
    for key in ("telop_size", "telop_stroke_width"):
        if not isinstance(config[key], int) or config[key] < 0 or (key == "telop_size" and config[key] == 0):
            raise ConfigError(f"config.json の {key} は正の整数にしてください（現在: {config[key]!r}）")
    for key in ("telop_y", "telop_max_width"):
        if not isinstance(config[key], (int, float)) or not 0 < config[key] <= 1:
            raise ConfigError(f"config.json の {key} は 0 より大きく 1 以下の数にしてください（現在: {config[key]!r}）")
    if not isinstance(config["telop_line_chars"], int) or config["telop_line_chars"] < 0:
        raise ConfigError(f"config.json の telop_line_chars は 0 以上の整数にしてください（現在: {config['telop_line_chars']!r}）")
    if config["telop_mode"] not in ("text", "video"):
        raise ConfigError(f"config.json の telop_mode は \"text\" か \"video\" にしてください（現在: {config['telop_mode']!r}）")
    if not isinstance(config["telop_template"], str) or not config["telop_template"].strip():
        raise ConfigError("config.json の telop_template にひな形の名前を書いてください")
    if config["sizing"] not in ("fit", "fill"):
        raise ConfigError(f"config.json の sizing は \"fit\" か \"fill\" にしてください（現在: {config['sizing']!r}）")
    return config

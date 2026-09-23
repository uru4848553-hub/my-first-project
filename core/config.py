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
    if config["sizing"] not in ("fit", "fill"):
        raise ConfigError(f"config.json の sizing は \"fit\" か \"fill\" にしてください（現在: {config['sizing']!r}）")
    return config

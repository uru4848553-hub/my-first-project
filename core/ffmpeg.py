"""ffprobe / ffmpeg の呼び出し。"""
import json
import shutil
import subprocess


class FFmpegError(RuntimeError):
    pass


def _run(args):
    exe = shutil.which(args[0])
    if not exe:
        raise FFmpegError(f"{args[0]} が見つかりません（PATH を確認してください）")
    proc = subprocess.run([exe, *args[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise FFmpegError(f"{args[0]} が失敗しました: {proc.stderr.strip()[-500:]}")
    return proc.stdout


def probe_duration(path):
    """メディアの長さ（秒）"""
    out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path])
    try:
        return float(json.loads(out)["format"]["duration"])
    except (KeyError, ValueError, TypeError) as e:
        raise FFmpegError(f"長さを取得できません: {path}") from e

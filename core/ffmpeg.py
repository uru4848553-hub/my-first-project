"""ffprobe / ffmpeg の呼び出し。"""
import json
import os
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


def _fraction(text):
    try:
        num, _, den = text.partition("/")
        value = float(num) / float(den or 1)
        return value if value > 0 else None
    except (ValueError, ZeroDivisionError):
        return None


def probe_video(path):
    """動画の {duration, fps, width, height}（duration は秒）"""
    out = _run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,duration:format=duration",
                "-of", "json", path])
    data = json.loads(out)
    streams = data.get("streams") or []
    if not streams:
        raise FFmpegError(f"映像がありません: {path}")
    st = streams[0]
    duration = None
    for value in (st.get("duration"), data.get("format", {}).get("duration")):
        try:
            duration = float(value)
            break
        except (TypeError, ValueError):
            continue
    if duration is None:
        raise FFmpegError(f"長さを取得できません: {path}")
    return {
        "duration": duration,
        "fps": _fraction(st.get("avg_frame_rate", "")) or _fraction(st.get("r_frame_rate", "")),
        "width": st.get("width"),
        "height": st.get("height"),
    }


def extract_last_frame(src, dst):
    """動画の最終フレームを PNG に書き出す"""
    # 末尾1秒だけデコードし、1枚の画像を上書きし続ける → 最後に残るのが最終フレーム
    _run(["ffmpeg", "-y", "-v", "error", "-sseof", "-1", "-i", src, "-an", "-update", "1", dst])
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        _run(["ffmpeg", "-y", "-v", "error", "-i", src, "-an", "-update", "1", dst])
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        raise FFmpegError(f"最終フレームを書き出せません: {src}")
    return dst

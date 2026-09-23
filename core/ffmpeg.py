"""ffprobe / ffmpeg の呼び出し。"""
import json
import os
import shutil
import subprocess


class FFmpegError(RuntimeError):
    pass


TIMEOUT_SEC = 600


def _run(args, timeout=TIMEOUT_SEC):
    exe = shutil.which(args[0])
    if not exe:
        raise FFmpegError(f"{args[0]} が見つかりません（PATH を確認してください）")
    try:
        proc = subprocess.run([exe, *args[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"{args[0]} が {timeout} 秒たっても終わりません") from e
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


# 静止画を動画にするときの映像フィルタ：大きすぎる画像は 3840 以内に縮小し、H.264 用に偶数サイズへ、BT.709 の映像レベルへ
# （YUV 4:2:0 への変換で奇数サイズが切り捨てられないよう、先に RGB のまま偶数サイズにする）
STILL_FILTER = ("scale=w='min(iw,3840)':h='min(ih,3840)':force_original_aspect_ratio=decrease,format=rgb24,"
                "pad=ceil(iw/2)*2:ceil(ih/2)*2,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p")


def probe_image(path):
    """画像として読めるか確かめ、(幅, 高さ) を返す"""
    out = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                "-of", "json", path], timeout=60)
    streams = json.loads(out).get("streams") or []
    if not streams or not streams[0].get("width"):
        raise FFmpegError(f"画像として読めません: {path}")
    return streams[0]["width"], streams[0]["height"]


def still_to_video(src, dst, frames, fps):
    """静止画を、その画像が frames フレーム続く動画（H.264・高画質）にする"""
    # 読めない画像に -loop 1 を使うと ffmpeg が終わらないので、先に確かめる
    probe_image(src)
    _run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-i", src,
          "-frames:v", str(frames), "-vf", STILL_FILTER,
          "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "12",
          "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
          "-an", "-movflags", "+faststart", dst])
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        raise FFmpegError(f"静止画を動画にできません: {src}")
    return dst

"""尺調整（フェーズ3）。

plan.json の各セクションに、タイムラインへ置くクリップの列（clips）を付ける。
- 静止画：セクション尺そのまま
- 動画がセクションより長い：素材の先頭から使い、セクション尺で切る
- 動画がセクションより短い：動画の直後に最終フレームの静止画（media/_freeze/ に PNG で書き出す）を置いて埋める
"""
import math
import os

from core.ffmpeg import FFmpegError, extract_last_frame, probe_video

FREEZE_DIR = "_freeze"
LONG_FREEZE_SEC = 2.0


def video_frames(duration, fps):
    """動画の長さ（秒）のうち、タイムライン上で使えるフレーム数（端数は切り捨て）"""
    return math.floor(duration * fps + 1e-6)


def section_clips(section, fps, available_frames=None, freeze_path=None):
    """1セクション分のクリップの列と、静止フレームで埋めたフレーム数を返す。

    available_frames: 動画のとき、タイムライン換算で使えるフレーム数
    """
    start = section["start_frame"]
    frames = section["duration_frames"]
    media = section["media"]
    if media["kind"] == "image":
        return [{"type": "image", "path": media["path"], "record_frame": start, "frames": frames}], 0

    use = min(available_frames, frames)
    clips = [{"type": "video", "path": media["path"], "record_frame": start, "frames": use,
              "source_in_sec": 0.0, "source_out_sec": round(use / fps, 6)}]
    freeze = frames - use
    if freeze > 0:
        clips.append({"type": "freeze", "path": freeze_path, "record_frame": start + use, "frames": freeze})
    return clips, freeze


def freeze_path_for(video_path):
    folder, name = os.path.split(video_path)
    return os.path.join(folder, FREEZE_DIR, os.path.splitext(name)[0] + "_last.png")


def _ensure_freeze(video_path, log):
    """最終フレームの PNG を毎回書き出し直す。
    （コピーで差し替えた動画は更新日時が古いままのことがあり、日時では新旧を判定できないため）"""
    dst = freeze_path_for(video_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    log(f"最終フレームを書き出し中: {os.path.basename(video_path)} → {FREEZE_DIR}/{os.path.basename(dst)}")
    return extract_last_frame(video_path, dst)


def apply_fit(plan, log=print):
    """plan の各セクションに clips を付ける（plan を直接書き換える）。戻り値: (エラー, 警告)"""
    fps = plan["fps"]
    errors = []
    warnings = []
    probes = {}

    for sec in plan["sections"]:
        media = sec["media"]
        available = None
        freeze_path = None
        if media["kind"] == "video":
            path = media["path"]
            try:
                info = probes.get(path) or probe_video(path)
            except FFmpegError as e:
                errors.append(f"{sec['label']}: 動画を読めません（{media['name']}）: {e}")
                continue
            probes[path] = info
            media.update({"duration_sec": round(info["duration"], 3), "fps": info["fps"],
                          "width": info["width"], "height": info["height"]})
            available = video_frames(info["duration"], fps)
            if available <= 0:
                errors.append(f"{sec['label']}: 動画が短すぎます（{media['name']}、{info['duration']:.3f}秒）")
                continue
            if available < sec["duration_frames"]:
                try:
                    freeze_path = _ensure_freeze(path, log)
                except FFmpegError as e:
                    errors.append(f"{sec['label']}: 最終フレームを書き出せません（{media['name']}）: {e}")
                    continue

        clips, freeze = section_clips(sec, fps, available, freeze_path)
        sec["clips"] = clips
        sec["freeze_frames"] = freeze
        if freeze / fps >= LONG_FREEZE_SEC:
            w = f"静止フレームで埋めた尺が{freeze / fps:.1f}秒（素材不足の可能性）"
            sec["warnings"].append(w)
            warnings.append(f"{sec['label']}: {w}")

    plan["errors"].extend(errors)
    return errors, warnings

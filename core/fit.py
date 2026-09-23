"""尺調整（フェーズ3）。

plan.json の各セクションに、タイムラインへ置くクリップの列（clips）を付ける。
- 静止画：セクション尺そのまま
- 動画がセクションより長い：素材の先頭から使い、セクション尺で切る
- 動画がセクションより短い：動画の直後に最終フレームの静止画（media/_freeze/ に PNG で書き出す）を置いて埋める

静止画（素材の画像・最終フレームの PNG）は、その画像が必要な尺だけ続く動画（mp4）にしてから置く。
Resolve は静止画を AppendToTimeline で置くと endFrame を無視して既定の長さ（5秒）で置くため（実機で確認）。
元の画像は clip の "image"、置く動画は "path" に入る。
"""
import hashlib
import math
import os

from core.ffmpeg import FFmpegError, extract_last_frame, probe_video, still_to_video

FREEZE_DIR = "_freeze"
STILLS_DIR = "_stills"
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


def freeze_dir_for(video_path):
    return os.path.join(os.path.dirname(video_path), FREEZE_DIR)


def _ensure_freeze(video_path, log):
    """最終フレームを PNG に書き出す。ファイル名は「動画名_last_内容のハッシュ.png」。

    - 毎回書き出し直す（コピーで差し替えた動画は更新日時が古いままのことがあり、日時では新旧を判定できない）
    - 内容が変われば別名になる。Resolve は同じパスの画像を取り込み済みだと古い画像を使い続けるうえ、
      メディアプールから消すと既存のタイムラインからも消えてしまうため、上書きせず別ファイルにする
    """
    folder = freeze_dir_for(video_path)
    os.makedirs(folder, exist_ok=True)
    stem = os.path.splitext(os.path.basename(video_path))[0]
    tmp = os.path.join(folder, stem + "_last.tmp.png")
    extract_last_frame(video_path, tmp)
    with open(tmp, "rb") as fp:
        digest = hashlib.sha1(fp.read()).hexdigest()[:8]
    dst = os.path.join(folder, f"{stem}_last_{digest}.png")
    if os.path.exists(dst):
        os.remove(tmp)
    else:
        os.replace(tmp, dst)
        log(f"最終フレームを書き出しました: {os.path.basename(video_path)} → {FREEZE_DIR}/{os.path.basename(dst)}")
    return dst


def _file_hash(path):
    with open(path, "rb") as fp:
        return hashlib.sha1(fp.read()).hexdigest()[:8]


def still_video_path(image_path, frames):
    """静止画を動画にしたファイルの置き場所。素材の画像は media/_stills/、最終フレームは media/_freeze/ に並べる。
    名前に画像の内容のハッシュと長さを入れ、同じ画像・同じ長さなら使い回す。"""
    folder, name = os.path.split(image_path)
    stem = os.path.splitext(name)[0]
    if os.path.basename(folder) == FREEZE_DIR:
        # 最終フレームの PNG は名前にすでに内容のハッシュが入っている
        return os.path.join(folder, f"{stem}_{frames}f.mp4")
    return os.path.join(folder, STILLS_DIR, f"{stem}_{_file_hash(image_path)}_{frames}f.mp4")


def _ensure_still_video(image_path, frames, fps, log):
    dst = still_video_path(image_path, frames)
    if os.path.isfile(dst) and os.path.getsize(dst) > 0:
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst[:-4] + ".tmp.mp4"
    still_to_video(image_path, tmp, frames, fps)
    os.replace(tmp, dst)
    log(f"静止画を動画にしました: {os.path.basename(image_path)} → {os.path.basename(dst)}")
    return dst


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
        try:
            for clip in clips:
                if clip["type"] != "video":
                    clip["image"] = clip["path"]
                    clip["path"] = _ensure_still_video(clip["image"], clip["frames"], fps, log)
        except FFmpegError as e:
            errors.append(f"{sec['label']}: 静止画を動画にできません（{os.path.basename(clip['image'])}）: {e}")
            continue
        sec["clips"] = clips
        sec["freeze_frames"] = freeze
        if freeze / fps >= LONG_FREEZE_SEC:
            w = f"静止フレームで埋めた尺が{freeze / fps:.1f}秒（素材不足の可能性）"
            sec["warnings"].append(w)
            warnings.append(f"{sec['label']}: {w}")

    plan["errors"].extend(errors)
    return errors, warnings

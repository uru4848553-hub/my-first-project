"""素材フォルダ（media/）と音声フォルダ（audio/）の読み取り。"""
import os
import re
from dataclasses import dataclass

MEDIA_NAME = re.compile(r"^S(\d{2})([a-z])?_(.+)\.([^.]+)$")
VIDEO_EXTS = {"mp4", "mov"}
IMAGE_EXTS = {"png", "jpg", "jpeg"}
AUDIO_EXTS = {"wav", "mp3", "m4a"}
# OS が勝手に作るファイル
IGNORED_FILES = {"thumbs.db", "desktop.ini", ".ds_store"}


@dataclass
class MediaFile:
    path: str
    scene: str            # "S03"
    sub: str | None       # "a" / None
    kind: str             # "video" / "image"

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def key(self):
        return self.scene + (self.sub or "")


def _list_files(folder):
    names = []
    for entry in sorted(os.scandir(folder), key=lambda e: e.name):
        if not entry.is_file():
            continue
        if entry.name.startswith(".") or entry.name.lower() in IGNORED_FILES:
            continue
        names.append(entry.name)
    return names


def scan_media(media_dir):
    """media/ を読み、(素材リスト, エラー) を返す。サブフォルダ（_freeze など）は見ない。"""
    errors = []
    if not os.path.isdir(media_dir):
        return [], [f"media フォルダがありません: {media_dir}"]

    files = []
    for name in _list_files(media_dir):
        m = MEDIA_NAME.match(name)
        if not m:
            errors.append(f"命名ルール違反: media/{name}（S01_説明.mp4 や S03a_説明.png の形式にしてください）")
            continue
        ext = m.group(4).lower()
        if ext in VIDEO_EXTS:
            kind = "video"
        elif ext in IMAGE_EXTS:
            kind = "image"
        else:
            errors.append(f"対応していない拡張子: media/{name}（mp4, mov, png, jpg, jpeg のみ）")
            continue
        files.append(MediaFile(path=os.path.join(media_dir, name),
                               scene=f"S{m.group(1)}", sub=m.group(2), kind=kind))

    by_scene = {}
    for f in files:
        by_scene.setdefault(f.scene, []).append(f)
    for scene, group in sorted(by_scene.items()):
        subs = [f.sub for f in group]
        if None in subs and any(subs):
            errors.append(f"{scene}: 「a,b…なし」と「a,b…付き」の素材が混在しています"
                          f"（{', '.join(f.name for f in group)}）")
            continue
        keys = {}
        for f in group:
            keys.setdefault(f.key, []).append(f.name)
        for key, names in sorted(keys.items()):
            if len(names) > 1:
                errors.append(f"{key}: 同じシーンに素材が複数あります（{', '.join(names)}）")

    return files, errors


def find_audio(audio_dir):
    """audio/ の音声ファイルを1本探し、(パス or None, エラー) を返す。"""
    if not os.path.isdir(audio_dir):
        return None, [f"audio フォルダがありません: {audio_dir}"]
    found = [n for n in _list_files(audio_dir) if os.path.splitext(n)[1][1:].lower() in AUDIO_EXTS]
    if not found:
        return None, ["audio フォルダに音声ファイル（wav, mp3, m4a）がありません"]
    if len(found) > 1:
        return None, [f"audio フォルダの音声ファイルは1本だけにしてください（{', '.join(found)}）"]
    return os.path.join(audio_dir, found[0]), []

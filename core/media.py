"""素材フォルダ（media/）・音声フォルダ（audio/）・効果音フォルダ（se/）の読み取り。

素材の名前は次のどちらでもよい:
- S01_説明.mp4 / S03a_説明.png（仕様書の形）
- M01.mp4 / M01_説明.mp4 / M03_1.mp4 / M03_1_説明.png（絵コンテの形。M03_1 は台本の [a]、M03_2 は [b]）
"""
import os
import re
from dataclasses import dataclass

MEDIA_NAME = re.compile(r"^S(\d{2})([a-z])?_(.+)\.([^.]+)$")
MEDIA_NAME_M = re.compile(r"^M(\d{2})(?:_(\d{1,2})(?=[_.]))?(?:_(.*))?\.([^.]+)$", re.IGNORECASE)
SFX_NAME = re.compile(r"^K(\d{2})(?:[_\-\s].*)?\.([^.]+)$", re.IGNORECASE)
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


def parse_media_name(name):
    """素材のファイル名 → (シーン "S03", サブ "a" or None, 拡張子)。命名ルールに合わなければ None"""
    m = MEDIA_NAME.match(name)
    if m:
        return f"S{m.group(1)}", m.group(2), m.group(4)
    m = MEDIA_NAME_M.match(name)
    if m:
        sub = None
        if m.group(2):
            n = int(m.group(2))
            if not 1 <= n <= 26:
                return None
            sub = chr(ord("a") + n - 1)
        return f"S{m.group(1)}", sub, m.group(4)
    return None


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
        parsed = parse_media_name(name)
        if parsed is None:
            errors.append(f"命名ルール違反: media/{name}（S01_説明.mp4・S03a_説明.png、または M01.mp4・M03_1.mp4 の形式にしてください）")
            continue
        scene, sub, ext = parsed
        ext = ext.lower()
        if ext in VIDEO_EXTS:
            kind = "video"
        elif ext in IMAGE_EXTS:
            kind = "image"
        else:
            errors.append(f"対応していない拡張子: media/{name}（mp4, mov, png, jpg, jpeg のみ）")
            continue
        files.append(MediaFile(path=os.path.join(media_dir, name), scene=scene, sub=sub, kind=kind))

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


def find_bgm(bgm_dir):
    """bgm/ の音楽ファイル（なくてもよい）を探し、(パス or None, エラー) を返す。"""
    if not os.path.isdir(bgm_dir):
        return None, []
    found = [n for n in _list_files(bgm_dir) if os.path.splitext(n)[1][1:].lower() in AUDIO_EXTS]
    if len(found) > 1:
        return None, [f"bgm フォルダの音楽ファイルは1本だけにしてください（{', '.join(found)}）"]
    return (os.path.join(bgm_dir, found[0]) if found else None), []


def scan_sfx(se_dir):
    """se/ の効果音（K01_〜.wav など。なくてもよい）を読み、({ID: パス}, エラー) を返す。"""
    if not os.path.isdir(se_dir):
        return {}, []
    found, errors = {}, []
    for name in _list_files(se_dir):
        m = SFX_NAME.match(name)
        if not m or m.group(2).lower() not in AUDIO_EXTS:
            errors.append(f"命名ルール違反: se/{name}（K01_説明.wav のように K＋2桁の番号で始まる wav / mp3 / m4a にしてください）")
            continue
        sid = f"K{m.group(1)}"
        if sid in found:
            errors.append(f"{sid}: 効果音が複数あります（{os.path.basename(found[sid])}, {name}）")
            continue
        found[sid] = os.path.join(se_dir, name)
    return found, errors

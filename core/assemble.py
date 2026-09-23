"""アプリで選んだ台本・ナレーション・BGM・素材から、動画フォルダ（script.md / audio / bgm / media）を作る。

素材は、台本のセクション（S01, S03a …）ごとに選ばれたファイルを media/ に
「<セクション>_<元のファイル名>」でコピーするので、元のファイル名は自由でよい。
"""
import os
import re
import shutil

from core.media import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS

MEDIA_EXTS = VIDEO_EXTS | IMAGE_EXTS
_UNSAFE = re.compile(r'[\\/:*?"<>|]+')
_KEY_PREFIX = re.compile(r"^(S\d{2}[a-z]?)(?=[_\-\s.])", re.IGNORECASE)


def safe_name(name):
    """フォルダ名に使えない文字を除く"""
    return _UNSAFE.sub("_", name).strip().strip(".") or "動画"


def ext_of(path):
    return os.path.splitext(path)[1][1:].lower()


def auto_assign(keys, paths, assigned=None):
    """素材ファイルをセクションに割り当てる。

    - ファイル名が「S01_」「S03a_」などで始まるものは、そのセクションへ
    - 残りは、まだ素材のないセクションに、ファイル名の順で上から入れる
    戻り値: {セクション: パス}（assigned に追加した結果）、入りきらなかったパスのリスト
    """
    result = dict(assigned or {})
    rest = []
    keyset = {k.upper(): k for k in keys}
    for path in sorted(paths, key=lambda p: os.path.basename(p).lower()):
        m = _KEY_PREFIX.match(os.path.basename(path))
        key = keyset.get(m.group(1).upper()) if m else None
        if key:
            result[key] = path
        else:
            rest.append(path)
    left = []
    empty = [k for k in keys if k not in result]
    for path in rest:
        if empty:
            result[empty.pop(0)] = path
        else:
            left.append(path)
    return result, left


def _replace_files(folder, copies):
    """folder 直下のファイルを copies（(コピー元, コピー先のファイル名) の列）に入れ替える（サブフォルダは残す）。

    選ばれたファイルがこのフォルダの中にあっても消さないよう、先に一時フォルダへコピーしてから入れ替える。
    """
    os.makedirs(folder, exist_ok=True)
    staging = os.path.join(folder, "_staging")
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging)
    try:
        staged = []
        for src, name in copies:
            dst = os.path.join(staging, name)
            shutil.copy2(src, dst)
            staged.append(dst)
        for entry in os.scandir(folder):
            if entry.is_file():
                os.remove(entry.path)
        for path in staged:
            os.replace(path, os.path.join(folder, os.path.basename(path)))
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def assemble(base_dir, name, script_text, narration, materials, bgm=None, log=print):
    """動画フォルダを作り（あれば中身を入れ替え）、そのパスを返す。

    materials: {セクションのキー（"S01", "S03a" …）: 素材ファイルのパス}
    """
    folder = os.path.join(base_dir, safe_name(name))
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "script.md"), "w", encoding="utf-8") as fp:
        fp.write(script_text if script_text.endswith("\n") else script_text + "\n")

    log("ナレーションをコピー中...")
    _replace_files(os.path.join(folder, "audio"), [(narration, os.path.basename(narration))])
    _replace_files(os.path.join(folder, "bgm"), [(bgm, os.path.basename(bgm))] if bgm else [])

    log(f"素材をコピー中（{len(materials)}件）...")
    _replace_files(os.path.join(folder, "media"),
                   [(path, f"{key}_{os.path.basename(path)}") for key, path in sorted(materials.items())])
    return folder


def validate(sections, narration, materials, bgm=None):
    """スタート前の確認。問題のリストを返す（空なら OK）"""
    problems = []
    if not sections:
        problems.append("台本にシーン（## S01 など）がありません")
    if not narration:
        problems.append("ナレーションの音声ファイルを選んでください")
    elif not os.path.isfile(narration):
        problems.append(f"ナレーションのファイルがありません: {narration}")
    elif ext_of(narration) not in AUDIO_EXTS:
        problems.append("ナレーションは wav / mp3 / m4a にしてください")
    if bgm:
        if not os.path.isfile(bgm):
            problems.append(f"BGM のファイルがありません: {bgm}")
        elif ext_of(bgm) not in AUDIO_EXTS:
            problems.append("BGM は wav / mp3 / m4a にしてください")
    missing = [s.label for s in sections if s.key not in materials]
    if missing:
        problems.append(f"素材が選ばれていないシーンがあります: {', '.join(missing)}")
    for key, path in materials.items():
        if not os.path.isfile(path):
            problems.append(f"{key} の素材ファイルがありません: {path}")
        elif ext_of(path) not in MEDIA_EXTS:
            problems.append(f"{key} の素材は mp4 / mov / png / jpg にしてください（{os.path.basename(path)}）")
    return problems

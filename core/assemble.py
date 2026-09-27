"""アプリで選んだ台本・ナレーション・BGM・素材・効果音から、動画フォルダ（script.md / audio / bgm / media / se）を作る。

実行するたびに「保存先/動画名/日付_時刻」の新しいフォルダを作る（前回までのものは消さない・上書きしない）。

素材は、台本のセクション（S01, S03a …）ごとに選ばれたファイルを media/ に
「<セクション>_<元のファイル名>」でコピーするので、元のファイル名は自由でよい。
効果音（K01 …）も同じく se/ に「K01_<元のファイル名>」でコピーする。
"""
import os
import re
import shutil
from datetime import datetime

from core.media import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS

MEDIA_EXTS = VIDEO_EXTS | IMAGE_EXTS
_UNSAFE = re.compile(r'[\\/:*?"<>|]+')
_KEY_PREFIX = re.compile(r"^(S\d{2}[a-z]?)(?=[_\-\s.])", re.IGNORECASE)
_M_PREFIX = re.compile(r"^M(\d{2})(?:_(\d{1,2}))?(?=[_\-\s.])", re.IGNORECASE)
_K_PREFIX = re.compile(r"^(K\d{2})(?=[_\-\s.])", re.IGNORECASE)


def is_sfx_key(key):
    return key[:1].upper() == "K"


def key_of_name(name):
    """ファイル名の頭から割り当て先を読む: S01_ / S03a_ → そのまま、M01 → S01、M03_1 → S03a、K01 → K01"""
    m = _KEY_PREFIX.match(name)
    if m:
        return m.group(1)
    m = _M_PREFIX.match(name)
    if m:
        n = int(m.group(2)) if m.group(2) else 0
        if n > 26:
            return None
        return f"S{m.group(1)}" + (chr(ord("a") + n - 1) if n else "")
    m = _K_PREFIX.match(name)
    return m.group(1) if m else None


def safe_name(name):
    """フォルダ名に使えない文字を除く"""
    return _UNSAFE.sub("_", name).strip().strip(".") or "動画"


def ext_of(path):
    return os.path.splitext(path)[1][1:].lower()


def auto_assign(keys, paths, assigned=None):
    """素材ファイル（と効果音）をセクション（と効果音 ID）に割り当てる。

    - ファイル名が「S01_」「S03a_」「M01」「M03_1」「K01」などで始まるものは、そこへ
    - 残りは、まだ割り当てのない所に、ファイル名の順で上から入れる（音声は効果音へ、動画・画像はシーンへ）
    戻り値: {セクション: パス}（assigned に追加した結果）、入りきらなかったパスのリスト
    """
    result = dict(assigned or {})
    rest = []
    keyset = {k.upper(): k for k in keys}
    for path in sorted(paths, key=lambda p: os.path.basename(p).lower()):
        found = key_of_name(os.path.basename(path))
        key = keyset.get(found.upper()) if found else None
        if key and is_sfx_key(key) == (ext_of(path) in AUDIO_EXTS):
            result[key] = path
        else:
            rest.append(path)
    left = []
    for path in rest:
        sfx = ext_of(path) in AUDIO_EXTS
        empty = [k for k in keys if k not in result and is_sfx_key(k) == sfx]
        if empty:
            result[empty[0]] = path
        else:
            left.append(path)
    return result, left


def _copy_files(folder, copies):
    """copies（(コピー元, コピー先のファイル名) の列）を folder にコピーする。同じ名前があれば _2 などを付け、上書きしない"""
    os.makedirs(folder, exist_ok=True)
    for src, name in copies:
        stem, ext = os.path.splitext(name)
        dst, n = os.path.join(folder, name), 2
        while os.path.exists(dst):
            dst, n = os.path.join(folder, f"{stem}_{n}{ext}"), n + 1
        shutil.copy2(src, dst)


def run_folder(base_dir, name, now=None):
    """今回の実行用の新しいフォルダ（保存先/動画名/日付_時刻）。前回までのフォルダには触らない"""
    parent = os.path.join(base_dir, safe_name(name))
    stamp = f"{(now or datetime.now()):%Y%m%d_%H%M%S}"
    folder, n = os.path.join(parent, stamp), 2
    while os.path.exists(folder):
        folder, n = os.path.join(parent, f"{stamp}_{n}"), n + 1
    os.makedirs(folder)
    return folder


def copy_name(key, path):
    """コピー先の名前。元の名前がすでに「S01_」「K01_」で始まっていれば、そのまま使う"""
    name = os.path.basename(path)
    return name if name.upper().startswith(key.upper() + "_") else f"{key}_{name}"


def assemble(base_dir, name, script_text, narration, materials, bgm=None, log=print, now=None):
    """今回の実行用に新しい動画フォルダ（保存先/動画名/日付_時刻）を作ってコピーし、そのパスを返す。

    前回までのフォルダ・ファイルは消さず、上書きもしない（前に作ったタイムラインの素材が消えないように）。
    materials: {セクションのキー（"S01", "S03a" …）または効果音 ID（"K01" …）: ファイルのパス}
    """
    folder = run_folder(base_dir, name, now)
    with open(os.path.join(folder, "script.md"), "w", encoding="utf-8") as fp:
        fp.write(script_text if script_text.endswith("\n") else script_text + "\n")

    if narration:
        log("ナレーションをコピー中...")
        _copy_files(os.path.join(folder, "audio"), [(narration, os.path.basename(narration))])
    if bgm:
        _copy_files(os.path.join(folder, "bgm"), [(bgm, os.path.basename(bgm))])

    media = {k: p for k, p in materials.items() if not is_sfx_key(k)}
    sfx = {k: p for k, p in materials.items() if is_sfx_key(k)}
    log(f"素材をコピー中（{len(media)}件）...")
    _copy_files(os.path.join(folder, "media"), [(p, copy_name(k, p)) for k, p in sorted(media.items())])
    if sfx:
        log(f"効果音をコピー中（{len(sfx)}件）...")
        _copy_files(os.path.join(folder, "se"), [(p, copy_name(k, p)) for k, p in sorted(sfx.items())])
    return folder


def validate(sections, narration, materials, bgm=None, sfx_ids=()):
    """スタート前の確認。問題のリストを返す（空なら OK）"""
    problems = []
    if not sections:
        problems.append("台本にシーン（## S01 など）がありません")
    if not narration:
        pass    # ナレーションはなくてもよい（動画の長さで並べ、動画の音声を使う）
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
    missing = [k for k in sfx_ids if k not in materials]
    if missing:
        problems.append(f"効果音のファイルが選ばれていません: {', '.join(missing)}")
    for key, path in materials.items():
        if not os.path.isfile(path):
            problems.append(f"{key} のファイルがありません: {path}")
        elif is_sfx_key(key):
            if ext_of(path) not in AUDIO_EXTS:
                problems.append(f"効果音 {key} は wav / mp3 / m4a にしてください（{os.path.basename(path)}）")
        elif ext_of(path) not in MEDIA_EXTS:
            problems.append(f"{key} の素材は mp4 / mov / png / jpg にしてください（{os.path.basename(path)}）")
    return problems

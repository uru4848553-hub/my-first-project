"""台本と素材の照合、および入力フォルダ全体のチェック（フェーズ1）。"""
import os
from dataclasses import dataclass, field

from core.media import find_audio, scan_media
from core.script import parse_script


@dataclass
class Entry:
    """台本の1セクションと、それに割り当てる素材"""
    section: object       # core.script.Section
    media: object         # core.media.MediaFile


@dataclass
class ProjectCheck:
    folder: str
    scenes: list = field(default_factory=list)
    entries: list = field(default_factory=list)
    audio: str | None = None
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def name(self):
        return os.path.basename(os.path.normpath(self.folder))

    @property
    def ok(self):
        return not self.errors


def match_media(scenes, media_files):
    """セクションごとに素材を割り当て、(割り当て一覧, エラー) を返す。"""
    errors = []
    by_key = {}
    for f in media_files:
        by_key.setdefault(f.key, f)
    by_scene = {}
    for f in media_files:
        by_scene.setdefault(f.scene, []).append(f)

    entries = []
    used = set()
    mismatched = set()    # 「マーカーの有無」が台本と素材で食い違うシーン
    for scene in scenes:
        files = by_scene.get(scene.id, [])
        file_has_subs = any(f.sub for f in files)
        if files and scene.has_markers != file_has_subs:
            mismatched.add(scene.id)
            if scene.has_markers:
                errors.append(f"{scene.id}: 台本は [a] [b] … で分かれていますが、素材が"
                              f"「{scene.id}a_〜」のように分かれていません（{', '.join(f.name for f in files)}）")
            else:
                errors.append(f"{scene.id}: 素材が「{scene.id}a_〜」のように分かれていますが、"
                              f"台本に [a] [b] … のマーカーがありません（{', '.join(f.name for f in files)}）")
            continue

        for sec in scene.sections:
            f = by_key.get(sec.key)
            if f is None:
                errors.append(f"台本の {sec.label} に対応する素材がありません（{sec.key}_〜 のファイルが必要）")
                continue
            used.add(f.key)
            entries.append(Entry(section=sec, media=f))

    script_ids = {s.id for s in scenes}
    for f in media_files:
        if f.scene not in script_ids:
            errors.append(f"素材 {f.name} のシーン {f.scene} が台本にありません")
        elif f.scene not in mismatched and f.key not in used:
            errors.append(f"素材 {f.name} に対応するマーカー [{f.sub}] が台本の {f.scene} にありません")
    return entries, errors


def read_script(path):
    """UTF-8（BOM あり/なし）で読む。だめなら Shift_JIS で読み、警告を返す。"""
    with open(path, "rb") as fp:
        data = fp.read()
    try:
        return data.decode("utf-8-sig"), []
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp932"), ["script.md が UTF-8 ではありません（Shift_JIS として読みました）。UTF-8 で保存し直すことをおすすめします"]
    except UnicodeDecodeError:
        return None, ["script.md の文字コードを判別できません。UTF-8 で保存し直してください"]


def check_project(folder):
    result = ProjectCheck(folder=folder)
    if not os.path.isdir(folder):
        result.errors.append(f"フォルダがありません: {folder}")
        return result

    script_path = os.path.join(folder, "script.md")
    script = None
    if not os.path.isfile(script_path):
        result.errors.append("script.md がありません")
    else:
        text, notes = read_script(script_path)
        if text is None:
            result.errors.extend(notes)
        else:
            result.warnings.extend(notes)
            script = parse_script(text)
            result.scenes = script.scenes
            result.errors.extend(script.errors)
            result.warnings.extend(script.warnings)

    media_files, media_errors = scan_media(os.path.join(folder, "media"))
    result.errors.extend(media_errors)

    result.audio, audio_errors = find_audio(os.path.join(folder, "audio"))
    result.errors.extend(audio_errors)

    # 台本か素材の読み取りでエラーがあると照合結果が紛らわしくなるので、その場合は照合しない
    if script is not None and not script.errors and not media_errors:
        result.entries, match_errors = match_media(script.scenes, media_files)
        result.errors.extend(match_errors)
    return result

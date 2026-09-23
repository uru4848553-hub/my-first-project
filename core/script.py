"""台本（script.md）の解析。

## Sxx をシーン見出し、行頭の [a] [b] … をサブセクションの区切りとして、
セクション単位の原稿に分割する。
"""
import re
import string
from dataclasses import dataclass, field

SCENE_HEADING = re.compile(r"^##\s*S(\d{2})\s*$")
# 「## S1」「# s01」など、シーン見出しのつもりで書式が違うもの
SCENE_HEADING_LIKE = re.compile(r"^#+\s*[Ss]\d")
SUB_MARKER = re.compile(r"^\[([a-z])\]\s*(.*)$")
SUB_MARKER_UPPER = re.compile(r"^\[[A-Z]\]")


@dataclass
class Section:
    scene: str            # "S03"
    sub: str | None       # "a" / None（マーカーなし）
    line_no: int
    lines: list[str] = field(default_factory=list)

    @property
    def key(self):
        """素材ファイル名の先頭と対応する名前（"S01" / "S03a"）"""
        return self.scene + (self.sub or "")

    @property
    def label(self):
        """メッセージ用の表記（"S01" / "S03[a]"）"""
        return self.scene + (f"[{self.sub}]" if self.sub else "")

    @property
    def text(self):
        return "".join(self.lines)


@dataclass
class Scene:
    id: str               # "S01"
    line_no: int
    sections: list[Section] = field(default_factory=list)

    @property
    def number(self):
        return int(self.id[1:])

    @property
    def has_markers(self):
        return any(s.sub for s in self.sections)


@dataclass
class ScriptResult:
    scenes: list[Scene]
    errors: list[str]
    warnings: list[str]

    @property
    def sections(self):
        return [sec for scene in self.scenes for sec in scene.sections]


def parse_script(text):
    scenes = []
    errors = []
    warnings = []
    scene = None
    section = None
    preamble_reported = False

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue

        m = SCENE_HEADING.match(line)
        if m:
            scene = Scene(id=f"S{m.group(1)}", line_no=line_no)
            scenes.append(scene)
            section = None
            continue

        if line.startswith("#"):
            if SCENE_HEADING_LIKE.match(line):
                errors.append(f"script.md {line_no}行目: シーン見出しの書式が違います「{line}」"
                              "（「## S01」のように S＋2桁の数字）")
            continue

        if scene is None:
            if not preamble_reported:
                errors.append(f"script.md {line_no}行目: 最初のシーン見出し（## S01 など）より前に原稿があります")
                preamble_reported = True
            continue

        if SUB_MARKER_UPPER.match(line):
            errors.append(f"script.md {line_no}行目: マーカーは小文字で書いてください（[A] ではなく [a]）")
            continue

        m = SUB_MARKER.match(line)
        if m:
            section = Section(scene=scene.id, sub=m.group(1), line_no=line_no)
            scene.sections.append(section)
            if m.group(2):
                section.lines.append(m.group(2))
            continue

        if section is None:
            section = Section(scene=scene.id, sub=None, line_no=line_no)
            scene.sections.append(section)
        section.lines.append(line)

    _validate(scenes, errors, warnings)
    return ScriptResult(scenes, errors, warnings)


def _validate(scenes, errors, warnings):
    if not scenes:
        errors.append("script.md にシーン見出し（## S01 など）が1つもありません")
        return

    seen = {}
    for scene in scenes:
        if scene.id in seen:
            errors.append(f"script.md {scene.line_no}行目: シーン {scene.id} が重複しています"
                          f"（{seen[scene.id]}行目にもあります）")
        else:
            seen[scene.id] = scene.line_no

    numbers = [s.number for s in scenes]
    if numbers != sorted(numbers):
        warnings.append("script.md のシーン番号が昇順になっていません"
                        f"（{', '.join(s.id for s in scenes)}）。台本の順にタイムラインへ並べます")

    for scene in scenes:
        if not scene.sections:
            errors.append(f"script.md {scene.line_no}行目: {scene.id} の原稿が空です")
            continue
        if not scene.has_markers:
            continue

        if scene.sections[0].sub is None:
            errors.append(f"script.md {scene.sections[0].line_no}行目: {scene.id} は [a] などのマーカーで"
                          "分かれていますが、最初のマーカーより前に原稿があります")
        subs = [s.sub for s in scene.sections if s.sub]
        expected = list(string.ascii_lowercase[:len(subs)])
        if subs != expected:
            errors.append(f"script.md: {scene.id} のマーカーは [a] から順に付けてください"
                          f"（実際: {''.join(f'[{s}]' for s in subs)}）")
        for sec in scene.sections:
            if sec.sub and not sec.lines:
                errors.append(f"script.md {sec.line_no}行目: {sec.label} の原稿が空です")

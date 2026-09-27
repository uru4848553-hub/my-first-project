"""Resolve への配置（フェーズ4）。

plan.json（clips 付き）を読み、現在開いているプロジェクトに新しいタイムラインを作って並べる。
既存のタイムラインには触らない。

Resolve Scripting API は環境によって挙動が違う点があるため、次は実際の結果を見て確かめながら進める:
- タイムラインのフレームレート・解像度が設定どおりになったか（GetSetting で読み戻す）
- AppendToTimeline の endFrame が「含む」か「含まない」か（最初のクリップの長さで判定する）
- 置いたクリップの長さが plan どおりか
"""
import math
import os
from datetime import datetime

from core.telop import wrap_lines

# config.json の sizing → Resolve の「解像度が異なるファイル」の設定値
SIZING = {"fit": "scaleToFit", "fill": "scaleToCrop"}
DEFAULT_TEMPLATE = "テロップ"
TEMPLATE_ALIASES = ("テロップ", "telop")   # この名前のひな形も使う（大文字・小文字、前後の空白は区別しない）
TEMPLATE_HELP = ("Resolve のメディアプールに、テロップのひな形（Text+）を「{name}」という名前で用意してください："
                 "エフェクト → タイトル → Fusionタイトル →「Text+」をタイムラインに置き、フォント・大きさ・位置・色を整えてから、"
                 "そのクリップをメディアプールへドラッグし、名前を「{name}」に変える（プロジェクトごとに1回）")


def telop_mode(plan):
    """"text"（Resolve の Text+ で置く）か "video"（透明付きの動画で置く。以前の方式）"""
    return plan.get("telop_mode") or ("video" if any(t.get("path") for t in plan.get("telops") or []) else "text")
MARKER_COLOR = "Blue"


class PlaceError(RuntimeError):
    pass


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class Placer:
    def __init__(self, resolve, plan, log=print):
        self.resolve = resolve
        self.plan = plan
        self.log = log
        self.warnings = []
        self.fps = plan["fps"]
        self.end_inclusive = None   # AppendToTimeline の endFrame が含む側か（最初のクリップで判定）
        self.narration_track = 1
        self.alpha_done = set()
        self.alpha_warned = False

    # --- 準備 ---------------------------------------------------------

    def run(self, now=None):
        project = self.resolve.GetProjectManager().GetCurrentProject()
        if project is None:
            raise PlaceError("Resolve でプロジェクトが開かれていません")
        self.project = project
        self.media_pool = project.GetMediaPool()

        folder = self._bin(self.plan["name"])
        if self.plan.get("run"):
            folder = self._bin(self.plan["run"], parent=folder)
        self.media_pool.SetCurrentFolder(folder)
        items = self._import(folder)

        name = f"{self.plan['name']}_{(now or datetime.now()):%Y%m%d_%H%M}"
        self.timeline = self._create_timeline(name)
        self.start = self.timeline.GetStartFrame()

        for sec in self.plan["sections"]:
            for clip in sec["clips"]:
                self._place_clip(sec, clip, items[_norm(clip["path"])])
        telops = self.plan.get("telops") or []
        if telops and telop_mode(self.plan) == "text":
            self._place_text_telops(telops)
        else:
            for telop in telops:
                self._place_telop(telop, items[_norm(telop["path"])])
        self._place_narration(items[_norm(self.plan["audio"]["path"])])
        if self.plan.get("bgm"):
            self._place_bgm(items[_norm(self.plan["bgm"]["path"])])
        for sfx in self.plan.get("sfx") or []:
            self._place_sfx(sfx, items[_norm(sfx["path"])])
        self._add_markers()
        return self.timeline.GetName(), self.warnings

    def _bin(self, name, parent=None):
        root = parent or self.media_pool.GetRootFolder()
        for sub in root.GetSubFolderList() or []:
            if sub.GetName() == name:
                return sub
        folder = self.media_pool.AddSubFolder(root, name)
        if folder is None:
            raise PlaceError(f"メディアプールにビン「{name}」を作れません")
        return folder

    def _import(self, folder):
        """素材とナレーションをビンに取り込む。同じファイルが取り込み済みなら使い回す。"""
        paths = [c["path"] for s in self.plan["sections"] for c in s["clips"]] + [self.plan["audio"]["path"]]
        if self.plan.get("bgm"):
            paths.append(self.plan["bgm"]["path"])
        if telop_mode(self.plan) == "video":
            paths += [t["path"] for t in self.plan.get("telops") or []]
        paths += [x["path"] for x in self.plan.get("sfx") or []]
        existing = {}
        for clip in folder.GetClipList() or []:
            path = clip.GetClipProperty("File Path")
            if path:
                existing[_norm(path)] = clip

        items = {}
        for path in paths:
            key = _norm(path)
            if key in items:
                continue
            if key in existing:
                items[key] = existing[key]
                continue
            if not os.path.isfile(path):
                raise PlaceError(f"ファイルがありません: {path}")
            # 1ファイルずつ取り込む（まとめると連番の画像が1つの画像シーケンスにされることがある）
            imported = self.media_pool.ImportMedia([path])
            if not imported:
                raise PlaceError(f"メディアプールに取り込めません: {path}")
            items[key] = imported[0]
            self.log(f"取り込み: {os.path.basename(path)}")
        return items

    def _create_timeline(self, name):
        base, n = name, 2
        while any(self.project.GetTimelineByIndex(i).GetName() == name
                  for i in range(1, self.project.GetTimelineCount() + 1)):
            name, n = f"{base}_{n}", n + 1

        timeline = self.media_pool.CreateEmptyTimeline(name)
        if timeline is None:
            raise PlaceError(f"タイムライン「{name}」を作れません")
        self.project.SetCurrentTimeline(timeline)
        if self._setup_timeline(timeline):
            return timeline

        # タイムライン単位でフレームレートを変えられない場合、プロジェクトにほかのタイムラインがなければ
        # プロジェクトのフレームレートを変えて作り直す（既存タイムラインがあるときは変えない）
        if self.project.GetTimelineCount() == 1:
            self.log(f"タイムラインのフレームレートを変えられないため、プロジェクトのフレームレートを {self.fps} にして作り直します")
            self.media_pool.DeleteTimelines([timeline])
            self.project.SetSetting("timelineFrameRate", str(self.fps))
            timeline = self.media_pool.CreateEmptyTimeline(name)
            if timeline is not None:
                self.project.SetCurrentTimeline(timeline)
                if self._setup_timeline(timeline):
                    return timeline
        actual = timeline.GetSetting("timelineFrameRate") if timeline else "?"
        raise PlaceError(f"タイムラインを {self.fps}fps にできません（現在: {actual}）。"
                         f"プロジェクト設定 → マスター設定 → タイムラインフレームレートを {self.fps} にしてから再実行してください")

    def _setup_timeline(self, timeline):
        """解像度・フレームレート・解像度違いの扱いを設定する。フレームレートが合えば True。"""
        w, h = self.plan["width"], self.plan["height"]
        timeline.SetSetting("useCustomSettings", "1")
        timeline.SetSetting("timelineResolutionWidth", str(w))
        timeline.SetSetting("timelineResolutionHeight", str(h))
        timeline.SetSetting("timelineFrameRate", str(self.fps))
        sizing = SIZING[self.plan["sizing"]]
        timeline.SetSetting("timelineInputResMismatchBehavior", sizing)

        if _float(timeline.GetSetting("timelineFrameRate")) != float(self.fps):
            return False
        size = (timeline.GetSetting("timelineResolutionWidth"), timeline.GetSetting("timelineResolutionHeight"))
        if size != (str(w), str(h)):
            self.warnings.append(f"タイムラインの解像度を {w}×{h} にできませんでした（現在: {size[0]}×{size[1]}）")
        if timeline.GetSetting("timelineInputResMismatchBehavior") != sizing:
            self.warnings.append(f"解像度が異なる素材の扱い（{self.plan['sizing']}）を設定できませんでした。"
                                 "タイムライン設定で確認してください")
        return True

    # --- 配置 ---------------------------------------------------------

    def _append(self, info):
        items = self.media_pool.AppendToTimeline([info])
        return items[0] if items else None

    def _append_range(self, item, pos, src_frames, expected, track=1):
        """素材の先頭から src_frames フレームを pos に置く。最初の1本で endFrame の意味を確かめる。"""
        info = {"mediaPoolItem": item, "startFrame": 0, "trackIndex": track, "mediaType": 1,
                "recordFrame": self.start + pos}
        if self.end_inclusive is not None:
            return self._append(dict(info, endFrame=src_frames - 1 if self.end_inclusive else src_frames))
        placed = self._append(dict(info, endFrame=src_frames))
        if placed is not None:
            if placed.GetDuration() == expected + 1:
                self.timeline.DeleteClips([placed])
                self.end_inclusive = True
                placed = self._append(dict(info, endFrame=src_frames - 1))
            elif placed.GetDuration() == expected:
                self.end_inclusive = False
        return placed

    def _place_clip(self, sec, clip, item):
        """クリップを置く（静止画もフェーズ3で動画にしてあるので、すべて動画として扱う）"""
        label = f"{sec['label']}（{os.path.basename(clip.get('image') or clip['path'])}）"
        src_fps = _float(item.GetClipProperty("FPS")) or self.fps
        pos, frames = clip["record_frame"], clip["frames"]
        src = max(1, round(frames * src_fps / self.fps))
        placed = self._append_range(item, pos, src, frames)
        if placed is None:
            raise PlaceError(f"{label} をタイムラインに置けません")
        got = placed.GetDuration()
        if placed.GetStart() != self.start + pos or abs(got - frames) > 1:
            raise PlaceError(
                f"{label} の位置・長さが配置表と違います（予定: {pos}から{frames}フレーム、"
                f"実際: {placed.GetStart() - self.start}から{got}フレーム。素材の FPS {item.GetClipProperty('FPS')}、"
                f"長さ {item.GetClipProperty('Frames')} フレーム、渡した endFrame {src}）")

    def _ensure_tracks(self, kind, count, sub_type=None):
        while self.timeline.GetTrackCount(kind) < count:
            ok = self.timeline.AddTrack(kind, sub_type) if sub_type else self.timeline.AddTrack(kind)
            if not ok:
                return False
        return True

    def _set_alpha(self, item):
        """テロップの透明部分を透明として扱うよう、クリップ属性のアルファモードを設定する（1回だけ試す）"""
        if id(item) in self.alpha_done:
            return
        self.alpha_done.add(id(item))
        for key in ("Alpha mode", "Alpha Mode"):
            try:
                if item.SetClipProperty(key, "Straight"):
                    return
            except Exception:  # 項目名が違うと例外になる版がある
                pass
        if not self.alpha_warned:
            self.alpha_warned = True
            self.warnings.append("テロップのアルファモードを設定できませんでした。テロップの周りが黒くなる場合は、"
                                 "メディアプールでテロップのクリップを右クリック → クリップ属性 → アルファモードを「ストレート」にしてください")

    def _place_telop(self, telop, item):
        """テロップ（透明付きの動画）を V2（重なるときは V3 …）に置く。うまくいかなくても警告にとどめる。"""
        track = 2 + telop.get("lane", 0)
        label = f"テロップ {telop['label']}「{' / '.join(telop['lines'])}」"
        if not self._ensure_tracks("video", track):
            self.warnings.append(f"{label}: ビデオトラック V{track} を追加できないため置けませんでした")
            return
        self._set_alpha(item)
        src_fps = _float(item.GetClipProperty("FPS")) or self.fps
        frames = telop["frames"]
        placed = self._append_range(item, telop["record_frame"], max(1, round(frames * src_fps / self.fps)), frames, track)
        if placed is None:
            self.warnings.append(f"{label} を V{track} に置けませんでした")
        elif placed.GetStart() != self.start + telop["record_frame"] or abs(placed.GetDuration() - frames) > 1:
            self.warnings.append(f"{label} の位置・長さが想定と違います（予定: {telop['record_frame']}から{frames}フレーム、"
                                 f"実際: {placed.GetStart() - self.start}から{placed.GetDuration()}フレーム）")

    # --- テロップ（Resolve の Text+） ----------------------------------------

    def _find_clip(self, names):
        """メディアプール全体（すべてのビン）から、名前が names のどれかのクリップを探す（大文字・小文字は区別しない）"""
        wanted = {n.strip().casefold() for n in names}
        stack = [self.media_pool.GetRootFolder()]
        while stack:
            folder = stack.pop(0)
            for clip in folder.GetClipList() or []:
                if (clip.GetName() or "").strip().casefold() in wanted:
                    return clip
            stack.extend(folder.GetSubFolderList() or [])
        return None

    def _place_text_telops(self, telops):
        """テロップを、メディアプールのひな形（Text+）から V2（重なるときは V3 …）に置き、文字を入れる。
        Resolve 上でそのまま文字・見た目を直せる。うまくいかなくても警告にとどめる。"""
        name = self.plan.get("telop_template") or DEFAULT_TEMPLATE
        template = self._find_clip((name,) + TEMPLATE_ALIASES)
        if template is None:
            self.warnings.append(f"テロップのひな形（名前が「{name}」か「telop」のもの）がメディアプールにないため、テロップ（{len(telops)}件）を置けませんでした。"
                                 + TEMPLATE_HELP.format(name=name))
            return
        for telop in telops:
            self._place_text_telop(telop, template)

    def _append_title(self, template, pos, frames, track):
        """ひな形を pos から frames フレーム置く（置けた部分の TimelineItem の列を返す）。
        ひな形の長さより長く置けない場合は、続けて置き足して埋める"""
        src_fps = _float(template.GetClipProperty("FPS")) or self.fps
        placed_items, done = [], 0
        while done < frames:
            want = frames - done
            src = max(1, round(want * src_fps / self.fps))
            info = {"mediaPoolItem": template, "startFrame": 0, "trackIndex": track, "recordFrame": self.start + pos + done,
                    "endFrame": src - 1 if self.end_inclusive else src}
            item = self._append(dict(info, mediaType=1)) or self._append(info)
            if item is None or item.GetDuration() <= 0:
                break
            if item.GetDuration() > want:     # 長すぎたら置き直さず、警告だけ出す（次のテロップと重なる可能性）
                self.warnings.append(f"テロップが予定より長く置かれました（予定 {want}、実際 {item.GetDuration()} フレーム）")
            placed_items.append(item)
            done += item.GetDuration()
        return placed_items

    def _place_text_telop(self, telop, template):
        track = 2 + telop.get("lane", 0)
        label = f"テロップ {telop['label']}「{' / '.join(telop['lines'])}」"
        if not self._ensure_tracks("video", track):
            self.warnings.append(f"{label}: ビデオトラック V{track} を追加できないため置けませんでした")
            return
        items = self._append_title(template, telop["record_frame"], telop["frames"], track)
        if not items:
            self.warnings.append(f"{label} を V{track} に置けませんでした")
            return
        if len(items) > 1:
            self.warnings.append(f"{label}: ひな形の長さの上限のため、{len(items)}つのクリップに分けて置きました（文字を直すときは全部直してください）")
        if items[0].GetStart() != self.start + telop["record_frame"]:
            self.warnings.append(f"{label} の位置が想定と違います（予定: {telop['record_frame']}、実際: {items[0].GetStart() - self.start}フレーム）")
        for item in items:
            if not _set_text(item, telop["lines"], self.plan.get("telop_line_chars") or 0):
                self.warnings.append(f"{label}: 文字を入れられませんでした（ひな形が Text+ か確認してください）。Resolve で文字を入力してください")
                break

    def _place_sfx(self, sfx, item):
        """効果音を BGM の次のオーディオトラック（重なるときはさらに次）に、ファイルの長さのまま置く。"""
        track = self.narration_track + (2 if self.plan.get("bgm") else 1) + sfx.get("lane", 0)
        label = f"効果音 {sfx['id']}（{sfx['label']}）"
        if not self._ensure_tracks("audio", track, "stereo"):
            self.warnings.append(f"{label}: オーディオトラック A{track} を追加できないため置けませんでした")
            return
        info = {"mediaPoolItem": item, "trackIndex": track, "mediaType": 2, "recordFrame": self.start + sfx["record_frame"]}
        placed = self._append(info)
        if placed is None:
            self.warnings.append(f"{label} を A{track} に置けませんでした")
        elif placed.GetStart() != self.start + sfx["record_frame"]:
            self.warnings.append(f"{label} の位置が想定と違います（予定: {sfx['record_frame']}、実際: {placed.GetStart() - self.start}フレーム）")

    def _place_bgm(self, item):
        """BGM をナレーションの次のオーディオトラック（通常 A2）に置く。うまくいかなくても警告にとどめる。"""
        bgm = self.plan["bgm"]
        track = self.narration_track + 1
        while self.timeline.GetTrackCount("audio") < track:
            if not self.timeline.AddTrack("audio", "stereo"):
                self.warnings.append("BGM 用のオーディオトラックを追加できませんでした。BGM は手動で置いてください")
                return
        src_fps = _float(item.GetClipProperty("FPS")) or self.fps
        src = max(1, round(bgm["frames"] * src_fps / self.fps))
        info = {"mediaPoolItem": item, "startFrame": 0, "endFrame": src - 1 if self.end_inclusive else src,
                "trackIndex": track, "mediaType": 2, "recordFrame": self.start}
        placed = self._append(info)
        if placed is None:
            self.warnings.append(f"BGM を A{track} に置けませんでした。BGM は手動で置いてください")
            return
        if abs(placed.GetDuration() - bgm["frames"]) > 1:
            self.warnings.append(f"BGM の長さが想定と違います（想定 {bgm['frames']} フレーム、実際 {placed.GetDuration()} フレーム）")
        self.log(f"BGM を A{track} に置きました（音量は Resolve で調整してください）")

    def _place_narration(self, item):
        self.narration_track = 1
        info = {"mediaPoolItem": item, "trackIndex": 1, "mediaType": 2, "recordFrame": self.start}
        placed = self._append(info)
        if placed is None:
            # A1 とチャンネル構成（モノラル/ステレオ）が合わないと置けないことがあるので、モノラルのトラックを足して試す
            if self.timeline.AddTrack("audio", "mono"):
                index = self.timeline.GetTrackCount("audio")
                placed = self._append(dict(info, trackIndex=index))
                if placed is not None:
                    self.narration_track = index
                    self.warnings.append(f"ナレーションを A1 に置けなかったため、追加したモノラルトラック A{index} に置きました")
        if placed is None:
            raise PlaceError("ナレーションを A1 に置けません")
        expected = self.plan["audio"]["frames"]
        if abs(placed.GetDuration() - expected) > 1:
            self.warnings.append(f"ナレーションの長さが想定と違います（想定 {expected} フレーム、実際 {placed.GetDuration()} フレーム）")

    def _add_markers(self):
        for sec in self.plan["sections"]:
            marker = sec.get("marker")
            if marker and not self.timeline.AddMarker(sec["start_frame"], MARKER_COLOR,
                                                      marker["name"], marker["note"], 1):
                self.warnings.append(f"{marker['name']} のマーカーを付けられませんでした")
        # AddMarker の位置はタイムライン先頭からの相対フレームとして渡している。読み戻して確かめる
        expected = {sec["start_frame"] for sec in self.plan["sections"] if sec.get("marker")}
        actual = {int(f) for f in (self.timeline.GetMarkers() or {})}
        if expected - actual:
            self.warnings.append(f"マーカーの位置が想定と違います（想定: {sorted(expected)}、実際: {sorted(actual)}）")


TEXT_WIDTH = 0.9          # 1行を画面の幅の何割までにするか
DEFAULT_TEXT_SIZE = 0.08  # Text+ の文字の大きさ（Size）の既定値


def line_units(size):
    """Text+ の Size（画面の幅に対する文字の高さの割合）から、1行に入る全角文字数を見積もる"""
    try:
        size = float(size)
    except (TypeError, ValueError):
        size = DEFAULT_TEXT_SIZE
    if not size > 0:
        size = DEFAULT_TEXT_SIZE
    return max(2, math.floor(TEXT_WIDTH / size))


def _set_text(item, lines, line_chars=0):
    """Text+ のクリップに文字を入れる（ひな形の中の Text+ ツールすべて）。できたら True。
    Text+ は自動で折り返さないので、画面の幅に収まるように改行を入れる。
    1行の文字数は line_chars（0 ならひな形の文字の大きさから計算）"""
    try:
        comp = item.GetFusionCompByIndex(1)
        tools = comp.GetToolList(False, "TextPlus") if comp else None
    except Exception:  # Fusion を持たないクリップなど
        return False
    tools = list(tools.values()) if isinstance(tools, dict) else list(tools or [])
    if not tools:
        return False
    units = line_chars if line_chars > 0 else line_units(tools[0].GetInput("Size"))
    text = "\n".join(wrap_lines(lines, units))
    for tool in tools:
        tool.SetInput("StyledText", text)
    return tools[0].GetInput("StyledText") == text


def check_plan(plan):
    """配置してよい plan か確かめ、問題を返す"""
    problems = list(plan.get("errors") or [])
    for sec in plan.get("sections", []):
        if "clips" not in sec:
            problems.append(f"{sec['label']}: 尺調整（フェーズ3）が済んでいません")
            continue
        for clip in sec["clips"]:
            if not os.path.isfile(clip["path"]):
                problems.append(f"{sec['label']}: ファイルがありません: {clip['path']}")
    if not os.path.isfile(plan["audio"]["path"]):
        problems.append(f"ナレーションがありません: {plan['audio']['path']}")
    if plan.get("bgm") and not os.path.isfile(plan["bgm"]["path"]):
        problems.append(f"BGM がありません: {plan['bgm']['path']}")
    for t in (plan.get("telops") or []) if telop_mode(plan) == "video" else []:
        if not t.get("path") or not os.path.isfile(t["path"]):
            problems.append(f"テロップ {t['label']} の動画がありません（{t.get('path') or '未作成'}）")
    for x in plan.get("sfx") or []:
        if not os.path.isfile(x["path"]):
            problems.append(f"効果音がありません: {x['path']}")
    return problems


def place(resolve, plan, log=print, now=None):
    problems = check_plan(plan)
    if problems:
        raise PlaceError("配置表に問題があるため配置しません:\n  " + "\n  ".join(problems))
    return Placer(resolve, plan, log).run(now)

"""Resolve への配置（フェーズ4）。

plan.json（clips 付き）を読み、現在開いているプロジェクトに新しいタイムラインを作って並べる。
既存のタイムラインには触らない。

Resolve Scripting API は環境によって挙動が違う点があるため、次は実際の結果を見て確かめながら進める:
- タイムラインのフレームレート・解像度が設定どおりになったか（GetSetting で読み戻す）
- AppendToTimeline の endFrame が「含む」か「含まない」か（最初のクリップの長さで判定する）
- 置いたクリップの長さが plan どおりか
"""
import os
from datetime import datetime

# config.json の sizing → Resolve の「解像度が異なるファイル」の設定値
SIZING = {"fit": "scaleToFit", "fill": "scaleToCrop"}
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

    # --- 準備 ---------------------------------------------------------

    def run(self, now=None):
        project = self.resolve.GetProjectManager().GetCurrentProject()
        if project is None:
            raise PlaceError("Resolve でプロジェクトが開かれていません")
        self.project = project
        self.media_pool = project.GetMediaPool()

        folder = self._bin(self.plan["name"])
        self.media_pool.SetCurrentFolder(folder)
        items = self._import(folder)

        name = f"{self.plan['name']}_{(now or datetime.now()):%Y%m%d_%H%M}"
        self.timeline = self._create_timeline(name)
        self.start = self.timeline.GetStartFrame()

        for sec in self.plan["sections"]:
            for clip in sec["clips"]:
                self._place_clip(sec, clip, items[_norm(clip["path"])])
        self._place_narration(items[_norm(self.plan["audio"]["path"])])
        self._add_markers()
        return self.timeline.GetName(), self.warnings

    def _bin(self, name):
        root = self.media_pool.GetRootFolder()
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

    def _append_range(self, item, pos, src_frames, expected):
        """素材の先頭から src_frames フレームを pos に置く。最初の1本で endFrame の意味を確かめる。"""
        info = {"mediaPoolItem": item, "startFrame": 0, "trackIndex": 1, "mediaType": 1,
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

    def _place_narration(self, item):
        info = {"mediaPoolItem": item, "trackIndex": 1, "mediaType": 2, "recordFrame": self.start}
        placed = self._append(info)
        if placed is None:
            # A1 とチャンネル構成（モノラル/ステレオ）が合わないと置けないことがあるので、モノラルのトラックを足して試す
            if self.timeline.AddTrack("audio", "mono"):
                index = self.timeline.GetTrackCount("audio")
                placed = self._append(dict(info, trackIndex=index))
                if placed is not None:
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
    return problems


def place(resolve, plan, log=print, now=None):
    problems = check_plan(plan)
    if problems:
        raise PlaceError("配置表に問題があるため配置しません:\n  " + "\n  ".join(problems))
    return Placer(resolve, plan, log).run(now)

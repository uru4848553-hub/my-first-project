"""Resolve への配置のテスト。Resolve の代わりに、API の形をまねた偽物を使う。

偽物は「こう動くはず」という想定で書いているので、ここで確かめられるのは配置の手順と計算まで。
実際の Resolve での動きは実機で確認する。
"""
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from core.resolve_place import PlaceError, check_plan, place

START = 108000   # 30fps で 01:00:00:00


class FakeItem:
    # 静止画はフェーズ3で動画にしてから置くので、ここでは動画・音声だけをまねる
    # （実機の Resolve 21 は、静止画を AppendToTimeline で置くと endFrame を無視して既定の5秒で置く）

    def __init__(self, path, fps=30.0, frames=150):
        self.path, self.fps, self.frames = path, fps, frames

    def GetClipProperty(self, key):
        return {"File Path": self.path, "FPS": f"{self.fps:g}", "Frames": str(self.frames)}.get(key)


class FakeFolder:
    def __init__(self, name):
        self.name, self.subs, self.clips = name, [], []

    def GetName(self):
        return self.name

    def GetSubFolderList(self):
        return self.subs

    def GetClipList(self):
        return self.clips


class FakeTimelineItem:
    def __init__(self, item, start, duration, track, media_type):
        self.item, self.start, self.duration, self.track, self.media_type = item, start, duration, track, media_type

    def GetStart(self):
        return self.start

    def GetDuration(self):
        return self.duration


class FakeTimeline:
    def __init__(self, name, project_fps, fps_settable):
        self.name = name
        self.settings = {"timelineFrameRate": project_fps, "timelineResolutionWidth": "1920",
                         "timelineResolutionHeight": "1080", "timelineInputResMismatchBehavior": "centerCrop"}
        self.fps_settable = fps_settable
        self.items, self.markers = [], {}
        self.audio_tracks = 1

    def GetName(self):
        return self.name

    def GetStartFrame(self):
        return START

    def SetSetting(self, key, value):
        if key == "timelineFrameRate" and not self.fps_settable:
            return False
        self.settings[key] = value
        return True

    def GetSetting(self, key):
        return self.settings.get(key)

    def DeleteClips(self, items, ripple=False):
        for it in items:
            self.items.remove(it)
        return True

    def AddMarker(self, frame, color, name, note, duration):
        self.markers[frame] = {"color": color, "name": name, "note": note, "duration": duration}
        return True

    def GetMarkers(self):
        return dict(self.markers)

    def AddTrack(self, kind, sub=None):
        self.audio_tracks += 1
        return True

    def GetTrackCount(self, kind):
        return self.audio_tracks


class FakeMediaPool:
    def __init__(self, project, end_inclusive):
        self.project = project
        self.end_inclusive = end_inclusive
        self.root = FakeFolder("Master")
        self.current = self.root
        self.imports = []
        self.appends = []
        self.src_fps = {}

    def GetRootFolder(self):
        return self.root

    def AddSubFolder(self, parent, name):
        folder = FakeFolder(name)
        parent.subs.append(folder)
        return folder

    def SetCurrentFolder(self, folder):
        self.current = folder
        return True

    def ImportMedia(self, paths):
        self.imports.append(list(paths))
        items = [FakeItem(p, self.src_fps.get(os.path.splitext(p)[1], 30.0)) for p in paths]
        self.current.clips.extend(items)
        return items

    def CreateEmptyTimeline(self, name):
        if any(t.name == name for t in self.project.timelines):
            return None
        tl = FakeTimeline(name, self.project.settings["timelineFrameRate"], self.project.timeline_fps_settable)
        self.project.timelines.append(tl)
        return tl

    def DeleteTimelines(self, timelines):
        for t in timelines:
            self.project.timelines.remove(t)
        return True

    def AppendToTimeline(self, infos):
        tl = self.project.current
        placed = []
        for info in infos:
            self.appends.append(info)
            item = info["mediaPoolItem"]
            if info.get("mediaType") == 2:
                if self.project.audio_needs_mono and info["trackIndex"] == 1:
                    continue
                duration = item.frames
            else:
                src = info["endFrame"] - info["startFrame"] + (1 if self.end_inclusive else 0)
                duration = round(src * float(tl.settings["timelineFrameRate"]) / item.fps)
            ti = FakeTimelineItem(item, info["recordFrame"], duration, info["trackIndex"], info.get("mediaType"))
            tl.items.append(ti)
            placed.append(ti)
        return placed


class FakeProject:
    def __init__(self, end_inclusive=False, timeline_fps_settable=True, fps="24"):
        self.settings = {"timelineFrameRate": fps}
        self.timeline_fps_settable = timeline_fps_settable
        self.audio_needs_mono = False
        self.timelines = []
        self.current = None
        self.pool = FakeMediaPool(self, end_inclusive)

    def GetMediaPool(self):
        return self.pool

    def GetTimelineCount(self):
        return len(self.timelines)

    def GetTimelineByIndex(self, i):
        return self.timelines[i - 1]

    def SetCurrentTimeline(self, tl):
        self.current = tl
        return True

    def SetSetting(self, key, value):
        if self.timelines:
            return False
        self.settings[key] = value
        return True


class FakeResolve:
    def __init__(self, project):
        self.project = project

    def GetProjectManager(self):
        return self

    def GetCurrentProject(self):
        return self.project


NOW = datetime(2026, 9, 23, 14, 5)


class PlaceTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

        def f(name):
            path = os.path.join(self.dir, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").close()
            return path

        # 静止画はフェーズ3で動画（mp4）にしてある。元の画像は "image"
        v1, img, v3, freeze, img2, audio = (f("media/S01_a.mp4"), f("media/_stills/S02_b_abcd1234_30f.mp4"),
                                            f("media/S03a_c.mov"), f("media/_freeze/S03a_c_last_1234abcd_30f.mp4"),
                                            f("media/_stills/S03b_d_5678ef90_30f.mp4"), f("audio/narration.wav"))
        self.paths = [v1, img, v3, freeze, img2, audio]

        def sec(label, scene, start, frames, clips, marker=None):
            return {"label": label, "scene": scene, "start_frame": start, "duration_frames": frames,
                    "clips": clips, "marker": marker, "warnings": []}

        self.plan = {
            "name": "動画_テスト", "fps": 30, "width": 1080, "height": 1920, "sizing": "fit", "errors": [],
            "audio": {"path": audio, "frames": 150},
            "sections": [
                sec("S01", "S01", 0, 40, [{"type": "video", "path": v1, "record_frame": 0, "frames": 40}],
                    {"name": "S01", "note": "こんにちは"}),
                sec("S02", "S02", 40, 30, [{"type": "image", "path": img, "image": "S02_b.png", "record_frame": 40, "frames": 30}],
                    {"name": "S02", "note": "まず結論から"}),
                sec("S03[a]", "S03", 70, 50, [{"type": "video", "path": v3, "record_frame": 70, "frames": 20},
                                               {"type": "freeze", "path": freeze, "image": "S03a_c_last_1234abcd.png",
                                                "record_frame": 90, "frames": 30}],
                    {"name": "S03", "note": "画面を見て"}),
                sec("S03[b]", "S03", 120, 30, [{"type": "image", "path": img2, "image": "S03b_d.jpg", "record_frame": 120, "frames": 30}]),
            ],
        }

    def run_place(self, project):
        return place(FakeResolve(project), self.plan, log=lambda m: None, now=NOW)

    def video_items(self, project):
        return [(t.start - START, t.duration) for t in project.current.items if t.media_type == 1]

    def test_place(self):
        project = FakeProject()
        name, warnings = self.run_place(project)
        self.assertEqual(name, "動画_テスト_20260923_1405")
        self.assertEqual(warnings, [])
        tl = project.current

        # タイムライン設定
        self.assertEqual(tl.settings["timelineFrameRate"], "30")
        self.assertEqual((tl.settings["timelineResolutionWidth"], tl.settings["timelineResolutionHeight"]), ("1080", "1920"))
        self.assertEqual(tl.settings["timelineInputResMismatchBehavior"], "scaleToFit")
        self.assertEqual(project.settings["timelineFrameRate"], "24")   # プロジェクトは変えない

        # ビンと取り込み（1ファイルずつ）
        self.assertEqual([f.GetName() for f in project.pool.root.subs], ["動画_テスト"])
        self.assertEqual(project.pool.imports, [[p] for p in self.paths])

        # V1：plan どおりに隙間なく
        self.assertEqual(self.video_items(project), [(0, 40), (40, 30), (70, 20), (90, 30), (120, 30)])
        self.assertTrue(all(t.track == 1 for t in tl.items))
        # 動画素材は映像だけ（mediaType 1）
        self.assertEqual([a["mediaType"] for a in project.pool.appends[:5]], [1, 1, 1, 1, 1])

        # A1：ナレーションを0フレームから
        audio = [t for t in tl.items if t.media_type == 2]
        self.assertEqual([(a.start - START, a.duration, a.track) for a in audio], [(0, 150, 1)])

        # マーカー：シーン先頭だけ（フレーム位置はタイムライン先頭からの相対）
        self.assertEqual(sorted(tl.markers), [0, 40, 70])
        self.assertEqual(tl.markers[70], {"color": "Blue", "name": "S03", "note": "画面を見て", "duration": 1})

    def test_fill(self):
        self.plan["sizing"] = "fill"
        project = FakeProject()
        self.run_place(project)
        self.assertEqual(project.current.settings["timelineInputResMismatchBehavior"], "scaleToCrop")

    def test_end_frame_inclusive(self):
        project = FakeProject(end_inclusive=True)
        self.run_place(project)
        self.assertEqual(self.video_items(project), [(0, 40), (40, 30), (70, 20), (90, 30), (120, 30)])
        ends = [a["endFrame"] for a in project.pool.appends if a.get("mediaType") == 1]
        # 最初の1本は判定用に置き直す（40 → 39）
        self.assertEqual(ends, [40, 39, 29, 19, 29, 29])

    def test_source_fps_differs(self):
        project = FakeProject()
        project.pool.src_fps[".mov"] = 60.0
        self.run_place(project)
        s03a = [a for a in project.pool.appends if a["mediaPoolItem"].path.endswith(".mov")][0]
        self.assertEqual(s03a["endFrame"], 40)   # 60fps の素材で 20フレーム（30fps）分
        self.assertEqual(self.video_items(project)[2], (70, 20))

    def test_project_fps_changed_only_when_no_other_timelines(self):
        project = FakeProject(timeline_fps_settable=False)
        name, _ = self.run_place(project)
        self.assertEqual(project.settings["timelineFrameRate"], "30")
        self.assertEqual([t.name for t in project.timelines], [name])

    def test_fps_error_when_other_timelines_exist(self):
        project = FakeProject(timeline_fps_settable=False)
        project.timelines.append(FakeTimeline("既存", "24", False))
        with self.assertRaises(PlaceError) as cm:
            self.run_place(project)
        self.assertIn("30fps にできません", str(cm.exception))
        self.assertEqual(project.settings["timelineFrameRate"], "24")

    def test_name_collision_and_rerun_reuses_media(self):
        project = FakeProject()
        first, _ = self.run_place(project)
        second, _ = self.run_place(project)
        self.assertEqual(second, first + "_2")
        self.assertEqual(len(project.pool.root.subs), 1)            # ビンは使い回す
        self.assertEqual(len(project.pool.imports), len(self.paths))  # 2回目は取り込み直さない
        self.assertEqual(len(project.timelines[0].items), 6)         # 1本目のタイムラインは変えない

    def test_narration_on_mono_track(self):
        project = FakeProject()
        project.audio_needs_mono = True
        _, warnings = self.run_place(project)
        self.assertEqual([t.track for t in project.current.items if t.media_type == 2], [2])
        self.assertTrue(any("A2" in w for w in warnings))

    def patch_duration(self, project, suffix, duration):
        orig = project.pool.AppendToTimeline

        def patched(infos):
            placed = orig(infos)
            for p in placed:
                if p.item.path.endswith(suffix):
                    p.duration = duration
            return placed
        project.pool.AppendToTimeline = patched

    def test_too_long_is_error(self):
        project = FakeProject()
        self.patch_duration(project, "_30f.mp4", 200)   # 静止画の動画が予定（30フレーム）より長く置かれた
        with self.assertRaises(PlaceError) as cm:
            self.run_place(project)
        self.assertIn("S02（S02_b.png）", str(cm.exception))
        self.assertIn("実際: 40から200フレーム", str(cm.exception))
        self.assertIn("素材の FPS 30", str(cm.exception))

    def test_short_video_is_error(self):
        # 動画は繰り返して埋めない（頭に戻ってしまうため）
        project = FakeProject()
        self.patch_duration(project, ".mov", 10)
        with self.assertRaises(PlaceError) as cm:
            self.run_place(project)
        self.assertIn("S03[a]（S03a_c.mov）", str(cm.exception))

    def test_no_project(self):
        with self.assertRaises(PlaceError):
            place(FakeResolve(None), self.plan, log=lambda m: None)

    def test_check_plan(self):
        self.assertEqual(check_plan(self.plan), [])
        self.plan["errors"] = ["S02 の尺が0フレーム以下です"]
        del self.plan["sections"][1]["clips"]
        os.remove(self.paths[0])
        problems = check_plan(self.plan)
        self.assertEqual(len(problems), 3)
        with self.assertRaises(PlaceError):
            place(FakeResolve(FakeProject()), self.plan, log=lambda m: None)


if __name__ == "__main__":
    unittest.main()

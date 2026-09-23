"""配置表（plan.json）の生成。

セクションの開始時刻（秒）をフレームに丸め、終了フレーム＝次のセクションの開始フレームにして
隙間も重なりも出ないようにする。最後のセクションは音声の終端まで。
"""
import json
import math
import os
from datetime import datetime

MEMO_LENGTH = 20


def to_frames(starts, audio_duration, fps):
    """開始時刻（秒）の列 → (開始フレーム, 終了フレーム) の列"""
    total = math.ceil(audio_duration * fps - 1e-6)
    frames = [0] + [round(t * fps) for t in starts[1:]]
    return [(f, frames[i + 1] if i + 1 < len(frames) else total) for i, f in enumerate(frames)], total


def build_plan(check, timings, audio_duration, config, match_ratio=None, fake=False, bgm_duration=None,
               sfx_durations=None):
    """check: core.checks.ProjectCheck、timings: core.align.SectionTiming のリスト（entries と同じ順）
    sfx_durations: {効果音ID: 長さ（秒）}

    戻り値: (plan 辞書, エラー, 警告)
    """
    fps = config["fps"]
    errors = []
    warnings = []
    starts = [t.start for t in timings]

    for i in range(1, len(starts)):
        if starts[i] < starts[i - 1]:
            errors.append(f"{check.entries[i].section.label} の開始時刻（{starts[i]:.2f}秒）が直前のセクションより前です"
                          "（アライメント失敗の可能性）")
    if starts and starts[-1] >= audio_duration:
        errors.append(f"{check.entries[-1].section.label} の開始時刻が音声の長さ（{audio_duration:.2f}秒）を超えています")

    if fake:
        warnings.append("仮のアライメント（--fake-align：原稿の文字数で音声の長さを割り振っただけ）です。本番には使わないでください")
    if match_ratio is not None and match_ratio < 0.9:
        warnings.append(f"台本とアライメント結果の文字の一致度が低めです（{match_ratio:.0%}）")

    spans, total = to_frames(starts, audio_duration, fps)
    scene_text = {}
    for e in check.entries:
        scene_text[e.section.scene] = scene_text.get(e.section.scene, "") + e.section.text

    sections = []
    seen_scenes = set()
    for e, t, (start_f, end_f) in zip(check.entries, timings, spans):
        sec, media = e.section, e.media
        dur_f = end_f - start_f
        sec_warnings = []
        if dur_f <= 0:
            errors.append(f"{sec.label} の尺が0フレーム以下です（アライメント失敗の可能性）")
        elif dur_f < fps:
            sec_warnings.append(f"尺が1秒未満（{dur_f / fps:.2f}秒）")
        if fake:
            pass
        elif t.confidence is None:
            sec_warnings.append("台本の文字と対応する単語がない（読み上げと台本が違う可能性）")
        elif t.confidence < config["low_confidence"]:
            sec_warnings.append(f"アライメント信頼度が低い（{t.confidence:.2f}）。台本と実際の読み上げが違う可能性")
        warnings.extend(f"{sec.label}: {w}" for w in sec_warnings)

        is_scene_start = sec.scene not in seen_scenes
        seen_scenes.add(sec.scene)
        sections.append({
            "key": sec.key,
            "label": sec.label,
            "scene": sec.scene,
            "sub": sec.sub,
            "text": sec.text,
            "scene_start": is_scene_start,
            # シーン先頭のマーカー用（名前＝シーン番号、メモ＝シーン原稿の冒頭20文字）
            "marker": {"name": sec.scene, "note": scene_text[sec.scene][:MEMO_LENGTH]} if is_scene_start else None,
            "media": {"path": os.path.abspath(media.path), "name": media.name, "kind": media.kind},
            "start_sec": round(t.start, 3),
            "start_frame": start_f,
            "end_frame": end_f,
            "duration_frames": dur_f,
            "confidence": None if t.confidence is None else round(t.confidence, 3),
            "warnings": sec_warnings,
        })

    plan = {
        "version": 1,
        "name": check.name,
        "folder": os.path.abspath(check.folder),
        "created": datetime.now().isoformat(timespec="seconds"),
        "fps": fps,
        "width": config["width"],
        "height": config["height"],
        "sizing": config["sizing"],
        "audio": {"path": os.path.abspath(check.audio), "duration_sec": round(audio_duration, 3), "frames": total},
        "total_frames": total,
        "bgm": _bgm(check, bgm_duration, fps, total, warnings),
        "sections": sections,
        "telops": _telops(check, spans),
        "sfx": _sfx(check, spans, sfx_durations or {}, fps, total, warnings),
        "fake_align": fake,
        # エラーがある配置表はフェーズ4で使わない
        "errors": errors,
    }
    return plan, errors, warnings


def _bgm(check, duration, fps, total, warnings):
    """BGM（任意）：A2 に0フレームから、ナレーションの終わりまで（BGM が短ければ BGM の終わりまで）"""
    if not check.bgm or duration is None:
        return None
    frames = min(total, math.floor(duration * fps + 1e-6))
    if frames < total:
        warnings.append(f"BGM（{duration:.1f}秒）がナレーションより短いため、途中で終わります（繰り返しはしません）")
    return {"path": os.path.abspath(check.bgm), "duration_sec": round(duration, 3), "frames": frames}


def _lanes(items):
    """重ならないよう、各項目に置き場所の段（0 が一番下）を割り当てる（items は record_frame 順に並べ替える）"""
    items.sort(key=lambda x: (x["record_frame"], x["label"]))
    ends = []
    for item in items:
        end = item["record_frame"] + item["frames"]
        for lane, last in enumerate(ends):
            if last <= item["record_frame"]:
                ends[lane] = end
                break
        else:
            lane = len(ends)
            ends.append(end)
        item["lane"] = lane
    return items


def _scene_spans(check, spans):
    """{シーン: (開始フレーム, 終了フレーム)} と {セクションのキー: (開始, 終了)}"""
    by_scene, by_key = {}, {}
    for e, (start, end) in zip(check.entries, spans):
        first = by_scene.get(e.section.scene, (start, end))
        by_scene[e.section.scene] = (first[0], end)
        by_key[e.section.key] = (start, end)
    return by_scene, by_key


def _targets(check, spans):
    """テロップ・効果音を付けた場所の列: (ラベル, (開始, 終了), 付け先の Scene または Section)"""
    by_scene, by_key = _scene_spans(check, spans)
    for scene in check.scenes:
        if scene.id in by_scene:
            yield scene.id, by_scene[scene.id], scene
        for sec in scene.sections:
            if sec.key in by_key:
                yield sec.label, by_key[sec.key], sec


def _telops(check, spans):
    """テロップ：シーン全体（またはセクション）の頭から終わりまで。V2 から上に、重ならないよう置く"""
    telops = []
    for label, (start, end), target in _targets(check, spans):
        if target.telops and end > start:
            telops.append({"label": label, "lines": list(target.telops), "record_frame": start, "frames": end - start})
    return _lanes(telops)


def _sfx(check, spans, durations, fps, total, warnings):
    """効果音：シーン（またはセクション）の頭から（＋ずらす秒）。長さは効果音ファイルの長さ"""
    sfx = []
    for label, (start, _), target in _targets(check, spans):
        for sid, offset in target.sfx:
            path = check.sfx.get(sid)
            if not path or sid not in durations:
                continue
            record = start + round(offset * fps)
            frames = math.floor(durations[sid] * fps + 1e-6)
            if record >= total:
                warnings.append(f"{label}: 効果音 {sid} の位置（+{offset:g}秒）がナレーションの終わりを超えるため置きません")
                continue
            if frames <= 0:
                warnings.append(f"{label}: 効果音 {sid} が短すぎるため置きません")
                continue
            sfx.append({"label": label, "id": sid, "path": os.path.abspath(path), "name": os.path.basename(path),
                        "offset_sec": offset, "record_frame": record, "frames": frames})
    return _lanes(sfx)


def report_extra(plan):
    """report.md に足すテロップ・効果音の一覧"""
    fps = plan["fps"]
    out = []
    if plan.get("telops"):
        out += ["", "## テロップ", "", "| 場所 | 開始時刻 | 尺 | 文字 |", "|---|---|---|---|"]
        out += [f"| {t['label']} | {t['record_frame'] / fps:.2f}秒 | {t['frames'] / fps:.2f}秒 | "
                + " / ".join(t["lines"]).replace("|", "\\|") + " |" for t in plan["telops"]]
    if plan.get("sfx"):
        out += ["", "## 効果音", "", "| 場所 | 効果音 | 開始時刻 | 長さ |", "|---|---|---|---|"]
        out += [f"| {x['label']} | {x['name']} | {x['record_frame'] / fps:.2f}秒 | {x['frames'] / fps:.2f}秒 |"
                for x in plan["sfx"]]
    return out


def report_rows(plan):
    fps = plan["fps"]
    return [{"key": s["label"], "start": s["start_frame"] / fps, "duration": s["duration_frames"] / fps,
             "media": s["media"]["name"], "warnings": s["warnings"]} for s in plan["sections"]]


def write_plan(plan, folder):
    out_dir = os.path.join(folder, "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "plan.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(plan, fp, ensure_ascii=False, indent=2)
    return path

"""output/report.md の出力。"""
import os
from datetime import datetime


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_time(seconds):
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:05.2f}"


def build_report(check, rows=None, extra=None):
    """rows: シーン表の行。{key, start, duration, media, warnings} の辞書のリスト。
    省略時は割り当て結果から作る（開始時刻・尺は未確定なので —）。"""
    if rows is None:
        rows = [{"key": e.section.label, "start": None, "duration": None,
                 "media": e.media.name, "warnings": []} for e in check.entries]

    out = [f"# レポート: {check.name}", "",
           f"作成: {datetime.now():%Y-%m-%d %H:%M}", ""]
    if check.audio:
        out += [f"ナレーション: `{os.path.basename(check.audio)}`", ""]
    if getattr(check, "bgm", None):
        out += [f"BGM: `{os.path.basename(check.bgm)}`", ""]

    out += [f"## エラー（{len(check.errors)}件）", ""]
    out += [f"- {e}" for e in check.errors] or ["なし"]
    out += ["", f"## 警告（{len(check.warnings)}件）", ""]
    out += [f"- {w}" for w in check.warnings] or ["なし"]

    out += ["", "## シーン一覧", ""]
    if rows:
        out += ["| シーン | 開始時刻 | 尺 | 素材 | 警告 |", "|---|---|---|---|---|"]
        for r in rows:
            out.append("| " + " | ".join(_cell(v) for v in (
                r["key"], format_time(r["start"]), format_time(r["duration"]),
                r["media"], " / ".join(r["warnings"]) or "")) + " |")
    else:
        out.append("（エラーのため作成できませんでした）")
    out += extra or []
    return "\n".join(out) + "\n"


def write_report(check, rows=None, extra=None):
    out_dir = os.path.join(check.folder, "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.md")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(build_report(check, rows, extra))
    return path

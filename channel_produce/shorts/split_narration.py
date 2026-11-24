"""1本のナレーション（場面の間に長い間を入れて読ませたもの）を、場面ごとのファイルに切り分ける。

python channel_produce/shorts/split_narration.py <ショートのフォルダ> <ナレーション.mp3>
→ <フォルダ>/narr/S01.mp3, S02.mp3, … S09b.mp3

仕組み：無音（-35dB 以下が0.45秒以上）を探し、長い順に「場面の数−1」か所を選んで、その無音の真ん中で切る。
切った後、各ファイルの頭と終わりの無音を0.05秒まで詰める。
無音の数が足りないときは止める（場面の境目が分からないため。読ませ直すか、間を長くする）。
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.script import parse_script  # noqa: E402


def silences(path):
    out = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.45", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends))


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def main(folder, narration):
    folder, narration = Path(folder), Path(narration)
    result = parse_script((folder / "script.md").read_text(encoding="utf-8-sig"))
    keys = [s.key for sc in result.scenes for s in sc.sections]
    total = duration(narration)
    # 頭と終わりの無音は境目にしない
    gaps = [(s, e) for s, e in silences(narration) if s > 0.2 and e < total - 0.2]
    if len(gaps) < len(keys) - 1:
        raise SystemExit(f"場面の境目が足りません：無音 {len(gaps)} か所、必要 {len(keys) - 1} か所。読ませ直してください")
    chosen = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:len(keys) - 1])
    cuts = [0.0] + [(s + e) / 2 for s, e in chosen] + [total]
    out_dir = folder / "narr"
    out_dir.mkdir(exist_ok=True)
    trim = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
            "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse")
    for key, a, b in zip(keys, cuts, cuts[1:]):
        dst = out_dir / f"{key}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(narration),
                        "-af", trim, "-c:a", "libmp3lame", "-q:a", "2", str(dst)], check=True)
        print(f"{key}: {a:6.2f}〜{b:6.2f}秒 → {duration(dst):.2f}秒")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

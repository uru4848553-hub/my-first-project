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


def pick_gaps(gaps, lengths, total):
    """境目を「場面の数−1」か所選ぶ。各場面の文字数から予想した境目の時刻に近く、
    しかも長い無音ほど選ばれやすくする（文の途中の短い間を、場面の境目と取り違えないため）"""
    n = len(lengths) - 1
    pause_total = sum(e - s for s, e in sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:n])
    speech = max(total - pause_total, 1.0)
    cum, acc = [], 0
    for i, length in enumerate(lengths[:-1]):
        acc += length
        cum.append(acc)
    char_total = sum(lengths)
    mids = [(s + e) / 2 for s, e in gaps]
    # 予想の境目：話している時間を文字数で割り振り、それまでの境目の無音の平均の長さを足す
    avg_pause = pause_total / max(n, 1)
    expected = [speech * c / char_total + avg_pause * (i + 0.5) for i, c in enumerate(cum)]
    INF = float("inf")
    g = len(gaps)
    # dp[i][j]：i 番目の境目に j 番目の無音を使ったときの最小のずれ
    dp = [[INF] * g for _ in range(n)]
    back = [[-1] * g for _ in range(n)]
    for j in range(g):
        dp[0][j] = cost(mids[j], expected[0], gaps[j])
    for i in range(1, n):
        best, arg = INF, -1
        for j in range(g):
            if j - 1 >= 0 and dp[i - 1][j - 1] < best:
                best, arg = dp[i - 1][j - 1], j - 1
            if best < INF:
                dp[i][j] = best + cost(mids[j], expected[i], gaps[j])
                back[i][j] = arg
    j = min(range(g), key=lambda k: dp[n - 1][k])
    picked = []
    for i in range(n - 1, -1, -1):
        picked.append(gaps[j])
        j = back[i][j]
    return list(reversed(picked))


def cost(mid, expected, gap):
    """予想とのずれ（秒の2乗）から、無音の長さぶんを引く（長い無音ほど境目らしい）"""
    return (mid - expected) ** 2 - 4.0 * (gap[1] - gap[0])


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
    chosen = pick_gaps(gaps, [len(sec.text) for sc in result.scenes for sec in sc.sections], total)
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

"""ショートを、YouTube にそのまま投稿できる mp4 に仕上げる（DaVinci Resolve を使わない版）。

python channel_produce/shorts/render_final.py <ショートのフォルダ> [--voice-dir narr] [--out 完成_ナレーション入り.mp4]

使うもの（フォルダの中）
- script.md                ：台本（「テロップ：」「効果音：K01 +0.35」「[a]」付き）
- media/S01_〜.mp4 / .png  ：場面ごとの素材（素材の名前は自動配置ツールと同じ）
- narr/S01.mp3, S08a.mp3 … ：場面ごとのナレーション（1場面＝1ファイル）
- se/K01_〜.wav            ：効果音
- bgm.mp3（あれば）        ：BGM。ナレーションの下に小さく流す

仕組み
- 各場面の長さ＝その場面のナレーションの長さ＋少しの間。映像はその長さに合わせる
  （動く mp4 は足りなければ最後の絵で止める、画像はゆっくり寄る／引くを交互に）
- テロップはシーンの間ずっと、画面の上から25%の位置に白文字・黒縁で出す（自動配置ツールと同じ見た目）
- 音はナレーション＋効果音（＋BGM）を重ね、YouTube 向けの音量（-14 LUFS）にそろえる
"""
import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.config import DEFAULTS  # noqa: E402
from core.ffmpeg import still_to_video  # noqa: E402
from core.script import parse_script  # noqa: E402
from core.telop import render_png, style_of, wrap_lines  # noqa: E402

FPS = 30
PAD = 0.3          # 場面の終わりの間（秒）
PAD_FIRST = 0.1    # 最初の場面は間を短く（最初の1秒を詰める）
PAD_LAST = 0.9     # 最後の場面は少し長く
LEAD = 0.05        # 場面の頭からナレーションが始まるまで
LINE_UNITS = 13    # テロップ1行の文字数（全角）
TELOP_SIZE = 72


def telop_rows(lines):
    """「や（の前と、、や。の後で区切ってから、長い行だけ折り返す（"使／う」"のような変な改行を防ぐ）"""
    import re
    rows = []
    for line in lines:
        pieces = [p for p in re.split(r"(?=[「（])|(?<=[、。])", line) if p.strip()]
        # 短すぎるかけらは前の行につなげる
        merged = []
        for piece in pieces:
            if merged and len(merged[-1]) + len(piece) <= 7:
                merged[-1] += piece
            else:
                merged.append(piece)
        rows += wrap_lines([m.strip() for m in merged], LINE_UNITS)
    return rows


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def run(args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def find_media(media_dir, key):
    found = [p for p in glob.glob(str(media_dir / f"{key}_*")) if Path(p).suffix.lower() in (".mp4", ".mov", ".png", ".jpg", ".jpeg")]
    if len(found) != 1:
        raise SystemExit(f"{key} の素材が見つからないか、2つ以上あります: {found}")
    return Path(found[0])


SIZE = [1080, 1920]   # 横長（長尺）のときは --landscape で 1920×1080


def video_segment(src, frames, dst):
    """動画を frames フレームにする（短ければ最後の絵で止め、長ければ切る）"""
    w, h = SIZE
    run(["-i", str(src), "-an", "-vf",
         f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
         f"tpad=stop_mode=clone:stop_duration=600,trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p",
         "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-r", str(FPS), str(dst)])


def subtitle_chunks(text):
    """字幕のかたまり：文（。？！）ごと。長い文は、真ん中に近い「、」で2つに分ける"""
    import re
    chunks = []
    for sent in [x for x in re.split(r"(?<=[。？！])", text) if x.strip()]:
        if len(sent) > 30 and "、" in sent:
            commas = [m.end() for m in re.finditer("、", sent)]
            cut = min(commas, key=lambda c: abs(c - len(sent) / 2))
            chunks += [sent[:cut], sent[cut:]]
        else:
            chunks.append(sent)
    return [c.strip() for c in chunks if c.strip()]


def ass_time(t):
    h, rem = divmod(max(t, 0), 3600)
    m, sec = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{sec:05.2f}"


def write_ass(path, events, font_name, size):
    w, h = SIZE
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 0", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
             "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Sub,{font_name},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,0,2,80,80,40,1",
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for start, end, text in events:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{text}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(folder, voice_dir, out_name, bgm_volume, subtitles=False):
    folder = Path(folder)
    result = parse_script((folder / "script.md").read_text(encoding="utf-8-sig"))
    if result.errors:
        raise SystemExit("台本のエラー:\n" + "\n".join(result.errors))
    sections = [(scene, sec) for scene in result.scenes for sec in scene.sections]

    # 1. 場面ごとの時間を決める（フレームの境目は累積で丸めて、隙間・重なりを作らない）
    times, t = [], 0.0
    for i, (scene, sec) in enumerate(sections):
        narr = folder / voice_dir / f"{sec.key}.mp3"
        if not narr.exists():
            raise SystemExit(f"ナレーションがありません: {narr}")
        pad = PAD_FIRST if i == 0 else (PAD_LAST if i == len(sections) - 1 else PAD)
        d = LEAD + duration(narr) + pad
        times.append((t, d, narr))
        t += d
    total = t
    bounds = [round(s * FPS) for s, _, _ in times] + [round(total * FPS)]

    config = dict(DEFAULTS)
    config["width"], config["height"] = SIZE
    if not config.get("telop_font"):
        for cand in ("C:/Windows/Fonts/meiryob.ttc", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                     "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"):
            if os.path.exists(cand):
                config["telop_font"] = cand
                break
    config["telop_size"] = TELOP_SIZE
    style = style_of(config)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 2. 映像：場面ごとに作ってつなぐ
        parts, image_index = [], 0
        for i, (scene, sec) in enumerate(sections):
            frames = bounds[i + 1] - bounds[i]
            src = find_media(folder / "media", sec.key)
            dst = tmp / f"v{i:02d}.mp4"
            if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
                still_to_video(str(src), str(dst), frames, FPS, motion="in" if image_index % 2 == 0 else "out", zoom=1.08)
                image_index += 1
            else:
                video_segment(src, frames, dst)
            parts.append(dst)
        listfile = tmp / "list.txt"
        listfile.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        base = tmp / "base.mp4"
        run(["-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(base)])

        # 3. テロップ：シーンの頭から終わりまで
        overlays, ov_inputs = [], []
        idx = 0
        for scene in result.scenes:
            lines = list(scene.telops)
            if not lines:
                continue
            first = next(i for i, (sc, _) in enumerate(sections) if sc is scene)
            last = max(i for i, (sc, _) in enumerate(sections) if sc is scene)
            start, end = bounds[first] / FPS, bounds[last + 1] / FPS
            png = tmp / f"t{idx:02d}.png"
            render_png(telop_rows(lines), style, png)
            ov_inputs += ["-i", str(png)]
            overlays.append((start, end))
            idx += 1
        graph, last_v = [], "0:v"
        for k, (start, end) in enumerate(overlays):
            graph.append(f"[{last_v}][{k + 1}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'[o{k}]")
            last_v = f"o{k}"

        # 3.5 字幕（長尺）：場面のナレーションの長さを、文の文字数で割り振る
        if subtitles:
            events = []
            for i, (scene, sec) in enumerate(sections):
                start = bounds[i] / FPS + LEAD
                speak = duration(times[i][2])
                chunks = subtitle_chunks(sec.text)
                total_chars = sum(len(c) for c in chunks) or 1
                t0 = start
                for c in chunks:
                    t1 = t0 + speak * len(c) / total_chars
                    events.append((t0, t1 + 0.15, c))
                    t0 = t1
            ass = tmp / "sub.ass"
            font_file = config["telop_font"]
            write_ass(ass, events, "Meiryo" if "meiryo" in font_file.lower() else "IPAGothic", 54)
            fonts_dir = str(Path(font_file).parent).replace("\\", "/").replace(":", "\\:")
            ass_arg = str(ass).replace("\\", "/").replace(":", "\\:")
            graph.append(f"[{last_v}]subtitles=filename='{ass_arg}':fontsdir='{fonts_dir}'[subv]")
            last_v = "subv"

        # 4. 音：ナレーション＋効果音（＋BGM）
        a_inputs, a_labels = [], []
        n_in = 1 + len(overlays)
        for i, (start, d, narr) in enumerate(times):
            a_inputs += ["-i", str(narr)]
            ms = int((bounds[i] / FPS + LEAD) * 1000)
            graph.append(f"[{n_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
            a_labels.append(f"[n{i}]")
            n_in += 1
        for scene in result.scenes:
            first = next(i for i, (sc, _) in enumerate(sections) if sc is scene)
            fx_list = [(scene, s) for s in scene.sfx] + [
                (sec, s) for sc, sec in sections if sc is scene for s in sec.sfx]
            for owner, (sid, offset) in fx_list:
                anchor = bounds[first] if owner is scene else bounds[next(i for i, (_, se) in enumerate(sections) if se is owner)]
                files = glob.glob(str(folder / "se" / f"{sid}_*"))
                if not files:
                    raise SystemExit(f"効果音がありません: {sid}")
                a_inputs += ["-i", files[0]]
                ms = int((anchor / FPS + (offset or 0)) * 1000)
                graph.append(f"[{n_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},volume=0.8[f{n_in}]")
                a_labels.append(f"[f{n_in}]")
                n_in += 1
        bgm = folder / "bgm.mp3"
        if bgm.exists():
            a_inputs += ["-stream_loop", "-1", "-i", str(bgm)]
            graph.append(f"[{n_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={bgm_volume},"
                         f"atrim=0:{total:.3f},afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5[bgm]")
            a_labels.append("[bgm]")
            n_in += 1
        graph.append("".join(a_labels) + f"amix=inputs={len(a_labels)}:normalize=0,apad,atrim=0:{total:.3f},"
                     "loudnorm=I=-14:TP=-1.5:LRA=11[aud]")

        out = folder / out_name
        run(["-i", str(base), *ov_inputs, *a_inputs, "-filter_complex", ";".join(graph),
             "-map", f"[{last_v}]" if last_v != "0:v" else "0:v", "-map", "[aud]",
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)])
    print(f"ok: {out}（{total:.1f}秒）")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--voice-dir", default="narr")
    ap.add_argument("--out", default="完成_ナレーション入り.mp4")
    ap.add_argument("--bgm-volume", type=float, default=0.12)
    ap.add_argument("--landscape", action="store_true", help="横長（1920×1080）で書き出す（長尺）")
    ap.add_argument("--subtitles", action="store_true", help="ナレーションの字幕を画面の下に出す（長尺）")
    a = ap.parse_args()
    if a.landscape:
        SIZE[:] = [1920, 1080]
    build(a.folder, a.voice_dir, a.out, a.bgm_volume, subtitles=a.subtitles)


if __name__ == "__main__":
    main()

"""配置テスト用の素材一式を ffmpeg で作る（録音なしで Resolve への配置を試すため）。

使い方:
    run.bat tools\\make_sample.py                       # samples\\動画_生成テスト に作る
    run.bat tools\\make_sample.py "D:\\動画\\動画_テスト"   # 場所を指定

作ったあと:
    run.bat autoedit.py samples\\動画_生成テスト --fake-align

中身:
    S01_opening.mp4   横長 1920x1080・6秒（縦長タイムラインへの fit/fill を確認）
    S02_graph.png     正方形 1080x1080
    S03a_screen.mp4   縦長 1080x1920・1秒しかない（最終フレームの静止画で埋まるのを確認）
    S03b_result.jpg   縦長 1080x1920
    audio/narration.wav  15秒・モノラル（小さな音量の正弦波。読み上げではない）
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "samples", "動画_生成テスト")

SCRIPT = """\
# 配置テスト用（tools/make_sample.py が作成）

## S01
こんにちは、ヒロキです。今日はAI副業の始め方を話します。

## S02
まず結論から言うと、最初の3ヶ月は収益ゼロを覚悟してください。

## S03
[a] 実際の画面を見てください。ここで設定を開きます。
[b] すると、このように結果が表示されます。
"""


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not shutil.which("ffmpeg"):
        print("[エラー] ffmpeg が見つかりません")
        return 1
    if os.path.exists(folder):
        print(f"[エラー] すでにあります: {folder}（作り直すときは先に削除してください）")
        return 1

    media = os.path.join(folder, "media")
    audio = os.path.join(folder, "audio")
    os.makedirs(media)
    os.makedirs(audio)
    with open(os.path.join(folder, "script.md"), "w", encoding="utf-8") as fp:
        fp.write(SCRIPT)

    print("素材を作成中...")
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=6", "-pix_fmt", "yuv420p",
           os.path.join(media, "S01_opening.mp4"))
    ffmpeg("-f", "lavfi", "-i", "smptebars=size=1080x1080", "-frames:v", "1", os.path.join(media, "S02_graph.png"))
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30:duration=1", "-pix_fmt", "yuv420p",
           os.path.join(media, "S03a_screen.mp4"))
    ffmpeg("-f", "lavfi", "-i", "color=c=0x2060a0:size=1080x1920", "-frames:v", "1", os.path.join(media, "S03b_result.jpg"))
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=15", "-af", "volume=0.05", "-ac", "1", "-ar", "48000",
           os.path.join(audio, "narration.wav"))

    print(f"作成しました: {folder}")
    print(f'次に:  .\\run.bat autoedit.py "{folder}" --fake-align')
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""ショート用の効果音を ffmpeg で合成する（著作権のない自作の音）。

自動配置ツールは、動画フォルダの se/K01_〜.wav を、台本の「効果音：K01 +0.35」の位置に置く。
"""
import subprocess
from pathlib import Path

# 名前: (秒, ffmpeg の aevalsrc の式, 後処理フィルタ)
SOUNDS = {
    # 画面が割れる：高い音のノイズが一瞬で鳴って消える＋低い衝撃
    "ガシャッ": (0.45, "(random(0)*2-1)*exp(-9*t)*0.9+sin(2*PI*90*t)*exp(-25*t)*0.6", "highpass=f=300"),
    # 階が積み上がる：木をたたくような短い低い音
    "トン": (0.18, "sin(2*PI*t*(180-300*t))*exp(-22*t)", "lowpass=f=1200"),
    # 速報：2つの高い音
    "ピロン": (0.36, "if(lt(t,0.14),sin(2*PI*880*t),sin(2*PI*1320*t))*exp(-6*mod(t,0.14))*0.6", ""),
    # 紙の束が落ちる：こもったノイズ
    "ドサッ": (0.35, "(random(0)*2-1)*exp(-14*t)+sin(2*PI*70*t)*exp(-18*t)*0.8", "lowpass=f=900"),
    # ペンで線を引く：こすれるノイズ
    "シャッ": (0.55, "(random(0)*2-1)*(1-exp(-30*t))*exp(-4*t)*0.6", "bandpass=f=3500:width_type=h:w=3000"),
    # ひらめき：明るい高い音
    "ピコン": (0.3, "(sin(2*PI*1568*t)+0.5*sin(2*PI*2349*t))*exp(-10*t)*0.5", ""),
}


def make(name, path):
    sec, expr, post = SOUNDS[name]
    af = f"aformat=channel_layouts=mono,{post + ',' if post else ''}afade=t=out:st={sec * 0.8:.3f}:d={sec * 0.2:.3f},volume=0.8"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={sec}",
                    "-af", af, "-c:a", "pcm_s16le", str(path)], check=True)
    return path

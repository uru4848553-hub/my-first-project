# 確認用mp4の組み立て（ffmpeg + Pillow）。場面の境目はナレーションの無音位置から決めた
import subprocess, os
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
NAVY, WHITE, ORANGE, YELLOW = (20, 34, 74, 255), (255, 255, 255, 255), (255, 138, 0, 255), (255, 214, 64, 255)
cuts = [0, 3.93, 8.26, 13.20, 21.34, 27.54, 35.24]
scenes = [
 dict(img="hiro_S01_困り顔", top=["AIで仕事が速くなったのに"], big="暇にならない", bot=[]),
 dict(img="hiro_S02_考える", top=[], big="仕事が増える", bot=["空いた時間に別の仕事が", "回ってくる"]),
 dict(img="hiro_S03_驚き", top=[], big="ズルい？", bot=["AIを使ったと言えば", "「ズルしてるみたい」"]),
 dict(img="hiro_S04_警告", top=["ある研究では"], big="怠け者に見える", bot=["AI利用者は", "低く見られやすい"], note=True),
 dict(img="hiro_S05_したり顔", top=["ある会社の観察"], big="仕事が増えた", bot=["途中経過の報告（1社）"], note=True),
 dict(img="hiro_S06_ひらめき", top=[], big="浮いた時間は？", bot=["何に使っていますか"]),
]
def fit(text, max_w, max_size, min_size=40):
    s = max_size
    while s > min_size:
        f = ImageFont.truetype(FONT, s)
        if f.getlength(text) <= max_w: return f
        s -= 4
    return ImageFont.truetype(FONT, min_size)
def put(d, text, cy, font, fill, strokes):
    w = font.getlength(text); x = (W - w) / 2
    for sw, sc in strokes: d.text((x, cy), text, font=font, fill=sc, stroke_width=sw, stroke_fill=sc, anchor="lm")
    d.text((x, cy), text, font=font, fill=fill, stroke_width=3, stroke_fill=fill, anchor="lm")
os.makedirs("build", exist_ok=True)
for i, s in enumerate(scenes):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for j, t in enumerate(s["top"]):
        put(d, t, 215 + j * 100, fit(t, 960, 84), WHITE, [(14, NAVY)])
    f = fit(s["big"], 940, 210)
    put(d, s["big"], 1290, f, ORANGE, [(30, NAVY), (20, WHITE)])
    for j, t in enumerate(s["bot"]):
        put(d, t, 1470 + j * 92, fit(t, 960, 70), WHITE, [(12, NAVY)])
    if s.get("note"):
        put(d, "※確認用｜研究は原文確認前", 1760, fit("※確認用｜研究は原文確認前", 900, 44), YELLOW, [(8, NAVY)])
    im.save(f"build/telop_{i+1}.png")
    dur = cuts[i + 1] - cuts[i]; n = int(dur * 30) + 1
    zoom = "min(1+0.0007*on,1.09)" if i % 2 == 0 else "max(1.09-0.0007*on,1.0)"
    fc = (f"[0:v]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
          f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps=30[v];"
          f"[v][1:v]overlay=0:0,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", f"media/{s['img']}.png", "-i", f"build/telop_{i+1}.png",
                    "-filter_complex", fc, "-t", f"{dur:.3f}", "-r", "30", "-c:v", "libx264", "-crf", "18", f"build/scene_{i+1}.mp4"], check=True)
open("build/list.txt", "w").write("".join(f"file 'scene_{i+1}.mp4'\n" for i in range(len(scenes))))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "build/list.txt", "-i", "audio/narration.mp3",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", "確認用_AIで速くなったのに暇にならない.mp4"], check=True)
print("done")

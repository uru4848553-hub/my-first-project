# 確認用mp4（ショート2）の組み立て。ffmpeg + Pillow。場面の境目はナレーションの場面間の無音から決めた
import subprocess, os
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
NAVY, WHITE, ORANGE = (20, 34, 74, 255), (255, 255, 255, 255), (255, 138, 0, 255)
cuts = [0, 8.92, 17.21, 25.97, 33.20, 41.56]
TOP = [("年収別", 112), ("AIは課金すべき？", 74)]  # 既存ショートに合わせ、全場面で固定
scenes = [
 dict(img="hiro_S01_疑問", big="課金する？", bot=[]),
 dict(img="hiro_S02_安心", big="300万", bot=["まずは無料で十分"]),
 dict(img="hiro_S03_時間がない", big="500万", bot=["下書きだけAIに任せる"]),
 dict(img="hiro_S04_自信", big="700万", bot=["課金で時間を買う"]),
 dict(img="hiro_S05_提案", big="時間？予算？", bot=["足りない方をAIで補う"]),
]
def fit(text, max_w, max_size, min_size=40):
    s = max_size
    while s > min_size:
        f = ImageFont.truetype(FONT, s)
        if f.getlength(text) <= max_w: return f
        s -= 4
    return ImageFont.truetype(FONT, min_size)
def put(d, text, cy, font, fill, strokes):
    x = (W - font.getlength(text)) / 2
    for sw, sc in strokes: d.text((x, cy), text, font=font, fill=sc, stroke_width=sw, stroke_fill=sc, anchor="lm")
    for dx, dy in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, cy + dy), text, font=font, fill=fill, anchor="lm")
os.makedirs("build", exist_ok=True)
for i, s in enumerate(scenes):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = 190
    for t, size in TOP:
        put(d, t, y, fit(t, 940, size), WHITE, [(14, NAVY)]); y += int(size * 1.35)
    put(d, s["big"], 1290, fit(s["big"], 940, 210), ORANGE, [(30, NAVY), (20, WHITE)])
    for j, t in enumerate(s["bot"]):
        put(d, t, 1470 + j * 92, fit(t, 960, 72), WHITE, [(12, NAVY)])
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
                "-shortest", "-movflags", "+faststart", "確認用_無料で足りる人と課金が得な人.mp4"], check=True)
print("done")

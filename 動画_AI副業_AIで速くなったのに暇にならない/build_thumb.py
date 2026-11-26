# サムネイル（9:16, 1080x1920）。既存のヒロ画像に文字を重ねる（クレジット不要）
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
NAVY, WHITE, ORANGE = (20, 34, 74, 255), (255, 255, 255, 255), (255, 138, 0, 255)
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
def make(src, top, big, small, out):
    im = Image.open(src).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = ImageEnhance.Contrast(im.crop((l, t, l + W, t + H))).enhance(1.08)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    put(d, top, 230, fit(top, 940, 96), WHITE, [(16, NAVY)])
    put(d, big, 420, fit(big, 960, 250), ORANGE, [(36, NAVY), (24, WHITE)])
    if small: put(d, small, 1560, fit(small, 940, 80), WHITE, [(14, NAVY)])
    Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save(out, quality=92)
make("media/hiro_S01_困り顔.png", "AIで仕事が速くなったのに", "暇にならない", "", "サムネイル_A.jpg")
make("media/hiro_S03_驚き.png", "AIを使ったと言うと", "ズルい？", "", "サムネイル_B.jpg")

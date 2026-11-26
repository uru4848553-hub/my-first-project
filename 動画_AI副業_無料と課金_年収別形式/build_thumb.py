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
im = Image.open("media/hiro_S01_疑問.png").convert("RGB")
s = max(W / im.width, H / im.height)
im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
l, t = (im.width - W) // 2, (im.height - H) // 2
im = ImageEnhance.Contrast(im.crop((l, t, l + W, t + H))).enhance(1.08)
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
put(d, "年収別", 150, fit("年収別", 940, 120), WHITE, [(16, NAVY)])
put(d, "AIは課金すべき？", 265, fit("AIは課金すべき？", 940, 84), WHITE, [(14, NAVY)])
put(d, "無料？課金？", 410, fit("無料？課金？", 960, 210), ORANGE, [(36, NAVY), (24, WHITE)])
Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save("サムネイル.jpg", quality=92)

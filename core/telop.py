"""テロップ（台本の「テロップ：〜」）の画像と動画を作る。

テロップは、タイムラインと同じ大きさの透明な PNG に文字を描き、表示する尺だけ続く
透明付きの動画（ProRes 4444）にして V2 に置く。静止画のままだと Resolve が既定の長さ（5秒）で
置いてしまうため（フェーズ4で確認）、素材の静止画と同じく動画にする。
Resolve 上では文字の打ち直しはできないので、直すときは台本を直して再実行する。
"""
import hashlib
import json
import os

from core.ffmpeg import FFmpegError, _run

TELOP_DIR = "_telop"

# 見つかった最初のフォントを使う（config.json の telop_font で指定もできる）
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\meiryob.ttc",        # メイリオ Bold
    r"C:\Windows\Fonts\YuGothB.ttc",        # 游ゴシック Bold
    r"C:\Windows\Fonts\BIZ-UDGothicB.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
LINE_SPACING = 1.25
BREAK_AFTER_OK = set("。、，．！？」』）)!?,.")   # 行頭に来ないようにする文字


class TelopError(RuntimeError):
    pass


def find_font(config):
    path = config.get("telop_font") or ""
    if path:
        if not os.path.isfile(path):
            raise TelopError(f"config.json の telop_font のフォントがありません: {path}")
        return path
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise TelopError("テロップ用の日本語フォントが見つかりません。config.json の telop_font にフォントファイルを指定してください")


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise TelopError("テロップを作るには Pillow が必要です。"
                         "PowerShell で  .\\run.bat -m pip install pillow  を実行してください") from e
    return Image, ImageDraw, ImageFont


def wrap(text, font, max_width):
    """1行が max_width を超えないよう折り返す（「。」「、」などは行頭に来ないよう前の行に付ける）"""
    lines, cur = [], ""
    for ch in text:
        if cur and font.getlength(cur + ch) > max_width and ch not in BREAK_AFTER_OK:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def style_of(config):
    return {
        "width": config["width"], "height": config["height"],
        "font": find_font(config),
        "size": config["telop_size"], "y": config["telop_y"],
        "color": config["telop_color"], "stroke_color": config["telop_stroke_color"],
        "stroke": config["telop_stroke_width"], "max_width": config["telop_max_width"],
    }


def render_png(lines, style, dst):
    """テロップの行（台本の1行＝画面の1行、長ければ折り返す）を透明な PNG に描く"""
    Image, ImageDraw, ImageFont = _pil()
    try:
        font = ImageFont.truetype(style["font"], style["size"])
    except OSError as e:
        raise TelopError(f"フォントを読めません: {style['font']}") from e
    w, h = style["width"], style["height"]
    rows = [r for line in lines for r in wrap(line, font, w * style["max_width"] - style["stroke"] * 2)]
    step = style["size"] * LINE_SPACING
    top = h * style["y"] - step * (len(rows) - 1) / 2
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for i, row in enumerate(rows):
        draw.text((w / 2, top + step * i), row, font=font, fill=style["color"], anchor="mm",
                  stroke_width=style["stroke"], stroke_fill=style["stroke_color"])
    image.save(dst)
    return dst


def png_to_video(src, dst, frames, fps):
    """透明な PNG を、frames フレーム続く透明付きの動画（ProRes 4444）にする"""
    _run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-i", src,
          "-frames:v", str(frames), "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
          "-alpha_bits", "8", "-qscale:v", "9", "-vendor", "apl0", "-an", dst])
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        raise FFmpegError(f"テロップを動画にできません: {src}")
    return dst


def telop_paths(folder, name, lines, style, frames):
    """同じ文字・同じ見た目なら PNG を使い回し、長さも同じなら動画も使い回す"""
    key = json.dumps({"lines": lines, "style": style}, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    base = os.path.join(folder, "media", TELOP_DIR, f"{name}_{digest}")
    return base + ".png", f"{base}_{frames}f.mov"


def apply_telops(plan, config, log=print):
    """plan["telops"] の各テロップの PNG と動画を作り、path（動画）と image（PNG）を入れる。戻り値: エラー"""
    telops = plan.get("telops") or []
    if not telops:
        return []
    try:
        style = style_of(config)
    except TelopError as e:
        plan["errors"].append(str(e))
        return [str(e)]
    errors = []
    for t in telops:
        png, mov = telop_paths(plan["folder"], t["label"].replace("[", "").replace("]", ""),
                               t["lines"], style, t["frames"])
        try:
            os.makedirs(os.path.dirname(png), exist_ok=True)
            if not os.path.isfile(png):
                render_png(t["lines"], style, png)
            if not (os.path.isfile(mov) and os.path.getsize(mov) > 0):
                tmp = mov[:-4] + ".tmp.mov"
                png_to_video(png, tmp, t["frames"], plan["fps"])
                os.replace(tmp, mov)
                log(f"テロップを作りました: {t['label']}「{' / '.join(t['lines'])}」")
        except (TelopError, FFmpegError, OSError) as e:
            errors.append(f"{t['label']}: テロップを作れません: {e}")
            continue
        t["image"], t["path"] = png, mov
    plan["errors"].extend(errors)
    return errors

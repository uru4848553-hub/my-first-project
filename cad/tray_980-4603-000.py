"""ITT Cannon 980-4603-000 XLM梱包トレー 3Dモデル（図面の上面図から凹み形状を読み取った近似）。
実行: python tray_980-4603-000.py  → 980-4603-000.step を出力
座標: 原点=トレー中心、X右、Y上（図面の上面図と同じ向き）、Z=0がフランジ面、Z=40.5が上面ランド。
"""
import math
import cadquery as cq

W0, W1 = 210.0, 202.0      # 底面外形 / 上面外形
H = 40.5                   # 全高
T = 0.8                    # 板厚
R = 15.0                   # 外形コーナー R15
FLOOR_Z = 5.0              # 凹み底面の高さ
DRAFT = 3.0                # 凹みの抜き勾配(deg)  ※上端18.5 → 底15 の図面値に合わせた
WALL_DRAFT = math.degrees(math.atan(((W0 - W1) / 2) / H))

ROW_SQ = [8.3 + 33.0 * k for k in range(-2, 2)]      # 角形(クリップ付き)凹みの行 Y
ROW_RC = [-7.5 + 33.0 * k for k in range(-2, 2)]     # 長方形凹み・横腕の行 Y

# 凹み一覧: (中心x, 中心y, 幅x, 幅y, コーナーR)   ※上端寸法
POCKETS = []
# 1) クリップ付き角形凹み 4列×4行
SQUARES = [(x, y) for x in (-52.5, -17.5, 17.5, 52.5) for y in ROW_SQ]
for x, y in SQUARES:
    POCKETS.append((x, y, 18.5, 18.5, 2.5))
# 2) 中央3列の長方形凹み（x=0,±35）
for x in (-35.0, 0.0, 35.0):
    for y in ROW_RC:
        POCKETS.append((x, y, 15.4, 12.5, 2.0))
    # 3) 上端の縦長スロット
    POCKETS.append((x, 72.3, 19.0, 43.0, 2.0))
# 4) 両側の縦通路・上端スロット（x=±70）・横腕・ベイ（図面の外側の線で寸法を取る）
TAB_H = 17.0                                               # 横腕の上端寸法（外側の線）
TAB_Y = [25.25 + 33.0 * i for i in range(-3, 2)]            # 横腕5段の中心Y
TAB_Y[0] = -73.2                                            # 最下段のみ図面で約0.5mm上
BAYS = []                                                   # ベイ: (yLo, yHi, 下側フックあり, 上側フックあり)
for i in range(-3, 0):                                      # 横腕どうしの間の4か所
    BAYS.append((TAB_Y[i + 3] + TAB_H / 2, TAB_Y[i + 4] - TAB_H / 2, True, True))
BAYS.append((TAB_Y[4] + TAB_H / 2, 82.6, True, False))      # 最上段の横腕より上: 下側の隅のみ
BAYS.append((-87.0, TAB_Y[0] - TAB_H / 2, False, True))     # 最下段の横腕より下: 上側の隅のみ
for s in (-1, 1):
    POCKETS.append((s * 70.0, 68.8, 19.4, 50.0, 2.5))       # 上端スロット
    POCKETS.append((s * 70.45, -7.0, 15.5, 146.0, 2.0))     # 縦通路（y=-80〜66）
    POCKETS.append((s * 69.75, -87.5, 19.7, 15.0, 2.5))     # 通路下端の縦長凹み（L字の脚。y=-95〜-80）
    for y in TAB_Y:                                         # 横腕
        POCKETS.append((s * 79.35, y, 33.3, TAB_H, 2.5))
    for ylo, yhi, _, _ in BAYS:                             # ベイ（通路から外側へ広がる凹み）
        POCKETS.append((s * 81.0, (ylo + yhi) / 2, 8.6, yhi - ylo, 2.0))
# 5) 下端の半開きクリップ凹み
for x in (-52.5, -17.5, 17.5, 52.5):
    POCKETS.append((x, -87.0, 16.0, 13.0, 2.0))

# クリップ（L字フック）: 図面の拡大図より。凹みの上縁の隅から内側へ張り出すつば状ブロック。
# 凹み中心から見て |x| 2.6〜7.95、|y| 4.3〜8.1（上面図）、z は上面から6.5mm下(34.0。B-B断面の寸法6.5)〜上面。
HOOK_X, HOOK_Y, HOOK_BOT = (2.6, 9.6), (4.3, 9.6), 34.0   # 壁側は凹みの縁より外まで伸ばして壁と一体にする
HOOKS = []   # (x0, x1, y0, y1) 絶対座標の箱
def _box(cx, cy, sx, sy):
    xs = sorted((cx + sx * HOOK_X[0], cx + sx * HOOK_X[1]))
    ys = sorted((cy + sy * HOOK_Y[0], cy + sy * HOOK_Y[1]))
    return (xs[0], xs[1], ys[0], ys[1])
for x, y in SQUARES:
    for sx in (-1, 1):
        for sy in (-1, 1):
            HOOKS.append(_box(x, y, sx, sy))
for x in (-52.5, -17.5, 17.5, 52.5):          # 下端の半開き凹みは図の上側(凹みの+Y側)の2隅のみ
    for sx in (-1, 1):
        HOOKS.append(_box(x, -75.7, sx, -1))  # y=-85.3〜-80.0 に置く
# ベイのフック: 外側(壁側)の x=79.8〜86、横腕の縁から約3.6mm
for s in (-1, 1):
    for ylo, yhi, low, up in BAYS:
        xa, xb = sorted((s * 79.8, s * 86.0))
        if low:
            HOOKS.append((xa, xb, ylo, ylo + 3.6))
        if up:
            HOOKS.append((xa, xb, yhi - 3.6, yhi))


def hook(x0, x1, y0, y1):
    return (cq.Workplane("XY").workplane(offset=HOOK_BOT)
            .center((x0 + x1) / 2, (y0 + y1) / 2).sketch().rect(x1 - x0, y1 - y0)
            .vertices().fillet(1.0).finalize().extrude(H - HOOK_BOT))


# B-B断面のランプ: 上端スロット（Y+側）の端部。端の壁→z≈24の5.3mm幅の段→急な傾斜→底、の順。
# 各要素: (中心x, 半幅x, [(y, z), ...] ランプ上面の折れ線。最後の点が底面)
# ※下端の半開き凹みは傾斜ではなく通常の抜き勾配の壁（B-B断面の拡大図より）なのでランプなし
RAMPS = []
for x, w in ((-70.0, 19.4), (-35.0, 19.0), (0.0, 19.0), (35.0, 19.0), (70.0, 19.4)):
    RAMPS.append((x, w / 2 - 2.0, [(95.0, 40.0), (93.0, 40.0), (91.1, 24.0), (85.8, 23.2), (79.5, FLOOR_Z)]))


def ramp(x, hw, pts, d):
    """ランプ下の材料ブロック（YZ断面を押し出し）。d=板厚オフセット(上面を垂直に下げる)"""
    y_a, y_b = pts[0][0], pts[-1][0]
    poly = [(y_a, FLOOR_Z - d - 1.0)] + [(y, z - d) for y, z in pts] + [(y_b, FLOOR_Z - d - 1.0)]
    return (cq.Workplane("YZ").workplane(offset=x - hw + d).polyline(poly).close()
            .extrude(2 * (hw - d)))


def body(d):
    """d=0: 外形ソリッド、d=T: 板厚ぶん内側のソリッド（下面は開放）"""
    top = H - d
    s = (cq.Workplane("XY").workplane(offset=-1 if d else 0)
         .sketch().rect(W0 - 2 * d, W0 - 2 * d).vertices().fillet(R - d).finalize()
         .extrude(top + (1 if d else 0), taper=WALL_DRAFT))
    for x, y, w, h, r in POCKETS:
        depth = top + 0.01 - (FLOOR_Z - d)
        pocket = (cq.Workplane("XY").workplane(offset=top + 0.01).center(x, y)
                  .sketch().rect(w + 2 * d, h + 2 * d).vertices().fillet(max(r - 0.01, 0.1) + d).finalize()
                  .extrude(-depth, taper=DRAFT))
        s = s.cut(pocket)
    for x, hw, pts in RAMPS:
        s = s.union(ramp(x, hw, pts, d))
    if d == 0:                         # フックは中実のブロックとして外形側にだけ足す
        for box in HOOKS:
            s = s.union(hook(*box))
    return s


if __name__ == "__main__":
    tray = body(0).cut(body(T))
    cq.exporters.export(tray, "980-4603-000.step")
    bb = tray.val().BoundingBox()
    print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

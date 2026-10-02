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
FLOOR_Z = 5.8              # 凹み底面の高さ
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
    POCKETS.append((x, 73.3, 19.0, 45.0, 2.0))
# 4) 両側の縦通路と上端スロット（x=±70）
for s in (-1, 1):
    POCKETS.append((s * 70.0, 70.0, 19.4, 51.0, 2.5))      # 上端スロット
    POCKETS.append((s * 70.0, -11.0, 14.6, 154.0, 2.0))     # 縦通路
    for y in ROW_RC + [-7.5 + 33.0 * 2]:                    # 横腕（最上段を含む5段）
        POCKETS.append((s * 78.6, y, 31.9, 12.7, 2.5))
# 5) 下端の半開きクリップ凹み
for x in (-52.5, -17.5, 17.5, 52.5):
    POCKETS.append((x, -87.0, 16.0, 13.0, 2.0))

# クリップ（L字フック）: 図面の拡大図より。凹みの上縁の隅から内側へ張り出すつば状ブロック。
# 凹み中心から見て |x| 2.6〜7.95、|y| 4.3〜8.1（上面図）、z は上面から約6.3mm下(34.2)〜上面。
HOOK_X, HOOK_Y, HOOK_BOT = (2.6, 9.6), (4.3, 9.6), 34.2   # 壁側は凹みの縁より外まで伸ばして壁と一体にする
HOOKS = []   # (中心x, 中心y, sx, sy)
for x, y in SQUARES:
    for sx in (-1, 1):
        for sy in (-1, 1):
            HOOKS.append((x, y, sx, sy))
for x in (-52.5, -17.5, 17.5, 52.5):          # 下端の半開き凹みは図の上側(凹みの+Y側)の2隅のみ
    for sx in (-1, 1):
        HOOKS.append((x, -75.7, sx, -1))      # y=-85.3〜-80.0 に置く


def hook(x, y, sx, sy):
    x0, x1 = sorted((x + sx * HOOK_X[0], x + sx * HOOK_X[1]))
    y0, y1 = sorted((y + sy * HOOK_Y[0], y + sy * HOOK_Y[1]))
    return (cq.Workplane("XY").workplane(offset=HOOK_BOT)
            .center((x0 + x1) / 2, (y0 + y1) / 2).sketch().rect(x1 - x0, y1 - y0)
            .vertices().fillet(1.0).finalize().extrude(H - HOOK_BOT))


# B-B断面のランプ（傾斜底）: 上端スロット(Y+側)と下端の半開き凹み(Y-側)
# 各要素: (中心x, 半幅x, [(y, z), ...] ランプ上面の折れ線。最後の点が底面)
RAMPS = []
for x, w in ((-70.0, 19.4), (-35.0, 19.0), (0.0, 19.0), (35.0, 19.0), (70.0, 19.4)):
    RAMPS.append((x, w / 2 - 2.0, [(96.5, 38.0), (92.0, 24.0), (82.0, FLOOR_Z)]))
for x in (-52.5, -17.5, 17.5, 52.5):
    RAMPS.append((x, 6.5, [(-94.0, 36.0), (-80.5, FLOOR_Z)]))


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
        for x, y, sx, sy in HOOKS:
            s = s.union(hook(x, y, sx, sy))
    return s


if __name__ == "__main__":
    tray = body(0).cut(body(T))
    cq.exporters.export(tray, "980-4603-000.step")
    bb = tray.val().BoundingBox()
    print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

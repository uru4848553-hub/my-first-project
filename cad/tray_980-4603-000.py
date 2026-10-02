"""ITT Cannon 980-4603-000 XLM梱包トレー 3Dモデル（図面＋実物写真から読み取った近似）。
実行: python tray_980-4603-000.py  → 980-4603-000.step を出力
座標: 原点=トレー中心、X右、Y上（図面の上面図と同じ向き）、Z=0がフランジ面、Z=40.5が上面。

形状の構造（実物写真・A-A/B-B断面より）
  * 外周リム: 上面(z=40.5)の帯。外形は 210(底)→202(上) の抜き勾配つき R15。
  * 内側は低い「床」(z=FL_FIELD)。凹みではなく、床から柱が立っている。
  * 柱: 台形の柱(底18.5→上15.9)。上端6.5mmは十字形（四隅を段落ち＝クリップ/L字フック）。
        内側4列×4行=16本。上端・下端・左右の外周にも同じ柱が並び、リムとつながる。
  * 溝(低い部分 z=DIP): 長方形の窪み、上端スロット、左右の縦通路と横腕、下端の縦長凹み。
"""
import math
import cadquery as cq

# ---------------- 寸法 ----------------
W0, W1 = 210.0, 202.0          # 底面外形 / 上面外形
H = 40.5                       # 全高
T = 0.8                        # 板厚
R = 15.0                       # 外形コーナー R15
FL_FIELD = 6.3                 # 床(柱の根元)の高さ  (A-A断面)
DIP = 4.0                      # 溝の底の高さ        (A-A/B-B断面)
WALL_DRAFT = math.degrees(math.atan(((W0 - W1) / 2) / H))

PITCH = 35.0
PIL_X = [-52.5, -17.5, 17.5, 52.5]                  # 内側の柱の列
PIL_Y = {k: 8.3 + 33.0 * k for k in range(-3, 3)}   # 柱の行 k=-3(下端)..2(上端)
PIL_BASE, PIL_TOP = 18.5, 15.9                      # 柱の底/上端の幅
PIL_TAPER = math.degrees(math.atan(((PIL_BASE - PIL_TOP) / 2) / (H - FL_FIELD)))
SIDE_X = 87.5                                       # 左右の外周の柱の列

# 床の範囲（リムの内側）。上面の図面の外側の線
FIELD = dict(x0=-96.0, x1=96.0, y0=-95.0, y1=93.8, r=8.0)

# クリップ（上端6.5mmの十字形の四隅を段落ちにする）
# 柱の中心から |x| 2.9〜、|y| 4.3〜 の四隅。段の高さは上面から6.5mm下（B-B断面の寸法6.5）
RELIEF_X, RELIEF_Y, SHOULDER = (2.9, 12.0), (4.3, 12.0), 34.0

# ---------------- 溝（低い部分）一覧 ----------------
# (中心x, 中心y, 幅x, 幅y)  ※全て z=DIP まで。壁は垂直
DIPS = []
ROW_RC = [-7.5 + 33.0 * k for k in range(-2, 2)]     # 長方形の窪みの行
for x in (-35.0, 0.0, 35.0):
    for y in ROW_RC:
        DIPS.append((x, y, 15.4, 12.5))
    DIPS.append((x, 72.3, PITCH - PIL_BASE, 43.0))   # 上端スロット（柱の間）
TAB_H = 17.0
TAB_Y = [25.25 + 33.0 * i for i in range(-3, 2)]
TAB_Y[0] = -73.2
for s in (-1, 1):
    DIPS.append((s * 70.0, 72.3, PITCH - PIL_BASE, 43.0))      # 上端スロット
    DIPS.append((s * 70.45, -7.0, 15.5, 146.0))                # 縦通路 (y=-80〜66)
    DIPS.append((s * 69.75, -87.5, 19.7, 15.0))                # 通路下端の縦長凹み (L字の脚)
    for y in TAB_Y:                                            # 横腕
        DIPS.append((s * 79.35, y, 33.3, TAB_H))

# B-B断面: 上端スロット端部のランプ（壁→z≈24の5.3mm段→急な傾斜→底）
RAMPS = [(x, 7.0, [(95.0, 40.0), (93.0, 40.0), (91.1, 24.0), (85.8, 23.2), (79.5, DIP)])
         for x in (-70.0, -35.0, 0.0, 35.0, 70.0)]


# ---------------- 柱の一覧 ----------------
# (x0, x1, y0, y1, 段落ちにする隅[(sx, sy)...])  x0..y1 は底の範囲。リム側はリムの中まで伸ばす。
PILLARS = []
for k in range(-3, 3):
    yc = PIL_Y[k]
    ya, yb = yc - PIL_BASE / 2, yc + PIL_BASE / 2
    if k == 2:
        yb = 99.0                       # 上端: リムにつながる
    if k == -3:
        ya = -99.0                      # 下端: リムにつながる
    for x in PIL_X:
        if k == 2:
            corners = [(-1, -1), (1, -1)]
        elif k == -3:
            corners = [(-1, 1), (1, 1)]
        else:
            corners = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        PILLARS.append((x - PIL_BASE / 2, x + PIL_BASE / 2, ya, yb, (x, yc), corners))
    for s in (-1, 1):                   # 左右の外周の柱（外側はリムにつながる）
        xa, xb = sorted((s * (SIDE_X - PIL_BASE / 2), s * 99.0))
        if k == 2:
            corners = [(-s, -1)]
        elif k == -3:
            corners = [(-s, 1)]
        else:
            corners = [(-s, -1), (-s, 1)]
        PILLARS.append((xa, xb, ya, yb, (s * SIDE_X, yc), corners))


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").workplane(offset=z0).center((x0 + x1) / 2, (y0 + y1) / 2)
            .rect(x1 - x0, y1 - y0).extrude(z1 - z0))


def outer(d):
    top = H - d
    return (cq.Workplane("XY").workplane(offset=-1 if d else 0)
            .sketch().rect(W0 - 2 * d, W0 - 2 * d).vertices().fillet(R - d).finalize()
            .extrude(top + (1 if d else 0), taper=WALL_DRAFT))


def field(d):
    f = FIELD
    w, h = f["x1"] - f["x0"] + 2 * d, f["y1"] - f["y0"] + 2 * d
    cx, cy = (f["x0"] + f["x1"]) / 2, (f["y0"] + f["y1"]) / 2
    return (cq.Workplane("XY").workplane(offset=FL_FIELD - d).center(cx, cy)
            .sketch().rect(w, h).vertices().fillet(f["r"] + d).finalize()
            .extrude(H + 1 - FL_FIELD))


def dip(x, y, w, h, d):
    return box(x - w / 2 - d, x + w / 2 + d, y - h / 2 - d, y + h / 2 + d, DIP - d, FL_FIELD + 1)


def ramp(x, hw, pts, d):
    y_a, y_b = pts[0][0], pts[-1][0]
    poly = [(y_a, DIP - d - 1.0)] + [(y, z - d) for y, z in pts] + [(y_b, DIP - d - 1.0)]
    return (cq.Workplane("YZ").workplane(offset=x - hw + d).polyline(poly).close()
            .extrude(2 * (hw - d)))


def pillar(x0, x1, y0, y1, c, corners, d):
    """台形の柱。上端は十字形（四隅を z=SHOULDER まで落とす）。d=板厚オフセット"""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    z0 = FL_FIELD - d - 0.5
    body = (cq.Workplane("XY").workplane(offset=z0).center(cx, cy)
            .sketch().rect(x1 - x0 - 2 * d, y1 - y0 - 2 * d).vertices().fillet(2.5).finalize()
            .extrude(H - d - z0, taper=PIL_TAPER))
    for sx, sy in corners:
        xa, xb = sorted((c[0] + sx * (RELIEF_X[0] - d), c[0] + sx * RELIEF_X[1]))
        ya, yb = sorted((c[1] + sy * (RELIEF_Y[0] - d), c[1] + sy * RELIEF_Y[1]))
        body = body.cut(box(xa, xb, ya, yb, SHOULDER - d, H + 1))
    return body


def solid(d):
    """d=0: 外形ソリッド、d=T: 板厚ぶん内側のソリッド（下面は開放）"""
    s = outer(d).cut(field(d))
    for x, y, w, h in DIPS:
        s = s.cut(dip(x, y, w, h, d))
    for x, hw, pts in RAMPS:
        s = s.union(ramp(x, hw, pts, d))
    for x0, x1, y0, y1, c, corners in PILLARS:
        s = s.union(pillar(x0, x1, y0, y1, c, corners, d))
    # 柱がリムの外へはみ出さないよう外形で切り取る
    return s.intersect(outer(d))


if __name__ == "__main__":
    tray = solid(0).cut(solid(T))
    cq.exporters.export(tray, "980-4603-000.step")
    bb = tray.val().BoundingBox()
    print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

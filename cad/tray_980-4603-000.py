"""ITT Cannon 980-4603-000 XLM梱包トレー 3Dモデル（図面＋実物写真から読み取った近似）。
実行: python tray_980-4603-000.py           → 980-4603-000.step（板厚 t=0.8 の薄板。閉じた1つのソリッド）を出力
      python tray_980-4603-000.py --filled  → 参考: 中身の詰まったブロック版を出力（t=0.8 は無視される）
座標: 原点=トレー中心、X右、Y上（図面の上面図と同じ向き）、Z=0がフランジ面、Z=40.5が上面。

形状の構造（実物写真・A-A/B-B断面より）
  * 外周リム: 外壁は根元207→上面202、内壁は上面192→床182。上面の帯の幅は5。中空のテント形。
    根元に幅1.5・厚さ0.8の縁(つば)が出て、その外形が 210 (4-R15)。
  * 内側は低い「床」。床は3段（フランジ面から床の上面＝板の内側の面までの高さ。板は面の下に厚さ0.8）: 4（一番低い: 長方形の窪み・スロット・横腕）、
    6（〇: 柱の横のすき間、+2）、8（×: 柱の縦のすき間、+4）。B-B の補助線 z=4,6,8 と寸法 2,4,4。
  * 柱: 台形の柱(底19.5×20→段で15.5×16)。上端6.5mmは十字形（腕 6.5 と 10、四隅を段落ち＝クリップ/L字フック）。
        内側4列×4行=16本。上端・下端・左右の外周にも同じ柱が並び、リムとつながる。
  * 上端スロットの端だけ、B-B 断面のとおり 段(幅5, z=23.4) と 傾斜(長さ約10) がある。
"""
import math
import cadquery as cq

# ---------------- 寸法 ----------------
LIP_W = 210.0                  # 底の縁(つば)の外形  (4-R15)
W0, W1 = 207.0, 202.0          # 壁の根元の外形(210-縁) / 上面外形
FLOOR_W, TOP_IN_W = 182.0, 192.0   # リム内壁の床の高さでの幅 / 上面での幅  (5+192+5=202)
H = 40.5                       # 全高
T = 0.8                        # 板厚
R = 15.0                       # 縁の外形コーナー 4-R15
R_BASE = R - (LIP_W - W0) / 2   # 壁の根元のコーナーR（縁と同心）
# 床の高さ（フランジ面から床の上面まで。B-B の補助線と寸法 2, 4, 4）。板厚 t=0.8 は面の下側につく（下面は 3.2 / 5.2 / 7.2）
FLOOR = 4.0                    # 一番低い床（印のない場所: 長方形の窪み・スロット・横腕・縦通路下端・リムの足元）
LEVEL_O = 6.0                  # 〇: 柱の横のすき間（床+2）
LEVEL_X = 8.0                  # ×: 柱の縦のすき間（床+4）
FL_FIELD = FLOOR
PIL_REF_Z = LEVEL_X            # 柱の底幅(19.5)は×の帯の上面(z=8)での寸法。×の帯は柱の下までつながる
WALL_DRAFT = math.degrees(math.atan(((W0 - W1) / 2) / H))

PITCH = 35.0
PIL_X = [-52.5, -17.5, 17.5, 52.5]                  # 内側の柱の列
PIL_Y = {k: 8.2 + 33.0 * k for k in range(-3, 3)}   # 柱の行 k=-3(下端)..2(上端)。-8.3の行と半ピッチずれ
# 柱の寸法（A-A, B-B の寸法より）
#   X: 底19.5 → 段(z=34)で15.5（隙間は上端19.5・底15.5）。十字の腕の幅6.5（隙間28.5）。逃がしの幅4.5。
#   Y: 底20  → 段で16（隙間は段の下で17、上で23）。十字の腕の幅10（B-B の(10)）。逃がしの幅3。
PIL_BASE_X, PIL_BASE_Y = 19.5, 20.0
PIL_BASE = PIL_BASE_X              # 隙間(スロット幅など)の計算用: 35-19.5=15.5
ARM_X, ARM_Y = 6.5, 10.0           # 十字の腕の幅（Y方向に伸びる腕のX幅 / X方向に伸びる腕のY幅）
SIDE_X = 87.5                                       # 左右の外周の柱の列（A-A の(11.8): 96-(87.5-3.25)）
SHOULDER = 34.0                                     # 段の高さ（上面から6.5mm下。B-B の 6.5）
PIL_TAPER = math.degrees(math.atan(2.0 / (SHOULDER - PIL_REF_Z)))   # 底→段で片側2.0ずつ細くなる

# 床の範囲（リムの内側）。上面の図面の外側の線
FIELD = dict(x0=-96.0, x1=96.0, y0=-96.0, y1=96.0, r=8.0)   # 上面(z=40.5)での内側の縁。5+192+5
FIELD_TAPER = math.degrees(math.atan(((TOP_IN_W - FLOOR_W) / 2) / (H - FLOOR)))   # 内壁の傾き(≈7.8°)

# クリップ（上端6.5mmの十字形の四隅を段落ちにする）
# 柱の中心から |x|>=3.25（腕6.5）、|y|>=5（腕10）の四隅。段の高さは上面から6.5mm下
RELIEF_X, RELIEF_Y = (ARM_X / 2, 12.0), (ARM_Y / 2, 12.0)   # 逃がし: |x|>=3.25, |y|>=5.0

# ---------------- 床の段（〇・×）----------------
# 印のない場所は FLOOR（一番低い）。柱の列に沿って連続した帯（×=柱の列、〇=すき間の列）を床から立ち上げ、
# 窪み（長方形の窪み・横腕・スロット）を〇の帯へ傾斜つきで彫り込む。こうすると
#   ×の帯が柱の下までつながり、〇と×が角だけで接する所もできない。
STRIP_Y = 94.0                                        # 帯はリムの内側まで（リムの中に食い込ませて一体にする）
STRIPS = []                                           # (x0, x1, 高さ)
for xp in PIL_X:                                      # × (LEVEL_X): 柱の列。幅19.5（柱の底の幅）
    STRIPS.append((xp - PIL_BASE_X / 2, xp + PIL_BASE_X / 2, LEVEL_X))
Q_COLS = (-70.0, -35.0, 0.0, 35.0, 70.0)
Q_HALF = (PITCH - PIL_BASE_X) / 2                     # 7.75（柱どうしのすき間15.5の半分）
for xq in Q_COLS:                                     # 〇 (LEVEL_O): すき間の列
    STRIPS.append((xq - Q_HALF, xq + Q_HALF, LEVEL_O))

# 窪み（印なし）: Y方向の壁が傾斜。上端(〇の高さ)で幅17、底で幅12.6（B-B）。
PAD_TOP, PAD_FLOOR = 17.0, 12.6
PAD_ROWS = [-8.3 + 33.0 * j for j in range(-2, 3)]    # 窪みの行（B-B: C線から8.3、ピッチ33）
PADS = []                                             # (x0, x1, 行のy)
for xq in Q_COLS:
    if abs(xq) > 60:                                  # x=±70 の列は横腕(通路の幅15.5＋13.3)まで続く
        sg = 1 if xq > 0 else -1
        x0, x1 = sorted((sg * (xq * sg - Q_HALF), sg * 91.5))
    else:
        x0, x1 = xq - Q_HALF, xq + Q_HALF
    for yb in PAD_ROWS:
        PADS.append((x0, x1, yb))
# 窪みの行の外側: 上端スロット(y=60〜94)・下端の縦長凹み(y=-94〜-75)も床まで下げる（壁は垂直）
LOW_BOXES = []                                        # (x0, x1, y0, y1)
for xq in Q_COLS:
    LOW_BOXES.append((xq - Q_HALF, xq + Q_HALF, 60.0, STRIP_Y))
    LOW_BOXES.append((xq - Q_HALF, xq + Q_HALF, -STRIP_Y, -75.0))

# B-B断面: 上端スロット端部（拡大図より）
#   リム内壁(上面96→z=23.7で93.7) → 長さ5.2の平らな段(z=23.5) → 傾斜(長さ7、高さ約20) → 底(FLOOR)
#   段・傾斜はスロットの幅いっぱい（柱の壁の中まで）に付ける。
LEDGE_Z, LEDGE_Y0, LEDGE_LEN, RAMP_RUN = 23.5, 93.7, 5.2, 7.0
RAMPS = [(x, 10.0, [(97.0, LEDGE_Z), (LEDGE_Y0 - LEDGE_LEN, LEDGE_Z), (LEDGE_Y0 - LEDGE_LEN - RAMP_RUN, FLOOR)])
         for x in (-70.0, -35.0, 0.0, 35.0, 70.0)]


# ---------------- 柱の一覧 ----------------
# (x0, x1, y0, y1, 段落ちにする隅[(sx, sy)...])  x0..y1 は底の範囲。リム側はリムの中まで伸ばす。
PILLARS = []
for k in range(-3, 3):
    yc = PIL_Y[k]
    ya, yb = yc - PIL_BASE_Y / 2, yc + PIL_BASE_Y / 2
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
        PILLARS.append((x - PIL_BASE_X / 2, x + PIL_BASE_X / 2, ya, yb, (x, yc), corners))
    for s in (-1, 1):                   # 左右の外周の柱（外側はリムにつながる）
        xa, xb = sorted((s * (SIDE_X - PIL_BASE_X / 2), s * 99.0))
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
            .sketch().rect(W0 - 2 * d, W0 - 2 * d).vertices().fillet(R_BASE - d).finalize()
            .extrude(top + (1 if d else 0), taper=WALL_DRAFT))


def field(d):
    """リム内側の床の範囲。上面で192、床で182になるよう内壁を傾ける"""
    f = FIELD
    w, h = f["x1"] - f["x0"] + 2 * d, f["y1"] - f["y0"] + 2 * d
    return (cq.Workplane("XY").workplane(offset=H + 0.01)
            .sketch().rect(w, h).vertices().fillet(f["r"] + d).finalize()
            .extrude(-(H + 0.01 - (FL_FIELD - d)), taper=FIELD_TAPER))


def lip_solid():
    """底の縁(つば)をソリッドで: 外形210(R15)、厚さ0.8の板（壁の根元207の下も埋まる）"""
    return cq.Workplane("XY").sketch().rect(LIP_W, LIP_W).vertices().fillet(R).finalize().extrude(T)


def lip():
    """（薄板版）底の縁(つば): 外形210(R15)、壁の外側から出る幅1.5・厚さ0.8"""
    outer_ = (cq.Workplane("XY").sketch().rect(LIP_W, LIP_W).vertices().fillet(R).finalize().extrude(T))
    inner_ = (cq.Workplane("XY").workplane(offset=-1).sketch().rect(W0 - 2 * T, W0 - 2 * T)
              .vertices().fillet(R_BASE - T).finalize().extrude(T + 2))
    return outer_.cut(inner_)


R_PIL = 4.0                    # 柱の角のR。傾きで半径が縮んでも上端まで残る大きさ（小さいと円すいの先が尖って退化辺になる）
def strip(x0, x1, level, d):
    """床から立ち上げた帯（柱の列に沿って連続）。d=板厚オフセット"""
    return box(x0 + d, x1 - d, -STRIP_Y + d, STRIP_Y - d, FLOOR - d - 0.5, level - d)


def pad_cut(x0, x1, yb, d):
    """窪み: Y方向の壁が傾斜（上端17→底12.6）。帯の幅より少し広くして、帯の横の壁には触れない"""
    top = LEVEL_O + 1.0
    slope = (PAD_TOP - PAD_FLOOR) / 2 / (LEVEL_O - FLOOR)
    h0 = PAD_FLOOR / 2 + d
    hh = h0 + slope * (top - (FLOOR - d))
    poly = [(yb - hh, top), (yb + hh, top), (yb + h0, FLOOR - d), (yb - h0, FLOOR - d)]
    m = 1.0                                           # 帯より広げる量（空気を切るだけ）
    return (cq.Workplane("YZ").workplane(offset=x0 - m - d).polyline(poly).close().extrude(x1 - x0 + 2 * m + 2 * d))


def ramp(x, hw, pts, d):
    """スロット端のランプ下の材料（YZ断面を押し出し）。d=板厚オフセット"""
    y_a, y_b = pts[0][0], pts[-1][0]
    poly = [(y_a, FLOOR - d - 1.0)] + [(y, z - d) for y, z in pts] + [(y_b, FLOOR - d - 1.0)]
    return (cq.Workplane("YZ").workplane(offset=x - hw + d).polyline(poly).close()
            .extrude(2 * (hw - d)))


def pillar(x0, x1, y0, y1, c, corners, d):
    """台形の柱。上端は十字形（四隅を z=SHOULDER まで落とす）。d=板厚オフセット"""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    z0 = FL_FIELD - d - 0.5
    grow = 2 * (PIL_REF_Z - FLOOR + 0.5) * math.tan(math.radians(PIL_TAPER))   # 底の幅は z=PIL_REF_Z での寸法
    body = (cq.Workplane("XY").workplane(offset=z0).center(cx, cy)
            .sketch().rect(x1 - x0 - 2 * d + grow, y1 - y0 - 2 * d + grow).vertices().fillet(R_PIL).finalize()
            .extrude(H - d - z0, taper=PIL_TAPER))
    for sx, sy in corners:
        xa, xb = sorted((c[0] + sx * (RELIEF_X[0] - d), c[0] + sx * RELIEF_X[1]))
        ya, yb = sorted((c[1] + sy * (RELIEF_Y[0] - d), c[1] + sy * RELIEF_Y[1]))
        body = body.cut(box(xa, xb, ya, yb, SHOULDER - d, H + 1))
    return body


def solid(d):
    """d=0: 外形ソリッド、d=T: 板厚ぶん内側のソリッド（下面は開放）"""
    s = outer(d).cut(field(d))
    for x0, x1, level in STRIPS:
        if level == LEVEL_O:
            s = s.union(strip(x0, x1, level, d))
    for x0, x1, yb in PADS:
        s = s.cut(pad_cut(x0, x1, yb, d))
    for x0, x1, y0, y1 in LOW_BOXES:
        s = s.cut(box(x0 - d, x1 + d, y0 - d, y1 + d, FLOOR - d, LEVEL_X + 1))
    for x0, x1, level in STRIPS:
        if level == LEVEL_X:
            s = s.union(strip(x0, x1, level, d))
    for x, hw, pts in RAMPS:
        s = s.union(ramp(x, hw, pts, d))
    for x0, x1, y0, y1, c, corners in PILLARS:
        s = s.union(pillar(x0, x1, y0, y1, c, corners, d))
    # 柱がリムの外へはみ出さないよう外形で切り取る
    return s.intersect(outer(d))


if __name__ == "__main__":
    import sys
    if "--filled" in sys.argv:
        tray = solid(0).union(lip_solid())
        out = "980-4603-000_filled.step"
    else:
        tray = solid(0).cut(solid(T)).union(lip())     # 板厚 T=0.8 の薄板
        out = "980-4603-000.step"
    cq.exporters.export(tray, out)
    bb = tray.val().BoundingBox()
    print(out, "valid:", tray.val().isValid(), "solids:", tray.solids().size(), "shells:", len(tray.shells().vals()))
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

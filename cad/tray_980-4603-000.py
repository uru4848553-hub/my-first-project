"""ITT Cannon 980-4603-000 XLM梱包トレー 3Dモデル（図面＋実物写真から読み取った近似）。
実行: python tray_980-4603-000.py  → 980-4603-000.step を出力
座標: 原点=トレー中心、X右、Y上（図面の上面図と同じ向き）、Z=0がフランジ面、Z=40.5が上面。

形状の構造（実物写真・A-A/B-B断面より）
  * 外周リム: 中空のテント形。外壁は根元207→上面202、内壁は上面192→床182。上面の帯の幅は5。
    根元に幅1.5・厚さ0.8の縁(つば)が出て、その外形が 210 (4-R15)。
  * 内側は低い「床」(z=FL_FIELD)。凹みではなく、床から柱が立っている。
  * 柱: 台形の柱(底19.5×20→段で15.5×16)。上端6.5mmは十字形（腕 6.5 と 10、四隅を段落ち＝クリップ/L字フック）。
        内側4列×4行=16本。上端・下端・左右の外周にも同じ柱が並び、リムとつながる。
  * 溝(底 z=DIP): 上端スロット、左右の横腕(通路の幅を含む x=62.25〜91)、下端の縦長凹み、長方形の窪み。床より約2.3mm低い。
    縦通路そのものは床と同じ高さ。
    上端スロットの端だけ、B-B 断面のとおり 段(幅5, z=23.4) と 傾斜(長さ約10) がある。
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
# 床の高さ: B-B の寸法 6.5+30+4=40.5 と補助線 z=4,6,8（フランジ面から、板の下面）。上面(=この値)は板厚0.8を足す
FL_FIELD = 6.0 + 0.8           # 柱の根元の床（平らな部分）: 下面6 → 上面6.8
# （下面z=8の段＝柱の根元の縁は、位置が読み切れないため未反映）
DIP = 4.0 + 0.8                # 溝（スロット・横腕・長方形の窪み）の底: 下面4 → 上面4.8（床との段差は B-B の寸法 2）
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
PIL_TAPER = math.degrees(math.atan(2.0 / (SHOULDER - FL_FIELD)))   # 底→段で片側2.0ずつ細くなる

# 床の範囲（リムの内側）。上面の図面の外側の線
FIELD = dict(x0=-96.0, x1=96.0, y0=-96.0, y1=96.0, r=8.0)   # 上面(z=40.5)での内側の縁。5+192+5
FIELD_TAPER = math.degrees(math.atan(((TOP_IN_W - FLOOR_W) / 2) / (H - 3.8)))   # 内壁の傾き(≈7.8°)

# クリップ（上端6.5mmの十字形の四隅を段落ちにする）
# 柱の中心から |x|>=3.25（腕6.5）、|y|>=5（腕10）の四隅。段の高さは上面から6.5mm下
RELIEF_X, RELIEF_Y = (ARM_X / 2, 12.0), (ARM_Y / 2, 12.0)   # 逃がし: |x|>=3.25, |y|>=5.0

# ---------------- 溝（床より低い部分）----------------
# (中心x, 中心y, 幅x, 幅y)  壁は垂直。リム側は床の縁(±91)まで。
DIPS = []                                             # 壁が垂直な溝（スロット・通路下端）
DIPS_Y = []                                           # Y方向の壁が斜めな溝: 上端17 → 底12.6（長方形の窪み・横腕）
PAD_TOP, PAD_FLOOR = 17.0, 12.6                       # B-B: 上端の幅17 / 底(上面図の内側の線)12.6
ROW_RC = [-8.3 + 33.0 * k for k in range(-2, 2)]      # B-B: C線から8.3、ピッチ33
SLOT_Y0, SLOT_Y1 = 50.8, 91.0                         # 上端スロット（y=91 が床の縁）
for x in (-35.0, 0.0, 35.0):
    for y in ROW_RC:
        DIPS_Y.append((x, y, PITCH - PIL_BASE, PAD_TOP))                  # 長方形の窪み（X幅は柱の隙間15.5）
    DIPS.append((x, (SLOT_Y0 + SLOT_Y1) / 2, PITCH - PIL_BASE, SLOT_Y1 - SLOT_Y0))   # 上端スロット（柱の間 15.5）
TAB_H = 17.0
TAB_Y = [-8.3 + 33.0 * i for i in range(-2, 3)]                 # 上端から43.3、下端から26.8 の線 (B-B)
for s_ in (-1, 1):
    DIPS.append((s_ * 70.0, (SLOT_Y0 + SLOT_Y1) / 2, PITCH - PIL_BASE, SLOT_Y1 - SLOT_Y0))   # 上端スロット
    # 縦通路(x=62.25〜77.75)は床と同じ高さの平らな帯。溝ではない（A-A: 通路の床は柱の根元と同じ高さ）
    DIPS.append((s_ * 70.0, -85.5, 15.5, 11.0))                   # 通路下端の縦長凹み (L字の脚。y=-91〜-80)
    for y in TAB_Y:                                               # 横腕: 通路の幅(15.5)＋13.3 = x=62.25〜91 が一段低い（右の縁 x=77.75 に段）
        DIPS_Y.append((s_ * 76.625, y, 28.75, PAD_TOP))

# B-B断面: 上端スロット端部（拡大図より）
#   リム内壁(上面96→z=23.7で93.7) → 長さ5.2の平らな段(z=23.5) → 傾斜(長さ7、高さ約20) → 底(DIP)
#   段・傾斜はスロットの幅いっぱい（柱の壁の中まで）に付ける。
LEDGE_Z, LEDGE_Y0, LEDGE_LEN, RAMP_RUN = 23.5, 93.7, 5.2, 7.0
RAMPS = [(x, 10.0, [(97.0, LEDGE_Z), (LEDGE_Y0 - LEDGE_LEN, LEDGE_Z), (LEDGE_Y0 - LEDGE_LEN - RAMP_RUN, DIP)])
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


def lip():
    """底の縁(つば): 外形210(R15)、壁の外側から出る幅1.5・厚さ0.8"""
    outer_ = (cq.Workplane("XY").sketch().rect(LIP_W, LIP_W).vertices().fillet(R).finalize().extrude(T))
    inner_ = (cq.Workplane("XY").workplane(offset=-1).sketch().rect(W0 - 2 * T, W0 - 2 * T)
              .vertices().fillet(R_BASE - T).finalize().extrude(T + 2))
    return outer_.cut(inner_)


def dip(x, y, w, h, d):
    return box(x - w / 2 - d, x + w / 2 + d, y - h / 2 - d, y + h / 2 + d, DIP - d, FL_FIELD + 1)


def dip_y(x, y, w, h, d):
    """Y方向の壁が斜めな溝。上端(z=FL_FIELD)で幅h、底(z=DIP)で幅 PAD_FLOOR"""
    h1 = h / 2 + d
    h0 = h1 - (PAD_TOP - PAD_FLOOR) / 2
    slope = (h1 - h0) / (FL_FIELD - (DIP - d))
    top = FL_FIELD + 1.0
    hh = h1 + slope * 1.0
    poly = [(y - hh, top), (y + hh, top), (y + h0, DIP - d), (y - h0, DIP - d)]
    return (cq.Workplane("YZ").workplane(offset=x - w / 2 - d).polyline(poly).close().extrude(w + 2 * d))


def ramp(x, hw, pts, d):
    """スロット端のランプ下の材料（YZ断面を押し出し）。d=板厚オフセット"""
    y_a, y_b = pts[0][0], pts[-1][0]
    poly = [(y_a, DIP - d - 1.0)] + [(y, z - d) for y, z in pts] + [(y_b, DIP - d - 1.0)]
    return (cq.Workplane("YZ").workplane(offset=x - hw + d).polyline(poly).close()
            .extrude(2 * (hw - d)))


def pillar(x0, x1, y0, y1, c, corners, d):
    """台形の柱。上端は十字形（四隅を z=SHOULDER まで落とす）。d=板厚オフセット"""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    z0 = FL_FIELD - d - 0.5
    grow = 2 * 0.5 * math.tan(math.radians(PIL_TAPER))     # 0.5mm下から始めるぶん、床の高さで寸法どおりになるよう広げる
    body = (cq.Workplane("XY").workplane(offset=z0).center(cx, cy)
            .sketch().rect(x1 - x0 - 2 * d + grow, y1 - y0 - 2 * d + grow).vertices().fillet(2.5).finalize()
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
    for x, y, w, h in DIPS_Y:
        s = s.cut(dip_y(x, y, w, h, d))
    for x, hw, pts in RAMPS:
        s = s.union(ramp(x, hw, pts, d))
    for x0, x1, y0, y1, c, corners in PILLARS:
        s = s.union(pillar(x0, x1, y0, y1, c, corners, d))
    # 柱がリムの外へはみ出さないよう外形で切り取る
    return s.intersect(outer(d))


if __name__ == "__main__":
    tray = solid(0).cut(solid(T)).union(lip())
    cq.exporters.export(tray, "980-4603-000.step")
    bb = tray.val().BoundingBox()
    print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

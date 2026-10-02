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

# クリップ(コーナーの突起): 角形凹みの内側4隅に立てる小柱
POST, POST_TOP = 3.5, 36.0
POSTS = [(x + sx * 5.9, y + sy * 5.9) for x, y in SQUARES for sx in (-1, 1) for sy in (-1, 1)]


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
    p = POST - 2 * d
    for x, y in POSTS:
        post = (cq.Workplane("XY").workplane(offset=FLOOR_Z - d - 0.5)
                .center(x, y).rect(p, p).extrude(POST_TOP - d - FLOOR_Z + d + 0.5))
        s = s.union(post)
    return s


if __name__ == "__main__":
    tray = body(0).cut(body(T))
    cq.exporters.export(tray, "980-4603-000.step")
    bb = tray.val().BoundingBox()
    print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
    print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

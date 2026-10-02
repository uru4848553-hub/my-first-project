"""ITT Cannon 980-4603-000 XLM梱包トレー 簡易3Dモデル（図面からの近似）。
実行: python tray_980-4603-000.py  → 980-4603-000.step を出力
"""
import math
import cadquery as cq

W0, W1 = 210.0, 202.0      # 底面(フランジ面)外形 / 上面外形
H = 40.5                   # 全高
T = 0.8                    # 板厚
R = 15.0                   # 外形コーナー R15
PITCH_X, PITCH_Y = 35.0, 33.0
NX = NY = 5
POCKET_X, POCKET_Y = 28.5, 26.5   # 凹み上端寸法（リブ幅6.5）
FLOOR_Z = 5.8                     # 凹み底面の高さ
POCKET_DRAFT = math.degrees(math.atan(4.5 / (H - FLOOR_Z)))
WALL_DRAFT = math.degrees(math.atan(((W0 - W1) / 2) / H))


def body(d):
    """d=0: 外形ソリッド、d=T: 板厚ぶん内側のソリッド（下面は開放）"""
    top = H - d
    s = (cq.Workplane("XY").workplane(offset=-1 if d else 0)
         .sketch().rect(W0 - 2 * d, W0 - 2 * d).vertices().fillet(R - d).finalize()
         .extrude(top + (1 if d else 0), taper=WALL_DRAFT))
    for i in range(NX):
        for j in range(NY):
            x = (i - (NX - 1) / 2) * PITCH_X
            y = (j - (NY - 1) / 2) * PITCH_Y
            pocket = (cq.Workplane("XY").workplane(offset=top + 0.01)
                      .center(x, y).rect(POCKET_X + 2 * d, POCKET_Y + 2 * d)
                      .extrude(-(top + 0.01 - (FLOOR_Z - d)), taper=POCKET_DRAFT))
            s = s.cut(pocket)
    return s


tray = body(0).cut(body(T))
cq.exporters.export(tray, "980-4603-000.step")
bb = tray.val().BoundingBox()
print("valid:", tray.val().isValid(), "solids:", tray.solids().size())
print("bbox: %.1f x %.1f x %.1f" % (bb.xlen, bb.ylen, bb.zlen), "volume mm3: %.0f" % tray.val().Volume())

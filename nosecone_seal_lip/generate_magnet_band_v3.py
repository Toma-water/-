#!/usr/bin/env python3
"""磁石バンド v3: 新しいノーズコーン外形(曲線のみ) + M3ネジ穴。CAD(STEP)+STL出力。

ユーザー提供の新スケッチに従う:
- リム外形 = 1/4楕円の曲線のみ(直線スカート無し)。高さ135.60 × 半幅45.60。
  バンドが沿うのはこの曲線を左右対称に合わせた半楕円(先端で滑らかにつながる)。
- 片側の半割にだけ取り付ける。段差(リップ)無し = 合わせ面はフラット。
- 固定はM3ネジ → Φ3.4の貫通穴を壁に6か所(くぎ固定は廃止)。
- 磁石座(内向きの小さな突起)5か所は前版と同じ考え方:
  座の上面 = 合わせ面-3mm。厚さ3mmの磁石を貼ると磁石面がツライチ。
  相手側の半割には磁石(極性逆) or 鉄ワッシャーを直接接着する。

cadqueryでソリッドを構築し、同一モデルから STEP(CAD) と STL を出力する。
出力座標系: ノーズコーン軸=+Y(先端が+Y)。Z=0が印刷ベッド面、Z=8が合わせ面。
"""

import numpy as np

# ---------------- 外形パラメータ (mm) ----------------
A_LEN = 135.60   # 曲線の全長方向(軸方向)の長さ = スケッチの高さ
B_RAD = 45.60    # 半幅(半径) = スケッチの幅
# ---------------- バンドパラメータ (mm) ----------------
GLUE_GAP = 0.2   # 外形線→バンド外面のオフセット(接着剤層)
THICKNESS = 2.4  # 肉厚
GLUE_H = 8.0     # バンド高さ(=接着ゾーン)。上面が合わせ面
INNER = GLUE_GAP + THICKNESS
# ---------------- 磁石座パラメータ (mm) ----------------
MAG_T = 3.0        # 磁石の厚み(座上面 = 合わせ面 - MAG_T)
MAG_POCKET = 10.8  # 磁石の窓(φ10ディスク + 遊び)
RIM_TH = 1.2       # 位置決め縁の肉厚
RIM_H = 1.5        # 位置決め縁の高さ
OVERLAP = 1.6      # 壁への食い込み(先端の曲率でも密着するよう1.6)
PAD_W = MAG_POCKET + 2 * RIM_TH   # 座の幅(接線方向) 13.2
PAD_D = MAG_POCKET + 2 * RIM_TH   # 座の奥行(内向き) 13.2
PAD_TOP = GLUE_H - MAG_T          # 座の上面 z=5
B_START = INNER - OVERLAP         # 座の付け根 u=1.0
BOSS_FRACS = [0.10, 0.30, 0.50, 0.70, 0.90]  # 弧長方向の配置(0.5=先端)
# ---------------- ネジ穴パラメータ (mm) ----------------
HOLE_D = 3.4       # M3通し穴(3.2〜3.4指定の上限側)
HOLE_Z = 4.0       # 穴中心の高さ(接着ゾーン中央)
HOLE_FRACS = [0.045, 0.20, 0.40, 0.60, 0.80, 0.955]
# ------------------------------------------------------


def ellipse_frames(fracs):
    """弧長分率fracsの位置の (点P, 接線t, 内向き法線n) を返す。

    パス: P(th) = (A cos th, B sin th), th∈[-90°, +90°]。
    始点(0,-B) → 先端(A,0) → 終点(0,+B)。内向き=進行方向左。
    """
    th = np.linspace(-np.pi / 2, np.pi / 2, 20001)
    P = np.stack([A_LEN * np.cos(th), B_RAD * np.sin(th)], axis=1)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    frames = []
    for f in fracs:
        i = int(np.argmin(np.abs(s - f * s[-1])))
        t = np.array([-A_LEN * np.sin(th[i]), B_RAD * np.cos(th[i])])
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])  # 内向き(進行方向左)
        frames.append((P[i], t, n))
    return frames, s[-1]


def build():
    import cadquery as cq

    # --- パス: 半楕円ワイヤ ---
    path_wire = cq.Wire.makeEllipse(
        A_LEN, B_RAD, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1),
        cq.Vector(1, 0, 0), angle1=-90.0, angle2=90.0,
        rotation_angle=0.0, closed=False,
    )
    path = cq.Workplane("XY", obj=path_wire)

    # --- バンド本体: 矩形断面(2.4×8)をパスに沿って掃引 ---
    # 始点(0,-B)での断面: YZ平面上, 内向き=+y
    prof_center_y = -B_RAD + GLUE_GAP + THICKNESS / 2.0
    band = (
        cq.Workplane("YZ")
        .center(prof_center_y, GLUE_H / 2.0)
        .rect(THICKNESS, GLUE_H)
        .sweep(path, isFrenet=True)
    )

    boss_frames, total_len = ellipse_frames(BOSS_FRACS)
    hole_frames, _ = ellipse_frames(HOLE_FRACS)
    print(f"path length: {total_len:.1f} mm")

    # --- 磁石座: pad + 位置決め縁(トレイ) ---
    for P0, t, n in boss_frames:
        psi = np.degrees(np.arctan2(n[1], n[0]))  # 内向き法線の角度
        base = cq.Vector(P0[0] + B_START * n[0], P0[1] + B_START * n[1], 0)

        pad = cq.Workplane("XY").box(
            PAD_W, PAD_D, PAD_TOP, centered=(True, False, False))
        ring = cq.Workplane("XY").box(
            PAD_W, PAD_D, RIM_H, centered=(True, False, False)
        ).translate((0, 0, PAD_TOP))
        pocket = cq.Workplane("XY").box(
            MAG_POCKET, MAG_POCKET, RIM_H + 1.0, centered=(True, False, False)
        ).translate((0, (PAD_D - MAG_POCKET) / 2.0, PAD_TOP))
        boss = pad.union(ring.cut(pocket))
        # 局所+y → 内向き法線n に回転して配置
        boss = boss.rotate((0, 0, 0), (0, 0, 1), psi - 90.0).translate(base)
        band = band.union(boss)

    # --- M3ネジ穴(Φ3.4, 壁を法線方向に貫通) ---
    for P0, t, n in hole_frames:
        start = cq.Vector(P0[0] - 2.0 * n[0], P0[1] - 2.0 * n[1], HOLE_Z)
        cyl = cq.Solid.makeCylinder(
            HOLE_D / 2.0, 8.0, start, cq.Vector(n[0], n[1], 0))
        band = band.cut(cq.Workplane("XY", obj=cyl))

    # --- 縦長(ポートレート)向きに回転: 先端を+Yへ ---
    band = band.rotate((0, 0, 0), (0, 0, 1), 90.0)
    solid = band.val()
    assert solid.isValid(), "BREP solid is not valid"
    bb = solid.BoundingBox()
    print(f"bbox: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, "
          f"volume {solid.Volume()/1000:.1f} cm^3")
    return band


def main():
    from pathlib import Path

    import cadquery as cq

    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    band = build()
    cq.exporters.export(band, str(out / "nosecone_magnet_band_v3.step"))
    cq.exporters.export(
        band, str(out / "nosecone_magnet_band_v3.stl"),
        tolerance=0.02, angularTolerance=0.15)
    print("wrote", out / "nosecone_magnet_band_v3.step")
    print("wrote", out / "nosecone_magnet_band_v3.stl")


if __name__ == "__main__":
    main()

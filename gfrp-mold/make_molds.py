#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GFRP ボディ用 雄型(マンドレル)CAD生成スクリプト
- 完成ボディ内径(GFRP内径) = 90mm  -> 型の外径 = 90mm (R=45)
- 必要高さ 60mm + 余裕 20mm        -> 型高さ = 80mm
GFRP を型の外側に巻いて硬化させ、型を抜く。
3案を生成して STL で出力する(Bambu Studio にそのままインポート可 / 単位mm)。

  案1  breakaway   : 壊して剥がす薄肉カップ(内側に割れ起点のVノッチ)
  案2  taper       : テーパー(抜き勾配)付きマンドレル + ベースフランジ
  案3  collapsible : 中子(センターキー)+ 3分割セグメントの組立コラプシブル型
"""
import os
import numpy as np
import trimesh
from shapely.geometry import Polygon

# ---- 基本寸法 (mm) ----
D_INNER   = 90.0          # GFRP 内径 = 型外径
R_OUT     = D_INNER / 2   # 45.0
H_BODY    = 60.0          # 完成品狙い高さ
H_MARGIN  = 40.0          # 余裕(上端トリミング代)
H_MOLD    = 100.0         # 型高さ = 100mm (高さ方向100mm指定)
SECT      = 256           # 円周分割(滑らかさ)

OUT = os.path.join(os.path.dirname(__file__), "stl")
os.makedirs(OUT, exist_ok=True)


def revolve(profile):
    """profile=[[r,z],...] を Z 軸回転して watertight ソリッドを作る"""
    m = trimesh.creation.revolve(np.array(profile, dtype=float), sections=SECT)
    m.merge_vertices()
    return m


def save(mesh, name):
    mesh.rezero  # noop, keep modeled coords
    path = os.path.join(OUT, name)
    mesh.export(path)
    wt = mesh.is_watertight
    print(f"  {name:32s} watertight={wt}  vol={mesh.volume/1000:8.2f} cm^3  "
          f"bbox={np.round(mesh.extents,1).tolist()}")
    if not wt:
        print("    !! WARNING: not watertight")
    return mesh


# =====================================================================
# 案1: breakaway (壊して剥がす薄肉カップ)
# =====================================================================
def make_breakaway():
    wall   = 2.5          # 薄肉(クラッシュしやすい)
    base_t = 4.0          # 底/フランジ厚
    fl_r   = R_OUT + 10   # フランジ外径 110
    ri     = R_OUT - wall # 内壁 42.5
    prof = [
        [0,      0],
        [fl_r,   0],
        [fl_r,   base_t],
        [R_OUT,  base_t],
        [R_OUT,  H_MOLD],
        [ri,     H_MOLD],
        [ri,     base_t],
        [0,      base_t],
    ]
    cup = revolve(prof)

    # 内壁に割れ起点の縦Vノッチを 6本(壁を ~1mm まで薄くする)
    cutters = []
    n_notch = 6
    notch_depth = 1.5     # 材料側へ削り込む量(残り壁 ~1.0mm)
    notch_w     = 1.2     # 周方向幅
    box = trimesh.creation.box(extents=[notch_depth + 1.0, notch_w, H_MOLD - base_t + 2])
    for i in range(n_notch):
        a = np.deg2rad(i * 360.0 / n_notch)
        c = box.copy()
        # 箱中心を内壁付近に配置(外端が R_OUT - wall + notch_depth まで入る)
        rc = ri + notch_depth - (notch_depth + 1.0) / 2 + 0.5
        T = trimesh.transformations.translation_matrix(
            [rc * np.cos(a), rc * np.sin(a), base_t + (H_MOLD - base_t) / 2])
        Rz = trimesh.transformations.rotation_matrix(a, [0, 0, 1])
        c.apply_transform(trimesh.transformations.concatenate_matrices(T, Rz))
        cutters.append(c)
    notches = trimesh.util.concatenate(cutters)
    cup = trimesh.boolean.difference([cup, notches])
    cup.merge_vertices()
    return cup


# =====================================================================
# 案2: taper (抜き勾配付きマンドレル + フランジ)
# =====================================================================
def make_taper():
    draft_deg = 1.0                       # 片側勾配
    base_t = 4.0
    fl_r   = R_OUT + 10                   # フランジ 110
    top_r  = R_OUT - H_MOLD * np.tan(np.deg2rad(draft_deg))  # ~43.6
    # 中空シェル(壁4mm)+ 上面閉じ + 引抜き用センター穴(下から rod)
    wall = 4.0
    prof = [
        [0,            0],
        [fl_r,         0],
        [fl_r,         base_t],
        [R_OUT,        base_t],
        [top_r,        H_MOLD],            # 外側テーパー(上ほど細い=上に抜ける)
        [0,            H_MOLD],            # 上面中心(閉じ)
        [0,            H_MOLD - 3],        # 上面厚3
        # 内側を中空化(壁4mm相当を残してくり抜き)
        [top_r - wall, H_MOLD - 3],
        [R_OUT - wall, base_t + 0.0],
        [0,            base_t],
    ]
    return revolve(prof)


# =====================================================================
# 案3 (改): keystone collapsible
#   - 外周は隙間ゼロで突き合わせる真円筒φ90(真空引き対応)
#   - 中央テーパー穴にセンターキー(中子)を入れ、内側から支えて
#     真空圧で潰れないようにする
#   - 抜き手順: センターキー上抜き → キーストーン上抜き →
#     残り3セグメントを内側へ寄せて抜く
# =====================================================================
BORE_R0   = 12.0          # 中心テーパー穴 下半径
BORE_R1   = 20.0          # 中心テーパー穴 上半径
KEY_CL    = 0.20          # センターキーのはめあいクリアランス(片側)
KEYSTONE  = 60.0          # キーストーンの開き角(度)


def _bore_tube():
    """外径φ90 straight・中心テーパー穴(下BORE_R0 -> 上BORE_R1)のチューブ"""
    prof = [
        [BORE_R0, 0],
        [R_OUT,   0],
        [R_OUT,   H_MOLD],
        [BORE_R1, H_MOLD],
        [BORE_R0, 0],          # 軸に接しない環状断面なので明示的に閉じる
    ]
    return revolve(prof)


def _wedge(angle0_deg, angle1_deg, r=R_OUT + 6, h=H_MOLD + 2):
    """原点中心の扇形プリズム(z=0..h)。隙間ゼロで突き合わせる用。"""
    pts = [[0, 0]]
    for a in np.linspace(np.deg2rad(angle0_deg), np.deg2rad(angle1_deg), 64):
        pts.append([r * np.cos(a), r * np.sin(a)])
    poly = Polygon(pts)
    return trimesh.creation.extrude_polygon(poly, height=h)


def _cut(tube, a0, a1):
    s = trimesh.boolean.intersection([tube, _wedge(a0, a1)])
    s.merge_vertices()
    return s


def make_collapsible_parts():
    """keystone + 3 segments を返す(全て隙間ゼロ・合計360°)"""
    tube = _bore_tube()
    half = KEYSTONE / 2.0           # 30
    # キーストーン: -30..+30
    keystone = _cut(tube, -half, half)
    # 引抜き用 φ5 穴(上端トリミング代の範囲内, z=H_MOLD-18..H_MOLD)
    hole = trimesh.creation.cylinder(radius=2.5, height=22, sections=48)
    hole.apply_translation([32 * np.cos(0), 32 * np.sin(0), H_MOLD - 6])
    keystone = trimesh.boolean.difference([keystone, hole]); keystone.merge_vertices()
    # 残り300°を3等分(100°ずつ)
    rest0, rest1 = half, 360.0 - half      # 30 .. 330
    span = (rest1 - rest0) / 3.0           # 100
    segs = [_cut(tube, rest0 + i * span, rest0 + (i + 1) * span) for i in range(3)]
    return keystone, segs


def make_collapsible_key():
    """センターキー(中子): テーパー嵌合 + 引抜きノブ。真空圧をこれが受ける。"""
    prof = [
        [0,                0],
        [BORE_R0 - KEY_CL, 0],
        [BORE_R1 - KEY_CL, H_MOLD],
        [8,                H_MOLD],
        [8,                H_MOLD + 18],     # 引抜きノブ
        [0,                H_MOLD + 18],
    ]
    return revolve(prof)


def make_collapsible_base():
    """位置決めベースプレート: 外周リップでセグメント底を真円に揃える + 中心座"""
    prof = [
        [0,        0],
        [R_OUT+3,  0],          # 外径φ96
        [R_OUT+3,  8],          # 外周リップ(高さ8: セグメント底外周を保持)
        [R_OUT,    8],
        [R_OUT,    5],          # プレート上面 z5(ここにセグメントが立つ)
        [BORE_R0,  5],
        [BORE_R0,  4],          # 中心 1mm ザグリ(キー底の座)
        [0,        4],
    ]
    return revolve(prof)


# =====================================================================
if __name__ == "__main__":
    print(f"GFRP body mold  外径={D_INNER}mm  高さ={H_MOLD}mm (狙い{H_BODY}+余裕{H_MARGIN})")
    print("[案1] breakaway")
    save(make_breakaway(), "1_breakaway_mandrel.stl")

    print("[案2] taper")
    save(make_taper(), "2_taper_mandrel.stl")

    print("[案3] keystone collapsible (隙間ゼロ・真円筒・真空対応)")
    keystone, segs = make_collapsible_parts()
    save(keystone, "3_collapsible_keystone.stl")
    for i, s in enumerate(segs, 1):
        save(s, f"3_collapsible_segment_{i}of3.stl")
    save(make_collapsible_key(),  "3_collapsible_center_key.stl")
    save(make_collapsible_base(), "3_collapsible_base_plate.stl")
    print("done ->", OUT)

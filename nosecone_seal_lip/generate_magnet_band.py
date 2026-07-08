#!/usr/bin/env python3
"""磁石式(作り直し版): バンド本体 + 内向きの小さな磁石座(突起)。

以前の独立タブ(nosecone_magnet_tab.stl)を置き換える。
v1のバンド本体(接着ゾーン)をベースに、その内面に「内向きに少しだけ
出っ張った」磁石座を数か所つけたもの。

★重要な設計判断: 磁石版は「1つのSTLを両半割に左右反転で使う」前提なので、
  v1のリップ(差し込み舌)は付けない。リップが両側にあると閉じたときに互いに
  ぶつかるため。代わりに合わせ面(z=GLUE_H=8)でフラットに突き合わせ、
  気密はこの平らなリム面に貼るスポンジテープで確保する。保持は磁石が担う。

磁石座(突起)の断面イメージ (u=内向き距離, z=高さ, z=0が底):

   z
   ↑         ← 合わせ面(GLUE_H=8)でフラットに突き合わせ
 8 ┤██ ─────────────── リム面(スポンジテープで気密)
   │██                ┌── 磁石(例 φ10×3)を接着 ──┐
 5 ┤██  ←pad上面 ──── │===========================│  ← z=5..8
   │██ ┌──────────────┴───────────────────────┐ 縁(位置決め)
   │██ │           磁石座 (pad)                │
 0 ┤██ └────────────────────────────────────┘
   壁                突起 約13mm

- 磁石は +z(合わせ面)を向く。対向する半割の磁石と面接触して閉じる。
- 突起の張り出しは内向き約13mm・幅13mmと小さめ → パラシュート放出の邪魔をしない。
- 両半割とも同じSTLを印刷し、左右反転して取り付ける。
  ★磁石の極性は2つの半割で逆にすること(N面とS面が向き合うように)。
- 気密シールも欲しい場合は v1(nosecone_seal_lip_band.stl)を固定側にだけ使い、
  この磁石バンドは相手側に使う、という組み合わせも可。
"""

import numpy as np

from generate_seal_lip import (
    GLUE_GAP,
    GLUE_H,
    THICKNESS,
    OUT_DIR,
    inward_normals,
    load_path,
    orient_outward,
    rotate_portrait,
    write_stl,
)
from generate_snap_and_magnet import check_mesh, sweep_var, triangulate  # noqa: F401

# ---------------- 磁石座パラメータ (mm) ----------------
MAG_T = 3.0            # 磁石の厚み(これに合わせて座の高さが決まる)
MAG_POCKET = 10.8      # 磁石のはまる窓(φ10ディスク or 10角ブロック + 遊び)
RIM_TH = 1.2           # 位置決め縁の肉厚
RIM_H = 1.5            # 位置決め縁の高さ
OVERLAP = 1.0          # 壁への食い込み量(融着のため)
N_MAGNETS = 5          # 磁石の数(先端1 + 左右2ずつ)
POS_FRACTIONS = [0.10, 0.30, 0.50, 0.70, 0.90]  # 弧長方向の配置(0.5=先端)
# 導出
INNER = GLUE_GAP + THICKNESS      # 接着ゾーン内面 u=2.6
PAD_TOP = GLUE_H - MAG_T          # 座の上面 z=5.0 (磁石を載せると z=8=合わせ面)
PAD_W = MAG_POCKET + 2 * RIM_TH   # 座の幅(接線方向) 13.2
PAD_D = MAG_POCKET + 2 * RIM_TH   # 座の奥行(内向き)  13.2
B_START = INNER - OVERLAP         # 座の付け根 u (壁に食い込む) = 1.6
# --------------------------------------------------------


def make_box(a0, a1, b0, b1, z0, z1, P0, t, n):
    """局所枠(t=接線, n=内向き法線)で軸平行ボックスを作り、外向きに整える。"""
    def V(a, b, z):
        return [P0[0] + b * n[0] + a * t[0],
                P0[1] + b * n[1] + a * t[1], z]

    c = {(i, j, k): V(a, b, z)
         for i, a in ((0, a0), (1, a1))
         for j, b in ((0, b0), (1, b1))
         for k, z in ((0, z0), (1, z1))}
    quads = [
        (c[0, 0, 0], c[1, 0, 0], c[1, 1, 0], c[0, 1, 0]),  # z0
        (c[0, 0, 1], c[0, 1, 1], c[1, 1, 1], c[1, 0, 1]),  # z1
        (c[0, 0, 0], c[0, 0, 1], c[1, 0, 1], c[1, 0, 0]),  # b0
        (c[0, 1, 0], c[1, 1, 0], c[1, 1, 1], c[0, 1, 1]),  # b1
        (c[0, 0, 0], c[0, 1, 0], c[0, 1, 1], c[0, 0, 1]),  # a0
        (c[1, 0, 0], c[1, 0, 1], c[1, 1, 1], c[1, 1, 0]),  # a1
    ]
    tris = []
    for p, q, r, s in quads:
        tris.append((p, q, r))
        tris.append((p, r, s))
    tris, _ = orient_outward(np.array(tris, dtype=float))
    return tris


def make_boss(P0, t, n):
    """磁石座1個: pad(下の塊) + 位置決め縁4枚。ボックスの集合を返す。"""
    hw = PAD_W / 2.0
    b_end = B_START + PAD_D
    # 磁石窓を座の中央に置く
    pk_b0 = B_START + (PAD_D - MAG_POCKET) / 2.0
    pk_b1 = pk_b0 + MAG_POCKET
    boxes = [make_box(-hw, hw, B_START, b_end, 0.0, PAD_TOP, P0, t, n)]
    # 縁(トレイ): 左右 + 前後
    ztop = PAD_TOP + RIM_H
    boxes.append(make_box(-hw, -MAG_POCKET / 2, B_START, b_end, PAD_TOP, ztop, P0, t, n))
    boxes.append(make_box(MAG_POCKET / 2, hw, B_START, b_end, PAD_TOP, ztop, P0, t, n))
    boxes.append(make_box(-MAG_POCKET / 2, MAG_POCKET / 2, B_START, pk_b0, PAD_TOP, ztop, P0, t, n))
    boxes.append(make_box(-MAG_POCKET / 2, MAG_POCKET / 2, pk_b1, b_end, PAD_TOP, ztop, P0, t, n))
    for i, b in enumerate(boxes):
        check_mesh(b, f"boss_box_{i}")
    return boxes


def boss_frames(path, normals):
    """配置分率から各磁石座の(中心点, 接線, 内向き法線)を返す。"""
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    frames = []
    for f in POS_FRACTIONS:
        i = int(np.argmin(np.abs(s - f * total)))
        frames.append((path[i], tang[i], normals[i]))
    return frames


def rect_profile(_w=0.0):
    """磁石バンド本体の断面。接着ゾーンのみの長方形(リップ無し)。"""
    return np.array([
        (GLUE_GAP, 0.0),     # 外面・底
        (GLUE_GAP, GLUE_H),  # 外面・合わせ面(リム)
        (INNER, GLUE_H),     # 内面・合わせ面(リム)
        (INNER, 0.0),        # 内面・底
    ])


def main():
    OUT_DIR.mkdir(exist_ok=True)
    path = load_path()
    normals = inward_normals(path)

    # 本体バンド(v1と同一形状)
    band = sweep_var(path, normals, rect_profile, np.zeros(len(path)))
    band, _ = orient_outward(band)
    check_mesh(band, "magnet band body")

    # 磁石座を追加
    parts = [band]
    for P0, t, n in boss_frames(path, normals):
        parts.extend(make_boss(P0, t, n))

    tris = np.concatenate(parts, axis=0)
    tris = rotate_portrait(tris)
    mn, mx = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    vol = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum() / 6
    print(f"magnet band: size {np.round(mx-mn,2)}  tris {len(tris)}  "
          f"vol {vol/1000:.1f} cm^3  magnets {N_MAGNETS}")
    write_stl(OUT_DIR / "nosecone_magnet_band.stl", tris, "nosecone magnet band")


if __name__ == "__main__":
    main()

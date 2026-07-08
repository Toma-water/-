#!/usr/bin/env python3
"""ノーズコーン合わせ目シール用リップバンド(段差付き)STL生成スクリプト。

黄色ライン(型のパーティング面 Z=55.3mm 上の縁ライン)のサンプル点列に沿って、
垂直に立ち上がる「壁」状のリップバンドを掃引して作る。

断面(工具箱スタイルの段差付き, 単位mm):

        u→ (シェル内側方向)
   z
   ↑        o2      o1+T
   |        ┌────────┐ ← 天面 (z = GLUE_H + LIP_H)
   |   リップ│        │   … 反対側シェルに差し込まれる部分
   |        │        │
   |   ┌────┘段差    │ ← 合わせ面 (z = GLUE_H)
   |   │STEP         │
   |   │接着ゾーン    │   … 固定側シェル内面に接着+釘/リベット固定
   |   └─────────────┘ ← 底 (z = 0)
   |   o1           o1+T

- 接着ゾーン外面: 黄色ラインから GLUE_GAP だけ内側 (接着剤の層のぶん)
- リップ外面:     さらに STEP だけ内側 (相手シェル内面とのクリアランス)
- 出力座標系: ノーズコーン軸 = +Y (先端が+Y側)。Z=0 が印刷ベッド面。
  合わせ面(パーティング面)は Z = GLUE_H。

パラメータは現物合わせで調整すること。まず test coupon を印刷して
実機のGFRPシェルで嵌合確認するのを推奨。
"""

import csv
import struct
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SAMPLES_CSV = HERE / "nosecone_yellow_edge_samples.csv"
OUT_DIR = HERE / "output"

# ---------------- パラメータ (mm) ----------------
GLUE_GAP = 0.2    # 黄色ライン→接着ゾーン外面のオフセット(接着剤層)
STEP = 0.4        # 段差 = リップ外面の追加オフセット(相手シェルとのクリアランス)
THICKNESS = 2.4   # 接着ゾーンの肉厚 (リップ肉厚 = THICKNESS - STEP = 2.0)
GLUE_H = 8.0      # 接着ゾーン高さ(固定側シェル内に入る深さ)
LIP_H = 8.0       # リップ高さ(合わせ面から反対側シェルへの突き出し量)
COUPON_LEN = 40.0 # テストクーポンの長さ
# --------------------------------------------------


def load_path():
    """CSVから連結された外形パス(401点, XY)を返す。"""
    edges = {}
    with open(SAMPLES_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            edges.setdefault(int(row["edge_index"]), []).append(
                (float(row["x_mm"]), float(row["y_mm"]))
            )
    pts = list(edges[0])
    for i in (1, 2, 3):
        seg = edges[i]
        # 継ぎ目の重複点を除去
        if np.hypot(seg[0][0] - pts[-1][0], seg[0][1] - pts[-1][1]) < 1e-6:
            seg = seg[1:]
        pts.extend(seg)
    return np.array(pts)


def inward_normals(path):
    """パス各点の内側向き単位法線。(進行方向右手 = 外形の内側)"""
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    return np.stack([tang[:, 1], -tang[:, 0]], axis=1)


def profile_points():
    """断面6角形 (u, z)。u = 黄色ラインから内側への距離。"""
    o1 = GLUE_GAP
    o2 = GLUE_GAP + STEP
    inner = GLUE_GAP + THICKNESS
    top = GLUE_H + LIP_H
    return np.array([
        (o1, 0.0),        # A 接着ゾーン外面・底
        (o1, GLUE_H),     # B 接着ゾーン外面・合わせ面
        (o2, GLUE_H),     # C 段差の入隅
        (o2, top),        # D リップ外面・天
        (inner, top),     # E 内面・天
        (inner, 0.0),     # F 内面・底
    ])


def sweep(path, normals):
    """断面をパスに沿って掃引し、三角形配列 (n,3,3) を返す。"""
    prof = profile_points()
    n_pts, n_prof = len(path), len(prof)
    # 各断面の頂点: P = path + u*normal, z
    verts = np.empty((n_pts, n_prof, 3))
    for j, (u, z) in enumerate(prof):
        verts[:, j, 0] = path[:, 0] + u * normals[:, 0]
        verts[:, j, 1] = path[:, 1] + u * normals[:, 1]
        verts[:, j, 2] = z

    tris = []
    # 側面
    for i in range(n_pts - 1):
        for j in range(n_prof):
            k = (j + 1) % n_prof
            a, b = verts[i, j], verts[i, k]
            c, d = verts[i + 1, k], verts[i + 1, j]
            tris.append((a, b, c))
            tris.append((a, c, d))
    # 端面キャップ: L字形なので入隅C(index 2)から扇状に分割
    cap = [(2, 3, 4), (2, 4, 5), (2, 5, 0), (2, 0, 1)]
    for i, flip in ((0, True), (n_pts - 1, False)):
        for (p, q, r) in cap:
            t = (verts[i, p], verts[i, q], verts[i, r])
            tris.append((t[0], t[2], t[1]) if flip else t)
    return np.array(tris)


def orient_outward(tris):
    """符号付き体積が正(法線が外向き)になるよう全体を揃える。"""
    vol = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum() / 6
    if vol < 0:
        tris = tris[:, ::-1, :]
        vol = -vol
    return tris, vol


def rotate_portrait(tris):
    """(x,y)->(-y,x): ノーズコーン軸を+Yへ(先端が+Y、開放端が-Y)。"""
    out = tris.copy()
    out[..., 0], out[..., 1] = -tris[..., 1], tris[..., 0].copy()
    return out


def write_stl(path, tris, name):
    tris = np.asarray(tris, dtype=np.float64)
    n = len(tris)
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lens = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lens, out=np.zeros_like(normals), where=lens > 0)
    with open(path, "wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b"\0"))
        f.write(struct.pack("<I", n))
        rec = np.zeros((n, 50), dtype=np.uint8)
        data = np.concatenate(
            [normals[:, None, :], tris], axis=1
        ).astype("<f4").reshape(n, 48 // 4)
        rec[:, :48] = data.view(np.uint8).reshape(n, 48)
        f.write(rec.tobytes())
    print(f"wrote {path}  ({n} tris)")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    path = load_path()
    normals = inward_normals(path)

    # --- 本体: 全周U字リップバンド ---
    tris = sweep(path, normals)
    tris, vol = orient_outward(tris)
    tris = rotate_portrait(tris)
    mn, mx = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    print(f"band bbox: {np.round(mn,2)} .. {np.round(mx,2)}  "
          f"size {np.round(mx-mn,2)}  volume {vol/1000:.1f} cm^3")
    write_stl(OUT_DIR / "nosecone_seal_lip_band.stl", tris, "nosecone seal lip band")

    # --- テストクーポン: 直線部の40mm切り出し相当(直線押し出し) ---
    straight = np.stack(
        [np.linspace(0, COUPON_LEN, 21), np.zeros(21)], axis=1
    )
    c_norm = np.tile([[0.0, -1.0]], (21, 1))  # 上辺エッジと同じ向き(内側=-Y)
    ctris = sweep(straight, c_norm)
    ctris, cvol = orient_outward(ctris)
    write_stl(OUT_DIR / "nosecone_seal_lip_test_coupon.stl", ctris,
              "seal lip fit test coupon")
    print(f"coupon volume {cvol/1000:.2f} cm^3")


if __name__ == "__main__":
    main()

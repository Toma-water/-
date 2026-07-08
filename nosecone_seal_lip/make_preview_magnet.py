#!/usr/bin/env python3
"""磁石バンド(作り直し版)のプレビュー → output/preview_magnet_band.png"""

import struct

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import generate_magnet_band as g
import generate_seal_lip as g1

plt.rcParams["font.family"] = "IPAGothic"

RED = "#e74c3c"
GFRP = "#95a5a6"
YELLOW = "#d4a017"
MAG = "#5d6d7e"

fig = plt.figure(figsize=(15, 7))

# ---------- (1) 3D ----------
ax = fig.add_subplot(1, 2, 1, projection="3d")
with open(g1.OUT_DIR / "nosecone_magnet_band.stl", "rb") as f:
    f.seek(80)
    (n,) = struct.unpack("<I", f.read(4))
    d = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
    tris = d[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(float)
ax.add_collection3d(Poly3DCollection(tris, facecolor=RED, edgecolor="none", alpha=0.9))
pts = tris.reshape(-1, 3)
mn, mx = pts.min(0), pts.max(0)
c = (mn + mx) / 2
r = (mx - mn).max() / 2
ax.set_xlim(c[0] - r, c[0] + r)
ax.set_ylim(c[1] - r, c[1] + r)
ax.set_zlim(0, 2 * r * 0.4)
ax.set_box_aspect((1, 1, 0.4))
ax.view_init(elev=32, azim=-58)
ax.set_title("3Dビュー: バンド本体(高さ8mm) + 内向き磁石座5か所")
ax.set_xlabel("X mm")
ax.set_ylabel("Y mm")

# ---------- (2) 磁石座の断面 ----------
ax2 = fig.add_subplot(1, 2, 2)
# バンド本体 長方形断面 (u,z) 接着ゾーンのみ・リップ無し
ax2.add_patch(Rectangle((g1.GLUE_GAP, 0), g.INNER - g1.GLUE_GAP, g.GLUE_H,
                        facecolor="#f1948a", edgecolor=RED, lw=1.0))
# 磁石座 pad (u: B_START..B_START+PAD_D, z:0..PAD_TOP)
b0, b1 = g.B_START, g.B_START + g.PAD_D
ax2.add_patch(Rectangle((b0, 0), g.PAD_D, g.PAD_TOP, facecolor="#f1948a",
                        edgecolor=RED, lw=1.0))
# 位置決め縁(前後端, 高さRIM_H)
pk0 = b0 + (g.PAD_D - g.MAG_POCKET) / 2
pk1 = pk0 + g.MAG_POCKET
ax2.add_patch(Rectangle((b0, g.PAD_TOP), pk0 - b0, g.RIM_H,
                        facecolor="#cb4335", edgecolor=RED, lw=0.6))
ax2.add_patch(Rectangle((pk1, g.PAD_TOP), b1 - pk1, g.RIM_H,
                        facecolor="#cb4335", edgecolor=RED, lw=0.6))
# 磁石(このハーフ, 上向き, z=5..8) → 合わせ面でツライチ
ax2.add_patch(Rectangle((pk0, g.PAD_TOP), g.MAG_POCKET, g.MAG_T,
                        facecolor=MAG, edgecolor="k", lw=0.8))
# 対向ハーフの磁石(z=8..11, 反転) 参考表示
ax2.add_patch(Rectangle((pk0, g.GLUE_H), g.MAG_POCKET, g.MAG_T,
                        facecolor="#aeb6bf", edgecolor="k", lw=0.8, ls="--"))
# GFRPシェル(このハーフ, 壁の外側)
ax2.add_patch(Rectangle((-1.2, 0), 1.2, g.GLUE_H, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
# 対向ハーフのGFRPシェル(合わせ面より上, 参考)
ax2.add_patch(Rectangle((-1.2, g.GLUE_H), 1.2, 4.0, facecolor="#c8ccd0",
                        edgecolor="k", lw=0.5, ls="--"))
ax2.axhline(g.GLUE_H, color="k", ls=":", lw=0.9)
ax2.axvline(0, color=YELLOW, ls="--", lw=1.3)
ax2.annotate("合わせ面(z=8)でフラット突き合わせ\n磁石上面がツライチ / リム面にテープ",
             (10, g.GLUE_H), fontsize=9, va="bottom")
ax2.annotate("このハーフの磁石\n(例 φ10×3, +z向き)", (pk0 + 5, 6.5),
             fontsize=9, ha="center", xytext=(9, 3.2),
             arrowprops=dict(arrowstyle="->", lw=0.9))
ax2.annotate("対向ハーフの磁石\n(反転・逆極性)", (pk1, g.GLUE_H + 1.5),
             fontsize=9, xytext=(9.5, 12),
             arrowprops=dict(arrowstyle="->", lw=0.8))
ax2.annotate("磁石座(内向き突起)\n約13mm・小さめ", (b0 + 6, 2.5),
             fontsize=9, ha="center", color="#8a1a0f")
ax2.annotate("位置決め縁 1.5", (b0 + 0.5, g.PAD_TOP + g.RIM_H), fontsize=8,
             xytext=(1.5, 9.4), arrowprops=dict(arrowstyle="->", lw=0.7))
ax2.annotate("リム面(平ら)\nスポンジテープで気密", (g1.GLUE_GAP + 1.0, g.GLUE_H),
             fontsize=9, xytext=(-6.8, 12.5),
             arrowprops=dict(arrowstyle="->", lw=0.8))
ax2.annotate("接着ゾーン8mm\n(接着+くぎ)", (g1.GLUE_GAP + 0.5, 3),
             fontsize=9, xytext=(-6.8, 4), arrowprops=dict(arrowstyle="->", lw=0.8))
ax2.set_aspect("equal")
ax2.set_xlim(-8, 18)
ax2.set_ylim(-1.5, 14)
ax2.set_title("磁石座の断面 (単位mm)")
ax2.set_xlabel("シェル内側方向 →")
ax2.set_ylabel("高さ z")

fig.suptitle("磁石式(作り直し): バンド本体 + 内向き磁石座 (1STLを両半割に反転使用)",
             fontsize=14)
fig.tight_layout()
fig.savefig(g1.OUT_DIR / "preview_magnet_band.png", dpi=130)
print("wrote", g1.OUT_DIR / "preview_magnet_band.png")

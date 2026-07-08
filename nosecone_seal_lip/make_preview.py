#!/usr/bin/env python3
"""生成したリップバンドのプレビュー図(3面)を output/preview.png に描画する。"""

import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrow, Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import generate_seal_lip as g

plt.rcParams["font.family"] = "IPAGothic"

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"

RED = "#c0392b"
RED_FILL = "#e74c3c"
GFRP = "#95a5a6"
YELLOW = "#d4a017"


def load_stl(path):
    with open(path, "rb") as f:
        f.seek(80)
        (n,) = struct.unpack("<I", f.read(4))
        d = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
        return d[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(float)


fig = plt.figure(figsize=(16, 7))

# ---------- (1) 3D view ----------
ax = fig.add_subplot(1, 3, 1, projection="3d")
tris = load_stl(OUT / "nosecone_seal_lip_band.stl")
col = Poly3DCollection(tris, facecolor=RED_FILL, edgecolor="none", alpha=0.9)
ax.add_collection3d(col)
pts = tris.reshape(-1, 3)
mn, mx = pts.min(0), pts.max(0)
c = (mn + mx) / 2
r = (mx - mn).max() / 2
ax.set_xlim(c[0] - r, c[0] + r)
ax.set_ylim(c[1] - r, c[1] + r)
ax.set_zlim(0, 2 * r * 0.35)
ax.set_box_aspect((1, 1, 0.35))
ax.view_init(elev=35, azim=-60)
ax.set_title("3Dビュー (立ち壁のU字バンド, 高さ16mm)")
ax.set_xlabel("X mm")
ax.set_ylabel("Y mm")

# ---------- (2) 平面図 ----------
ax2 = fig.add_subplot(1, 3, 2)
path = g.load_path()
# 出力座標系に合わせて回転 (x,y)->(-y,x)
yl = np.stack([-path[:, 1], path[:, 0]], axis=1)
nrm = g.inward_normals(path)
nrm_r = np.stack([-nrm[:, 1], nrm[:, 0]], axis=1)
outer = yl + (g.GLUE_GAP) * nrm_r
inner = yl + (g.GLUE_GAP + g.THICKNESS) * nrm_r
band = np.vstack([outer, inner[::-1]])
ax2.add_patch(Polygon(band, closed=True, facecolor=RED_FILL, edgecolor=RED, lw=0.5))
ax2.plot(yl[:, 0], yl[:, 1], color=YELLOW, lw=1.8, ls="--",
         label="黄色ライン(シェル内面基準)")
ax2.set_aspect("equal")
ax2.set_xlim(-70, 70)
ax2.set_ylim(-95, 150)
ax2.set_title("平面図: 縦に長いアーチ (約90 × 215 mm)")
ax2.set_xlabel("X mm")
ax2.set_ylabel("Y mm")
ax2.legend(loc="lower center", fontsize=9)
ax2.annotate("先端側", (0, 137), ha="center", fontsize=10)
ax2.annotate("開放端(機体側)", (0, -90), ha="center", fontsize=10)

# ---------- (3) 断面図 ----------
ax3 = fig.add_subplot(1, 3, 3)
prof = g.profile_points()  # (u, z)
# 表示: u を右向き(シェル外側が左), z 上向き
ax3.add_patch(Polygon(prof, closed=True, facecolor=RED_FILL, edgecolor=RED, lw=1.2))
t_sh = 1.2  # GFRP想定板厚(表示用)
# 固定側シェル(下半分)
ax3.add_patch(Rectangle((-t_sh, -3), t_sh, g.GLUE_H + 3, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
# 相手側シェル(上半分, 合わせ面に0.3mm浮かせて表示)
ax3.add_patch(Rectangle((-t_sh, g.GLUE_H + 0.3), t_sh,
                        g.LIP_H + 2.7, facecolor=GFRP, edgecolor="k", lw=0.5))
ax3.axvline(0, color=YELLOW, ls="--", lw=1.5)
ax3.axhline(g.GLUE_H, color="k", ls=":", lw=0.8)
ax3.annotate("黄色ライン\n(シェル内面)", (0, -2.6), ha="left", fontsize=9,
             color="#8a6d00", xytext=(0.9, -2.9))
ax3.annotate("合わせ面", (3.6, g.GLUE_H), fontsize=9, va="bottom")
ax3.annotate("GFRPシェル\n(固定側)", (-t_sh - 0.15, 2.5), ha="right", fontsize=9)
ax3.annotate("GFRPシェル\n(相手側)", (-t_sh - 0.15, 12.5), ha="right", fontsize=9)
ax3.annotate("接着ゾーン 8mm\n(接着+くぎ/リベット)", (2.75, 4.0), fontsize=9,
             va="center")
ax3.annotate("リップ 8mm\n(相手シェルに差し込み)", (2.75, 12.0), fontsize=9,
             va="center")
ax3.annotate("段差 0.4\n(クリアランス)", (0.6, 8.6), fontsize=8,
             xytext=(1.2, 9.8), arrowprops=dict(arrowstyle="->", lw=0.8))
ax3.annotate("接着すき間 0.2", (0.2, 1.0), fontsize=8, xytext=(1.0, 0.6),
             arrowprops=dict(arrowstyle="->", lw=0.8))
ax3.annotate("肉厚 2.4", (1.4, -0.9), fontsize=8, ha="center")
ax3.annotate("リップ肉厚 2.0", (1.6, 16.4), fontsize=8, ha="center")
# くぎの表示
ax3.plot([-t_sh - 0.6, g.GLUE_GAP + g.THICKNESS + 0.2], [4, 4],
         color="k", lw=1.0)
ax3.plot([-t_sh - 0.6], [4], marker="<", color="k", ms=5)
ax3.set_aspect("equal")
ax3.set_xlim(-5.5, 8.5)
ax3.set_ylim(-4, 19.5)
ax3.set_title("断面図 (単位mm)")
ax3.set_xlabel("シェル内側方向 →")
ax3.set_ylabel("高さ")

fig.suptitle("ノーズコーン合わせ目 シールリップバンド設計", fontsize=14)
fig.tight_layout()
fig.savefig(OUT / "preview.png", dpi=130)
print("wrote", OUT / "preview.png")

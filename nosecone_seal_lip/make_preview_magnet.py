#!/usr/bin/env python3
"""リムバンドv3のプレビュー → output/preview_rim_band.png"""

import struct

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import generate_magnet_band_v3 as g

plt.rcParams["font.family"] = "IPAGothic"

RED = "#e74c3c"
GFRP = "#95a5a6"
YELLOW = "#d4a017"
BLUE = "#2471a3"

OUT = __import__("pathlib").Path(__file__).resolve().parent / "output"

fig = plt.figure(figsize=(16, 7))

# ---------- (1) 3D ----------
ax = fig.add_subplot(1, 3, 1, projection="3d")
with open(OUT / "nosecone_rim_band_v3.stl", "rb") as f:
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
ax.set_title("3Dビュー: リムバンド + M3穴6か所")
ax.set_xlabel("X mm")
ax.set_ylabel("Y mm")

# ---------- (2) 平面図 ----------
ax2 = fig.add_subplot(1, 3, 2)
th = np.linspace(-np.pi / 2, np.pi / 2, 400)
P = np.stack([g.A_LEN * np.cos(th), g.B_RAD * np.sin(th)], axis=1)
Pp = np.stack([-P[:, 1], P[:, 0]], axis=1)  # portrait回転
ax2.plot(Pp[:, 0], Pp[:, 1], color=YELLOW, ls="--", lw=1.8,
         label="新外形(シェル内面基準)")
tang = np.stack([g.A_LEN * -np.sin(th), g.B_RAD * np.cos(th)], axis=1)
tang /= np.linalg.norm(tang, axis=1, keepdims=True)
nrm = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
nrm_p = np.stack([-nrm[:, 1], nrm[:, 0]], axis=1)
outer = Pp + g.GLUE_GAP * nrm_p
inner = Pp + g.INNER * nrm_p
ax2.add_patch(Polygon(np.vstack([outer, inner[::-1]]), closed=True,
                      facecolor="#f1948a", edgecolor=RED, lw=0.6))
holes, _ = g.ellipse_frames(g.HOLE_FRACS)
for P0, t, nn in holes:
    ax2.plot(-P0[1], P0[0], "o", ms=7, mfc="white", mec=BLUE, mew=1.8)
ax2.plot([], [], "o", ms=7, mfc="white", mec=BLUE, mew=1.8, ls="",
         label="M3穴 Φ3.4×6")
ax2.set_aspect("equal")
ax2.set_xlim(-72, 72)
ax2.set_ylim(-25, 155)
ax2.set_title("平面図 (全長135.6 × 全幅91.2)")
ax2.annotate("先端側", (0, 143), ha="center", fontsize=10)
ax2.annotate("開放端(機体側)", (0, -12), ha="center", fontsize=10)
ax2.legend(loc="lower left", fontsize=9)

# ---------- (3) 断面 ----------
ax3 = fig.add_subplot(1, 3, 3)
ax3.add_patch(Rectangle((g.GLUE_GAP, 0), g.THICKNESS, g.GLUE_H,
                        facecolor="#f1948a", edgecolor=RED, lw=1.2))
# GFRPシェル + 対向ハーフ
ax3.add_patch(Rectangle((-1.2, 0), 1.2, g.GLUE_H, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
ax3.add_patch(Rectangle((-1.2, g.GLUE_H), 1.2, 4.0, facecolor="#c8ccd0",
                        edgecolor="k", lw=0.5, ls="--"))
# M3穴
ax3.add_patch(Rectangle((g.GLUE_GAP - 1.6, g.HOLE_Z - g.HOLE_D / 2),
                        g.THICKNESS + 1.6, g.HOLE_D, facecolor="white",
                        edgecolor=BLUE, lw=1.4, ls="--"))
ax3.axhline(g.GLUE_H, color="k", ls=":", lw=0.9)
ax3.axvline(0, color=YELLOW, ls="--", lw=1.3)
ax3.annotate("合わせ面(z=8)フラット\n(気密が要るならスポンジテープ)",
             (2.2, g.GLUE_H + 0.4), fontsize=9)
ax3.annotate(f"M3ネジ Φ3.4貫通穴\n(シェルと共締め, z={g.HOLE_Z}, 6か所)",
             (1.4, g.HOLE_Z), fontsize=9, color=BLUE, xytext=(3.8, 5.0),
             arrowprops=dict(arrowstyle="->", lw=0.9, color=BLUE))
ax3.annotate("GFRPシェル\n(このハーフ)", (-1.4, 2.0), ha="right", fontsize=9)
ax3.annotate("相手側シェル", (-1.4, 10.0), ha="right", fontsize=9)
ax3.annotate("バンド肉厚2.4\n高さ8", (g.INNER + 0.3, 1.0), fontsize=9)
ax3.set_aspect("equal")
ax3.set_xlim(-8, 12)
ax3.set_ylim(-1.5, 13.5)
ax3.set_title("断面 (単位mm)")
ax3.set_xlabel("シェル内側方向 →")
ax3.set_ylabel("高さ z")

fig.suptitle("リムバンド v3: 新外形(曲線のみ135.6×45.6)・段差なし・磁石座なし・M3ネジ固定",
             fontsize=14)
fig.tight_layout()
fig.savefig(OUT / "preview_rim_band.png", dpi=130)
print("wrote", OUT / "preview_rim_band.png")

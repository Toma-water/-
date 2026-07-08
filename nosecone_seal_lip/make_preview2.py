#!/usr/bin/env python3
"""スナップ嵌合バンド+磁石タブのプレビュー図 → output/preview_snap_magnet.png"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle

import generate_seal_lip as g1
import generate_snap_and_magnet as g2

plt.rcParams["font.family"] = "IPAGothic"

RED = "#c0392b"
BLUE = "#2471a3"
GFRP = "#95a5a6"
YELLOW = "#d4a017"
MAG = "#7d3c98"

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 7))

# ---------- (1) スナップ嵌合: 閉じた状態の断面 ----------
fp = g2.female_profile()
mp = g2.male_profile(1.0)
ax1.add_patch(Polygon(fp, closed=True, facecolor="#ec7063",
                      edgecolor=RED, lw=1.2, label="受け(シェルA側)"))
ax1.add_patch(Polygon(mp, closed=True, facecolor="#85c1e9",
                      edgecolor=BLUE, lw=1.2, label="攻め(シェルB側)"))
t_sh = 1.2
ax1.add_patch(Rectangle((-t_sh, -11), t_sh, 11, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
ax1.add_patch(Rectangle((-t_sh, 0.3), t_sh, 10.7, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
ax1.axvline(0, color=YELLOW, ls="--", lw=1.5)
ax1.axhline(0, color="k", ls=":", lw=0.8)
ax1.annotate("シェルA(下半分)", (-t_sh - 0.2, -6), ha="right", fontsize=9)
ax1.annotate("シェルB(上半分)", (-t_sh - 0.2, 6), ha="right", fontsize=9)
ax1.annotate("合わせ面", (5.6, 0.1), fontsize=9)
ax1.annotate("接着ゾーン8mm\n(接着+くぎ)", (4.1, 5.5), fontsize=9, color=BLUE)
ax1.annotate("受けバンド\n接着ゾーン8mm", (4.1, -4.0), fontsize=9, color=RED,
             xytext=(4.1, -3.2))
ax1.annotate("ビード(爪)0.3\nカチッとはまる", (g2.M_OUTER - g2.BEAD, g2.BEAD_Z),
             fontsize=9, xytext=(4.6, -7.6),
             arrowprops=dict(arrowstyle="->", lw=0.9))
ax1.annotate("溝(全周)", (g2.G_FLOOR, g2.BEAD_Z + 0.3), fontsize=9,
             xytext=(-4.6, -8.6), color="#8a1a0f",
             arrowprops=dict(arrowstyle="->", lw=0.9))
ax1.annotate("段差ledge=シール面\n(スポンジテープ推奨)", (1.2, 0.0), fontsize=8,
             xytext=(-5.4, 2.6), arrowprops=dict(arrowstyle="->", lw=0.8))
ax1.annotate("舌 7.5mm", (g2.M_INNER + 0.15, -5.0), fontsize=9, color=BLUE)
ax1.set_aspect("equal")
ax1.set_xlim(-6.5, 8.5)
ax1.set_ylim(-12.5, 11.5)
ax1.set_title("スナップ嵌合 断面(閉じた状態, 単位mm)")
ax1.set_xlabel("シェル内側方向 →")
ax1.legend(loc="upper right", fontsize=9)

# ---------- (2) 平面図: ビード区間の位置 ----------
path = g1.load_path()
yl = np.stack([-path[:, 1], path[:, 0]], axis=1)
w = g2.bead_windows(path)
ax2.plot(yl[:, 0], yl[:, 1], color="#aab7b8", lw=5, solid_capstyle="round",
         label="バンド全周(受け=溝は全周)")
on = w > 0.5
ax2.scatter(yl[on, 0], yl[on, 1], s=14, color=BLUE, zorder=3,
            label="ビード区間 30mm×4(攻め側)")
ax2.set_aspect("equal")
ax2.set_xlim(-75, 75)
ax2.set_ylim(-100, 155)
ax2.set_title("平面図: ビード(爪)の配置")
ax2.annotate("先端側", (0, 142), ha="center", fontsize=10)
ax2.annotate("開放端(機体側)", (0, -92), ha="center", fontsize=10)
ax2.legend(loc="lower center", fontsize=9)

# ---------- (3) 磁石タブ 断面 ----------
prof = g2.magnet_tab_profile(False)
ax3.add_patch(Polygon(prof, closed=True, facecolor="#d7bde2",
                      edgecolor=MAG, lw=1.2))
fence = g2.magnet_tab_profile(True)
ax3.plot([0, g2.TAB_D], [g2.TAB_TOP + g2.FENCE_H] * 2, color=MAG, lw=1.0,
         ls="--")
ax3.add_patch(Rectangle((-1.2, -16), 1.2, 16, facecolor=GFRP,
                        edgecolor="k", lw=0.5))
# 磁石 (φ10×3 例)
ax3.add_patch(Rectangle((1.0, g2.TAB_TOP), 10, 3, facecolor="#5d6d7e",
                        edgecolor="k", lw=0.8))
ax3.axhline(0, color="k", ls=":", lw=0.8)
ax3.axvline(0, color=YELLOW, ls="--", lw=1.2)
ax3.annotate("合わせ面", (8.6, 0.25), fontsize=9)
ax3.annotate("磁石(例: φ10×3)\n上面が合わせ面と\nツライチになる", (6, -1.5),
             fontsize=9, xytext=(8.2, 3.0),
             arrowprops=dict(arrowstyle="->", lw=0.9))
ax3.annotate("上面 = 合わせ面-3mm", (12.2, g2.TAB_TOP - 1.2), fontsize=8)
ax3.annotate("両端に縁0.8mm(位置決め用, 幅方向)",
             (12.0, g2.TAB_TOP + g2.FENCE_H), fontsize=8, color=MAG,
             xytext=(3.0, 4.6),
             arrowprops=dict(arrowstyle="->", lw=0.8, color=MAG))
ax3.annotate("GFRPシェル内面に\n接着(エポキシ)", (-1.4, -9), ha="right",
             fontsize=9)
ax3.annotate("奥行き12mm・幅24mm\nパラシュートの邪魔に\nならない小型サイズ",
             (5.5, -9.5), fontsize=9, ha="center")
ax3.set_aspect("equal")
ax3.set_xlim(-7, 20)
ax3.set_ylim(-16.5, 6.5)
ax3.set_title("磁石タブ 断面(1種類を各位置×2個印刷)")
ax3.set_xlabel("シェル内側方向 →")

fig.suptitle("v2: スナップ嵌合バンド(受け/攻め) + 磁石タブ", fontsize=14)
fig.tight_layout()
fig.savefig(g1.OUT_DIR / "preview_snap_magnet.png", dpi=130)
print("wrote", g1.OUT_DIR / "preview_snap_magnet.png")

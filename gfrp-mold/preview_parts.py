#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""8つのSTLパーツを個別に3Dレンダリングして一覧図(グリッド)を出力する。"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(__file__)
STL = os.path.join(HERE, "stl")
LIGHT = np.array([0.4, 0.5, 0.85]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

PARTS = [
    ("3_collapsible_keystone.stl",     "1. keystone (shell)",        (0.93, 0.55, 0.20)),
    ("3_collapsible_segment_1of3.stl", "2. segment 1/3 (shell)",     (0.83, 0.30, 0.28)),
    ("3_collapsible_segment_2of3.stl", "3. segment 2/3 (shell)",     (0.27, 0.55, 0.83)),
    ("3_collapsible_segment_3of3.stl", "4. segment 3/3 (shell)",     (0.34, 0.73, 0.43)),
    ("3_collapsible_center_key.stl",   "5. center key (core)",       (0.96, 0.83, 0.25)),
    ("3_collapsible_base_plate.stl",   "6. base plate (bottom)",     (0.55, 0.55, 0.60)),
    ("1_breakaway_mandrel.stl",        "7. breakaway mandrel",       (0.85, 0.45, 0.40)),
    ("2_taper_mandrel.stl",            "8. taper mandrel",           (0.40, 0.65, 0.85)),
]


def shaded(mesh, base):
    inten = np.clip(mesh.face_normals @ LIGHT, 0, 1) * 0.65 + 0.35
    return np.clip(np.array(base)[None, :] * inten[:, None], 0, 1)


def draw(ax, name, title, color):
    m = trimesh.load(os.path.join(STL, name))
    pc = Poly3DCollection(m.triangles)
    pc.set_facecolor(shaded(m, color)); pc.set_edgecolor((0, 0, 0, 0.05)); pc.set_linewidth(0.15)
    ax.add_collection3d(pc)
    mn, mx = m.bounds; c = (mn + mx) / 2; r = (mx - mn).max() / 2 + 2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(min(0, mn[2]), c[2]+r)
    try: ax.set_box_aspect((1, 1, 1))
    except Exception: pass
    ax.view_init(elev=20, azim=-60)
    H = mx[2] - mn[2]
    rad = np.sqrt(m.vertices[:, 0]**2 + m.vertices[:, 1]**2).max()
    ax.set_title(f"{title}\nH={H:.0f}mm  max_dia={rad*2:.0f}mm", fontsize=9)
    ax.set_xticklabels([]); ax.set_yticklabels([]); ax.set_zlabel("mm", fontsize=7)
    ax.tick_params(labelsize=6)


fig = plt.figure(figsize=(15, 8))
for i, (name, title, color) in enumerate(PARTS, 1):
    ax = fig.add_subplot(2, 4, i, projection="3d")
    draw(ax, name, title, color)
fig.suptitle("GFRP body mold - 8 parts  (ID90 x H110mm set)", fontsize=13)
fig.tight_layout()
out = os.path.join(HERE, "figs", "parts_overview.png")
fig.savefig(out, dpi=130); plt.close(fig)
print("->", out)

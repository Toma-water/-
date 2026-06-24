#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STL のプレビュー画像(PNG)を生成して確認用に出力する。"""
import os, glob
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(__file__)
STL  = os.path.join(HERE, "stl")


def add_mesh(ax, mesh, color, alpha=1.0):
    tris = mesh.triangles
    pc = Poly3DCollection(tris, alpha=alpha)
    pc.set_facecolor(color)
    pc.set_edgecolor((0, 0, 0, 0.04))
    ax.add_collection3d(pc)


def set_box(ax, meshes):
    allv = np.vstack([m.vertices for m in meshes])
    mn, mx = allv.min(0), allv.max(0)
    c = (mn + mx) / 2
    r = (mx - mn).max() / 2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    try: ax.set_box_aspect((1, 1, 1))
    except Exception: pass
    ax.view_init(elev=22, azim=35)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z (mm)")


def single(name, color):
    m = trimesh.load(os.path.join(STL, name))
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection="3d")
    add_mesh(ax, m, color)
    set_box(ax, [m]); ax.set_title(name, fontsize=9)
    out = os.path.join(HERE, "preview_" + name.replace(".stl", ".png"))
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)
    print("  ", out)


def assembly():
    cols = [(0.85,0.35,0.30),(0.30,0.55,0.85),(0.35,0.75,0.45)]
    segs = [trimesh.load(os.path.join(STL, f"3_collapsible_segment_{i}of3.stl")) for i in (1,2,3)]
    key  = trimesh.load(os.path.join(STL, "3_collapsible_center_key.stl"))
    base = trimesh.load(os.path.join(STL, "3_collapsible_base_plate.stl"))
    base.apply_translation([0,0,-8])
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection="3d")
    for s,c in zip(segs, cols): add_mesh(ax, s, c, 0.92)
    add_mesh(ax, key, (0.95,0.8,0.25), 0.95)
    add_mesh(ax, base, (0.6,0.6,0.6), 0.5)
    set_box(ax, segs+[key])
    ax.set_title("案3 collapsible 組立(キー+3分割+ベース)", fontsize=9)
    out = os.path.join(HERE, "preview_3_collapsible_assembly.png")
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    print("  ", out)


if __name__ == "__main__":
    single("1_breakaway_mandrel.stl", (0.85,0.45,0.40))
    single("2_taper_mandrel.stl",     (0.40,0.65,0.85))
    assembly()
    print("done")

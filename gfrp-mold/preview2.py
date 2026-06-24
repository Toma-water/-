#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案3(keystone collapsible)の詳細プレビュー図を生成する。
英語ラベルで文字化けを回避。出力: gfrp-mold/figs/*.png"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle, FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(__file__)
STL  = os.path.join(HERE, "stl")
FIG  = os.path.join(HERE, "figs")
os.makedirs(FIG, exist_ok=True)

LIGHT = np.array([0.4, 0.5, 0.85]); LIGHT = LIGHT / np.linalg.norm(LIGHT)


def load(name):
    return trimesh.load(os.path.join(STL, name))


def shaded(mesh, base):
    n = mesh.face_normals
    inten = np.clip(n @ LIGHT, 0, 1) * 0.65 + 0.35
    base = np.array(base)
    return np.clip(base[None, :] * inten[:, None], 0, 1)


def add(ax, mesh, base, alpha=1.0, edge=False):
    pc = Poly3DCollection(mesh.triangles, alpha=alpha)
    pc.set_facecolor(shaded(mesh, base))
    pc.set_edgecolor((0, 0, 0, 0.12) if edge else (0, 0, 0, 0))
    pc.set_linewidth(0.2)
    ax.add_collection3d(pc)


def frame(ax, meshes, elev=20, azim=-60, title="", pad=2):
    allv = np.vstack([m.vertices for m in meshes])
    mn, mx = allv.min(0), allv.max(0); c = (mn + mx) / 2; r = (mx - mn).max() / 2 + pad
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(min(0,mn[2]), c[2]+r)
    try: ax.set_box_aspect((1, 1, 1))
    except Exception: pass
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("X [mm]"); ax.set_zlabel("Z [mm]")


COL = dict(keystone=(0.93, 0.55, 0.20),
           s1=(0.83, 0.30, 0.28), s2=(0.27, 0.55, 0.83), s3=(0.34, 0.73, 0.43),
           key=(0.96, 0.83, 0.25), base=(0.55, 0.55, 0.58))


def parts():
    return {
        "keystone": load("3_collapsible_keystone.stl"),
        "s1": load("3_collapsible_segment_1of3.stl"),
        "s2": load("3_collapsible_segment_2of3.stl"),
        "s3": load("3_collapsible_segment_3of3.stl"),
        "key": load("3_collapsible_center_key.stl"),
        "base": load("3_collapsible_base_plate.stl"),
    }


# ---- Fig 1: exploded ----
def fig_exploded():
    p = parts()
    fig = plt.figure(figsize=(8, 8)); ax = fig.add_subplot(111, projection="3d")
    disp = {
        "base": [0, 0, -55],
        "s1":   [ 70 * np.cos(np.deg2rad(80)),  70 * np.sin(np.deg2rad(80)), 0],
        "s2":   [ 70 * np.cos(np.deg2rad(200)), 70 * np.sin(np.deg2rad(200)), 0],
        "s3":   [ 70 * np.cos(np.deg2rad(320)), 70 * np.sin(np.deg2rad(320)), 0],
        "keystone": [70 * np.cos(0), 70 * np.sin(0), 0],
        "key":  [0, 0, 70],
    }
    ms = []
    for k, m in p.items():
        mm = m.copy(); mm.apply_translation(disp[k]); ms.append(mm)
        add(ax, mm, COL[k], edge=True)
        c = mm.bounds.mean(0)
        ax.text(c[0], c[1], mm.bounds[1][2] + 4, k, fontsize=8, ha="center")
    frame(ax, ms, elev=18, azim=-65, title="Fig.1  Exploded view (6 parts)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_exploded.png"), dpi=130); plt.close(fig)


# ---- Fig 2: assembled + cross section ----
def fig_assembled_section():
    p = parts()
    fig = plt.figure(figsize=(11, 5.5))
    # assembled
    ax1 = fig.add_subplot(121, projection="3d")
    shell = ["keystone", "s1", "s2", "s3"]
    for k in shell: add(ax1, p[k], COL[k], edge=True)
    knob = p["key"].copy()
    add(ax1, knob, COL["key"], alpha=0.5)
    frame(ax1, [p[k] for k in shell], elev=20, azim=-60,
          title="Fig.2a  Assembled  (OD = phi 90, true cylinder)")
    # cross section: cut x<=0
    ax2 = fig.add_subplot(122, projection="3d")
    box = trimesh.creation.box(extents=[200, 200, 300])
    box.apply_translation([-100, 0, 0])   # keep x<=0
    cms = []
    for k in shell + ["key", "base"]:
        m = p[k]
        try:
            cut = trimesh.boolean.intersection([m, box])
            if cut.is_empty or len(cut.faces) == 0: cut = m
        except Exception:
            cut = m
        cut.merge_vertices(); cms.append(cut)
        add(ax2, cut, COL[k], edge=True)
    frame(ax2, cms, elev=8, azim=-90,
          title="Fig.2b  Cross-section (center key supports from inside)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_assembled_section.png"), dpi=130); plt.close(fig)


# ---- Fig 3: top view dimensioned schematic ----
def fig_top():
    fig, ax = plt.subplots(figsize=(7, 7)); ax.set_aspect("equal")
    R = 45
    # outer cylinder
    ax.add_patch(Circle((0, 0), R, fill=False, lw=2, color="k"))
    # bore (top radius 20)
    ax.add_patch(Circle((0, 0), 20, fill=False, lw=1.2, ls="--", color="0.4"))
    # center key
    ax.add_patch(Circle((0, 0), 19.8, fill=True, color=COL["key"], alpha=0.5))
    # seams at 30,130,230,330 deg ; keystone -30..30
    seam = [30, 130, 230, 330]
    for a in seam:
        ar = np.deg2rad(a)
        ax.plot([0, R*np.cos(ar)], [0, R*np.sin(ar)], color="0.3", lw=1)
    # color wedges
    wedges = [(-30, 30, COL["keystone"], "keystone 60deg"),
              (30, 130, COL["s1"], "segment1 100deg"),
              (130, 230, COL["s2"], "segment2 100deg"),
              (230, 330, COL["s3"], "segment3 100deg")]
    for a0, a1, c, lab in wedges:
        ax.add_patch(Wedge((0, 0), R, a0, a1, fc=c, alpha=0.35, ec="none"))
        am = np.deg2rad((a0 + a1) / 2)
        ax.text(32*np.cos(am), 32*np.sin(am), lab.split()[0], ha="center", va="center", fontsize=8)
    # dimension phi90
    ax.annotate("", xy=(-R, -R-8), xytext=(R, -R-8),
                arrowprops=dict(arrowstyle="<->", color="b"))
    ax.text(0, -R-12, "OD = phi 90.0  (= GFRP inner dia.)", ha="center", color="b", fontsize=10)
    ax.text(0, R+6, "Seams butt with ZERO gap -> true circle\n(wrap release film for vacuum)",
            ha="center", fontsize=9, color="0.2")
    ax.text(0, -4, "bore\nphi24-40\n(taper)", ha="center", va="center", fontsize=7, color="0.3")
    ax.set_xlim(-65, 65); ax.set_ylim(-70, 62); ax.axis("off")
    ax.set_title("Fig.3  Top view / seam layout (vacuum-safe, true phi90)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_topview.png"), dpi=130); plt.close(fig)


# ---- Fig 4: removal sequence ----
def fig_sequence():
    p = parts()
    shell = ["keystone", "s1", "s2", "s3"]
    fig = plt.figure(figsize=(13, 4))
    steps = [
        ("1) Cured. Assembled state", {}),
        ("2) Pull CENTER KEY up", {"key": [0, 0, 60]}),
        ("3) Pull KEYSTONE up", {"key": [0, 0, 60], "keystone": [0, 0, 70]}),
        ("4) Collapse segments inward", {"key": [0, 0, 60], "keystone": [0, 0, 70],
                                         "s1": [-14*np.cos(np.deg2rad(80)), -14*np.sin(np.deg2rad(80)), 0],
                                         "s2": [-14*np.cos(np.deg2rad(200)), -14*np.sin(np.deg2rad(200)), 0],
                                         "s3": [-14*np.cos(np.deg2rad(320)), -14*np.sin(np.deg2rad(320)), 0]}),
    ]
    for i, (title, disp) in enumerate(steps, 1):
        ax = fig.add_subplot(1, 4, i, projection="3d")
        ms = []
        order = shell + (["key"] if i >= 1 else [])
        for k in order:
            m = p[k].copy()
            if k in disp: m.apply_translation(disp[k])
            ms.append(m)
            add(ax, m, COL[k], alpha=0.95, edge=False)
        frame(ax, [p[k] for k in shell] + [p["key"]], elev=16, azim=-60, title=title)
        ax.set_xlabel(""); ax.set_zlabel("")
    fig.suptitle("Fig.4  Demolding sequence (part keeps true phi90, no deformation)", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_sequence.png"), dpi=130); plt.close(fig)


if __name__ == "__main__":
    fig_exploded(); print("fig1 ok")
    fig_assembled_section(); print("fig2 ok")
    fig_top(); print("fig3 ok")
    fig_sequence(); print("fig4 ok")
    print("-> figs/")

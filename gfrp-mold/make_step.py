#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GFRP ボディ用 型を STEP(B-repソリッド)で生成する。
Fusion 360 でネイティブに開いて編集できるように、STL(メッシュ)ではなく
cadquery(OpenCASCADE)でパラメトリックに再構築して STEP 出力する。
寸法は STL 版と同一: 型外径 φ90 / 高さ 110mm。
"""
import os, math
import numpy as np
import cadquery as cq

R_OUT    = 45.0
H_MOLD   = 110.0
BORE_R0  = 12.0     # 中心テーパー穴 下半径
BORE_R1  = 20.0     # 中心テーパー穴 上半径
KEY_CL   = 0.20     # センターキー嵌合クリアランス
DRAFT    = 1.0      # 案2 抜き勾配(度)

OUT = os.path.join(os.path.dirname(__file__), "step")
os.makedirs(OUT, exist_ok=True)


def save(part, name):
    solid = part.val() if isinstance(part, cq.Workplane) else part
    path = os.path.join(OUT, name)
    cq.exporters.export(part if isinstance(part, cq.Workplane) else cq.Workplane(obj=part),
                        path, exportType="STEP")
    try:
        v = solid.Volume() / 1000.0
        bb = solid.BoundingBox()
        print(f"  {name:34s} vol={v:8.2f} cm^3  "
              f"bbox=[{bb.xlen:.1f},{bb.ylen:.1f},{bb.zlen:.1f}]")
    except Exception as e:
        print(f"  {name:34s} exported ({e})")


# ---- 共通: 中心テーパー穴つきチューブ(外径φ90) ----
def bore_tube():
    cyl = cq.Workplane("XY").circle(R_OUT).extrude(H_MOLD)
    cone = cq.Solid.makeCone(BORE_R0, BORE_R1, H_MOLD)  # 下r12 -> 上r20
    return cyl.cut(cq.Workplane(obj=cone))


def wedge(a0deg, a1deg, r=60.0, h=H_MOLD + 4):
    """原点中心の扇形プリズム。半径方向の切断面(2枚)は厳密な平面。
    円弧側(r=60)は部品外(φ90より外)なので多角形近似で問題なし。"""
    pts = [(0.0, 0.0)]
    for a in np.linspace(math.radians(a0deg), math.radians(a1deg), 90):
        pts.append((r * math.cos(a), r * math.sin(a)))
    return cq.Workplane("XY").polyline(pts).close().extrude(h)


# ---- 案3: keystone collapsible ----
def keystone():
    ks = bore_tube().intersect(wedge(-30, 30))
    # 引抜き用 φ5 穴(上端トリミング代の範囲: z=H-18..H)
    hole = cq.Workplane("XY", origin=(32, 0, H_MOLD - 18)).circle(2.5).extrude(20)
    return ks.cut(hole)


def segment(i):
    a0 = 30 + i * 100
    return bore_tube().intersect(wedge(a0, a0 + 100))


def center_key():
    cone = cq.Solid.makeCone(BORE_R0 - KEY_CL, BORE_R1 - KEY_CL, H_MOLD)  # 11.8 -> 19.8
    key = cq.Workplane(obj=cone)
    knob = cq.Workplane("XY", origin=(0, 0, H_MOLD)).circle(8).extrude(18)
    return key.union(knob)


def base_plate():
    base = cq.Workplane("XY").circle(R_OUT + 3).extrude(8)          # R48 h8
    inner = cq.Workplane("XY", origin=(0, 0, 5)).circle(R_OUT).extrude(4)  # 内側を z5..9 除去→外周リップ残す
    base = base.cut(inner)
    recess = cq.Workplane("XY", origin=(0, 0, 4)).circle(BORE_R0).extrude(1.001)  # 中心1mmザグリ
    return base.cut(recess)


# ---- 案1: breakaway ----
def breakaway():
    wall = 2.5; base_t = 4.0; fl_r = R_OUT + 10
    cup = cq.Workplane("XY").circle(R_OUT).extrude(H_MOLD)
    bore = cq.Workplane("XY", origin=(0, 0, base_t)).circle(R_OUT - wall).extrude(H_MOLD)
    cup = cup.cut(bore)
    flange = cq.Workplane("XY").circle(fl_r).extrude(base_t)
    cup = cup.union(flange)
    for i in range(6):
        a = i * 60.0
        box = cq.Workplane("XY", origin=(R_OUT - wall + 0.3, 0, base_t + (H_MOLD - base_t) / 2)) \
            .box(3.0, 1.2, H_MOLD - base_t)
        box = box.rotate((0, 0, 0), (0, 0, 1), a)
        cup = cup.cut(box)
    return cup


# ---- 案2: taper ----
def taper():
    base_t = 4.0; fl_r = R_OUT + 10; wall = 4.0
    top_r = R_OUT - H_MOLD * math.tan(math.radians(DRAFT))
    outer = cq.Workplane(obj=cq.Solid.makeCone(R_OUT, top_r, H_MOLD))
    flange = cq.Workplane("XY").circle(fl_r).extrude(base_t)
    solid = outer.union(flange)
    inner_cone = cq.Solid.makeCone(R_OUT - wall, top_r - wall, H_MOLD)
    clip = cq.Workplane("XY", origin=(0, 0, base_t)).box(200, 200, (H_MOLD - 3 - base_t),
                                                         centered=(True, True, False))
    inner = cq.Workplane(obj=inner_cone).intersect(clip)
    return solid.cut(inner)


if __name__ == "__main__":
    print(f"STEP export  外径φ{R_OUT*2:.0f}  高さ{H_MOLD:.0f}mm -> {OUT}")
    print("[案3 collapsible]")
    save(keystone(),      "3_collapsible_keystone.step")
    for i in range(3):
        save(segment(i),  f"3_collapsible_segment_{i+1}of3.step")
    save(center_key(),    "3_collapsible_center_key.step")
    save(base_plate(),    "3_collapsible_base_plate.step")
    print("[案1 breakaway]")
    save(breakaway(),     "1_breakaway_mandrel.step")
    print("[案2 taper]")
    save(taper(),         "2_taper_mandrel.step")
    print("done")

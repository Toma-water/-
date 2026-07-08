#!/usr/bin/env python3
"""ノーズコーン用 スナップ嵌合バンド(受け/攻め) + 磁石タブ のSTL生成。

v1 (generate_seal_lip.py) の改良版。

【スナップ式】閉じたときの断面 (u = 黄色ラインから内側への距離, z = 合わせ面基準):

  シェルB(上半分)../..            ┌───┐
                 ../..  攻めバンド │   │  接着ゾーン (u 0.2..3.8, 上に8mm)
  ── 合わせ面 ────┬──ledge──┬─────┤   │
  シェルA(下半分)..│ 受けバンド│ 0.2 │舌 │  舌 (u 2.4..3.8, 下に7.5mm)
                ..│ u0.2..2.2│ 隙間 │   │
                ..│  溝▷     │  ◁ビード │  ビード(爪)が溝にカチッとはまる
                ..└─────────┴─────┴───┘

- 受け(female): シェルAの内面に接着。内面(u=2.2)に全周の溝。
- 攻め(male):  シェルBの内面に接着。合わせ面から下に舌が伸び、
  舌の外面のビード(高さ0.3mm, 4区間×30mm)が受けの溝に飛び込む。
- 保持: ビード区間の合計長で調整可能。開放は引き離す力で外れる(55°フランク)。
- 段差(ledge)が受けの上面に着座 → ここがエアシール面(薄いスポンジテープ推奨)。
- 接着ゾーン外面にはドラフト(0.2→1.0mm)を付け、シェル曲面の逃げとした。

【磁石式】くさび形タブ。上面が合わせ面の3mm下 → 厚さ3mmの磁石を貼ると
磁石面が合わせ面とツライチになり、対になるタブの磁石と面接触する。
両端に0.8mmの縁(フェンス)があり磁石の位置決めに使う。1種類のSTLを
必要個数(位置数×2)印刷する。※両半分で磁石の極性を逆に貼ること。
"""

import numpy as np

from generate_seal_lip import (
    OUT_DIR,
    inward_normals,
    load_path,
    orient_outward,
    rotate_portrait,
    write_stl,
)

# ---------------- スナップ嵌合パラメータ (mm) ----------------
GLUE_GAP = 0.2      # 黄色ライン→接着面のオフセット(接着剤層)
DRAFT = 0.8         # 接着ゾーン外面のドラフト量(シェル曲面の逃げ)
GLUE_H = 8.0        # 接着ゾーン高さ(受け=下向き, 攻め=上向き)
F_INNER = 2.2       # 受けバンド内面のu位置(肉厚 2.0 at 合わせ面)
CLEAR = 0.2         # 受け内面と舌外面のクリアランス
TONGUE_T = 1.4      # 舌の肉厚
TONGUE_L = 7.5      # 舌の長さ(合わせ面から下へ)
BEAD = 0.3          # ビード(爪)の張り出し量
BEAD_Z = -6.15      # ビード中心の高さ(合わせ面基準)
GROOVE_D = 0.4      # 溝の深さ
FLANK_RET = 0.28    # 保持フランクの高さ幅(≈55°)
BEAD_SEGS = [40.0, 155.0, 306.0, 421.0]  # ビード区間の中心(周長方向 mm)
BEAD_LEN = 30.0     # 各ビード区間の長さ
BEAD_RAMP = 3.0     # 区間端のなめらかな立ち上がり長
# 導出値
M_OUTER = F_INNER + CLEAR            # 舌の外面 u=2.4
M_INNER = M_OUTER + TONGUE_T         # 舌の内面 u=3.8
G_FLOOR = F_INNER - GROOVE_D         # 溝底 u=1.8

# ---------------- 磁石タブ パラメータ (mm) ----------------
TAB_W = 24.0        # 幅(合わせ目に沿う方向)
TAB_D = 12.0        # 上面の奥行き(内側への張り出し)
TAB_TOP = -3.0      # 上面の高さ(合わせ面基準) = 磁石厚3mmでツライチ
TAB_BOT = -12.0     # 下端
TAB_DRAFT = 1.7     # 背面(接着面)のドラフト
FENCE_W = 1.0       # 縁の幅
FENCE_H = 0.8       # 縁の高さ


def male_profile(w):
    """攻めバンド断面 (u, z)。w=ビード窓(0..1)。z=0が合わせ面。"""
    b = M_OUTER - BEAD * w
    return np.array([
        (GLUE_GAP, 0.0),                       # 段差ledge外端(受け上面に着座)
        (GLUE_GAP + DRAFT, GLUE_H),            # 接着ゾーン外面・上(ドラフト)
        (M_INNER, GLUE_H),                     # 接着ゾーン内面・上
        (M_INNER, -(TONGUE_L - 0.5)),          # 舌内面・先端チャンファ始まり
        (M_INNER - 0.5, -TONGUE_L),            # 先端内チャンファ
        (M_OUTER + 0.5, -TONGUE_L),            # 先端面
        (M_OUTER, -(TONGUE_L - 0.5)),          # 先端外チャンファ
        (M_OUTER, BEAD_Z - 0.45),              # ビード進入フランク基部
        (b, BEAD_Z - 0.15),                    # ビード頂(下)
        (b, BEAD_Z + 0.15),                    # ビード頂(上)
        (M_OUTER, BEAD_Z + 0.15 + FLANK_RET),  # 保持フランク基部
        (M_OUTER, 0.0),                        # 舌外面が合わせ面に達する角
    ])


def female_profile(_w=0.0):
    """受けバンド断面 (u, z)。内面に全周溝。z=0が合わせ面(上面)。"""
    gz = BEAD_Z  # 溝中心はビード中心に一致
    return np.array([
        (GLUE_GAP, 0.0),                       # 上面外端
        (F_INNER - 0.5, 0.0),                  # 上面内端(進入チャンファ始まり)
        (F_INNER, -0.6),                       # 進入チャンファ終わり
        (F_INNER, gz + 0.2 + FLANK_RET),       # 溝上フランク基部(保持側)
        (G_FLOOR, gz + 0.2),                   # 溝底・上
        (G_FLOOR, gz - 0.2),                   # 溝底・下
        (F_INNER, gz - 0.6),                   # 溝下フランク基部
        (F_INNER, -GLUE_H),                    # 内面・下端
        (GLUE_GAP + DRAFT, -GLUE_H),           # 外面・下端(ドラフト)
    ])


def shoelace(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def triangulate(poly):
    """単純多角形の耳切り三角形分割。CW巻き(v1のキャップ規約)で返す。"""
    n = len(poly)
    idx = list(range(n))
    if shoelace(poly) < 0:  # CCWに揃えて処理
        idx.reverse()

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        d1, d2, d3 = cross(a, b, p), cross(b, c, p), cross(c, a, p)
        return d1 > 1e-9 and d2 > 1e-9 and d3 > 1e-9

    tris = []
    guard = 10 * n
    while len(idx) > 3 and guard:
        guard -= 1
        m = len(idx)
        for k in range(m):
            i, j, l = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            if cross(poly[i], poly[j], poly[l]) <= 1e-12:
                continue
            if any(inside(poly[p], poly[i], poly[j], poly[l])
                   for p in idx if p not in (i, j, l)):
                continue
            tris.append((l, j, i))  # CW向きで格納
            idx.pop(k)
            break
        else:
            raise RuntimeError("ear clipping failed")
    if not guard:
        raise RuntimeError("ear clipping stalled")
    tris.append((idx[2], idx[1], idx[0]))
    return tris


def sweep_var(path, normals, profile_fn, windows):
    """位置ごとに変わる断面をパスに沿って掃引する(v1 sweepの一般化)。"""
    n_pts = len(path)
    profs = [profile_fn(w) for w in windows]
    m = len(profs[0])
    verts = np.empty((n_pts, m, 3))
    for i in range(n_pts):
        u, z = profs[i][:, 0], profs[i][:, 1]
        verts[i, :, 0] = path[i, 0] + u * normals[i, 0]
        verts[i, :, 1] = path[i, 1] + u * normals[i, 1]
        verts[i, :, 2] = z

    # 断面の巻きをv1と同じCWに揃える(キャップの向き規約のため)
    if shoelace(profs[0]) > 0:
        verts = verts[:, ::-1, :]
        profs = [p[::-1] for p in profs]

    tris = []
    for i in range(n_pts - 1):
        for j in range(m):
            k = (j + 1) % m
            a, b = verts[i, j], verts[i, k]
            c, d = verts[i + 1, k], verts[i + 1, j]
            tris.append((a, b, c))
            tris.append((a, c, d))
    cap = triangulate(profs[0])
    for i, flip in ((0, True), (n_pts - 1, False)):
        for (p, q, r) in triangulate(profs[i]):
            t = (verts[i, p], verts[i, q], verts[i, r])
            tris.append((t[0], t[2], t[1]) if flip else t)
    return np.array(tris)


def bead_windows(path):
    """パス各点のビード窓関数(0..1, 区間端はコサインランプ)。"""
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    w = np.zeros(len(s))
    half = BEAD_LEN / 2
    for c in BEAD_SEGS:
        d = np.abs(s - c)
        w = np.maximum(w, np.clip((half - d) / BEAD_RAMP, 0.0, 1.0))
    w = 0.5 - 0.5 * np.cos(np.pi * np.clip(w, 0, 1))
    return np.maximum(w, 1e-4)  # 完全な縮退三角形を避ける微小値


def check_mesh(tris, name):
    """向き付き稜線の整合チェック(ウォータータイト確認)。"""
    from collections import Counter
    c = Counter()
    for tr in tris:
        v = [tuple(np.round(p, 6)) for p in tr]
        for i in range(3):
            c[(v[i], v[(i + 1) % 3])] += 1
    bad = sum(1 for e, k in c.items() if c.get((e[1], e[0]), 0) != k)
    if bad:
        raise RuntimeError(f"{name}: {bad} unmatched directed edges")


def flip_z(tris, top):
    out = tris.copy()
    out[..., 2] = top - tris[..., 2]
    return out[:, ::-1, :]


def make_band(profile_fn, windows_fn, fname, flip_top=None, zshift=0.0):
    path = load_path()
    normals = inward_normals(path)
    windows = windows_fn(path)
    tris = sweep_var(path, normals, profile_fn, windows)
    if flip_top is not None:
        tris = flip_z(tris, flip_top)     # 印刷向き: 上下反転
    else:
        tris[..., 2] += zshift            # 印刷向き: 底をZ=0へ
    tris, vol = orient_outward(tris)
    tris = rotate_portrait(tris)
    check_mesh(tris, fname)
    mn, mx = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    print(f"{fname}: size {np.round(mx-mn,2)}  vol {vol/1000:.1f} cm^3")
    write_stl(OUT_DIR / fname, tris, fname.replace(".stl", ""))
    return tris


def make_coupon(profile_fn, window, fname, flip_top=None, zshift=0.0):
    """嵌合テスト用 40mm 直線クーポン。"""
    path = np.stack([np.linspace(0, 40.0, 21), np.zeros(21)], axis=1)
    normals = np.tile([[0.0, -1.0]], (21, 1))
    tris = sweep_var(path, normals, profile_fn, np.full(21, window))
    if flip_top is not None:
        tris = flip_z(tris, flip_top)
    else:
        tris[..., 2] += zshift
    tris, vol = orient_outward(tris)
    check_mesh(tris, fname)
    write_stl(OUT_DIR / fname, tris, fname.replace(".stl", ""))


def magnet_tab_profile(fence):
    """磁石タブ断面 (d=シェルからの奥行き, z)。fence=Trueで上面+0.8mmの縁。"""
    top = TAB_TOP + (FENCE_H if fence else 0.0)
    return np.array([
        (0.0, top),
        (TAB_D, top),
        (TAB_D, -4.5),
        (3.2, TAB_BOT),
        (TAB_DRAFT, TAB_BOT),
    ])


def make_magnet_tab():
    eps = 0.02
    ws = np.array([0.0, FENCE_W, FENCE_W + eps,
                   TAB_W - FENCE_W - eps, TAB_W - FENCE_W, TAB_W])
    fences = [True, True, False, False, True, True]
    path = np.stack([ws, np.zeros(len(ws))], axis=1)
    normals = np.tile([[0.0, -1.0]], (len(ws), 1))
    tris = sweep_var(path, normals,
                     lambda f: magnet_tab_profile(bool(f)),
                     np.array(fences, dtype=float))
    tris, vol = orient_outward(tris)
    # 印刷向き: 端面を下にして立てる (w軸→Z, d→X, z→Y)
    out = np.empty_like(tris)
    out[..., 0] = tris[..., 1]            # d → X
    out[..., 1] = tris[..., 2] - TAB_BOT  # z → Y (正に平行移動)
    out[..., 2] = tris[..., 0]            # w → Z
    out = out[:, ::-1, :]                 # 軸入替の鏡映を打ち消す
    out, vol = orient_outward(out)
    check_mesh(out, "magnet_tab")
    mn, mx = out.reshape(-1, 3).min(0), out.reshape(-1, 3).max(0)
    print(f"magnet tab: size {np.round(mx-mn,2)}  vol {vol/1000:.1f} cm^3")
    write_stl(OUT_DIR / "nosecone_magnet_tab.stl", out, "nosecone magnet tab")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    # 受け(シェルA側): 印刷向き=そのまま底上げ (深い側が下)
    make_band(female_profile, lambda p: np.zeros(len(p)),
              "nosecone_snap_band_female.stl", zshift=GLUE_H)
    # 攻め(シェルB側): 印刷向き=上下反転 (接着ゾーン上面が下)
    make_band(male_profile, bead_windows,
              "nosecone_snap_band_male.stl", flip_top=GLUE_H)
    # 嵌合テスト用クーポン(40mm直線, 攻めはビード全長)
    make_coupon(female_profile, 0.0,
                "nosecone_snap_coupon_female.stl", zshift=GLUE_H)
    make_coupon(male_profile, 1.0,
                "nosecone_snap_coupon_male.stl", flip_top=GLUE_H)
    make_magnet_tab()


if __name__ == "__main__":
    main()

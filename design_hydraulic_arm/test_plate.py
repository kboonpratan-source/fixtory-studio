#!/usr/bin/env python3
"""
test_plate.py — เพลททดสอบ 1 เพลท (Bambu A1 256×256) ก่อนพิมพ์ทั้งชุด · ใช้พารามิเตอร์เดิมทั้งหมดจาก params.py
ไม่แก้แบบเดิม: เรียกฟังก์ชันจาก build_parts.py แล้วเลือก/ตัดเฉพาะส่วนที่ต้องทดสอบ

  python3 test_plate.py [--T=6] [--SYR_D=29.5] ...

คูปอง (ป้ายนูน 0.6 มม. บนผิวบน):
  T1  คู่ทดสอบร่องสลัก: ชิ้น 13a (ร่อง 6.3 ยาว 22.9 / 11.7) + ชิ้น 12 และ 14 (ลิ้นเสียบร่องชิ้น 13 ตามการประกอบ)
  T2  ชิ้น 19 ×2 (รูแกนหมุน Ø PIVOT_D) — ทดสอบน็อต M4 หมุน
  T3  แถบรู: SYR_D · SYR2_D · HOSE_D · FIX_D (รูยึด M4)
  T4  คูปองรอยต่อจิ๊กซอว์ของฐาน (ตัดเฉพาะบริเวณปุ่มบนแนวตัดจริง) A/B ต่อกันได้
  T5  ชิ้น 9 ×1 (ผนังบางสุด ~2 มม.)
ผลลัพธ์: out/3mf/HydraulicArm2x_TEST_plate.3mf + .zip (ไม่ commit) · out/check/test_plate.png · out/check/test_plate.json
"""
import os, sys, json, math, zipfile
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely import affinity
from shapely.ops import unary_union
import build_parts as B

p = B.p
OUT = B.OUT
LABEL_H = 0.6   # ความสูงป้ายนูน (มม.)

# ------------------------------------------------------------------ ป้ายนูน
def text_poly(s, size):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), s, size=size, prop=FontProperties(family='DejaVu Sans', weight='bold'))
    G = None
    for ring in tp.to_polygons():
        if len(ring) < 3: continue
        q = Polygon(ring).buffer(0)
        G = q if G is None else G.symmetric_difference(q)
    b = G.bounds
    return affinity.translate(G, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)

def place_label(G, s, sizes=(6.0, 5.0, 4.2)):
    """หาตำแหน่งในเนื้อชิ้นที่วางป้ายได้ (ห่างรู/ขอบ ≥ 1 มม.) ใกล้จุดกลางที่สุด"""
    c = G.representative_point()
    minx, miny, maxx, maxy = G.bounds
    for size in sizes:
        txt0 = text_poly(s, size)
        for ang in (0, 90):
            txt = affinity.rotate(txt0, ang, origin=(0, 0))
            cands = [(x, y) for x in np.arange(minx, maxx, 0.75) for y in np.arange(miny, maxy, 0.75)]
            cands.sort(key=lambda q: (q[0] - c.x) ** 2 + (q[1] - c.y) ** 2)
            for (x, y) in cands:
                T = affinity.translate(txt, x, y)
                if G.contains(box(*T.bounds).buffer(1.0)):
                    return T
    return None

# ------------------------------------------------------------------ คูปอง
def hole_strip():
    gap = 4.0   # เนื้อระหว่างรู/ขอบ
    ds = [('SYR', p['SYR_D']), ('SYR2', p['SYR2_D']), ('HOSE', p['HOSE_D']), ('FIX', p['FIX_D'])]
    W = p['SYR_D'] + 2 * gap + 8.0           # เผื่อแถบป้ายด้านล่าง
    x = gap; holes = []
    for nm, d in ds:
        holes.append((nm, d, x + d / 2)); x += d + gap
    L = x
    G = box(0, 0, L, W)
    G = G.buffer(-2, join_style=1).buffer(2, join_style=1)  # มุมมน
    yc = gap + p['SYR_D'] / 2
    for nm, d, xc in holes:
        G = G.difference(Point(xc, yc).buffer(d / 2, resolution=96))
    return G, holes, yc

def jigsaw_coupons(win_w=46.0, win_h=56.0):
    Gb, _ = B.build_type('BASE')
    parts, meta = B.split_base(Gb)
    cy = meta['cut_y']; cx = meta['cut_x']
    A, Bp = parts[0], parts[1]          # ซ้ายบน / ซ้ายล่าง (แนวตัดนอน y=cy)
    # ปุ่มจิ๊กซอว์ = เนื้อที่ข้ามแนวตัด
    knobs = []
    for P, side in ((A, +1), (Bp, -1)):
        over = P.intersection(box(-1e4, cy + 0.5, 1e4, 1e4) if side > 0 else box(-1e4, -1e4, 1e4, cy - 0.5))
        for g in getattr(over, 'geoms', [over]):
            if g.area > 5: knobs.append((g.centroid.x, side))
    knobs.sort(key=lambda k: abs(k[0] - (Gb.bounds[0] + cx) / 2))
    for kx, side in knobs:
        W = box(kx - win_w / 2, cy - win_h / 2, kx + win_w / 2, cy + win_h / 2)
        if W.bounds[2] > cx - 3: continue
        ca = A.intersection(W).buffer(0); cb = Bp.intersection(W).buffer(0)
        if ca.geom_type == 'Polygon' and cb.geom_type == 'Polygon' and ca.area > 400 and cb.area > 400:
            return ca, cb, dict(cut_y=float(cy), knob_x=float(kx), window=[win_w, win_h])
    raise RuntimeError('no jigsaw window')

# ------------------------------------------------------------------ จัดเพลท
def orient(G, L):
    """ชิ้นจากสแกนวางแนวแกนอยู่แล้ว — เลือกหมุน 0/90 องศาให้กล่องเล็กสุด (ไม่เอียง)"""
    org = G.centroid
    best = None
    for a in (0, 90):
        Q = affinity.rotate(G, a, origin=org); b = Q.bounds; ar = (b[2] - b[0]) * (b[3] - b[1])
        if best is None or ar < best[0] - 1: best = (ar, a)
    a = best[1]
    G2 = affinity.rotate(G, a, origin=org); L2 = affinity.rotate(L, a, origin=org) if L is not None else None
    b = G2.bounds
    return affinity.translate(G2, -b[0], -b[1]), (affinity.translate(L2, -b[0], -b[1]) if L2 is not None else None)

def main():
    items = []   # (name, coupon, G)
    G13, _ = B.build_type('P13A'); items.append(('13a', 'T1', G13))
    G12, _ = B.build_type('P12'); items.append(('12', 'T1', G12))
    G14, _ = B.build_type('P14'); items.append(('14', 'T1', G14))
    G19, _ = B.build_type('P19'); items += [('19#1', 'T2', G19), ('19#2', 'T2', G19)]
    Gs, holes, yc = hole_strip(); items.append(('holes', 'T3', Gs))
    ja, jb, jmeta = jigsaw_coupons(); items += [('jig-A', 'T4', ja), ('jig-B', 'T4', jb)]
    G9, _ = B.build_type('P09'); items.append(('9', 'T5', G9))

    placed_items = []
    for name, cp, G in items:
        G = B.clean(G).simplify(0.02, preserve_topology=True)   # ตัดจุดซ้ำซ้อนเล็กมาก (ให้ mesh ปิดสนิท)
        lab = place_label(G, cp + ('A' if name == 'jig-A' else 'B' if name == 'jig-B' else ''))
        Q, Lq = orient(G, lab)
        b = Q.bounds
        placed_items.append(dict(name=name, coupon=cp, G=Q, L=Lq, w=b[2], h=b[3]))
    # MaxRects (ใช้ของเดิม) — เพลทเดียว
    inner = p['BED'] - 2 * p['PLATE_MARGIN']; gap = 6.0
    order = sorted(placed_items, key=lambda it: -(max(it['w'], it['h']) * 1000 + it['w'] * it['h'] / 1000))
    mr = B.MaxRects(inner + gap, inner + gap)
    plate = []
    for it in order:
        r = mr.insert(it['w'] + gap, it['h'] + gap)
        assert r, ('ไม่พอเพลทเดียว', it['name'])
        x, y, rot = r
        G, L = it['G'], it['L']
        if rot:
            G = affinity.rotate(G, 90, origin=(0, 0)); L = affinity.rotate(L, 90, origin=(0, 0)) if L is not None else None
            b = G.bounds; G = affinity.translate(G, -b[0], -b[1]); L = affinity.translate(L, -b[0], -b[1]) if L is not None else None
        dx, dy = x + p['PLATE_MARGIN'], y + p['PLATE_MARGIN']
        plate.append(dict(it, G=affinity.translate(G, dx, dy), L=affinity.translate(L, dx, dy) if L is not None else None))
    # จัดกึ่งกลางเพลท
    ub = unary_union([q['G'] for q in plate]).bounds
    sx = (p['BED'] - (ub[2] - ub[0])) / 2 - ub[0]; sy = (p['BED'] - (ub[3] - ub[1])) / 2 - ub[1]
    for q in plate:
        q['G'] = affinity.translate(q['G'], sx, sy)
        if q['L'] is not None: q['L'] = affinity.translate(q['L'], sx, sy)
    # ---------------- ตรวจ
    ub = unary_union([q['G'] for q in plate]).bounds
    assert ub[0] >= 0 and ub[1] >= 0 and ub[2] <= p['BED'] and ub[3] <= p['BED'], ub
    for a in range(len(plate)):
        for c in range(a + 1, len(plate)):
            assert plate[a]['G'].distance(plate[c]['G']) >= gap - 0.01, (plate[a]['name'], plate[c]['name'])
        if plate[a]['L'] is not None:
            assert plate[a]['G'].contains(plate[a]['L']), plate[a]['name']
    checks = []
    for q in plate:
        for ring in q['G'].interiors:
            H = Polygon(ring); bb = H.bounds; w, h = bb[2] - bb[0], bb[3] - bb[1]
            circ = 4 * math.pi * H.area / ring.length ** 2
            if circ > 0.99: checks.append((q['name'], 'รูกลม', round(2 * math.sqrt(H.area / math.pi), 2)))
            elif abs(min(w, h) - p['SLOT_W']) < 0.05 or True:
                mrr = H.minimum_rotated_rectangle; cc = np.array(mrr.exterior.coords)
                e = sorted([np.linalg.norm(cc[1] - cc[0]), np.linalg.norm(cc[2] - cc[1])])
                checks.append((q['name'], 'ร่อง', round(e[0], 2), round(e[1], 2)))
    # ---------------- น้ำหนัก
    tot_g = 0; rows = []
    for q in plate:
        v, g = B.pla_weight(q['G'])
        if q['L'] is not None: g += q['L'].area * LABEL_H / 1000 * p['PLA_DENSITY']
        tot_g += g; b = q['G'].bounds
        rows.append(dict(name=q['name'], coupon=q['coupon'], size=f"{b[2]-b[0]:.1f}×{b[3]-b[1]:.1f}", g=round(g, 1),
                         label=q['L'] is not None))
    vol_cm3 = sum(B.pla_weight(q['G'])[1] for q in plate) / p['PLA_DENSITY']
    # เวลาพิมพ์ประมาณ: Bambu A1 0.2 มม. Standard — ชิ้นเล็กหลายชิ้น เฉลี่ยราว 7 mm³/s รวมเดินหัว/ชั้นแรก + เตรียมเครื่อง ~6 นาที
    t_min = vol_cm3 * 1000 / 7.0 / 60 + 6
    # ---------------- 3MF
    import trimesh
    d3 = os.path.join(OUT, '3mf'); os.makedirs(d3, exist_ok=True)
    sc = trimesh.Scene()
    for q in plate:
        m = trimesh.creation.extrude_polygon(q['G'], p['T'], engine='earcut'); assert m.is_watertight, q['name']
        ms = [m]
        if q['L'] is not None:
            for g in getattr(q['L'], 'geoms', [q['L']]):
                t = trimesh.creation.extrude_polygon(g, LABEL_H, engine='earcut'); t.apply_translation([0, 0, p['T']])
                ms.append(t)
        M = trimesh.util.concatenate(ms)
        nm = f"{q['coupon']}_{q['name'].replace('#', '_n')}"
        sc.add_geometry(M, geom_name=nm, node_name=nm)
    f3 = os.path.join(d3, 'HydraulicArm2x_TEST_plate.3mf'); sc.export(f3, file_type='3mf')
    fz = os.path.join(d3, 'HydraulicArm2x_TEST_plate.zip')
    with zipfile.ZipFile(fz, 'w', zipfile.ZIP_DEFLATED) as z: z.write(f3, os.path.basename(f3))
    assert os.path.getsize(fz) <= 2_000_000
    # ---------------- ภาพเพลท
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Rectangle
    from matplotlib import font_manager
    th = [f for f in font_manager.findSystemFonts() if 'Sarabun' in f or 'Loma' in f or 'Garuda' in f or 'Waree' in f or 'FreeSerif' in f]
    fp = font_manager.FontProperties(fname=th[0]) if th else None
    fig, ax = plt.subplots(figsize=(8.6, 9.4))
    ax.add_patch(Rectangle((0, 0), p['BED'], p['BED'], fill=False, lw=1.4, ec='k'))
    col = {'T1': '#4C9BE8', 'T2': '#E8A33C', 'T3': '#6CC07A', 'T4': '#C77DD8', 'T5': '#E86A6A'}
    for q in plate:
        ax.add_patch(MP(np.array(q['G'].exterior.coords), closed=True, fc=col[q['coupon']], ec='k', lw=0.6, alpha=0.85))
        for h in q['G'].interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc='white', ec='k', lw=0.5))
        if q['L'] is not None:
            for g in getattr(q['L'], 'geoms', [q['L']]):
                ax.add_patch(MP(np.array(g.exterior.coords), closed=True, fc='#222', ec='none'))
                for h in g.interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc=col[q['coupon']], ec='none'))
        b = q['G'].bounds
        ax.text((b[0] + b[2]) / 2, b[1] - 3.2, q['name'], ha='center', va='center', fontsize=7)
    ax.set_xlim(-3, p['BED'] + 3); ax.set_ylim(-3, p['BED'] + 3)   # มุมมองบนแบบ Bambu Studio (y ขึ้น); ax.set_aspect('equal'); ax.set_axis_off()
    ttl = (f'Hydraulic Arm 2x — TEST plate (Bambu A1 256×256, T={p["T"]:g})\n'
           f'~{tot_g:.0f} g PLA (infill 15%, 3 walls) · ~{t_min / 60:.1f} h (est.) · slot {p["SLOT_W"]:.1f} · pivot Ø{p["PIVOT_D"]} · fix Ø{p["FIX_D"]}\n'
           f'T1 slot pair 13a+12+14 · T2 part 19 ×2 · T3 holes Ø{p["SYR_D"]}/{p["SYR2_D"]}/{p["HOSE_D"]}/{p["FIX_D"]} · T4 base jigsaw · T5 part 9')
    ax.set_title(ttl, fontsize=9)
    fig.tight_layout()
    fpng = os.path.join(OUT, 'check', 'test_plate.png'); fig.savefig(fpng, dpi=160); plt.close(fig)
    summ = dict(params={k: p[k] for k in ('T', 'SLOT_W', 'PIVOT_D', 'FIX_D', 'SYR_D', 'SYR2_D', 'HOSE_D', 'PILOT_D', 'JIG_CLR')},
                total_g=round(tot_g, 1), est_print_min=round(t_min), parts=rows, jigsaw=jmeta,
                features=checks, bed=p['BED'], extent=[round(v, 1) for v in unary_union([q['G'] for q in plate]).bounds],
                zip=os.path.basename(fz), zip_bytes=os.path.getsize(fz))
    json.dump(summ, open(os.path.join(OUT, 'check', 'test_plate.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != 'features'}, ensure_ascii=False, indent=1))
    for c in checks: print(c)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
build_parts.py — สร้างแบบแขนกลไฮดรอลิก 2x จาก build/traced_1x.json (ผลจาก trace_scans.py)

  python3 build_parts.py [--T=6] [--SYR_D=29.5] [--SLOT_CLR=0.3] ... (ดู params.py)

ผลลัพธ์ (โฟลเดอร์ out/):
  laser/board_X.svg, .dxf      แผ่นตัดเลเซอร์ขนาดจริง (มม.) เส้นตัดแดง 0.1
  print_1to1_A4.pdf            แบบพิมพ์กระดาษ 1:1 ต่อ A4 (แถบวัด 100 มม. + เลขแผ่น)
  parts_table.csv / .md        ตารางชิ้น น้ำหนัก น็อต กระบอก/สายยาง
  check/overlay_S*.png         ภาพซ้อนเวกเตอร์ใหม่ทับสแกน (×2 เท่ากัน)
  check/plates_preview.png     ภาพเพลท 3MF
  3mf/plate_NN.3mf             (ไม่ commit — อัปโหลด Google Drive)
"""
import os, sys, json, math, csv
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, LineString, box
from shapely import affinity
from shapely.ops import unary_union
from params import from_argv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
p = from_argv(sys.argv[1:])
S = p['SCALE']
R = json.load(open(os.path.join(HERE, 'build', 'traced_1x.json')))
PX = R['px_mm']

NUM = {'BASE': 'ฐาน', 'P01': '1', 'P02A': '2', 'P02B': '2', 'P03': '3', 'P04': '4', 'P05': '5', 'P06': '6', 'P07': '7',
       'P08': '8', 'P09': '9', 'P10': '10', 'P11A': '11', 'P11B': '11', 'P12': '12', 'P13A': '13', 'P13B': '13',
       'P13C': '13', 'P14': '14', 'P15': '15', 'P16': '16', 'P17': '17', 'P18A': '18', 'P18B': '18', 'P19': '19', 'P20': '20'}
LABEL = {'BASE': 'BASE', 'P02A': '2a', 'P02B': '2b', 'P11A': '11a', 'P11B': '11b', 'P13A': '13a', 'P13B': '13b',
         'P13C': '13c', 'P18A': '18a', 'P18B': '18b'}
def label(t): return LABEL.get(t, NUM[t])

def clean(G):
    G = G.buffer(0)
    if G.geom_type == 'MultiPolygon':
        G = max(G.geoms, key=lambda q: q.area)
    return G

def rect_along(p0, u, length, width, ext0=0.0, ext1=0.0):
    """สี่เหลี่ยมจาก p0 ไปตามทิศ u ยาว length กว้าง width (ต่อปลาย ext)"""
    u = np.array(u, float); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]])
    a = np.array(p0) - u * ext0; b = np.array(p0) + u * (length + ext1)
    w = width / 2
    return Polygon([a + v * w, b + v * w, b - v * w, a - v * w])

def rect_center(c, L, W, ang):
    a = math.radians(ang); u = np.array([math.cos(a), math.sin(a)])
    return rect_along(np.array(c) - u * L / 2, u, L, W)

# ------------------------------------------------------------------ hole classes
def hole_class(typ, f, all_feats):
    d = f['d']
    if d >= 12: return 'SYR', p['SYR_D']
    if d >= 8: return 'SYR2', p['SYR2_D']
    if d >= 4.2: return 'HOSE', p['HOSE_D']
    if typ == 'BASE': return 'FIX', p['FIX_D']
    if typ == 'P04':
        cs = np.array([g['c'] for g in all_feats if g['kind'] == 'circle']); cen = cs.mean(0)
        return ('PIVOT', p['PIVOT_D']) if np.hypot(*(np.array(f['c']) - cen)) < 3 else ('FIX', p['FIX_D'])
    if typ == 'P16':
        ys = [g['c'][1] for g in all_feats if g['kind'] == 'circle']
        if f['c'][1] == max(ys): return 'FIX', p['FIX_D']
    return ('PIVOT', p['PIVOT_D']) if d >= 2.0 else ('FIX', p['FIX_D'])

# ------------------------------------------------------------------ build one type (2x, พิกัดสแกน×2)
def build_type(tid):
    t = R['types'][tid]
    O1 = Polygon(t['outline'])
    fill1, cuts, holes_info = [], [], []
    SW = p['SLOT_W']
    notches = list(t['notches'])
    # ชิ้นสมมาตรแกนตั้ง: เติมร่องคู่สะท้อนที่ตรวจไม่เจอ
    if t['sym'] and 'x' in t['sym'] and tid != 'BASE':
        mx = (O1.bounds[0] + O1.bounds[2]) / 2
        for n in list(notches):
            mc = [2 * mx - n['c'][0], n['c'][1]]
            if not any(np.hypot(m['c'][0] - mc[0], m['c'][1] - mc[1]) < 1.0 for m in notches):
                m = dict(n); m['c'] = mc
                m['open_end'] = [2 * mx - n['open_end'][0], n['open_end'][1]]
                m['closed_end'] = [2 * mx - n['closed_end'][0], n['closed_end'][1]]
                notches.append(m)
    if tid == 'P06':
        # ร่องข้างกลางชิ้น (ขอบหยักจากเงาสแกน ตรวจอัตโนมัติไม่ได้) — วัดจากสแกน: ปลายปิด (80.84,137.15) ลึก 8.7 เปิดไปทาง -x
        notches.append(dict(c=[76.5, 137.15], L=8.7, W=4.6, ang=0.0, open_end=[72.14, 137.15], closed_end=[80.84, 137.15]))
    for n in notches:
        ce, oe = np.array(n['closed_end']), np.array(n['open_end'])
        u = (oe - ce) / np.linalg.norm(oe - ce)
        fill1.append(rect_along(ce, u, n['L'], n['W'] + 0.8, ext0=0.2, ext1=0.0).intersection(O1.convex_hull))
        cuts.append(rect_along(ce * S, u, n['L'] * S, SW, ext1=3.0))
        holes_info.append(('NOTCH', n['L'] * S, SW))
    ts = t.get('extra', {}).get('tslot')
    if ts:
        fill1.append(Polygon(ts['region']).buffer(0.05))
        b, st = ts['bar'], ts['stem']
        yc = (b['y0'] + b['y1']) / 2
        cuts.append(box(b['x0'] * S, yc * S - SW / 2, b['x1'] * S, yc * S + SW / 2))
        sx = (st['x0'] + st['x1']) / 2 * S; sw = (st['x1'] - st['x0']) * S
        ye = st['edge_y'] * S + (-3 if st['up'] else 3)
        cuts.append(box(sx - sw / 2, min(yc * S, ye), sx + sw / 2, max(yc * S, ye)))
        holes_info.append(('TSLOT', (b['x1'] - b['x0']) * S, SW))
    if tid == 'P02A':
        # เขี้ยวล็อกบนหูทั้งสองข้าง (ต้นฉบับหลุดออกด้านเดียว) — ร่องขั้นบันได ×2
        minx, miny, maxx, maxy = O1.bounds
        strip = O1.intersection(box(minx, miny, minx + 1.0, maxy))
        cy = (strip.bounds[1] + strip.bounds[3]) / 2
        fill1.append(box(minx, cy - 1.2, minx + 5.4, cy + 1.2))
        for side in (-1, 1):
            x_edge = (minx if side < 0 else maxx) * S
            u = np.array([1.0 if side < 0 else -1.0, 0.0])
            cuts.append(rect_along([x_edge, cy * S], u, 2.7 * S, 1.6 * S, ext0=3))
            cuts.append(rect_along([x_edge, cy * S], u, 5.0 * S, 0.8 * S, ext0=3))
        holes_info.append(('BARB', 5.0 * S, 1.6 * S))
    G1 = unary_union([O1] + fill1)
    # ปิดรอยแหว่งจิ๋ว (<0.8 มม. ที่ 1:1) ที่เหลือจากเงาสแกน/สะพานไมโครแท็บ
    G1 = G1.buffer(0.4, join_style=2).buffer(-0.4, join_style=2)
    if tid == 'BASE':
        G1 = O1
    G = affinity.scale(G1, S, S, origin=(0, 0))
    G = Polygon(G.exterior) if G.geom_type == 'Polygon' else clean(G)
    for f in t['feats']:
        if f['kind'] == 'circle':
            cls, d = hole_class(tid, f, t['feats'])
            cx_, cy_ = f['c'][0] * S, f['c'][1] * S
            if tid == 'P09' and f['d'] < 2.0 and ts:
                # รูนำเล็กชิดร่อง T: ใช้รูนำสกรูเกลียวปล่อย และเลื่อนออกจากร่อง (ผนังเดิมเหลือ 0.7 มม.)
                cls, d = 'PILOT', p['PILOT_D']
                ybar = (ts['bar']['y0'] + ts['bar']['y1']) / 2 * S
                cy_ += p['P09_PILOT_SHIFT'] * (1 if cy_ > ybar else -1)
            cuts.append(Point(cx_, cy_).buffer(d / 2, resolution=64))
            holes_info.append((cls, d, d))
        elif f['kind'] == 'slot':
            cuts.append(rect_center([f['c'][0] * S, f['c'][1] * S], f['L'] * S, SW, f['ang']))
            holes_info.append(('SLOT', f['L'] * S, SW))
    G = clean(G.difference(unary_union(cuts)))
    return G, holes_info

# ------------------------------------------------------------------ instances
def inst_geom(G, i):
    Q = G
    if i['mirror']: Q = affinity.scale(Q, -1, 1, origin=(0, 0))
    Q = affinity.rotate(Q, i['rot'], origin=(0, 0))
    return affinity.translate(Q, i['dx'] * S, i['dy'] * S)

# ------------------------------------------------------------------ jigsaw split
def knob_shape(x, c, r, sign):
    """ปุ่มจิ๊กซอว์ บนเส้น y=c ยื่นไปทาง sign (+1 ลง / -1 ขึ้น)"""
    neck = box(x - 0.5 * r, min(c - sign * 0.3, c + sign * 1.3 * r), x + 0.5 * r, max(c - sign * 0.3, c + sign * 1.3 * r))
    head = Point(x, c + sign * 1.45 * r).buffer(r, resolution=48)
    return unary_union([neck, head])

def cut_ok(G, c, x0, x1, margin=2.5):
    """เส้นตัด y=c ช่วง x0..x1 ต้องไม่ผ่านรู/ร่อง"""
    holes = unary_union([Polygon(h) for h in G.interiors]) if G.interiors else None
    ln = LineString([(x0, c), (x1, c)]).intersection(Polygon(G.exterior))
    if holes is not None and ln.buffer(margin).intersects(holes): return False
    return True

def find_knobs(G, c, x0, x1, n, sign0=1):
    """หาตำแหน่ง/ขนาดปุ่มที่อยู่ในเนื้อชิ้นทั้งสองฝั่ง ห่างรู/ขอบ ≥1.5"""
    out = []
    seg = (x1 - x0) / n
    for k in range(n):
        sign = sign0 if k % 2 == 0 else -sign0
        best = None
        for r in np.arange(min(7.0, seg / 3.2), 2.4, -0.5):
            for frac in np.linspace(0.5, 0.15, 8):
                for xx in (x0 + seg * (k + frac), x0 + seg * (k + 1 - frac)):
                    K = knob_shape(xx, c, r, sign)
                    if G.contains(K.buffer(1.5)) and Polygon(G.exterior).contains(knob_shape(xx, c, r, -sign).buffer(1.5)):
                        if all(K.distance(o[3]) > 3 for o in out):
                            best = (xx, r, sign, K); break
                if best: break
            if best: break
        if best: out.append(best)
    return out

def jig_split_h(G, c, knobs):
    big = 1e5
    A = G.intersection(box(-big, -big, big, c)); B = G.intersection(box(-big, c, big, big))
    for (x, r, sign, K) in knobs:
        if sign > 0:   # ยื่นลง: ปุ่มเป็นของ A
            A = unary_union([A, K.intersection(G)]); B = B.difference(K.buffer(p['JIG_CLR']))
        else:
            B = unary_union([B, K.intersection(G)]); A = A.difference(K.buffer(p['JIG_CLR']))
    return clean(A), clean(B)

def split_long(G, name):
    """ชิ้นยาว (แนวตั้ง) → 2 ท่อน ตัดแนวนอน"""
    minx, miny, maxx, maxy = G.bounds
    L = maxy - miny
    lo, hi = maxy - p['MAX_LEN'] + 5, miny + p['MAX_LEN'] - 5
    cands = sorted(np.arange(max(lo, miny + 20), min(hi, maxy - 20), 0.5), key=lambda y: abs(y - (miny + maxy) / 2))
    for c in cands:
        if not cut_ok(G, c, minx - 1, maxx + 1): continue
        kn = find_knobs(G, c, minx, maxx, 1)
        if kn and kn[0][1] >= 3.0:
            A, B = jig_split_h(G, c, kn)
            return [A, B], dict(cut_y=c, knobs=[(k[0], k[1]) for k in kn])
    raise RuntimeError('split fail ' + name)

def split_base(G):
    """แผ่นฐาน → 4 ชิ้น (ตัดตั้ง + ตัดนอน) รอยต่อจิ๊กซอว์ 2 ปุ่มต่อช่วง"""
    minx, miny, maxx, maxy = G.bounds
    cx0 = (minx + maxx) / 2; cy0 = (miny + maxy) / 2
    Gr = affinity.rotate(G, 90, origin=(0, 0))     # (x,y)→(-y,x): เส้นตั้ง x=c ⇔ เส้นนอน y'=c
    holes = unary_union([Polygon(h) for h in G.interiors])
    def clearance_v(x):
        return LineString([(x, miny - 1), (x, maxy + 1)]).distance(holes)
    def clearance_h(y):
        return LineString([(minx - 1, y), (maxx + 1, y)]).distance(holes)
    lim = p['BED'] - 2 * p['PLATE_MARGIN']
    cx = max([x for x in np.arange(cx0 - 45, cx0 + 45, 0.25) if max(x - minx, maxx - x) <= lim],
             key=lambda x: min(clearance_v(x), 6) - 0.02 * abs(x - cx0))
    cy = max(np.arange(cy0 - 40, cy0 + 40, 0.5), key=lambda y: min(clearance_h(y), 15) - 0.02 * abs(y - cy0))
    assert clearance_v(cx) >= 2.0 and clearance_h(cy) >= 4.0, (cx, cy)
    kn_v = []
    for (a, b) in ((miny, cy), (cy, maxy)):
        kn_v += find_knobs(Gr, cx, -b + 10, -a - 10, 2)
    Lr, Rr = jig_split_h(Gr, cx, kn_v)   # Lr: y'<cx ⇒ x<cx (ซ้าย)
    left = affinity.rotate(Lr, -90, origin=(0, 0)); right = affinity.rotate(Rr, -90, origin=(0, 0))
    parts = []
    for half, (a, b) in ((left, (minx, cx)), (right, (cx, maxx))):
        kn = find_knobs(half, cy, a + 8, b - 8, 2)
        A, B = jig_split_h(half, cy, kn)
        parts += [A, B]
    return parts, dict(cut_x=cx, cut_y=cy)

# ------------------------------------------------------------------ PLA weight
def pla_weight(G):
    T = p['T']; area = G.area
    perim = G.exterior.length + sum(i.length for i in G.interiors)
    ww = p['WALLS'] * p['LINE_W']; hm = max(T - 2 * p['TOPBOT'], 0)
    v = perim * ww * hm + area * 2 * min(p['TOPBOT'], T / 2) + max(area - perim * ww, 0) * hm * p['INFILL']
    return area * T / 1000.0, v / 1000.0 * p['PLA_DENSITY']

# ------------------------------------------------------------------ MaxRects
class MaxRects:
    def __init__(s, W, H): s.W, s.H = W, H; s.free = [(0, 0, W, H)]; s.used = []
    def insert(s, w, h):
        best = None
        for (fx, fy, fw, fh) in s.free:
            for (ww, hh, rot) in ((w, h, False), (h, w, True)):
                if ww <= fw + 1e-6 and hh <= fh + 1e-6:
                    sc = (min(fw - ww, fh - hh), fy, fx)
                    if best is None or sc < best[0]: best = (sc, fx, fy, ww, hh, rot)
        if best is None: return None
        _, x, y, ww, hh, rot = best
        nr = (x, y, ww, hh); s.used.append(nr)
        newf = []
        for f in s.free:
            fx, fy, fw, fh = f
            if x >= fx + fw or x + ww <= fx or y >= fy + fh or y + hh <= fy: newf.append(f); continue
            if x > fx: newf.append((fx, fy, x - fx, fh))
            if x + ww < fx + fw: newf.append((x + ww, fy, fx + fw - x - ww, fh))
            if y > fy: newf.append((fx, fy, fw, y - fy))
            if y + hh < fy + fh: newf.append((fx, y + hh, fw, fy + fh - y - hh))
        s.free = [a for a in newf if not any(a != b and a[0] >= b[0] and a[1] >= b[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3] for b in newf)]
        return x, y, rot

def min_bbox_orient(G):
    """หมุนชิ้นให้ bounding box เล็กสุด (ประหยัดเพลท)"""
    mrr = G.minimum_rotated_rectangle
    c = np.array(mrr.exterior.coords)[:4]
    e = c[1] - c[0]; ang = math.degrees(math.atan2(e[1], e[0]))
    best = None
    for a in (-ang, -ang + 90, 0):
        Q = affinity.rotate(G, a, origin='centroid')
        b = Q.bounds; ar = (b[2] - b[0]) * (b[3] - b[1])
        if best is None or ar < best[0] - 1: best = (ar, Q)
    return best[1]

# ================================================================== main
def main():
    os.makedirs(OUT, exist_ok=True)
    for d in ('laser', 'check', '3mf'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
    geoms, info = {}, {}
    for tid in R['types']:
        geoms[tid], info[tid] = build_type(tid)
    insts = []
    for i in R['instances']:
        insts.append(dict(i, G=inst_geom(geoms[i['type']], i)))
    # ---------------- ตรวจ
    report = []
    for tid, G in geoms.items():
        assert G.is_valid and G.geom_type == 'Polygon', tid
    # ---------------- ตารางชิ้น
    qty = {}
    for i in insts: qty[i['type']] = qty.get(i['type'], 0) + 1
    rows = []
    for tid in sorted(geoms, key=lambda k: (99 if k == 'BASE' else int(''.join(ch for ch in NUM[k] if ch.isdigit())), k)):
        G = geoms[tid]; b = G.bounds
        vol, w = pla_weight(G)
        hi = info[tid]
        cnt = {}
        for (cls, a, bb) in hi: cnt[cls] = cnt.get(cls, 0) + 1
        rows.append(dict(type=tid, label=label(tid), name=R['types'][tid]['name'], qty=qty[tid], w=b[2] - b[0], h=b[3] - b[1],
                         area_cm2=G.area / 100, vol=vol, g=w, feats=cnt))
    # ---------------- พิมพ์ 3 มิติ: แบ่งชิ้น + เพลท
    printparts = []
    splits = {}
    for tid, G in geoms.items():
        b = G.bounds; L = max(b[2] - b[0], b[3] - b[1])
        Gl = G
        if tid == 'BASE':
            parts, meta = split_base(G); splits[tid] = meta
        elif L > p['MAX_LEN']:
            rot = (b[2] - b[0]) > (b[3] - b[1])
            Gl = affinity.rotate(G, 90, origin=(0, 0)) if rot else G
            parts, meta = split_long(Gl, tid); splits[tid] = meta
        else:
            parts = [G]
        for k in range(qty[tid]):
            for j, Q in enumerate(parts):
                nm = f"{label(tid)}" + (f"-{'ABCD'[j]}" if len(parts) > 1 else '') + (f"#{k + 1}" if qty[tid] > 1 else '')
                printparts.append(dict(type=tid, name=nm, G=Q))
    inner = p['BED'] - 2 * p['PLATE_MARGIN']; gap = p['PART_GAP']
    items = []
    for it in printparts:
        Q = min_bbox_orient(it['G']); b = Q.bounds
        Q = affinity.translate(Q, -b[0], -b[1])
        items.append(dict(it, G=Q, w=b[2] - b[0], h=b[3] - b[1]))
        assert b[2] - b[0] <= inner + 1e-6 or b[3] - b[1] <= inner, it['name']
    items.sort(key=lambda it: -(max(it['w'], it['h']) * 1000 + it['w'] * it['h'] / 1000))
    plates = []
    for it in items:
        placed = False
        for pl in plates:
            r = pl['mr'].insert(it['w'] + gap, it['h'] + gap)
            if r: pl['items'].append((it, r)); placed = True; break
        if not placed:
            mr = MaxRects(inner + gap, inner + gap); r = mr.insert(it['w'] + gap, it['h'] + gap)
            assert r, it['name']
            plates.append(dict(mr=mr, items=[(it, r)]))
    plate_geoms = []
    for pl in plates:
        lst = []
        for it, (x, y, rot) in pl['items']:
            Q = it['G']
            if rot:
                Q = affinity.rotate(Q, 90, origin=(0, 0)); b = Q.bounds; Q = affinity.translate(Q, -b[0], -b[1])
            Q = affinity.translate(Q, x + p['PLATE_MARGIN'], y + p['PLATE_MARGIN'])
            lst.append((it['name'], it['type'], Q))
        plate_geoms.append(lst)
    # ---------------- ตรวจเพลท
    for k, lst in enumerate(plate_geoms):
        allb = unary_union([q for _, _, q in lst]).bounds
        assert allb[0] >= 0 and allb[1] >= 0 and allb[2] <= p['BED'] and allb[3] <= p['BED'], (k, allb)
        for a in range(len(lst)):
            for c in range(a + 1, len(lst)):
                assert lst[a][2].distance(lst[c][2]) >= gap - 0.01, (k, lst[a][0], lst[c][0])
    json.dump(dict(params=p, rows=rows, splits={k: {kk: (vv if not isinstance(vv, np.floating) else float(vv)) for kk, vv in v.items()} for k, v in splits.items()},
                   plates=[[n for n, _, _ in lst] for lst in plate_geoms]),
              open(os.path.join(OUT, 'build_summary.json'), 'w'), ensure_ascii=False, indent=1, default=float)
    import exporters
    exporters.run(p, R, geoms, info, insts, rows, plate_geoms, splits, OUT, label)

if __name__ == '__main__':
    main()

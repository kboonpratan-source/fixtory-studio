#!/usr/bin/env python3
"""
trace_scans.py — สกัดเส้นตัดจากสแกน 200 dpi (S1..S4) แล้วสร้างเวกเตอร์สะอาดที่ขนาด 1:1 ของต้นฉบับ
ผลลัพธ์: build/traced_1x.json  (หน่วย มม. พิกัดสแกน y ชี้ลง)

ขั้นตอน
 1. แยกเนื้อไม้ (สีเหลือง) / เส้นเลเซอร์ (เข้ม) → ชิ้น = connected component ของเนื้อไม้ที่ถูกเส้นตัดแบ่ง
 2. ขยายขอบออกจนทับ "กึ่งกลางเส้นตัด" (เลือกค่าที่ความเข้มเฉลี่ยตามขอบมากสุด)
 3. ประกอบขอบใหม่เป็น เส้นตรง (fit least-squares, snap 0/90°) + ส่วนโค้ง (fillet/วงกลม fit) — ไม่ใช่ polyline สั่น ๆ จากพิกเซล
 4. รู: วงกลม → fit วงกลม · ร่องปิด → สี่เหลี่ยม · ร่องเปิด (notch) หาโดย morphological closing
 5. ชิ้นสมมาตร: ใช้ครึ่งหนึ่งแล้วสะท้อน · ชิ้นซ้ำ: ใช้ชิ้นต้นแบบเดียว วางทับตำแหน่งอื่นด้วยการหมุน/กลับด้านที่ IoU ดีสุด
ใช้: python3 trace_scans.py <โฟลเดอร์สแกน>
"""
import sys, json, math, os
import numpy as np, cv2
from shapely.geometry import Polygon, MultiPolygon, Point, LineString, box
from shapely import affinity
from shapely.ops import unary_union

PX = 25.4 / 200.0          # มม./พิกเซล
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build'); os.makedirs(BUILD, exist_ok=True)

# ---------------------------------------------------------------- 1. segmentation
def segment(path):
    im = cv2.imread(path)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    wood = ((hsv[..., 0] >= 12) & (hsv[..., 0] <= 40) & (hsv[..., 1] >= 14) & (g > 150)).astype(np.uint8)
    wood = cv2.morphologyEx(wood, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    line = (g < 150).astype(np.uint8)
    lined = cv2.dilate(line, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    mat = wood & (1 - lined)
    n, lab, st, _ = cv2.connectedComponentsWithStats(mat, connectivity=4)
    return im, cv2.GaussianBlur(g.astype(float), (3, 3), 0), lab, st, hsv

def ring_dark(g, ring_coords):
    ring = LineString(ring_coords); L = ring.length
    ts = np.linspace(0, L, max(60, int(L / 1.5)))
    pts = np.array([ring.interpolate(t).coords[0] for t in ts])
    xi = np.clip(pts[:, 0].round().astype(int), 0, g.shape[1] - 1)
    yi = np.clip(pts[:, 1].round().astype(int), 0, g.shape[0] - 1)
    return g[yi, xi].mean()

def raw_piece(g, lab, idx, hsv=None):
    """คืน (outline_mm Polygon แบบดิบที่กึ่งกลางเส้นตัด, รายการรูดิบ Polygon mm)"""
    m = (lab == idx).astype(np.uint8)
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]
    outer = max([c for j, c in enumerate(cs) if hier[j][3] < 0], key=cv2.contourArea)
    P = Polygon(outer[:, 0, :] + 0.5).buffer(0)
    d = min(np.arange(2, 7.5, 0.5), key=lambda d: ring_dark(g, P.buffer(d).exterior.coords))
    O = P.buffer(d)
    holes = []
    for j, c in enumerate(cs):
        if hier[j][3] < 0 or cv2.contourArea(c) < 12: continue
        H = Polygon(c[:, 0, :] + 0.5).buffer(0)
        best, bd = None, 1e9
        for dh in np.arange(1, 6.5, 0.5):
            Hh = H.buffer(-dh)
            if Hh.is_empty: break
            if Hh.geom_type != 'Polygon': Hh = max(Hh.geoms, key=lambda q: q.area)
            v = ring_dark(g, Hh.exterior.coords)
            if v < bd: bd, best = v, Hh
        if best is None:
            best = H.buffer(-2.5)
            if best.is_empty: continue
            if best.geom_type != 'Polygon': best = max(best.geoms, key=lambda q: q.area)
        if hsv is not None:
            # รูจริง: ข้างในมืด หรือ เทา/ขาวไม่มีสี (เห็นฝาสแกน) · ลายไม้/คราบ: น้ำตาลอมเหลือง
            mk = np.zeros(lab.shape, np.uint8)
            cv2.fillPoly(mk, [np.array(H.buffer(-0.5).exterior.coords if not H.buffer(-0.5).is_empty and H.buffer(-0.5).geom_type == 'Polygon' else H.exterior.coords).round().astype(np.int32)], 1)
            if mk.sum() == 0: continue
            sat = float(np.median(hsv[..., 1][mk > 0])); val = float(np.percentile(hsv[..., 2][mk > 0], 25))
            if not (val < 95 or sat < 30): continue
        holes.append(affinity.scale(best, PX, PX, origin=(0, 0)))
    return affinity.scale(O, PX, PX, origin=(0, 0)), holes

# ---------------------------------------------------------------- 2. line + arc reconstruction
def arc_pts(c, r, a0, a1, ccw):
    """จุดบนส่วนโค้งจาก a0 ถึง a1 (เรเดียน) ความละเอียด sagitta ≤ 0.01 มม."""
    if ccw:
        while a1 <= a0: a1 += 2 * math.pi
    else:
        while a1 >= a0: a1 -= 2 * math.pi
    span = abs(a1 - a0)
    step = 2 * math.acos(max(-1, 1 - 0.01 / max(r, 0.02))) if r > 0.02 else span
    n = max(2, int(math.ceil(span / max(step, 1e-3))) + 1)
    return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(a0, a1, n)]

def fit_circle(p):
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    b = (p ** 2).sum(1)
    cx, cy, k = np.linalg.lstsq(A, b, rcond=None)[0]
    return np.array([cx, cy]), math.sqrt(max(k + cx * cx + cy * cy, 1e-9))

def fit_line(p, snap_deg=1.2):
    c = p.mean(0); u, s, vt = np.linalg.svd(p - c); d = vt[0]
    ang = math.degrees(math.atan2(d[1], d[0])) % 180
    for a in (0, 90, 180):
        if abs(ang - a) < snap_deg:
            a = math.radians(a); d = np.array([math.cos(a), math.sin(a)])
            if a == math.radians(90): c = np.array([np.median(p[:, 0]), c[1]])
            else: c = np.array([c[0], np.median(p[:, 1])])
            break
    return c, d / np.linalg.norm(d)

def inter(c1, d1, c2, d2):
    A = np.array([d1, -d2]).T
    t = np.linalg.solve(A, c2 - c1)
    return c1 + t[0] * d1

def reconstruct(poly, dp_tol=0.30, lmin=1.6):
    """แปลงขอบดิบ → เส้นตรง + ส่วนโค้งจริง"""
    pts = np.array(poly.exterior.coords[:-1])
    # ทำให้ทิศทางเป็น CCW ในระบบ y-ลง (= CW ทางคณิต) ให้คงที่
    if Polygon(pts).exterior.is_ccw: pts = pts[::-1]
    # resample ให้ห่างเท่า ๆ กัน
    ring = LineString(np.vstack([pts, pts[:1]])); L = ring.length
    pts = np.array([ring.interpolate(t).coords[0] for t in np.arange(0, L, 0.05)])
    n = len(pts)
    a = cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), dp_tol, True)[:, 0, :]
    # index ของ vertex DP ในลำดับจุด
    idx = sorted(set(int(np.argmin(((pts - v) ** 2).sum(1))) for v in a))
    segs = []
    for k in range(len(idx)):
        i0, i1 = idx[k], idx[(k + 1) % len(idx)]
        span = (i1 - i0) % n
        if span * 0.05 >= lmin:
            segs.append((i0, span))
    if len(segs) < 2:
        c, r = fit_circle(pts)
        return Point(*c).buffer(r, resolution=256), dict(kind='circle', c=c.tolist(), r=r)
    lines = []
    for i0, span in segs:
        cut = int(span * 0.15)
        ii = [(i0 + j) % n for j in range(cut, span - cut + 1)]
        c, d = fit_line(pts[ii])
        # ทิศให้ตามลำดับ
        if np.dot(pts[(i0 + span) % n] - pts[i0], d) < 0: d = -d
        lines.append(dict(c=c, d=d, i0=i0, i1=(i0 + span) % n))
    # รวมเส้นที่ต่อเนื่องเกือบเส้นเดียว (สะพานไมโครแท็บ)
    merged = True
    while merged and len(lines) > 2:
        merged = False
        for k in range(len(lines)):
            A, B = lines[k], lines[(k + 1) % len(lines)]
            if np.dot(A['d'], B['d']) > math.cos(math.radians(2.5)):
                v = B['c'] - A['c']; off = abs(A['d'][0] * v[1] - A['d'][1] * v[0])
                if off < 0.25:
                    i0 = A['i0']; i1 = B['i1']; span = (i1 - i0) % n
                    ii = [(i0 + j) % n for j in range(int(span * .05), int(span * .95))]
                    c, d = fit_line(pts[ii])
                    if np.dot(A['d'], d) < 0: d = -d
                    lines[k] = dict(c=c, d=d, i0=i0, i1=i1); lines.pop((k + 1) % len(lines)); merged = True
                    break
    out = []
    feats = []
    m = len(lines)
    for k in range(m):
        A, B = lines[k], lines[(k + 1) % m]
        # จุดช่วงเปลี่ยน
        j0, j1 = A['i1'], B['i0']; span = (j1 - j0) % n
        tp = pts[[(j0 + j) % n for j in range(span + 1)]]
        cosang = float(np.dot(A['d'], B['d']))
        sep = abs(A['d'][0] * (B['c'] - A['c'])[1] - A['d'][1] * (B['c'] - A['c'])[0])
        if cosang < -0.80 and sep < 4.0:
            # ก้นร่องแคบ → ปลายตัดฉาก ที่จุดลึกสุด
            ext = tp[np.argmax(tp @ A['d'])] if len(tp) else pts[j0]
            pa = A['c'] + np.dot(ext - A['c'], A['d']) * A['d']
            pb = B['c'] + np.dot(ext - B['c'], B['d']) * B['d']
            out.append(('pt', [tuple(pa), tuple(pb)])); continue
        if cosang < -0.80 or span * 0.05 > 6.0:
            # กลับทาง (ปลายมน) หรือโค้งยาว → fit วงกลม
            if len(tp) < 5:
                tp = pts[[(j0 + j) % n for j in range(-3, span + 4)]]
            c, r = fit_circle(tp)
            pa = A['c'] + np.dot(c - A['c'], A['d']) * A['d']
            pb = B['c'] + np.dot(c - B['c'], B['d']) * B['d']
            a0 = math.atan2(pa[1] - c[1], pa[0] - c[0]); a1 = math.atan2(pb[1] - c[1], pb[0] - c[0])
            mid = tp[len(tp) // 2]; am = math.atan2(mid[1] - c[1], mid[0] - c[0])
            # เลือกทิศที่ผ่าน am
            def within(a0, a1, am, ccw):
                f = lambda x: x % (2 * math.pi)
                return (f(am - a0) <= f(a1 - a0)) if ccw else (f(a0 - am) <= f(a0 - a1))
            ccw = within(a0, a1, am, True)
            out.append(('arc', arc_pts(c, r, a0, a1, ccw)))
            feats.append(dict(kind='arc', c=c.tolist(), r=r))
            continue
        projA = A['c'] + np.dot(pts[j0] - A['c'], A['d']) * A['d']
        projB = B['c'] + np.dot(pts[j1] - B['c'], B['d']) * B['d']
        try:
            X = inter(A['c'], A['d'], B['c'], B['d'])
            bad = np.hypot(*(X - pts[j0])) > 2.5 or np.hypot(*(X - pts[j1])) > 2.5
        except np.linalg.LinAlgError:
            bad = True
        if bad:
            # เส้นเกือบขนาน/ขั้นบันได → ต่อปลายตรง ๆ
            out.append(('pt', [tuple(projA), tuple(projB)])); continue
        # มุมภายใน
        th = math.acos(max(-1, min(1, -cosang)))  # มุมระหว่าง -dA กับ dB
        dmin = float(np.min(np.hypot(*(pts - X).T))) if span > 0 else 0.0
        near = np.hypot(*(tp - X).T).min() if len(tp) else dmin
        s = math.sin(th / 2)
        r = near * s / (1 - s) if s < 0.999 else 0
        if r < 0.3 or near < 0.08: r = 0
        r = min(r, 25)
        if r == 0:
            out.append(('pt', [tuple(X)]))
        else:
            t = r / math.tan(th / 2)
            pa = X - A['d'] * t; pb = X + B['d'] * t
            # จุดศูนย์กลาง: ตั้งฉากจาก pa
            nA = np.array([-A['d'][1], A['d'][0]])
            c = pa + nA * r
            if abs(np.hypot(*(c - pb)) - r) > 1e-3 * max(1, r) + 0.02: c = pa - nA * r
            a0 = math.atan2(pa[1] - c[1], pa[0] - c[0]); a1 = math.atan2(pb[1] - c[1], pb[0] - c[0])
            d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            out.append(('arc', arc_pts(c, r, a0, a0 + d, d > 0)))
            feats.append(dict(kind='fillet', c=c.tolist(), r=r))
    ring = []
    for kind, p in out: ring += p
    global LAST_RING; LAST_RING = ring
    P = Polygon(ring).buffer(0)
    if P.geom_type == 'MultiPolygon': P = max(P.geoms, key=lambda q: q.area)
    return P, dict(kind='lines', n_lines=m, feats=feats)

# ---------------------------------------------------------------- 3. features
def classify_hole(H):
    """วงกลม / ร่องสี่เหลี่ยม / รูปอื่น"""
    pts = np.array(H.exterior.coords)
    c, r = fit_circle(pts)
    (cx, cy), (w, h), ang = cv2.minAreaRect(pts.astype(np.float32))
    if w < h: w, h, ang = h, w, ang + 90
    fill = H.area / max(w * h, 1e-9)
    circ = H.area / (math.pi * r * r)
    if circ > 0.72 and w / max(h, 1e-6) < 1.35:
        return dict(kind='circle', c=[float(c[0]), float(c[1])], d=float(2 * math.sqrt(H.area / math.pi)))
    a = ang % 180
    for s in (0, 90, 180):
        if abs(a - s) < 4: a = s % 180
    if fill > 0.62 and w / h > 1.8 and h < 4.5:
        return dict(kind='slot', c=[float(cx), float(cy)], L=float(w), W=float(h), ang=float(a))
    return dict(kind='other', poly=np.round(pts, 4).tolist())

def find_notches(P, wmax=3.6):
    """ร่องเปิดจากขอบ: closing แล้วลบเนื้อเดิม"""
    rr = wmax / 2 + 0.15
    C = P.buffer(rr, join_style=2).buffer(-rr, join_style=2)
    D = C.difference(P)
    res = []
    geoms = D.geoms if hasattr(D, 'geoms') else [D]
    for q in geoms:
        if q.area < 2.0: continue
        pts = np.array(q.exterior.coords)
        (cx, cy), (w, h), ang = cv2.minAreaRect(pts.astype(np.float32))
        if w < h: w, h, ang = h, w, ang + 90
        fill = q.area / (w * h)
        if not (1.0 <= h <= wmax + 0.3 and w >= 3.0 and fill > 0.72): continue
        a = ang % 180
        for s in (0, 90, 180):
            if abs(a - s) < 4: a = s % 180
        # ปลายเปิด: ด้านสั้นที่อยู่บนขอบ hull
        u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
        e1 = np.array([cx, cy]) + u * w / 2; e2 = np.array([cx, cy]) - u * w / 2
        open_end = e1 if P.distance(Point(*e1)) < 1e-6 and P.exterior.distance(Point(*e1)) > P.exterior.distance(Point(*e2)) else None
        # จุดปลายที่อยู่ "นอก" ชิ้นมากกว่า = ปลายเปิด
        o1 = C.exterior.distance(Point(*e1)); o2 = C.exterior.distance(Point(*e2))
        open_end, closed_end = (e1, e2) if o1 < o2 else (e2, e1)
        res.append(dict(region=q, c=[float(cx), float(cy)], L=float(w), W=float(h), ang=float(a),
                        open_end=open_end.tolist(), closed_end=closed_end.tolist()))
    return res

# ---------------------------------------------------------------- 4. symmetry / transforms
def mirror_sym(P, axis, m, side=1):
    """สมมาตร: ใช้ครึ่งหนึ่ง (side=+1 ขวา/ล่าง, -1 ซ้าย/บน) สะท้อนไปอีกข้าง"""
    big = 1e4
    if axis == 'x':
        half = P.intersection(box(m, -big, big, big) if side > 0 else box(-big, -big, m, big)); mir = affinity.scale(half, -1, 1, origin=(m, 0))
    else:
        half = P.intersection(box(-big, m, big, big) if side > 0 else box(-big, -big, big, m)); mir = affinity.scale(half, 1, -1, origin=(0, m))
    U = unary_union([half, mir]).buffer(1e-4).buffer(-1e-4)
    if U.geom_type == 'MultiPolygon': U = max(U.geoms, key=lambda q: q.area)
    return U

def iou(a, b):
    i = a.intersection(b).area; return i / max(a.union(b).area, 1e-9)

ORIENTS = [(rot, mir) for mir in (False, True) for rot in (0, 90, 180, 270)]
def place(P, rot, mir, target):
    """หมุน/กลับด้าน P แล้วเลื่อนให้ทับ target ที่สุด (centroid + ค้นละเอียด)"""
    Q = P
    if mir: Q = affinity.scale(Q, -1, 1, origin=(0, 0))
    Q = affinity.rotate(Q, rot, origin=(0, 0))
    tc = target.centroid; qc = Q.centroid
    dx, dy = tc.x - qc.x, tc.y - qc.y
    best = (iou(affinity.translate(Q, dx, dy), target), dx, dy)
    for step in (0.4, 0.15, 0.05):
        improved = True
        while improved:
            improved = False
            for ex, ey in ((step, 0), (-step, 0), (0, step), (0, -step)):
                v = iou(affinity.translate(Q, best[1] + ex, best[2] + ey), target)
                if v > best[0] + 1e-6: best = (v, best[1] + ex, best[2] + ey); improved = True
    return best

# ---------------------------------------------------------------- 5. piece catalogue
# (sheet, component-rank) → (type id, symmetry) ; rank = ลำดับตามพื้นที่ (ดู extract) ถูกตรวจด้วยตา
# ใช้ตำแหน่ง (จุดในชิ้น มม.) แทน rank เพื่อให้เสถียร
CATALOG = [
    # sheet, จุดอ้างอิงในชิ้น (มม.), type, ชื่อในคู่มือ, symmetry
    ('S1', (100, 120), 'BASE', 'แผ่นฐาน (base plate)', ('x', None)),
    ('S2', (8, 60),    'P03', 'ชิ้น 3', ('y', None)),
    ('S2', (50, 40),   'P01', 'ชิ้น 1', ('y', None)),
    ('S2', (64, 70),   'P16', 'ชิ้น 16', ('x', None)),
    ('S2', (76, 70),   'P16', 'ชิ้น 16', ('x', None)),
    ('S2', (91, 60),   'P15', 'ชิ้น 15', ('x', None)),
    ('S2', (103, 60),  'P15', 'ชิ้น 15', ('x', None)),
    ('S2', (6, 155),   'P05', 'ชิ้น 5 (จานหมุนมีด้าม)', (None, None)),
    ('S2', (95, 165),  'P04', 'ชิ้น 4 (จานฐาน)', ('xy', None)),
    ('S2', (52, 166),  'P12', 'ชิ้น 12', ('xy', None)),
    ('S3', (10, 40),   'P13A', 'ชิ้น 13', (None, None)),
    ('S3', (33, 40),   'P13B', 'ชิ้น 13', (None, None)),
    ('S3', (58, 40),   'P13A', 'ชิ้น 13', (None, None)),
    ('S3', (75, 40),   'P13B', 'ชิ้น 13', (None, None)),
    ('S3', (100, 40),  'P13A', 'ชิ้น 13', (None, None)),
    ('S3', (8, 110),   'P13C', 'ชิ้น 13 (ยาวมีหู)', (None, None)),
    ('S3', (78, 140),  'P06', 'ชิ้น 6', (None, None)),
    ('S3', (102, 140), 'P06', 'ชิ้น 6', (None, None)),
    ('S3', (50, 102),  'P07', 'ชิ้น 7', ('x', None)),
    ('S3', (50, 78),   'P20', 'ชิ้น 20', ('xy', None)),
    ('S3', (33, 112),  'P10', 'ชิ้น 10', ('x', None)),
    ('S3', (53, 112),  'P10', 'ชิ้น 10', ('x', None)),
    ('S3', (33, 130),  'P10', 'ชิ้น 10', ('x', None)),
    ('S3', (53, 130),  'P10', 'ชิ้น 10', ('x', None)),
    ('S3', (16, 158),  'P09', 'ชิ้น 9', ('x', None)),
    ('S3', (35, 158),  'P09', 'ชิ้น 9', ('x', None)),
    ('S3', (54, 158),  'P09', 'ชิ้น 9', ('x', None)),
    ('S3', (16, 174),  'P09', 'ชิ้น 9', ('x', None)),
    ('S3', (35, 174),  'P09', 'ชิ้น 9', ('x', None)),
    ('S3', (54, 174),  'P09', 'ชิ้น 9', ('x', None)),
    ('S4', (20, 3),    'P02A', 'ชิ้น 2 (มีเขี้ยวล็อก)', (None, None)),
    ('S4', (20, 32),   'P02B', 'ชิ้น 2', (None, None)),
    ('S4', (20, 84),   'P02A', 'ชิ้น 2 (มีเขี้ยวล็อก)', (None, None)),
    ('S4', (75, 30),   'P17', 'ชิ้น 17 (ฐานก้ามปู)', ('x', None)),
    ('S4', (40, 40),   'P18A', 'ชิ้น 18 (ก้ามปู ซ้าย)', (None, None)),
    ('S4', (45, 72),   'P18B', 'ชิ้น 18 (ก้ามปู ขวา)', (None, None)),
    ('S4', (70, 4),    'P19', 'ชิ้น 19 (ข้อต่อ)', (None, None)),
    ('S4', (70, 14),   'P19', 'ชิ้น 19 (ข้อต่อ)', (None, None)),
    ('S4', (59, 69.7), 'P19', 'ชิ้น 19 (ข้อต่อ)', (None, None)),
    ('S4', (5, 104),   'P11A', 'ชิ้น 11', ('x', None)),
    ('S4', (33, 104),  'P11B', 'ชิ้น 11', ('x', None)),
    ('S4', (60, 114),  'P08', 'ชิ้น 8', ('x', None)),
    ('S4', (20, 122),  'P09', 'ชิ้น 9', ('x', None)),
    ('S4', (70, 123),  'P09', 'ชิ้น 9', ('x', None)),
    ('S4', (92, 123),  'P09', 'ชิ้น 9', ('x', None)),
    ('S4', (62, 100),  'P14', 'ชิ้น 14', ('xy', None)),
    ('S4', (84, 94),   'P14', 'ชิ้น 14', ('xy', None)),
    ('S4', (98, 94),   'P14', 'ชิ้น 14', ('xy', None)),
    ('S4', (100, 86),  'P14', 'ชิ้น 14', ('xy', None)),
]

def main(scandir_):
    global scandir; scandir = scandir_
    sheets = {}
    for s in ('S1', 'S2', 'S3', 'S4'):
        im, g, lab, st, hsv = segment(os.path.join(scandir, f'{s}_scan_200dpi.jpg'))
        sheets[s] = (g, lab, st, hsv)
    pieces = []
    raw_cache = {}
    for (s, ref, typ, name, sym) in CATALOG:
        g, lab, st, hsv = sheets[s]
        px, py = int(ref[0] / PX), int(ref[1] / PX)
        # หา label ที่ใกล้จุดอ้างอิงที่สุด (จุดอาจตกบนรู)
        win = lab[max(0, py - 25):py + 26, max(0, px - 25):px + 26]
        vals, cnt = np.unique(win[win > 0], return_counts=True)
        lid = int(vals[np.argmax(cnt)])
        key = (s, lid)
        if key not in raw_cache: raw_cache[key] = raw_piece(g, lab, lid, hsv)
        O, holes = raw_cache[key]
        pieces.append(dict(sheet=s, ref=ref, type=typ, name=name, sym=sym[0], O=O, holes=holes, lid=lid))
    # --- แก้กรณีพิเศษ ---
    # S2: ชิ้น 15 สองชิ้นติดกัน → แบ่งด้วยเส้นกลาง
    for p in pieces:
        if p['type'] == 'P15':
            O = p['O']; xm = 97.1
            p['O'] = O.intersection(box(-1, -1, xm, 999) if p['ref'][0] < xm else box(xm, -1, 999, 999))
            if p['O'].geom_type == 'MultiPolygon': p['O'] = max(p['O'].geoms, key=lambda q: q.area)
            p['holes'] = [h for h in p['holes'] if (h.centroid.x < xm) == (p['ref'][0] < xm)]
    # S2: ชิ้น 1 มีเศษร่องค้าง (plug) ที่ร่องล่าง → ตัดออก
    g, lab, st, hsv = sheets['S2']
    plug_lid = int(lab[int(124.5 / PX), int(38 / PX)])
    if plug_lid > 0:
        plugO, _ = raw_piece(g, lab, plug_lid)
        for p in pieces:
            if p['type'] == 'P01': p['O'] = p['O'].difference(plugO.buffer(0.05))
            if p['O'].geom_type == 'MultiPolygon': p['O'] = max(p['O'].geoms, key=lambda q: q.area)
    # S1: แผ่นฐานถูกสแกนตัดขอบซ้าย/บน → ใช้ครึ่งขวาสะท้อน (แกนกลางจากร่อง/รูสมมาตร)
    out = []
    canon = {}
    for p in pieces:
        out.append(p)
    # --- สร้าง geometry สะอาดต่อ type (จากชิ้นแรกของ type) ---
    types = {}
    for p in pieces:
        types.setdefault(p['type'], []).append(p)
    result = dict(px_mm=PX, types={}, instances=[])
    for typ, inst in types.items():
        p0 = inst[0]
        O = p0['O']
        if typ in ('P04',):
            c, r = fit_circle(np.array(O.exterior.coords)); clean = Point(*c).buffer(r, resolution=256); info = dict(kind='circle')
        elif typ == 'P19':
            clean, info = build_link(O, p0['holes'])
        elif typ == 'P05':
            clean, info = build_p05(O, p0['holes'])
        elif typ == 'BASE':
            clean, info = None, dict(kind='base')
        else:
            clean, info = reconstruct(O)
            clean = unary_union([clean.intersection(O.buffer(0.4, join_style=2)), O.buffer(-0.4, join_style=2)])
            clean = clean.buffer(0.02).buffer(-0.02)
            if clean.geom_type == 'MultiPolygon': clean = max(clean.geoms, key=lambda q: q.area)
            clean = Polygon(clean.exterior)
        # features
        feats = piece_features(sheets[p0['sheet']], O) if typ != 'BASE' else []
        # local frame: origin ที่ bbox ของชิ้นสะอาด
        minx, miny, maxx, maxy = O.bounds
        sym = p0['sym']
        m = None
        if typ == 'BASE':
            # แผ่นฐานซีด → หาร่อง/รูด้วยเกณฑ์เฉพาะ (เข้ม หรือ ไม่มีสี = ทะลุเห็นฝาสแกน)
            feats = base_features(os.path.join(scandir, 'S1_scan_200dpi.jpg'))
            # แกนสมมาตรจากร่อง/รู (ขอบซ้าย/บนของสแกนถูกตัด) · ใช้ขอบขวา/ล่างจริง
            xs = [f['c'][0] for f in feats if f['kind'] in ('slot', 'circle')]
            m = float(np.median(xs))
            pts = np.array(O.exterior.coords)
            right = float(np.median(pts[(pts[:, 0] > maxx - 1.5) & (pts[:, 1] > 20) & (pts[:, 1] < maxy - 20)][:, 0]))
            bottom = float(np.median(pts[(pts[:, 1] > maxy - 1.5) & (pts[:, 0] > 20) & (pts[:, 0] < right - 20)][:, 1]))
            top = 0.0
            r = 3.0
            clean = box(2 * m - right, top, right, bottom).buffer(-r, join_style=2).buffer(r, resolution=64)
            feats = [f for f in feats if clean.buffer(-2.0).contains(Point(*f['c']))]
            info.update(W=2 * (right - m), H=bottom - top, r=r, axis=m)
            feats = sym_feats(feats, 'x', m)
            sym = None
        if sym:
            for ax in sym:
                mm_ = (minx + maxx) / 2 if ax == 'x' else (miny + maxy) / 2
                cands = [mirror_sym(clean, ax, mm_, side) for side in (1, -1)]
                clean = max(cands, key=lambda q: iou(q, O))
                feats = sym_feats(feats, ax, mm_)
        notches = find_notches(clean)
        extra = {}
        if typ in ('P09', 'P10'):
            extra['tslot'] = find_tslot(clean)
        if typ == 'P06':
            # ร่องข้างกลางชิ้นมีเงา/ขอบหยัก ตรวจอัตโนมัติไม่ได้ → ระบุจากการวัดบนสแกน (ปลายปิดห่างจากขอบซ้าย 8.8 มม.)
            pass
        result['types'][typ] = dict(extra=extra, name=p0['name'], sym=sym, outline=np.round(np.array(clean.exterior.coords), 4).tolist(),
                                    interiors=[np.round(np.array(i.coords), 4).tolist() for i in clean.interiors],
                                    feats=feats, notches=[{k: v for k, v in n.items() if k != 'region'} for n in notches],
                                    src=dict(sheet=p0['sheet'], ref=p0['ref']), info=info)
        canon[typ] = clean
    # --- วางชิ้นต้นแบบทับทุกตำแหน่ง ---
    for p in pieces:
        C = canon[p['type']]
        if p['type'] == 'BASE':
            result['instances'].append(dict(sheet=p['sheet'], type='BASE', name=p['name'], ref=p['ref'], rot=0, mirror=False, dx=0.0, dy=0.0,
                                            iou=iou(C, p['O']), raw=np.round(np.array(p['O'].exterior.coords), 3).tolist()))
            continue
        best = None
        for rot, mir in ORIENTS:
            v, dx, dy = place(C, rot, mir, p['O'])
            if best is None or v > best[0]: best = (v, rot, mir, dx, dy)
        v, rot, mir, dx, dy = best
        result['instances'].append(dict(sheet=p['sheet'], type=p['type'], name=p['name'], ref=p['ref'],
                                        rot=rot, mirror=mir, dx=dx, dy=dy, iou=v,
                                        raw=np.round(np.array(p['O'].exterior.coords), 3).tolist()))
        print(f"{p['sheet']} {p['type']:5s} rot{rot:3d} mir{int(mir)} IoU={v:.4f}")
    json.dump(result, open(os.path.join(BUILD, 'traced_1x.json'), 'w'))
    print('types', len(result['types']), 'instances', len(result['instances']))

def piece_features(sheet, O):
    """รู/ร่องปิดภายในชิ้น: พิกเซลที่เข้ม หรือไม่มีสี (ทะลุเห็นฝาสแกน) ห่างขอบชิ้น ≥0.6 มม."""
    g, lab, st, hsv = sheet
    v = hsv[..., 2]; sat = hsv[..., 1]
    inner = O.buffer(-0.6)
    mk = np.zeros(g.shape, np.uint8)
    polys = inner.geoms if inner.geom_type == 'MultiPolygon' else [inner]
    for q in polys:
        cv2.fillPoly(mk, [(np.array(q.exterior.coords) / PX).round().astype(np.int32)], 1)
    m = (((v < 125) | ((sat < 12) & (v < 238))) & (mk > 0)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    grp = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lb, stt, cen = cv2.connectedComponentsWithStats(grp, connectivity=8)
    out = []
    for i in range(1, n):
        if stt[i][4] < 25: continue
        ys, xs = np.nonzero(lb == i)
        pts = np.c_[xs, ys].astype(np.float32)
        (cx, cy), (w, h), ang = cv2.minAreaRect(pts)
        if w < h: w, h, ang = h, w, ang + 90
        w += 1; h += 1
        area = len(xs)
        if w / h < 1.6:
            # วงกลม: ใช้ min enclosing circle (เงาด้านล่างอาจทำให้ area น้อย)
            (ex, ey), er = cv2.minEnclosingCircle(pts)
            d = 2 * (er + 0.5) * PX
            out.append(dict(kind='circle', c=[float(ex * PX), float(ey * PX)], d=float(d)))
        else:
            a = ang % 180
            for s_ in (0, 90, 180):
                if abs(a - s_) < 6: a = s_ % 180
            out.append(dict(kind='slot', c=[float(cx * PX), float(cy * PX)], L=float(w * PX), W=float(h * PX), ang=float(a),
                            fill=float(area / (w * h))))
    return out

def find_tslot(P):
    """ร่องรูปตัว T เปิดออกขอบ (ชิ้น 9/10): คืนแถบขวาง (bar) และก้าน (stem)"""
    rr = 2.2
    C = P.buffer(rr, join_style=2).buffer(-rr, join_style=2)
    D = C.difference(P)
    geoms = D.geoms if hasattr(D, 'geoms') else [D]
    T = max(geoms, key=lambda q: q.area)
    x0, y0, x1, y1 = T.bounds
    ys = np.arange(y0 + 0.025, y1, 0.05)
    widths = []
    for y in ys:
        seg = T.intersection(LineString([(x0 - 1, y), (x1 + 1, y)]))
        if seg.is_empty: widths.append((0, 0, 0)); continue
        bx = seg.bounds; widths.append((bx[2] - bx[0], bx[0], bx[2]))
    w = np.array(widths)
    wmax = w[:, 0].max()
    bar = w[:, 0] > 0.6 * wmax
    yb = ys[bar]
    stem = (~bar) & (w[:, 0] > 0)
    sx0 = float(np.median(w[stem, 1])); sx1 = float(np.median(w[stem, 2]))
    ys_stem = ys[stem]
    # ทิศก้าน: ไปทางขอบที่ใกล้กว่า
    up = ys_stem.mean() < yb.mean()
    edge_y = P.bounds[1] if up else P.bounds[3]
    return dict(region=np.round(np.array(T.exterior.coords), 4).tolist(),
                bar=dict(x0=float(np.median(w[bar, 1])), x1=float(np.median(w[bar, 2])), y0=float(yb.min()), y1=float(yb.max())),
                stem=dict(x0=sx0, x1=sx1, edge_y=float(edge_y), up=bool(up)))

def base_features(path):
    im = cv2.imread(path); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    m = ((g < 120) | ((hsv[..., 1] < 9) & (g < 232))).astype(np.uint8)
    m[:, int(126.3 / PX):] = 0; m[int(223.9 / PX):, :] = 0; m[:, :int(0.6 / PX)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    grp = cv2.dilate(m, np.ones((7, 7), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(grp, connectivity=8)
    out = []
    for i in range(1, n):
        ys, xs = np.nonzero((lab == i) & (m > 0))
        if len(xs) < 40: continue
        x0, x1, y0, y1 = xs.min() * PX, (xs.max() + 1) * PX, ys.min() * PX, (ys.max() + 1) * PX
        w, h = x1 - x0, y1 - y0
        if max(w, h) / min(w, h) > 2.5:
            ang = 0.0 if w > h else 90.0
            out.append(dict(kind='slot', c=[(x0 + x1) / 2, (y0 + y1) / 2], L=max(w, h), W=min(w, h), ang=ang))
        elif max(w, h) < 2.5:
            out.append(dict(kind='circle', c=[float(xs.mean() * PX), float(ys.mean() * PX)], d=float(2 * math.sqrt(len(xs) / math.pi) * PX)))
    return out

def sym_feats(feats, ax, m):
    """เฉลี่ยตำแหน่งรูที่เป็นคู่สะท้อน · รูบนแกน snap ลงแกน"""
    k = 0 if ax == 'x' else 1
    out = []; used = set()
    for i, f in enumerate(feats):
        if i in used: continue
        if f['kind'] == 'other': out.append(f); continue
        c = np.array(f['c']); cm = c.copy(); cm[k] = 2 * m - c[k]
        if abs(c[k] - m) < 0.5:
            f = dict(f); f['c'] = list(c); f['c'][k] = m; out.append(f); continue
        j = None
        for jj, g2 in enumerate(feats):
            if jj != i and jj not in used and g2['kind'] == f['kind'] and np.hypot(*(np.array(g2['c']) - cm)) < 0.8:
                j = jj; break
        if j is None: out.append(f); continue
        used.add(j)
        g2 = feats[j]
        avg = (c + (np.array(g2['c']) * np.array([1, 1]) if False else 0))
        c2 = np.array(g2['c']).copy(); c2[k] = 2 * m - c2[k]
        ca = (c + c2) / 2
        f1 = dict(f); f1['c'] = ca.tolist()
        f2 = dict(g2); cb = ca.copy(); cb[k] = 2 * m - ca[k]; f2['c'] = cb.tolist()
        for key in ('d', 'L', 'W'):
            if key in f1: f1[key] = f2[key] = (f[key] + g2[key]) / 2
        out += [f1, f2]
    return out

def build_link(O, holes):
    """ชิ้น 19: ข้อต่อ = แท่งปลายมน (กว้างตามตัว) + วงกลมใหญ่รอบรูแกนหมุน + fillet มุมเว้า"""
    hs = sorted(holes, key=lambda h: -h.area)
    cb = fit_circle(np.array(hs[0].exterior.coords))[0]   # รูใหญ่
    cs = fit_circle(np.array(hs[1].exterior.coords))[0]   # รูเล็ก
    pts = np.array(O.exterior.coords)
    u = (cs - cb) / np.hypot(*(cs - cb)); v = np.array([-u[1], u[0]]); Lc = np.hypot(*(cs - cb))
    t = (pts - cb) @ u; n = (pts - cb) @ v
    mid = (t > Lc * 0.45) & (t < Lc * 0.85)
    w = float(np.median(np.abs(n[mid])))
    endp = t > Lc + 0.5
    r_s = float(np.median(np.hypot(*(pts[endp] - cs).T)))
    big = t < -0.5
    r_b = float(np.median(np.hypot(*(pts[big] - cb).T)))
    body = LineString([tuple(cb), tuple(cs)]).buffer(w, resolution=128)
    end = Point(*cs).buffer(r_s, resolution=128)
    U = unary_union([body, end, Point(*cb).buffer(r_b, resolution=128)])
    U = U.buffer(0.8, resolution=64).buffer(-0.8, resolution=64)
    return U, dict(kind='link', cb=cb.tolist(), cs=cs.tolist(), w=w, r_s=r_s, r_b=r_b)

def build_p05(O, holes=()):
    """ชิ้น 5: วงกลม + ด้ามยื่น (สร้างจากพารามิเตอร์ที่วัด)"""
    pts = np.array(O.exterior.coords)
    # วงกลม: ใช้จุดที่อยู่ฝั่งซ้ายของด้าม
    c0, r0 = fit_circle(pts[pts[:, 0] < np.percentile(pts[:, 0], 70)])
    cx, cy = c0
    x_end = pts[:, 0].max()
    hand = pts[(pts[:, 0] > cx + r0 + 2.0) & (pts[:, 0] < x_end - 2.0)]
    yc = cy
    if holes:   # แนวกลางด้าม = ศูนย์รูที่ปลายด้าม
        hc = max((fit_circle(np.array(h.exterior.coords))[0] for h in holes), key=lambda c: c[0])
        if hc[0] > cx + r0: yc = float(hc[1])
    hw = float(np.median(np.abs(hand[:, 1] - yc)))
    r_end, r_fil = 1.5, 3.0
    hw = float(np.median(np.abs(hand[:, 1] - yc)))
    handle = box(cx, yc - hw, x_end, yc + hw)
    handle = handle.buffer(-r_end, join_style=1).buffer(r_end, resolution=64)
    disc = Point(cx, cy).buffer(r0, resolution=256)
    U = unary_union([disc, handle.intersection(box(cx, -999, 999, 999))])
    U = U.buffer(r_fil, resolution=64).buffer(-r_fil, resolution=64)  # fillet มุมเว้า
    return U, dict(kind='p05', c=[cx, cy], r=r0, x_end=x_end, hw=hw)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '../ref_hydraulic_arm')

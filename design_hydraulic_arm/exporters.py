"""exporters.py — ส่งออก SVG/DXF (เลเซอร์), PDF 1:1 A4, ตาราง, ภาพตรวจ, 3MF"""
import os, io, csv, json, math, zipfile
import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely import affinity
from shapely.ops import unary_union

SCAN_DIR = os.environ.get('SCAN_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref_hydraulic_arm'))
FONT_TH = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'

# ------------------------------------------------------------------ laser boards
def make_boards(p, insts, label):
    """จัดแผ่น: ใช้การจัดวางเดิมของชุดคิต (×2) ซึ่งเรียงชิ้นแน่นอยู่แล้ว · รวมแผ่น S2+S4 ในไม้แผ่นเดียว"""
    def group(sheet, rot=0):
        L = [(label(i['type']), i['G']) for i in insts if i['sheet'] == sheet]
        if rot:
            L = [(n, affinity.rotate(g, rot, origin=(0, 0))) for n, g in L]
        b = unary_union([g for _, g in L]).bounds
        return [(n, affinity.translate(g, -b[0], -b[1])) for n, g in L], (b[2] - b[0], b[3] - b[1])
    m = p['BOARD_MARGIN']; BW, BH = p['BOARD_W'], p['BOARD_H']
    boards = []
    gA, sA = group('S1'); boards.append(('A', [(n, affinity.translate(g, m, m)) for n, g in gA], ['S1']))
    gB, sB = group('S2'); gD, sD = group('S4', rot=90)
    if sB[1] + sD[1] + 3 * m <= BH and max(sB[0], sD[0]) + 2 * m <= BW:
        boards.append(('B', [(n, affinity.translate(g, m, m)) for n, g in gB] +
                       [(n, affinity.translate(g, m, sB[1] + 2 * m)) for n, g in gD], ['S2', 'S4']))
        gC, sC = group('S3'); boards.append(('C', [(n, affinity.translate(g, m, m)) for n, g in gC], ['S3']))
    else:
        gC, sC = group('S3')
        boards += [('B', [(n, affinity.translate(g, m, m)) for n, g in gB], ['S2']),
                   ('C', [(n, affinity.translate(g, m, m)) for n, g in gC], ['S3']),
                   ('D', [(n, affinity.translate(gg, m, m)) for n, gg in group('S4')[0]], ['S4'])]
    out = []
    for name, parts, src in boards:
        b = unary_union([g for _, g in parts]).bounds
        assert b[2] <= BW - m + 0.01 and b[3] <= BH - m + 0.01, (name, b)
        out.append(dict(name=name, parts=parts, src=src, extent=(b[2] + m, b[3] + m)))
    return out

def rings(G):
    yield np.array(G.exterior.coords)
    for i in G.interiors: yield np.array(i.coords)

def write_svg(path, board, p):
    W, H = p['BOARD_W'], p['BOARD_H']
    o = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<!-- Fixtory Studio · แขนกลไฮดรอลิก 2x · แผ่น {board["name"]} · ไม้อัด {W:.0f}x{H:.0f} มม. หนา {p["T"]} · หน่วย มม. ขนาดจริง -->',
         '<g id="CUT" fill="none" stroke="#FF0000" stroke-width="0.1">']
    for n, G in board['parts']:
        d = ''
        for r in rings(G):
            d += 'M' + ' L'.join(f'{x:.3f},{y:.3f}' for x, y in r[:-1]) + ' Z '
        o.append(f'<path d="{d.strip()}"/>')
    o.append('</g>')
    o.append('<g id="LABEL_engrave_optional" fill="#0000FF" font-family="Arial" font-size="5" text-anchor="middle">')
    for n, G in board['parts']:
        c = G.representative_point()
        o.append(f'<text x="{c.x:.2f}" y="{c.y + 1.7:.2f}">{n}</text>')
    o.append('</g></svg>')
    open(path, 'w').write('\n'.join(o))

def write_dxf(path, board, p):
    import ezdxf
    doc = ezdxf.new('R2010'); doc.units = ezdxf.units.MM
    doc.header['$INSUNITS'] = 4; doc.header['$MEASUREMENT'] = 1
    doc.layers.add('CUT', color=1); doc.layers.add('LABEL', color=5)
    msp = doc.modelspace(); H = p['BOARD_H']
    for n, G in board['parts']:
        for r in rings(G):
            msp.add_lwpolyline([(x, H - y) for x, y in r[:-1]], close=True, dxfattribs={'layer': 'CUT', 'color': 1})
        c = G.representative_point()
        msp.add_text(n, height=4, dxfattribs={'layer': 'LABEL'}).set_placement((c.x, H - c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)

# ------------------------------------------------------------------ PDF 1:1 A4
def write_pdf(path, boards, p, rows):
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('TH', FONT_TH))
    PW, PH = 210, 297
    TX0, TY0, TW, TH = 10, 22, 190, 263      # พื้นที่ชิ้นงานบนหน้า (มม. จากล่างซ้าย)
    OV = 10                                   # ระยะซ้อนทับระหว่างหน้า
    c = canvas.Canvas(path, pagesize=(PW * mm, PH * mm))
    c.setTitle('Fixtory · Hydraulic Arm 2x · 1:1 A4 tiles')
    tiles = []
    for bd in boards:
        ex, ey = bd['extent']
        nx = max(1, math.ceil((ex - OV) / (TW - OV))); ny = max(1, math.ceil((ey - OV) / (TH - OV)))
        tiles.append((bd, nx, ny))
    total = sum(nx * ny for _, nx, ny in tiles)
    # ปก
    c.setFont('TH', 18); c.drawString(15 * mm, 280 * mm, 'Fixtory Studio — แขนกลไฮดรอลิก 2x (แบบกระดาษ 1:1)')
    c.setFont('TH', 11)
    lines = [f'พิมพ์ที่ขนาดจริง 100% (Actual size / ไม่ Fit to page) แล้ววัดแถบ 100 มม. ทุกหน้าให้ได้ 100 มม.',
             f'ความหนาวัสดุ T = {p["T"]} มม. · ร่องสลัก = {p["SLOT_W"]:.1f} มม. · รูแกนหมุน Ø{p["PIVOT_D"]} · รูยึด Ø{p["FIX_D"]} (M4)',
             f'รูกระบอกหลัก Ø{p["SYR_D"]} · รูกระบอกเล็ก Ø{p["SYR2_D"]} · รูสายยาง Ø{p["HOSE_D"]} — วัดกระบอกจริงก่อนตัด',
             f'ต่อกระดาษ: ซ้อนแถบเทา {OV} มม. ให้เครื่องหมาย + ตรงกัน · ทั้งหมด {total} หน้า (ไม่รวมปก)', '']
    for bd, nx, ny in tiles:
        lines.append(f'แผ่น {bd["name"]} (จากสแกน {"+".join(bd["src"])}) ขนาดงาน {bd["extent"][0]:.0f}×{bd["extent"][1]:.0f} มม. → {nx}×{ny} = {nx * ny} หน้า · ไม้อัด {p["BOARD_W"]:.0f}×{p["BOARD_H"]:.0f}')
    lines += ['', 'รายการชิ้น (เลขตามคู่มือ):']
    y = 268
    for t in lines:
        c.drawString(15 * mm, y * mm, t); y -= 6.5
    c.setFont('TH', 9)
    for r in rows:
        c.drawString(18 * mm, y * mm, f'ชิ้น {r["label"]:5s} ×{r["qty"]:2d}   {r["w"]:6.1f} × {r["h"]:6.1f} มม.   {r["name"]}')
        y -= 4.6
        if y < 15: break
    c.showPage()
    page = 0
    for bd, nx, ny in tiles:
        for j in range(ny):
            for i in range(nx):
                page += 1
                x0 = i * (TW - OV); y0 = j * (TH - OV)
                c.setFont('TH', 11)
                c.drawString(10 * mm, 289 * mm, f'แผ่น {bd["name"]} · หน้า {j * nx + i + 1}/{nx * ny} (แถว {j + 1} คอลัมน์ {i + 1}) · รวมหน้าที่ {page}/{total}')
                c.drawRightString(200 * mm, 289 * mm, 'Fixtory · Hydraulic Arm 2x · 1:1')
                # แถบซ้อน
                c.setFillGray(0.9); c.setStrokeGray(0.9)
                if i > 0: c.rect(TX0 * mm, TY0 * mm, OV * mm, TH * mm, fill=1, stroke=0)
                if j > 0: c.rect(TX0 * mm, (TY0 + TH - OV) * mm, TW * mm, OV * mm, fill=1, stroke=0)
                c.setFillGray(0); c.setStrokeGray(0)
                c.setLineWidth(0.2); c.setDash(2, 2); c.rect(TX0 * mm, TY0 * mm, TW * mm, TH * mm); c.setDash()
                # เครื่องหมาย + มุม
                for (ax, ay) in ((TX0, TY0), (TX0 + TW, TY0), (TX0, TY0 + TH), (TX0 + TW, TY0 + TH),
                                 (TX0 + OV, TY0 + TH - OV), (TX0 + TW - OV, TY0 + OV)):
                    c.line((ax - 3) * mm, ay * mm, (ax + 3) * mm, ay * mm); c.line(ax * mm, (ay - 3) * mm, ax * mm, (ay + 3) * mm)
                # ชิ้นงาน
                cp = c.beginPath(); cp.rect(TX0 * mm, TY0 * mm, TW * mm, TH * mm)
                c.saveState(); c.clipPath(cp, stroke=0, fill=0)
                c.setLineWidth(0.35)
                def tp(x, y): return (TX0 + x - x0) * mm, (TY0 + TH - (y - y0)) * mm
                win = box(x0 - 1, y0 - 1, x0 + TW + 1, y0 + TH + 1)
                for n, G in bd['parts']:
                    if not G.intersects(win): continue
                    for r in rings(G):
                        pth = c.beginPath(); X, Y = tp(*r[0]); pth.moveTo(X, Y)
                        for q in r[1:]: X, Y = tp(*q); pth.lineTo(X, Y)
                        pth.close(); c.drawPath(pth, stroke=1, fill=0)
                    rp = G.representative_point()
                    c.setFont('TH', 8); X, Y = tp(rp.x, rp.y); c.drawCentredString(X, Y, f'ชิ้น {n}')
                c.restoreState()
                # แถบวัด 100 มม.
                c.setLineWidth(0.4); bx, by = 15, 10
                c.line(bx * mm, by * mm, (bx + 100) * mm, by * mm)
                for k in range(11):
                    h = 3 if k % 5 == 0 else 1.8
                    c.line((bx + 10 * k) * mm, by * mm, (bx + 10 * k) * mm, (by + h) * mm)
                c.setFont('TH', 8); c.drawString((bx + 102) * mm, (by - 1) * mm, '100 มม. — วัดให้ได้ 100 มม. พอดี')
                c.drawRightString(200 * mm, 5 * mm, f'หน้า {page}/{total}')
                c.showPage()
    c.save()
    return total

# ------------------------------------------------------------------ overlay check images
def write_overlays(R, insts, p, outdir):
    import cv2
    PX = R['px_mm']; S = p['SCALE']; f = 1.5
    files = []
    for s in ('S1', 'S2', 'S3', 'S4'):
        im = cv2.imread(os.path.join(SCAN_DIR, f'{s}_scan_200dpi.jpg'))
        im = cv2.resize(im, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
        k = f / PX / S
        L = [i for i in insts if i['sheet'] == s]
        bb = unary_union([i['G'] for i in L]).bounds
        for i in L:
            for r in rings(i['G']):
                cv2.polylines(im, [(r * k).round().astype(np.int32)], True, (0, 0, 255), 2, cv2.LINE_AA)
            rp = i['G'].representative_point()
        x1 = int(min(im.shape[1], bb[2] * k + 40)); y1 = int(min(im.shape[0], bb[3] * k + 40))
        im = im[:y1, :x1]
        cv2.putText(im, f'{s}: new 2x vectors (red) over scan scaled 2x  |  slots={p["SLOT_W"]:.1f}mm, holes standardised',
                    (10, y1 - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 180), 2)
        from PIL import Image
        img = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        fn = os.path.join(outdir, f'overlay_{s}.png'); img.save(fn, optimize=True); files.append(fn)
    return files

def write_plate_preview(plates, p, fn):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Rectangle
    n = len(plates); cols = min(4, n); rows_ = math.ceil(n / cols)
    fig, axs = plt.subplots(rows_, cols, figsize=(4.2 * cols, 4.4 * rows_))
    axs = np.atleast_1d(axs).ravel()
    cmap = plt.get_cmap('tab20')
    for k, ax in enumerate(axs):
        ax.set_axis_off()
        if k >= n: continue
        ax.add_patch(Rectangle((0, 0), p['BED'], p['BED'], fill=False, lw=1.2, ec='k'))
        for j, (name, typ, G) in enumerate(plates[k]):
            col = cmap(hash(typ) % 20)
            ax.add_patch(MP(np.array(G.exterior.coords), closed=True, fc=col, ec='k', lw=0.4, alpha=0.85))
            for h in G.interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc='white', ec='k', lw=0.3))
            c = G.representative_point(); ax.text(c.x, c.y, name, fontsize=5.5, ha='center', va='center')
        ax.set_xlim(-3, p['BED'] + 3); ax.set_ylim(p['BED'] + 3, -3); ax.set_aspect('equal')
        ax.set_title(f'plate {k + 1:02d}  ({len(plates[k])} parts)  {p["BED"]:.0f}x{p["BED"]:.0f}', fontsize=9)
    fig.suptitle(f'Hydraulic Arm 2x — Bambu A1 plates, T={p["T"]} mm', fontsize=11)
    fig.tight_layout(); fig.savefig(fn, dpi=150); plt.close(fig)

def write_3mf(plates, p, outdir):
    import trimesh
    files = []
    for k, lst in enumerate(plates):
        sc = trimesh.Scene()
        for name, typ, G in lst:
            m = trimesh.creation.extrude_polygon(G, p['T'], engine='earcut')
            assert m.is_watertight, name
            sc.add_geometry(m, geom_name=name.replace('#', '_n'), node_name=name.replace('#', '_n'))
        fn = os.path.join(outdir, f'hydraulic_arm_2x_plate{k + 1:02d}.3mf')
        sc.export(fn, file_type='3mf'); files.append(fn)
    return files

def zip_3mf(files, outdir, limit=2_000_000):
    zips, cur, cur_size = [], [], 0
    for f in files:
        sz = os.path.getsize(f)
        if cur and cur_size + sz > limit * 0.92: zips.append(cur); cur, cur_size = [], 0
        cur.append(f); cur_size += sz
    if cur: zips.append(cur)
    out = []
    for k, grp in enumerate(zips):
        fn = os.path.join(outdir, f'hydraulic_arm_2x_3mf_part{k + 1}.zip')
        with zipfile.ZipFile(fn, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in grp: z.write(f, os.path.basename(f))
        assert os.path.getsize(fn) <= limit, fn
        out.append(fn)
    return out

# ------------------------------------------------------------------ table
SCREWS = [  # (ต้นฉบับ, จำนวน, 2x M4)
    ('M3×30', 3, 'M4×60'), ('M3×25', 3, 'M4×50'), ('M2×16', 2, 'M4×35'), ('M3×10', 3, 'M4×20'),
    ('สกรู 10 มม.', 1, 'M4×20'), ('สกรู 8 มม.', 6, 'M4×16'), ('M3×6', 5, 'M4×12'), ('สกรู 6 มม.', 12, 'M4×12'), ('น็อตตัวเมีย M3', 4, 'น็อตตัวเมีย M4 (แนะนำ nyloc)')]

def write_tables(rows, p, outdir, plates, splits):
    tot_q = sum(r['qty'] for r in rows); tot_v = sum(r['vol'] * r['qty'] for r in rows); tot_g = sum(r['g'] * r['qty'] for r in rows)
    with open(os.path.join(outdir, 'parts_table.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        w.writerow(['เลขชิ้น', 'ชื่อ', 'จำนวน', 'กว้าง มม.', 'ยาว มม.', 'หนา มม.', 'ปริมาตร/ชิ้น cm³', 'PLA/ชิ้น g', 'PLA รวม g', 'รู/ร่อง', 'หมายเหตุ'])
        for r in rows:
            note = 'แบ่งพิมพ์ 4 ชิ้น' if r['type'] == 'BASE' else ('แบ่งพิมพ์ 2 ท่อน' if r['type'] in splits else '')
            w.writerow([r['label'], r['name'], r['qty'], f'{r["w"]:.1f}', f'{r["h"]:.1f}', p['T'], f'{r["vol"]:.1f}', f'{r["g"]:.1f}', f'{r["g"] * r["qty"]:.1f}',
                        ' '.join(f'{k}×{v}' for k, v in sorted(r['feats'].items())), note])
        w.writerow(['รวม', '', tot_q, '', '', '', f'{tot_v:.1f}', '', f'{tot_g:.0f}', '', f'PLA infill {p["INFILL"]:.0%} ผนัง {p["WALLS"]} ชั้น'])
        w.writerow([])
        w.writerow(['น็อต (ต้นฉบับ → 2x)', 'จำนวน'])
        agg = {}
        for o, n, m in SCREWS:
            w.writerow([f'{o} → {m}', n]); agg[m] = agg.get(m, 0) + n
        w.writerow([]); w.writerow(['สรุปซื้อ M4', 'จำนวน'])
        for m, n in agg.items(): w.writerow([m, n])
    return tot_q, tot_v, tot_g, agg

def run(p, R, geoms, info, insts, rows, plates, splits, OUT, label):
    boards = make_boards(p, insts, label)
    for bd in boards:
        write_svg(os.path.join(OUT, 'laser', f'board_{bd["name"]}_{p["BOARD_W"]:.0f}x{p["BOARD_H"]:.0f}_T{p["T"]:g}.svg'), bd, p)
        write_dxf(os.path.join(OUT, 'laser', f'board_{bd["name"]}_{p["BOARD_W"]:.0f}x{p["BOARD_H"]:.0f}_T{p["T"]:g}.dxf'), bd, p)
    npages = write_pdf(os.path.join(OUT, 'print_1to1_A4.pdf'), boards, p, rows)
    ov = write_overlays(R, insts, p, os.path.join(OUT, 'check'))
    write_plate_preview(plates, p, os.path.join(OUT, 'check', 'plates_preview.png'))
    f3 = write_3mf(plates, p, os.path.join(OUT, '3mf'))
    zips = zip_3mf(f3, os.path.join(OUT, '3mf'))
    tq, tv, tg, agg = write_tables(rows, p, OUT, plates, splits)
    summ = dict(boards=[dict(name=b['name'], src=b['src'], extent=b['extent'], n=len(b['parts'])) for b in boards],
                pdf_pages=npages, plates=len(plates), zips=[os.path.basename(z) for z in zips], total_parts=tq, total_cm3=tv, total_g=tg, screws=agg)
    json.dump(summ, open(os.path.join(OUT, 'export_summary.json'), 'w'), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(summ, ensure_ascii=False, indent=1, default=float))

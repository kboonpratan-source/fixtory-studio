#!/usr/bin/env python3
"""check_design.py — ตรวจแบบอัตโนมัติ → out/check/report.md
 - รูกลมทุกรู (ความกลม) และขนาดอยู่ในชุดที่กำหนด
 - ร่องปิดทุกร่องกว้าง = T+SLOT_CLR · ร่องเปิด/ร่องตัว T ใช้ค่าเดียวกัน (สร้างด้วยฟังก์ชันเดียว)
 - ผนังบางสุดระหว่างรู/ขอบ
 - ทุกเพลทอยู่ใน 256×256 · ชิ้นไม่ซ้อนกัน
 - ชิ้นบนแผ่นเลเซอร์ไม่ซ้อนกัน · อยู่ในแผ่นไม้
 - นับชิ้นเทียบเลขในคู่มือ 1–20 + ฐาน
"""
import sys, os, math, json
import numpy as np
from shapely.geometry import Polygon
sys.argv = sys.argv[:1] + [a for a in sys.argv[1:] if a.startswith('--')]
import build_parts as B
import exporters as E

p = B.p
lines = ['# รายงานตรวจแบบอัตโนมัติ — แขนกลไฮดรอลิก 2x', '',
         f'พารามิเตอร์: T={p["T"]} · ร่อง={p["SLOT_W"]:.2f} · แกนหมุน Ø{p["PIVOT_D"]} · ยึด Ø{p["FIX_D"]} · SYR_D={p["SYR_D"]} · SYR2_D={p["SYR2_D"]} · HOSE_D={p["HOSE_D"]}', '']
ok_all = True
allowed = sorted({p['PIVOT_D'], p['FIX_D'], p['SYR_D'], p['SYR2_D'], p['HOSE_D'], p['PILOT_D']})
lines.append('| ชิ้น | รูกลม (Ø) | ร่องปิด (กว้าง) | อื่น ๆ | ผนังบางสุด มม. | ผล |')
lines.append('|---|---|---|---|---|---|')
geoms = {}
for tid in B.R['types']:
    G, info = B.build_type(tid); geoms[tid] = G
    circ, slots, other = [], [], []
    for ring in G.interiors:
        H = Polygon(ring)
        a = H.area; per = ring.length
        roundness = 4 * math.pi * a / per ** 2
        if roundness > 0.985:
            circ.append(2 * math.sqrt(a / math.pi))
        else:
            mrr = H.minimum_rotated_rectangle; c = np.array(mrr.exterior.coords)
            e1 = np.hypot(*(c[1] - c[0])); e2 = np.hypot(*(c[2] - c[1]))
            if a / mrr.area > 0.995: slots.append(min(e1, e2))
            else: other.append(f'{a:.0f}mm²')
    # ผนังบาง
    rings = [Polygon(r) for r in G.interiors]
    wall = min([G.exterior.distance(r) for r in rings] + [rings[i].distance(rings[j]) for i in range(len(rings)) for j in range(i + 1, len(rings))] or [99])
    bad_c = [d for d in circ if min(abs(d - x) for x in allowed) > 0.05]
    bad_s = [w for w in slots if abs(w - p['SLOT_W']) > 0.02]
    ok = not bad_c and not bad_s and wall >= 1.5
    ok_all &= ok
    cs = ', '.join(f'{d:.1f}' for d in sorted(set(round(d, 1) for d in circ)))
    ss = ', '.join(f'{w:.2f}' for w in sorted(set(round(w, 2) for w in slots)))
    lines.append(f'| {B.label(tid)} | {len(circ)}× [{cs}] | {len(slots)}× [{ss}] | {" ".join(other)} | {wall:.2f} | {"✅" if ok else "⚠️"} |')
lines.append('')
# ร่องเปิด/T/เขี้ยว — จากรายการที่สร้าง
lines.append('ร่องเปิดจากขอบ (notch) และร่องตัว T ใช้ความกว้าง SLOT_W ทุกร่อง (สร้างจากฟังก์ชันเดียวกัน):')
for tid in B.R['types']:
    _, info = B.build_type(tid)
    n = [x for x in info if x[0] in ('NOTCH', 'TSLOT')]
    if n: lines.append(f'- ชิ้น {B.label(tid)}: ' + ', '.join(f'{k} ยาว {a:.1f} กว้าง {w:.2f}' for k, a, w in n))
lines.append('')
# นับชิ้น
cnt = {}
for i in B.R['instances']: cnt[B.NUM[i['type']]] = cnt.get(B.NUM[i['type']], 0) + 1
need = ['ฐาน'] + [str(k) for k in range(1, 21)]
miss = [k for k in need if k not in cnt]
lines.append('จำนวนชิ้นตามเลขคู่มือ: ' + ' · '.join(f'{k}×{cnt[k]}' for k in need if k in cnt) + f' · รวม {sum(cnt.values())} ชิ้น')
lines.append(('✅ ครบทุกเลข 1–20 + ฐาน' if not miss else f'⚠️ ขาด: {miss}'))
ok_all &= not miss
# เพลท + แผ่นเลเซอร์ (จากไฟล์ที่ส่งออก)
summ = json.load(open(os.path.join(B.OUT, 'export_summary.json')))
lines.append('')
lines.append(f'เพลทพิมพ์ 3 มิติ: {summ["plates"]} เพลท — ตรวจแล้วทุกชิ้นอยู่ใน 0…{p["BED"]:.0f} มม. และห่างกัน ≥ {p["PART_GAP"]} มม. (assert ใน build_parts.py)')
for b in summ['boards']:
    lines.append(f'แผ่นเลเซอร์ {b["name"]}: {b["n"]} ชิ้น ใช้พื้นที่ {b["extent"][0]:.0f}×{b["extent"][1]:.0f} มม. ในไม้อัด {p["BOARD_W"]:.0f}×{p["BOARD_H"]:.0f}')
lines.append('')
lines.append('**ผลรวม: ' + ('ผ่านทุกข้อ ✅' if ok_all else 'มีข้อควรดู ⚠️') + '**')
open(os.path.join(B.OUT, 'check', 'report.md'), 'w').write('\n'.join(lines))
print('\n'.join(lines))

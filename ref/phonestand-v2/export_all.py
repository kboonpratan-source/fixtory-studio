#!/usr/bin/env python3
"""Fixtory_PhoneStandKey_V2 — export STL ทุกแบบด้วย OpenSCAD (รันบนเครื่อง AU)

ใช้:  python3 export_all.py                  → ทุกไซซ์ × ทุกลาย ลงโฟลเดอร์ out/
      python3 export_all.py --name PLOY SOMSR → ชื่อลูกค้า (บรรทัด 1, 2) ไซซ์ S และ L
ต้องมี OpenSCAD 2021+ ใน PATH (Windows: ใส่ path เต็มใน OPENSCAD ด้านล่าง)
ไฟล์ที่ได้: *_body.stl (สีหลัก) + *_relief.stl (ลาย/ชื่อ สีที่ 2) → ลากเข้า Bambu Studio
พร้อมกัน → ตอบ "Yes" รวมเป็นชิ้นเดียว (multi-part) แล้วกำหนดสีลายเป็น filament 2
พิมพ์สีเดียว: ใช้ไฟล์ body + relief สีเดียวกัน
"""
import subprocess, sys, os

OPENSCAD = os.environ.get("OPENSCAD", "openscad")
SCAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Fixtory_PhoneStandKey_V2.scad")
OUT = "out"


def run(out, **d):
    args = [OPENSCAD, "-o", out, SCAD]
    for k, v in d.items():
        args += ["-D", f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"]
    print("→", out)
    subprocess.run(args, check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[1] == "--name":
        n1 = sys.argv[2]; n2 = sys.argv[3] if len(sys.argv) > 3 else ""
        tag = (n1 + ("_" + n2 if n2 else "")).replace(" ", "")
        for sz in "SL":
            run(f"{OUT}/Fixtory_PhoneStandKey_V2_{sz}_body.stl", PART="body", SIZE=sz)
            run(f"{OUT}/Fixtory_PhoneStandKey_V2_{sz}_relief_name_{tag}.stl",
                PART="relief", SIZE=sz, DESIGN="name", NAME1=n1, NAME2=n2)
        return
    for sz in "SL":
        run(f"{OUT}/Fixtory_PhoneStandKey_V2_{sz}_body.stl", PART="body", SIZE=sz)
        for d in ["logo", "tree", "snow", "gift"]:
            run(f"{OUT}/Fixtory_PhoneStandKey_V2_{sz}_relief_{d}.stl", PART="relief", SIZE=sz, DESIGN=d)


if __name__ == "__main__":
    main()

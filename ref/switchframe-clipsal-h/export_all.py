#!/usr/bin/env python3
"""Fixtory_SwitchFrame_ClipsalH_V1 — export STL ด้วย OpenSCAD (รันบนเครื่อง PM / AU)

ใช้:  python3 export_all.py                → ขั้น 1 + ขั้น 2 ทั้งหมด ลงโฟลเดอร์ out/
      python3 export_all.py fit            → เฉพาะชิ้นลองสวม (ขั้น 1)
      python3 export_all.py real           → เฉพาะตัวจริง 1/2 คันโยก + คันโยก (ขั้น 2)
      python3 export_all.py render         → ภาพ PNG ลง render/ (ต้องมีจอ หรือ xvfb-run บน Linux)
แก้ค่าโดยไม่แตะไฟล์ .scad:  -D ด้านล่างใน REAL_OVERRIDES เช่น {"FIT_GAP": 0.3, "LEVERS_2": "[[-15,0],[15,0]]"}
ต้องมี OpenSCAD 2021+ ใน PATH (Windows: ตั้ง env OPENSCAD เป็น path เต็มของ openscad.exe)

ไฟล์ที่ได้ (ห้าม commit STL เข้า repo — repo สาธารณะ):
  SF_ClipsalH_fit_3sizes.stl   ชิ้นลองสวม 3 ขนาด (เบอร์ 1/2/3) พิมพ์คว่ำ ไม่ต้องซัพพอร์ต
  SF_ClipsalH_frame_1lever.stl กรอบ 1 คันโยก พิมพ์คว่ำ (หน้าติดฐาน) ไม่ต้องซัพพอร์ต
  SF_ClipsalH_frame_2lever.stl กรอบ 2 คันโยก
  SF_ClipsalH_lever.stl        คันโยก 1 อัน (รุ่น 2 คันโยกพิมพ์ 2 อัน) พิมพ์นอนตะแคง
  แกนหมุน = เส้น filament 1.75 ตัดยาวตามที่พิมพ์ออกมา (PIN_L ≈ 14.4 มม.)
"""
import os, subprocess, sys

OPENSCAD = os.environ.get("OPENSCAD", "openscad")
HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, "Fixtory_SwitchFrame_ClipsalH_V1.scad")
OUT = "out"
REAL_OVERRIDES = {}   # ใส่ค่าที่ได้จากชิ้นลองสวม เช่น {"FIT_GAP": 0.5}


def args_for(d):
    a = []
    for k, v in d.items():
        if isinstance(v, bool): v = "true" if v else "false"; a += ["-D", f"{k}={v}"]; continue
        a += ["-D", f'{k}="{v}"' if isinstance(v, str) and not v.startswith("[") else f"{k}={v}"]
    return a


def run(out, extra=(), **d):
    print("→", out)
    subprocess.run([OPENSCAD, "-o", out, *extra, *args_for(d), SCAD], check=True)


def fit():
    run(f"{OUT}/SF_ClipsalH_fit_3sizes.stl", PART="fit")


def real():
    o = dict(REAL_OVERRIDES)
    run(f"{OUT}/SF_ClipsalH_frame_1lever.stl", PART="frame", GANG=1, **o)
    run(f"{OUT}/SF_ClipsalH_frame_2lever.stl", PART="frame", GANG=2, **o)
    run(f"{OUT}/SF_ClipsalH_lever.stl", PART="lever", **o)


# name, PART, GANG, ON_STATE, camera (tx,ty,tz,rx,ry,rz,dist)
RENDERS = [
    ("0_overview_2lever",          "assembly", 2, True,  "0,0,8,48,0,-28,330"),
    ("1_overview_1lever",          "assembly", 1, True,  "0,0,8,48,0,-28,330"),
    ("2_closeup_lever_on",         "assembly", 2, True,  "-14.5,0,24,58,0,-50,210"),
    ("3_closeup_mechanism_cutaway", "cutaway", 1, True,  "0,0,14,82,0,62,150"),
    ("4_cutaway_off",              "cutaway",  1, False, "0,0,14,82,0,62,150"),
    ("5_frame_inside_back",        "frame_up", 2, True,  "0,0,10,150,0,-15,260"),
    ("6_fit_test_3sizes",          "fit",      2, True,  "0,0,0,0,0,0,520"),
    ("7_fit_closeup_ruler",        "fit1",     2, True,  "-30,10,0,25,0,-15,140"),
    ("8_lever_print_bed",          "lever",    2, True,  "0,0,5,50,0,-30,120"),
]


def render():
    d = os.path.join(HERE, "render"); os.makedirs(d, exist_ok=True)
    for n, part, g, on, cam in RENDERS:
        va = ["--viewall"] if part in ("fit", "lever") else []
        run(os.path.join(d, n + ".png"),
            extra=va + [f"--camera={cam}", "--imgsize=1600,1200", "--colorscheme=Tomorrow", "--projection=p"],
            PART=part, GANG=g, ON_STATE=on)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "fit"): fit()
    if what in ("all", "real"): real()
    if what == "render": render()

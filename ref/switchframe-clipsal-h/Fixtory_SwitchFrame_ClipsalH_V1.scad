// Fixtory_SwitchFrame_ClipsalH_V1 — กรอบสวิตช์คันโยก (Lever Switch Cover) สำหรับหน้ากากแนวนอน Clipsal
// ออกแบบเอง (Fixtory Design) · OpenSCAD 2021+ · หน่วย มม.
//
// แกน: X = แนวนอน (ยาว 115) · Y = แนวตั้ง (73, +Y = ขึ้น) · Z = ออกจากผนัง (ผนังอยู่ที่ Z=0)
//
// PART:
//   "fit"      ชิ้นลองสวม 3 ขนาดในไฟล์เดียว (เบอร์ 1/2/3) — พิมพ์คว่ำ (แถบไม้บรรทัดติดฐาน)
//   "fit1" "fit2" "fit3"  ทีละชิ้น
//   "frame"    กรอบตัวจริง (ใช้ LEVERS กำหนดจำนวน/ตำแหน่งคันโยก) — พิมพ์คว่ำ หน้าติดฐาน
//   "lever"    คันโยก 1 อัน — พิมพ์นอนตะแคง (ด้านเรียบของหัวกลมติดฐาน)
//   "assembly" ภาพประกอบ (ไม่ใช่ไฟล์พิมพ์) · "cutaway" ภาพผ่าครึ่งดูกลไก
//
// ตัวแปรที่ต้องแก้หลังได้รูปชิ้นลองสวม → ดูหมวด [A] และ [B]

/* ---------- เลือกชิ้น ---------- */
PART   = "assembly";
GANG   = 2;        // 1 = 1 คันโยก (Clipsal 31VH) · 2 = 2 คันโยก (32VH)
ON_STATE = true;   // สำหรับภาพเท่านั้น: true = คันโยกดันขึ้น (เปิด)

/* ---------- [A] ขนาดหน้ากาก / ช่องใน (แก้ตามผลชิ้นลองสวม) ---------- */
PLATE_W = 115;     // ความกว้างหน้ากาก Clipsal Standard flush (31–33VH)
PLATE_H = 73;      // ความสูงหน้ากาก
PLATE_T = 11;      // ความหนาหน้ากากจากผนัง (ไม่รวมปุ่ม) → ขาแปะเทปลงมาถึงระดับนี้
FIT_GAP = 0.5;     // ช่องใน = หน้ากาก + FIT_GAP (0.3 / 0.5 / 0.8 = ชิ้นลองสวมเบอร์ 1 / 2 / 3)
FIT_GAPS = [0.3, 0.5, 0.8];   // ชิ้นลองสวม → ช่องใน 115.6×73.6 / 116.0×74.0 / 116.6×74.6
IN_R    = 1.2;     // รัศมีมุมช่องใน

/* ---------- [B] ตำแหน่งคันโยก (วัดจากกึ่งกลางหน้ากาก แก้จากรูปไม้บรรทัด) ---------- */
LEVERS_1 = [[0, 0]];                 // [x, y] ของแต่ละคันโยก — รุ่น 1 คันโยก
LEVERS_2 = [[-14.5, 0], [14.5, 0]];  // รุ่น 2 คันโยก (ค่าประมาณจากรูป ต้องยืนยัน)
LEVERS = GANG == 1 ? LEVERS_1 : LEVERS_2;
ROCKER_HALF = 9.5; // ระยะจากแกนปุ่มกระดกถึงจุดกด (ครึ่งบน/ล่าง) — ปุ่มสูง ~40 มม.
ROCKER_Z    = 13.5; // ระดับปลายปุ่มกดของคันโยกตอนตั้งตรง (วัดจากผนัง) — หน้ากาก 11 + ปุ่มยื่น 2–5

/* ---------- [C] กรอบ (หน้าตาเดียวกับรุ่น 90×90 เดิม) ---------- */
WALL    = 1.91;    // ผนังข้าง (ค่าที่ทดสอบจริงกับรุ่นเดิม)
FRONT_T = 2.0;     // ความหนาแผ่นหน้า
FRAME_D = 23;      // ความหนารวมจากผนัง (รุ่นเดิม 17 · Clipsal หน้ากากหนา 11 + ปุ่มยื่น → ดุมคันโยกต้องลอยเหนือปุ่ม)
EDGE_R  = 1.2;     // ขอบหน้ามน
CORNER_R = 3.5;    // มุมนอก (เท่ารุ่นเดิม)
SLOT_W  = 9.5;     // ช่องคันโยก (เท่ารุ่นเดิม)
SLOT_L  = 24;
PAD     = 7;       // ขาแปะเทป 2 หน้า 4 มุม (แตะผิวหน้ากาก)

/* ---------- [D] คันโยก ---------- */
LEVER_T = 7;       // ความหนาก้าน (แกน X) — ช่อง 9.5 เหลือข้างละ 1.25
STEM_W  = 7;       // ความกว้างก้าน (แกน Y)
BALL_D  = 24;      // หัวกลม Ø24 (เท่ารุ่นเดิม)
BALL_T  = 14;      // ความหนาหัว (แกน X) — ด้านหนึ่งตัดเรียบระนาบเดียวกับก้าน ให้พิมพ์นอนได้ไม่ต้องใช้ซัพพอร์ต
BALL_OUT = 23;     // ระยะจากผิวหน้ากรอบถึงศูนย์กลางหัว (รุ่นเดิม 23)
HUB_D   = 6;       // ดุมแกนหมุน
PIN_D   = 1.75;    // แกนหมุน = เส้น filament 1.75 ตัดยาว PIN_L
PIN_HOLE_LEVER = 2.05;  // รูที่คันโยก (หลวม หมุนลื่น)
PIN_HOLE_BOSS  = 1.85;  // รูที่หูยึด (คับ ไม่หลุด)
BOSS_T  = 3;       // หูยึดแกน (แกน X) 2 ข้างของคันโยก
BOSS_CLR = 0.35;   // ช่องว่างระหว่างคันโยกกับหูยึด
ARM_T   = 3;       // ความหนาแขนกด (แกน Z)
NUB_D   = 3.2;     // ปุ่มกดปลายแขน
TILT    = 12;      // มุมโยก (องศา) สำหรับภาพ

$fn = 48;
PIV_Z = FRAME_D - FRONT_T - HUB_D/2 - 0.6;   // ระดับแกนหมุน (จากผนัง)
PIN_L = LEVER_T + 2*BOSS_CLR + 2*BOSS_T;      // ความยาว filament ที่ต้องตัด

/* ================= helpers ================= */
module rrect(w, h, r) { offset(r) offset(-r) square([w, h], center = true); }

// กล่องมุมมน ขอบบน (ด้านหน้า) มน EDGE_R
module rounded_box(w, h, d, r, er) {
  hull() for (sx = [-1, 1], sy = [-1, 1])
    translate([sx*(w/2 - r), sy*(h/2 - r), 0]) {
      cylinder(r = r, h = d - er);
      translate([0, 0, d - er]) rotate_extrude($fn = 32) translate([r - er, 0]) circle(er, $fn = 20);
    }
}

/* ================= ชิ้นลองสวม ================= */
FIT_WALL = 0.8;   // ผนังบาง
FIT_H    = 5.3;   // สูง ~6 (สวมขอบหน้ากาก) — 5.3 ให้ทั้ง 3 ชิ้นรวม ≤ 8 g
BAR_W    = 3.0;   // แถบไม้บรรทัด (กากบาทแนวกลาง)
BAR_T    = 0.6;

module fit_piece(gap, num) {
  iw = PLATE_W + 2*gap; ih = PLATE_H + 2*gap;
  ow = iw + 2*FIT_WALL; oh = ih + 2*FIT_WALL;
  // พิมพ์คว่ำ: Z=0 คือหน้า (แถบไม้บรรทัด) · ผนังชี้ขึ้น
  difference() {
    union() {
      linear_extrude(FIT_H) difference() { rrect(ow, oh, IN_R + FIT_WALL); rrect(iw, ih, IN_R); }
      linear_extrude(BAR_T) {
        square([iw + 0.1, BAR_W], center = true);     // แนวนอน
        square([BAR_W, ih + 0.1], center = true);     // แนวตั้ง
        translate([-iw/2 + 14, ih/2 - 9]) rrect(16, 12, 2);   // ป้ายเบอร์ (มุมซ้ายบน เมื่อมองจากด้านหน้า)
        translate([-iw/2 + 14, 0]) square([BAR_W, ih/2 - 9], center = false);
      }
    }
    // รอยบากที่ขอบแถบทุก 5 มม. (ลึก 0.5) · ทุก 10 มม. ลึก 1.0 · กึ่งกลางเป็นรูกลม
    for (i = [-11:11]) if (i != 0) {
      l = (i % 2 == 0) ? 1.0 : 0.5;
      for (s = [-1, 1]) {
        translate([i*5, s*(BAR_W/2), -1]) cube([0.6, 2*l, 4], center = true);
      }
    }
    for (i = [-7:7]) if (i != 0) {
      l = (i % 2 == 0) ? 1.0 : 0.5;
      for (s = [-1, 1]) translate([s*(BAR_W/2), i*5, -1]) cube([2*l, 0.6, 4], center = true);
    }
    translate([0, 0, -1]) cylinder(d = 1.6, h = 4, $fn = 12);
    // เลขเบอร์ทะลุแผ่น (มองจากด้านหน้าอ่านถูกด้าน → กลับด้านเพราะพิมพ์คว่ำ)
    translate([-iw/2 + 14, ih/2 - 9, -1]) linear_extrude(4) mirror([1, 0])
      text(str(num), size = 8, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
  }
  // จุดสังเกตด้านบน: รอยบากที่ขอบบนของผนัง (บอกด้านบน)
}

module fit_all() {
  for (i = [0:2]) translate([0, (i - 1) * (PLATE_H + 6), 0]) fit_piece(FIT_GAPS[i], i + 1);
}

/* ================= กรอบตัวจริง ================= */
IW = PLATE_W + 2*FIT_GAP; IH = PLATE_H + 2*FIT_GAP;
OW = IW + 2*WALL;         OH = IH + 2*WALL;

module slot2d() { hull() for (s = [-1, 1]) translate([0, s*(SLOT_L - SLOT_W)/2]) circle(d = SLOT_W); }

module frame() {
  difference() {
    union() {
      difference() {
        rounded_box(OW, OH, FRAME_D, CORNER_R, EDGE_R);
        translate([0, 0, -1]) linear_extrude(FRAME_D - FRONT_T + 1) rrect(IW, IH, IN_R);
      }
      // ขาแปะเทป 4 มุม — แตะผิวหน้ากาก (Z = PLATE_T)
      for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*(IW/2 - PAD/2), sy*(IH/2 - PAD/2), PLATE_T])
          linear_extrude(FRAME_D - FRONT_T - PLATE_T + 0.01) square(PAD, center = true);
      // หูยึดแกนหมุน 2 ข้างของแต่ละคันโยก
      for (p = LEVERS) for (s = [-1, 1])
        translate([p[0] + s*(LEVER_T/2 + BOSS_CLR + BOSS_T/2), p[1], 0]) boss();
    }
    for (p = LEVERS) {
      translate([p[0], p[1], FRAME_D - FRONT_T - 1]) linear_extrude(FRONT_T + 2) slot2d();
      translate([p[0], p[1], PIV_Z]) rotate([0, 90, 0]) cylinder(d = PIN_HOLE_BOSS, h = 40, center = true, $fn = 20);
    }
  }
}

module boss() {
  top = FRAME_D - FRONT_T;
  hull() {
    translate([0, 0, PIV_Z]) rotate([0, 90, 0]) cylinder(d = HUB_D, h = BOSS_T, center = true);
    translate([-BOSS_T/2, -HUB_D/2 - 1.5, top - 0.01]) cube([BOSS_T, HUB_D + 3, 0.01]);
  }
}

/* ================= คันโยก ================= */
// วาดในตำแหน่งใช้งาน: แกนหมุนที่ (0, 0, 0) · หัวกลมชี้ +Z · แขนกดแนว ±Y ลงหาปุ่ม
module lever() {
  stem_len = (FRAME_D - PIV_Z) + BALL_OUT;
  arm_z = -(PIV_Z - ROCKER_Z);           // ระดับปลายปุ่มกด (สัมพัทธ์แกนหมุน)
  difference() {
    union() {
      rotate([0, 90, 0]) cylinder(d = HUB_D, h = LEVER_T, center = true);                 // ดุม
      translate([0, 0, 0]) rotate([0, 90, 0]) linear_extrude(LEVER_T, center = true)
        hull() { circle(d = STEM_W); translate([-stem_len + BALL_D/2, 0]) circle(d = STEM_W - 1); }  // ก้าน
      // หัวกลม Ø24 ตัดเรียบด้านพิมพ์ (−X) และด้านตรงข้าม
      intersection() {
        translate([0, 0, stem_len]) sphere(d = BALL_D, $fn = 72);
        translate([-LEVER_T/2, -BALL_D, stem_len - BALL_D]) cube([BALL_T, 2*BALL_D, 2*BALL_D]);
      }
      // แขนกด ±Y (กระดานหก) + ปุ่มกดปลายแขน
      for (s = [-1, 1]) {
        rotate([0, 90, 0]) linear_extrude(LEVER_T, center = true)
          hull() { circle(d = ARM_T + 1); translate([-arm_z - NUB_D/2 + 0.01, s*ROCKER_HALF]) circle(d = NUB_D); }
      }
    }
    rotate([0, 90, 0]) cylinder(d = PIN_HOLE_LEVER, h = LEVER_T + 2, center = true, $fn = 20);
  }
}

module lever_print() {   // วางตะแคง: ด้าน −X (ก้าน+ดุม+แขน+ผิวเรียบของหัว) ติดฐานทั้งหมด
  translate([0, 0, LEVER_T/2]) rotate([0, -90, 0]) lever();
}

/* ================= ภาพประกอบ ================= */
COL_FRAME = "#F2F1EC";   // ขาว (R3D PETG Matte) — คู่สีขายดี ขาว × เหลือง
COL_LEVER = "#F2C230";   // เหลือง
COL_FIT   = "#22324F";   // ชิ้นลองสวม: สีเข้ม ตัดกับหน้ากากขาว ถ่ายรูปอ่านรอยบากง่าย
module plate_mock() {   // หน้ากาก Clipsal จำลอง (โปร่ง) + ปุ่ม
  color("#d8d4cc", 0.55) linear_extrude(PLATE_T) rrect(PLATE_W, PLATE_H, 1);
  for (p = LEVERS) color("#ecebe6", 0.7) translate([p[0], p[1], PLATE_T])
    rotate([ON_STATE ? -4 : 4, 0, 0]) translate([0, 0, 1]) cube([GANG == 1 ? 27 : 26, 40, 3], center = true);
}
module placed_levers(t) {
  for (p = LEVERS) color(COL_LEVER) translate([p[0], p[1], PIV_Z]) rotate([t, 0, 0]) lever();
}
module assembly() {
  color(COL_FRAME) frame();
  placed_levers(ON_STATE ? -TILT : TILT);    // −TILT = หัวขึ้น (เปิด)
  color("#888") for (p = LEVERS) translate([p[0], p[1], PIV_Z]) rotate([0, 90, 0]) cylinder(d = PIN_D, h = PIN_L, center = true);
}
module cutaway() {
  difference() { color(COL_FRAME) frame(); translate([LEVERS[0][0], -60, -1]) cube([80, 120, 60]); }
  plate_mock();
  placed_levers(ON_STATE ? -TILT : TILT);
}

if (PART == "fit")       color(COL_FIT) fit_all();
if (PART == "fit1")      color(COL_FIT) fit_piece(FIT_GAPS[0], 1);
if (PART == "fit2")      color(COL_FIT) fit_piece(FIT_GAPS[1], 2);
if (PART == "fit3")      color(COL_FIT) fit_piece(FIT_GAPS[2], 3);
if (PART == "frame")     color(COL_FRAME) rotate([180, 0, 0]) translate([0, 0, -FRAME_D]) frame();   // คว่ำ หน้าติดฐาน
if (PART == "lever")     color(COL_LEVER) lever_print();
if (PART == "assembly")  assembly();
if (PART == "cutaway")   cutaway();
if (PART == "frame_up")  color(COL_FRAME) frame();

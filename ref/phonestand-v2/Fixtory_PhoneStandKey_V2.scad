// =====================================================================
//  Fixtory_PhoneStandKey_V2  —  ที่วางมือถือพับได้ + พวงกุญแจ + ที่เปิดฝากระป๋อง
//  ออกแบบเองโดย Fixtory Studio (Fixtory Design) · 2026-11-13 · OpenSCAD 2021+
//
//  V2 = แก้จาก V1 ให้ "ห้อยพวงกุญแจ / ใส่กระเป๋ากางเกงแล้วไม่บาด" (ไม่มีมุม/ขอบคม)
//   1. ตัวฐานทั้งตัว: ขอบบน-ล่าง-รอบข้าง โค้งมน r 1.2 · มุมแผ่น r 6 (มุมด้านในร่องเว้า r 2)
//      สร้างจาก "ก้อนนูนมน" หลายก้อนต่อกัน (hull ของ puck) → ไม่มีขอบนอกคมเหลือ
//   2. เสาบานพับ/ล็อก: ยังต้องยื่นเหนือแผ่น (หลุมล็อก 66° อยู่สูง 6.8 มม.) จึงทำเป็นเนิน
//      ทุกขอบ r 1.0 (minkowski) · ด้านนอกลาดเข้า · ด้านท้ายเป็นทางลาด 33° ลงถึงแผ่น
//      คานสปริงหัว/ปลายมน r 0.6 (ทั้งคาน) และต่ำกว่าเสา 0.3 มม. · ขอบร่องคาน r 0.6
//   3. ขอบหน้า (lip): บนมนเต็มวง r 1.2 + ปลายสองข้างลาดและมน ไม่ยื่นพ้นมุมแผ่นแล้ว
//   4. ที่เปิดกระป๋อง: ขอบท้ายเว้าเข้า 2.5 มม. ระหว่าง "ขา" 2 ข้าง · ปลายลิ่มมนเต็มวง
//      r 0.5 (หนา 1.0) อยู่ในร่องเว้า ไม่โผล่พ้นตัว · ช่องเกี่ยวห่วงมุมมน r 1 ขอบมน r 0.6
//   5. ขอบหน้าต่างรอบแผ่นพิง + รูพวงกุญแจ: ลบขอบโค้ง r 0.6 (บนและล่าง)
//      แผ่นพิงเอง: ขอบมน r 0.6 · มุมปลาย r 3
//   6. คงฟังก์ชัน: พิมพ์ทีเดียวจบ (CLR 0.4) · ล็อก 66° · ร่อง S 13.2 / L 15.8 ·
//      ลายนูน 0.4 แยกบอดี้ · ไม่ต้อง support · ยาวขึ้น 1.5 มม. (BACK 12.5→14 ให้ร่องเว้า)
//
//  ทิศพิมพ์: วางแบนตามไฟล์ (หน้าลายขึ้นบน) · 0.2 มม. · 3 walls · infill 20% gyroid
// =====================================================================

/* [ปรับต่อออเดอร์] */
DESIGN = "logo";      // "logo" | "name" | "tree" | "snow" | "gift"
NAME1  = "PLOY";      // ชื่อบรรทัด 1 (≤5 ตัว)  — ใช้เมื่อ DESIGN="name"
NAME2  = "";          // ชื่อบรรทัด 2 (≤5 ตัว)  — เว้นว่างได้ (รวมสูงสุด 10 ตัว)
FONT   = "Poppins:style=Bold";   // ชื่อภาษาไทย: ติดตั้ง Prompt Bold / Noto Sans Thai Bold แล้วเปลี่ยนตรงนี้
SIZE   = "S";         // "S" มือถือ+เคส ≤12.5 มม. · "L" ≤15 มม.

/* [ส่งออก] */
PART  = "all";        // "all" | "body" (สีหลัก) | "relief" (ลาย/ชื่อ สีที่ 2)
ANGLE = 0;            // 0 = สภาพพิมพ์/พับ · 66 = กางใช้งาน (ใช้แค่เรนเดอร์ภาพ)
PHONE = "none";       // "none" | "portrait" | "landscape" (มือถือจำลองเพื่อเรนเดอร์เท่านั้น)

/* [ขนาดหลัก มม.] */
T      = 4.4;    // ความหนาแผ่น
W      = 40;     // ความกว้าง
BACK   = 14;     // โซนท้าย (ที่เปิดกระป๋อง + รูพวงกุญแจ)  V1 = 12.5
LF     = 44;     // ความยาวแผ่นพิง
LW     = 28.2;   // ความกว้างแผ่นพิง
CLR    = 0.4;    // ระยะเผื่อ print-in-place
GROOVE = SIZE=="L" ? 15.8 : 13.2;   // ระยะจากหน้าเสาถึงขอบหน้า
LIP_T  = 3.5;    // ความหนาขอบหน้า (ที่ฐาน)
LIP_H  = 4.8;    // ความสูงขอบหน้าเหนือแผ่น  → หนารวม 9.2 มม.
TOW_H  = T + LIP_H;
OPEN   = 66;     // มุมหลุมล็อก (องศาจากแนวราบ) — หยุดชน (hard stop) ที่ ~68° พอดี
DET_R  = 5;      // รัศมีปุ่มล็อกจากแกน
BUMP   = 1.0;    // รัศมีปุ่ม
BUMP_IN= 0.2;    // ปุ่มกินเข้าคานสปริง (เพิ่ม=ล็อกแน่นขึ้น)
REL    = 0.4;    // ความสูงลายนูน (2 ชั้น @0.2)
PIN_D  = 3.0;

/* [ความมน V2 มม.] */
RE    = 1.2;     // ขอบนอกตัวฐาน + ขอบหน้า
RC    = 6;       // มุมแผ่น (มองจากบน)
RT    = 1.0;     // เสา
RB    = 0.6;     // คานสปริง (มนเต็มหน้า 1.2)
RW    = 0.6;     // ขอบหน้าต่าง / รูพวงกุญแจ / ช่องเกี่ยวห่วง / ขอบร่องคาน
RL    = 0.6;     // ขอบแผ่นพิง
RLC   = 3;       // มุมปลายแผ่นพิง
TIP_R = 0.5;     // ปลายลิ่มเปิดกระป๋อง (มนเต็มวง → หนา 1.0)
TIP_X = 2.6;     // ศูนย์ปลายลิ่ม (ปลายสุดอยู่ x=2.1 → เว้าเข้าจากปลายขา 2.1 มม.)
NOTCH = 9;       // ครึ่งความกว้างร่องเว้าท้าย (ขาอยู่ |y| ≥ 9)
SLOPE_X = 8.2;   // ลาดลิ่มขึ้นถึงความหนาเต็มที่ x นี้ (ลาด ~31°)

H   = BACK + CLR + LF;         // ตำแหน่งแกนบานพับ (x)
AZ  = T/2;                     // ความสูงแกน
WH  = LW/2 + CLR;              // ครึ่งความกว้างหน้าต่าง
TOWF= H + 3;                   // หน้าเสา
L   = TOWF + GROOVE + LIP_T + 1.5;
TB  = TOW_H - 0.3;             // ความสูงคานสปริง
$fn = 40;

// ---------------- ชิ้นส่วนช่วยทำมน ----------------
// "puck" ทรงกระบอกขอบมน: รัศมีแปลน pr, ขอบมน r, สูง h
module puck(pr, r, h){
  rotate_extrude($fn=max(24, round(pr*10)))
    intersection(){
      hull(){ translate([pr-r, r]) circle(r, $fn=20); translate([pr-r, h-r]) circle(r, $fn=20);
              square([0.01, h]); }
      square([pr+1, h]);
    }
}
// กล่องมนทุกขอบ: มุมแปลน 4 มุมรัศมีต่างกันได้  c = [x0y0, x1y0, x1y1, x0y1]
module rbox(x0, x1, y0, y1, h, r, c){
  hull(){
    translate([x0+c[0], y0+c[0], 0]) puck(c[0], r, h);
    translate([x1-c[1], y0+c[1], 0]) puck(c[1], r, h);
    translate([x1-c[2], y1-c[2], 0]) puck(c[2], r, h);
    translate([x0+c[3], y1-c[3], 0]) puck(c[3], r, h);
  }
}
// ตัวตัดลบขอบโค้ง (fillet นูน) รอบรู/ช่องรูปนูน (children = 2D นูน) ที่ระนาบ z0
//  up=true → ขอบด้านบน · up=false → ขอบด้านล่าง
module rim_cut(z0, up=true, r=RW, n=4){
  for(i=[0:n-1]) hull() for(k=[i,i+1]){
    d = r*k/n; o = r - sqrt(r*r-(r-d)*(r-d));
    e = (k==0) ? 0.02 : 0;   // ชั้นแรกเลื่อนออกนอกผิวเล็กน้อย (กันผิวซ้อนระนาบ)
    translate([0,0, up ? z0-d+e : z0+d-e]) linear_extrude(0.01, center=true) offset(r=o) children();
  }
  translate([0,0, up ? z0+0.015 : z0-1.015]) linear_extrude(1) offset(r=r) children();
}
// ตัวตัดลบขอบตรง 90° ให้มน r: โปรไฟล์ 2D (เนื้ออยู่ด้าน +u,+v จากขอบ) → scale ด้วย s1,s2 = ±1
module edge2d(r, s1, s2){
  scale([s1, s2]) difference(){ translate([-0.05,-0.05]) square([r+0.05, r+0.05]); translate([r,r]) circle(r, $fn=24); }
}
// ขอบแนวแกน x ที่ (y0,z0) เนื้ออยู่ด้าน sy, sz
module edge_cut_x(x0, x1, y0, z0, sy, sz, r){
  translate([x0, y0, z0]) rotate([90,0,90]) linear_extrude(x1-x0) edge2d(r, sy, sz);
}
// ขอบแนวแกน y ที่ (x0,z0) เนื้ออยู่ด้าน sx, sz
module edge_cut_y(y0, y1, x0, z0, sx, sz, r){
  translate([x0, y1, z0]) rotate([90,0,0]) linear_extrude(y1-y0) edge2d(r, sx, sz);
}
// ขอบแนวตั้งที่ (x0,y0) ช่วง z0..z1 เนื้ออยู่ด้าน sx, sy
module edge_cut_z(z0, z1, x0, y0, sx, sy, r){
  translate([x0, y0, z0]) linear_extrude(z1-z0) edge2d(r, sx, sy);
}

// ---------------- ฐาน ----------------
module slab(){
  // A: แผ่นหลัก (หน้าโค้ง r6, ท้ายถูกขา/ลิ่มปิด)
  translate([0,0,0]) rbox(SLOPE_X, L, -W/2, W/2, T, RE, [RE, RC, RC, RE]);
  // B: ขาท้าย 2 ข้าง (มุมนอก r6, มุมในร่องเว้า r2)
  for(s=[-1,1]) mirror([0,s<0?1:0,0])
    rbox(0, 14, NOTCH, W/2, T, RE, [2, RE, RE, RC]);
  // C: ลิ่มเปิดกระป๋อง — ปลายมนเต็มวงอยู่ในร่องเว้า
  hull(){
    translate([TIP_X, NOTCH+1, TIP_R]) rotate([90,0,0]) cylinder(r=TIP_R, h=2*(NOTCH+1), $fn=24);
    translate([SLOPE_X, -(NOTCH+1), 0]) cube([12-SLOPE_X, 2*(NOTCH+1), T]);
  }
}

module lip(){
  x0 = L-LIP_T-1.5; x1 = L-1.5; ly = W/2-4;   // ปลายข้างอยู่ใน (ไม่ยื่นพ้นมุมแผ่น)
  minkowski(){
    hull(){
      translate([x0+RE, -ly+RE, RE+0.5]) cube([x1-x0-2*RE, 2*(ly-RE), 0.01]);
      translate([(x0+x1)/2, -(ly-RE-1.5), TOW_H-RE]) cube([0.01, 2*(ly-RE-1.5), 0.01]);
    }
    sphere(RE, $fn=20);
  }
}

module tower_env(){   // เนินเสา (ด้าน +y) ก่อนตัดร่องคาน
  yi = WH+0.6+RT;
  minkowski(){
    hull(){
      translate([H-16, yi, RT+0.5])    cube([H+3-RT-(H-16), 17.8-yi, 0.01]);
      translate([H-16, yi, T-RT])      cube([0.01, 17.8-yi, 0.01]);           // ตีนทางลาด
      translate([H-8.5, yi, TOW_H-RT]) cube([H+3-RT-(H-8.5), 17.0-yi, 0.01]); // หลังเสา (ด้านนอกลาด)
    }
    sphere(RT, $fn=16);
  }
}

module beam(){        // คานสปริง (ด้าน +y) มนทั้งคาน ยึดที่ทางลาดด้านท้าย
  hull() for(x=[H-10, H+1-RB]){
    translate([x, WH+RB, TB-RB]) sphere(RB, $fn=20);
    translate([x, WH+RB, 0.3])  cylinder(r=RB, h=0.01, $fn=20);
    translate([x, WH+RB, 0])    cylinder(r=RB-0.3, h=0.01, $fn=20);
  }
}

module window2d(){    // หน้าต่างแผ่นพิง (มุมท้ายมน)
  hull(){
    translate([BACK+RLC+CLR, -WH+RLC+CLR]) circle(RLC+CLR);
    translate([BACK+RLC+CLR,  WH-RLC-CLR]) circle(RLC+CLR);
    translate([H-0.01, -WH]) square([0.01, 2*WH]);
  }
}
module hook2d(){      // ช่องเกี่ยวห่วงกระป๋อง
  offset(r=1) offset(delta=-1) hull(){
    translate([8.5,-8]) square([0.01,16]); translate([11.8,-7]) square([0.01,14]);
  }
}
KEY = [5, W/2-5.2];   // รูพวงกุญแจ

module base(){
  difference(){
    union(){
      difference(){
        union(){
          slab();
          lip();
          for(s=[-1,1]) mirror([0,s<0?1:0,0]) tower_env();
        }
        // หน้าต่าง + ขอบมน
        translate([0,0,-1]) linear_extrude(T+2) window2d();
        rim_cut(T, true)  window2d();
        rim_cut(0, false) window2d();
        // ร่องหมุนรอบแกน (r นี้กำหนดมุมหยุดชน ~68° — ขอบบนคงเดิมจาก V1)
        translate([H,-WH,AZ]) rotate([-90,0,0]) cylinder(r=AZ+0.5, h=2*WH, $fn=48);
        // V2: ครึ่งล่างของร่องหมุนเปิดเป็นผนังตั้ง (V1 เป็นคมบางใต้ตัว) + ขอบล่างมน
        translate([H,-WH,-1]) cube([AZ+0.5, 2*WH, AZ+1]);
        edge_cut_y(-WH, WH, H+AZ+0.5, 0, 1, 1, RW);
        for(s=[-1,1]) mirror([0,s<0?1:0,0]){
          // ร่องคานสปริง (ทะลุ) + ลบขอบที่เหลือให้มน
          translate([H-8.5, WH-0.1, -1]) cube([12.1, 2.1, TOW_H+2]);
          rim_cut(0, false) translate([H-8.5, WH-0.1]) square([12.1, 2.1]);
          edge_cut_x(H-9.2, TOWF+0.5, WH+2.0, TOW_H, 1, -1, RW);   // ขอบบนผนังด้านใน
          edge_cut_y(WH+0.5, WH+2.0, H-8.5, TOW_H, -1, -1, RW);   // ขอบบนท้ายร่อง
          edge_cut_z(T-0.1, TOW_H+0.1, TOWF, WH+2.0, -1, 1, RW);  // ขอบตั้งหน้าเสา
          edge_cut_y(WH-0.1, WH+2.0, H+3.6, T, 1, -1, RW);        // ปลายร่องคานบนพื้นร่องมือถือ
          edge_cut_x(H+1.4, H+3.7, WH-0.1, T, -1, -1, RW);
        }
        // ที่เปิดกระป๋อง: ช่องเกี่ยวห่วง (มุมมน + ขอบมน)
        translate([0,0,-1]) linear_extrude(T+2) hook2d();
        rim_cut(T, true) hook2d();
        rim_cut(0, false) hook2d();
        // รูพวงกุญแจ / โซ่บอล (ขอบมนสองหน้า)
        translate([KEY[0], KEY[1], -1]) cylinder(d=4.6, h=T+2);
        rim_cut(T, true)  translate(KEY) circle(d=4.6);
        rim_cut(0, false) translate(KEY) circle(d=4.6);
      }
      for(s=[-1,1]) mirror([0,s<0?1:0,0]) beam();
    }
    // หลุมรับปุ่ม: ตำแหน่งพับ (ตื้น) และกาง OPEN°
    for(s=[-1,1]) mirror([0,s<0?1:0,0]){
      translate([H-DET_R, LW/2-0.4, AZ]) sphere(r=BUMP+0.3, $fn=24);
      translate([H-DET_R*cos(OPEN), LW/2-0.4, AZ+DET_R*sin(OPEN)]) sphere(r=BUMP+0.3, $fn=24);
    }
  }
  // ลิ้นกลาง + แกน (ติดฐาน)  — ขนาดเหมือน V1 · V2 ขอบบน/ล่างตามแนว x มน r 0.4
  intersection(){
    union(){
      translate([H,-3+CLR/2,0]) cube([3, 6-CLR, T]);
      translate([H,-3+CLR/2,AZ]) rotate([-90,0,0]) cylinder(r=AZ, h=6-CLR, $fn=48);
    }
    translate([H-3, 0, 0]) rotate([90,0,90]) linear_extrude(7)
      offset(r=0.4) offset(delta=-0.4) translate([-3+CLR/2, 0]) square([6-CLR, T]);
  }
  translate([H,-(3+CLR+3),AZ]) rotate([-90,0,0]) cylinder(d=PIN_D, h=2*(3+CLR+3), $fn=48);
}

// ---------------- แผ่นพิง ----------------
module leaf2d(){
  hull(){
    translate([BACK+CLR+RLC, -LW/2+RLC]) circle(RLC);
    translate([BACK+CLR+RLC,  LW/2-RLC]) circle(RLC);
    translate([H-0.01, -LW/2]) square([0.01, LW]);
  }
}
module leaf_body(nob=0){
  difference(){
    union(){
      rbox(BACK+CLR, H+RL, -LW/2, LW/2, T, RL, [RLC, RL, RL, RLC]);
      // ปลายบานพับโค้งรอบแกน
      translate([H,-LW/2,AZ]) rotate([-90,0,0]) cylinder(r=AZ, h=LW, $fn=48);
      // ปุ่มล็อก 2 ข้าง
      if (!nob) for(s=[-1,1]) translate([H-DET_R, s*(LW/2-0.4), AZ]) sphere(r=BUMP, $fn=24);
    }
    // ช่องกลางรับลิ้นฐาน + รูแกน
    translate([H-AZ-0.5,-3-CLR/2,-1]) cube([10, 6+CLR, T+2]);
    translate([H,-(3+CLR+3.6),AZ]) rotate([-90,0,0]) cylinder(d=PIN_D+0.8, h=2*(3+CLR+3.6), $fn=48);
    // ลบส่วนเกินเลยแกน
    translate([H+AZ,-W,-1]) cube([10, 2*W, T+2]);
    // V2: ขอบช่องกลาง (ส่วนที่ไม่มีรูแกน) มน r 0.4
    for(s=[-1,1]) mirror([0,s<0?1:0,0]) for(z=[0,T]){
      edge_cut_x(H-AZ-1, H-PIN_D/2-0.6, 3+CLR/2, z, 1, z==0?1:-1, 0.4);
    }
    for(z=[0,T]) edge_cut_y(-3-CLR/2-0.1, 3+CLR/2+0.1, H-AZ-0.5, z, -1, z==0?1:-1, 0.4);
  }
}

// ---------------- ลายนูน (2D) ----------------
TX0 = BACK + CLR + 1.5;      // เริ่มพื้นที่ลาย
TXL = LF - 4.5;              // ความยาวพื้นที่ลาย (หลบช่องบานพับ)
module art2d(){
  if (DESIGN=="name"){
    // ขนาดอัตโนมัติไม่ให้ล้นช่อง · ตัวพิมพ์ใหญ่สูง ≥6 มม. ได้เมื่อ ≤5 ตัว/บรรทัด (รวม 10)
    n = max(len(NAME1), len(NAME2));
    sz = min(NAME2=="" ? 9.2 : 8.6, (TXL-2)/(0.86*max(n,1)));
    if (sz*0.7 < 6) echo(str("⚠ ตัวอักษรสูงแค่ ~", sz*0.7, " มม. (<6) — แบ่งเป็น 2 บรรทัด / ≤5 ตัวต่อบรรทัด"));
    if (NAME2=="") text(NAME1, size=sz, font=FONT, halign="center", valign="center");
    else {
      translate([0, 5.6]) text(NAME1, size=sz, font=FONT, halign="center", valign="center");
      translate([0,-5.6]) text(NAME2, size=sz, font=FONT, halign="center", valign="center");
    }
  } else if (DESIGN=="tree"){
    translate([0,-1]) {
      for(i=[0:2]) translate([0, 6-i*5.2]) polygon([[-4.5-i*2.6,-3.6],[4.5+i*2.6,-3.6],[0,5]]);
      translate([-1.8,-10.2]) square([3.6,2.8]);
      translate([0,11.6]) star(3.0,1.35);
    }
  } else if (DESIGN=="snow"){
    for(a=[0:60:300]) rotate(a){
      translate([0,-0.6]) square([11.5,1.2]);
      for(d=[5,8.5]) translate([d,0]) for(s=[-1,1]) rotate(s*50) translate([0,-0.55]) square([3.2,1.1]);
    }
    circle(r=2.2, $fn=6);
  } else if (DESIGN=="gift"){
    difference(){
      union(){ translate([-10,-11]) square([20,14]); translate([-11.5,4]) square([23,4.5]); }
      translate([-1.1,-12]) square([2.2,22]);          // ริบบิ้น (ร่องแบ่ง)
    }
    for(s=[-1,1]) translate([s*3.6,11.4]) rotate(s*20) difference(){ scale([1.45,1]) circle(r=2.9); scale([1.45,1]) circle(r=1.5); }
  } else { // logo
    resize([TXL-5,0], auto=true) text("FIXTORY", size=9, font=FONT, halign="center", valign="center");
  }
}
module star(ro,ri){ polygon([for(i=[0:9]) let(r=i%2?ri:ro, a=90+i*36) [r*cos(a), r*sin(a)]]); }

module relief(){
  // V2: จำกัดลายให้อยู่บนหน้าเรียบของแผ่นพิง (ไม่ล้นลงขอบมน)
  translate([0, 0, T-0.01]) linear_extrude(REL+0.01)
    intersection(){
      translate([TX0 + TXL/2, 0]) intersection(){ art2d(); square([TXL, LW-3], center=true); }
      offset(delta=-(RL+0.3)) leaf2d();
    }
}

// ---------------- ประกอบ ----------------
module leaf_rot(){ translate([H,0,AZ]) rotate([0,ANGLE,0]) translate([-H,0,-AZ]) children(); }

module phone(){
  // มือถือจำลอง 6.7" + เคส ( 78 × 163 × 11 ) วางพิงแผ่น
  d = 11;
  tx = H - LF*cos(OPEN) + AZ*sin(OPEN); tz = AZ + LF*sin(OPEN) + AZ*cos(OPEN);
  a = atan((TOWF - tx)/(tz - TOW_H));
  bx = TOWF + (TOW_H - T)*tan(a);
  len = PHONE=="portrait" ? 163 : 78; wid = PHONE=="portrait" ? 78 : 163;
  color([0.18,0.19,0.22]) translate([bx, -wid/2, T]) rotate([0,-a,0]) cube([d, wid, len]);
}

if (PART=="body"){ base(); leaf_rot() leaf_body(); }
else if (PART=="relief"){ leaf_rot() relief(); }
else {
  color("#D9343F") base();
  color("#E04650") leaf_rot() leaf_body();
  color("#FFF4E6") leaf_rot() relief();
  if (PHONE!="none") phone();
}

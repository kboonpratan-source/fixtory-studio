// =====================================================================
//  Fixtory_PhoneStandKey_V1  —  ที่วางมือถือพับได้ + พวงกุญแจ + ที่เปิดฝากระป๋อง
//  ออกแบบเองโดย Fixtory Studio (Fixtory Design) · 2026-11-13 · OpenSCAD 2021+
//
//  แนวคิด: แผ่นเดียวบางแบบ "ตั๋ว" แผ่นพิงมือถือ (leaf) วางอยู่ในช่องหน้าต่างกลางแผ่น
//  ระนาบเดียวกับฐาน → พิมพ์ทีเดียวจบ (print-in-place) ไม่ต้องใช้ support
//   - บานพับ: ลิ้นกลางของฐาน + แกน Ø3 (ติดกับฐาน) สอดเข้ารูของแผ่นพิง
//   - ล็อกมุม: ปุ่มกลมข้างแผ่นพิง × "คานสปริง" แนวตั้งในเสาสองข้าง มีหลุมรับที่ 68°
//   - ร่องรับมือถือ + ขอบหน้ามีสันกันลื่น · ไซซ์ S (มือถือ+เคส ≤12.5) / L (≤15)
//   - ด้านท้าย: ปลายลิ่มบาง + ช่องเกี่ยวห่วง = ที่เปิดฝากระป๋อง
//   - รูพวงกุญแจ/โซ่บอลที่มุมท้าย
//   - ลายนูนต่ำบนแผ่นพิง เปลี่ยนได้ด้วยตัวแปร DESIGN (แยกบอดี้สำหรับ AMS 2 สี)
//
//  ทิศพิมพ์: วางแบนตามไฟล์ (หน้าลายขึ้นบน) · แรงงัดกระป๋องเป็นแรงดัดในระนาบชั้นพิมพ์
//            (ไม่ดึงแยกชั้น) · แนะนำ 0.2 มม. · 3 walls · infill 20% gyroid
// =====================================================================

/* [ปรับต่อออเดอร์] */
DESIGN = "logo";      // "logo" | "name" | "tree" | "snow" | "gift"
NAME1  = "PLOY";      // ชื่อบรรทัด 1 (≤5 ตัว)  — ใช้เมื่อ DESIGN="name"
NAME2  = "";          // ชื่อบรรทัด 2 (≤5 ตัว)  — เว้นว่างได้ (รวมสูงสุด 10 ตัว)
FONT   = "Poppins:style=Bold";   // ชื่อภาษาไทย: ติดตั้ง Prompt Bold / Noto Sans Thai Bold แล้วเปลี่ยนตรงนี้
SIZE   = "S";         // "S" มือถือ+เคส ≤12.5 มม. · "L" ≤15 มม.

/* [ส่งออก] */
PART  = "all";        // "all" | "body" (สีหลัก) | "relief" (ลาย/ชื่อ สีที่ 2)
ANGLE = 0;            // 0 = สภาพพิมพ์/พับ · 67 = กางใช้งาน (ใช้แค่เรนเดอร์ภาพ)
PHONE = "none";       // "none" | "portrait" | "landscape" (มือถือจำลองเพื่อเรนเดอร์เท่านั้น)

/* [ขนาดหลัก มม.] */
T      = 4.4;    // ความหนาแผ่น
W      = 40;     // ความกว้าง
BACK   = 12.5;   // โซนท้าย (ที่เปิดกระป๋อง + รูพวงกุญแจ)
LF     = 44;     // ความยาวแผ่นพิง
LW     = 28.2;   // ความกว้างแผ่นพิง
CLR    = 0.4;    // ระยะเผื่อ print-in-place
GROOVE = SIZE=="L" ? 15.8 : 13.2;   // ระยะจากหน้าเสาถึงขอบหน้า
LIP_T  = 3.5;    // ความหนาขอบหน้า
LIP_H  = 4.8;    // ความสูงขอบหน้าเหนือแผ่น  → หนารวม 9.2 มม.
TOW_H  = T + LIP_H;
OPEN   = 66;     // มุมหลุมล็อก (องศาจากแนวราบ) — หยุดชน (hard stop) ที่ ~68° พอดี
DET_R  = 5;      // รัศมีปุ่มล็อกจากแกน
BUMP   = 1.0;    // รัศมีปุ่ม
BUMP_IN= 0.2;    // ปุ่มกินเข้าคานสปริง (เพิ่ม=ล็อกแน่นขึ้น)
REL    = 0.4;    // ความสูงลายนูน (2 ชั้น @0.2)
PIN_D  = 3.0;

H   = BACK + CLR + LF;         // ตำแหน่งแกนบานพับ (x)
AZ  = T/2;                     // ความสูงแกน
WH  = LW/2 + CLR;              // ครึ่งความกว้างหน้าต่าง
TOWF= H + 3;                   // หน้าเสา
L   = TOWF + GROOVE + LIP_T + 1.5;
R_OUT = 6;
$fn = 48;

// ---------------- ฐาน ----------------
module outline2d(){ offset(r=R_OUT) offset(delta=-R_OUT) square([L, W], center=false); }

module base(){
  difference(){
    union(){
      translate([0,-W/2,0]) linear_extrude(T) outline2d();
      // ขอบหน้า + สันกันลื่น
      translate([L-LIP_T-1.5,-W/2+1,0]) hull(){
        cube([LIP_T, W-2, TOW_H-1]);
        translate([0.6,0,TOW_H-0.8]) cube([LIP_T-1.2, W-2, 0.8]);
      }
      // เสาบานพับ 2 ข้าง (มีคานสปริงด้านใน)
      for(s=[-1,1]) mirror([0,s<0?1:0,0])
        translate([H-9.5, WH, 0]) cube([12.5, W/2-WH-1.2, TOW_H]);
    }
    // หน้าต่างแผ่นพิง (+ร่องหมุนรอบแกน)
    translate([BACK,-WH,-1]) cube([H-BACK, 2*WH, T+2]);
    translate([H,-WH,AZ]) rotate([-90,0,0]) cylinder(r=AZ+0.5, h=2*WH);   // r นี้กำหนดมุมหยุดชน ~68°
    // ช่องหมุนของปลายแผ่นพิงเหนือแผ่น (เสา)
    for(s=[-1,1]) mirror([0,s<0?1:0,0]){
      // ร่องหลังคานสปริง + ช่องว่างปลายคาน → คานยึดแค่ด้านท้าย
      translate([H-8.5, WH+1.2, -1]) cube([11.5, 0.8, TOW_H+2]);
      translate([H+1.0, WH-0.1, -1]) cube([2.6, 1.4, TOW_H+2]);
      // หลุมรับปุ่ม: ตำแหน่งพับ (ตื้น) และกาง OPEN°
      translate([H-DET_R, LW/2-0.4, AZ]) sphere(r=BUMP+0.3);
      translate([H-DET_R*cos(OPEN), LW/2-0.4, AZ+DET_R*sin(OPEN)]) sphere(r=BUMP+0.3);
    }
    // ที่เปิดฝากระป๋อง: ปลายลิ่มบางด้านท้าย + ช่องเกี่ยวห่วง
    translate([0,11,0]) rotate([90,0,0])
      linear_extrude(22) polygon([[-1,1.4],[0,1.4],[6,T],[6,T+1],[-1,T+1]]);
    translate([6.5,-8,-1]) hull(){ cube([0.1,16,T+2]); translate([3.6,1,0]) cube([0.1,14,T+2]); }
    // รูพวงกุญแจ / โซ่บอล
    translate([5, W/2-5.2, -1]) cylinder(d=4.6, h=T+2);
  }
  // ลิ้นกลาง + แกน (ติดฐาน)
  translate([H,-3+CLR/2,0]) cube([3, 6-CLR, T]);
  translate([H,-3+CLR/2,AZ]) rotate([-90,0,0]) cylinder(r=AZ, h=6-CLR);
  translate([H,-(3+CLR+3),AZ]) rotate([-90,0,0]) cylinder(d=PIN_D, h=2*(3+CLR+3));
}

// ---------------- แผ่นพิง ----------------
module leaf_body(nob=0){
  difference(){
    union(){
      translate([BACK+CLR,-LW/2,0]) cube([LF, LW, T]);
      // ปลายบานพับโค้งรอบแกน
      translate([H,-LW/2,AZ]) rotate([-90,0,0]) cylinder(r=AZ, h=LW);
      // ปุ่มล็อก 2 ข้าง
      if (!nob) for(s=[-1,1]) translate([H-DET_R, s*(LW/2-0.4), AZ]) sphere(r=BUMP);
    }
    // ช่องกลางรับลิ้นฐาน + รูแกน
    translate([H-AZ-0.5,-3-CLR/2,-1]) cube([10, 6+CLR, T+2]);
    translate([H,-(3+CLR+3.6),AZ]) rotate([-90,0,0]) cylinder(d=PIN_D+0.8, h=2*(3+CLR+3.6));
    // ลบส่วนเกินเลยแกน
    translate([H+AZ,-W,-1]) cube([10, 2*W, T+2]);
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
  translate([TX0 + TXL/2, 0, T-0.01]) linear_extrude(REL+0.01)
    intersection(){ art2d(); square([TXL, LW-3], center=true); }
}

// ---------------- ประกอบ ----------------
module leaf_rot(){ translate([H,0,AZ]) rotate([0,ANGLE,0]) translate([-H,0,-AZ]) children(); }

module phone(){
  // มือถือจำลอง 6.7" + เคส ( 78 × 163 × 11 ) วางพิงแผ่น
  // พิงบนมุมบนเสา (TOWF, TOW_H) และขอบบนแผ่นพิง → เอียง ~28° จากแนวตั้ง
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

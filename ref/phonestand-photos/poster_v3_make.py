from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
D = os.path.dirname(os.path.abspath(__file__))
F = os.path.expanduser('~/.fonts/')
def font(w, s): return ImageFont.truetype(F + 'Prompt-%s.ttf' % w, s, layout_engine=ImageFont.Layout.RAQM)
def img(n): return Image.open(os.path.join(D, n)).convert('RGB')

W, H = 1133, 1700
RED, DRED, CREAM, INK, GREY = (214, 24, 32), (150, 10, 18), (253, 246, 238), (40, 22, 18), (120, 95, 90)
im = Image.new('RGB', (W, H), CREAM)
d = ImageDraw.Draw(im)
def T(xy, s, f, fill, anchor='la', stroke=0, sf=None):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sf)
def rpaste(ph, box, r=22):
    x, y, w, h = box; ph = ImageOps.fit(ph, (w, h))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), r, fill=255)
    im.paste(ph, (int(x), int(y)), m)

# ── hero (real photo) ──
HH = 800
hero = ImageOps.fit(img('hero.jpg'), (W, HH), centering=(0.62, 0.6))
im.paste(hero, (0, 0))
g = Image.new('L', (1, HH))
for y in range(HH): g.putpixel((0, y), int(max(0, 215 - y * 0.62)))
im.paste(Image.new('RGB', (W, HH), (60, 0, 4)), (0, 0), g.resize((W, HH)))
d = ImageDraw.Draw(im)

T((W / 2, 46), 'fixtory.studio', font('SemiBold', 36), 'white', anchor='mm')
T((W / 2, 84), 'ผลิตและจำหน่ายโดย Fixtory Studio', font('Regular', 22), 'white', anchor='mm')
T((52, 120), 'Mini Phone Stand', font('Bold', 86), 'white', stroke=3, sf=DRED)
sub = 'ขาตั้งมือถือจิ๋ว พกง่าย'; fs = font('SemiBold', 44); bw = d.textlength(sub, font=fs)
d.rounded_rectangle((48, 236, 48 + bw + 48, 310), 37, fill=RED)
T((72, 273), sub, fs, 'white', anchor='lm')
T((54, 338), 'ขาตั้ง • พวงกุญแจ • ที่เปิดฝากระป๋อง ในชิ้นเดียว', font('Medium', 30), 'white', stroke=2, sf=(60, 0, 4))

# material pill (like Lever Switch Cover)
mt = 'วัสดุ PETG'; fm = font('SemiBold', 30); mw = d.textlength(mt, font=fm)
d.rounded_rectangle((52, 384, 52 + mw + 40, 440), 28, fill='white')
T((72, 412), mt, fm, RED, anchor='lm')
T((52 + mw + 56, 412), 'แข็งแรง ทนทาน ใช้ได้นาน', font('Medium', 26), 'white', anchor='lm', stroke=2, sf=(60, 0, 4))

# hinge callout (real close-up)
cr = 290; cx, cy = W - 52 - cr, 430
d.ellipse((cx - 8, cy - 8, cx + cr + 8, cy + cr + 8), fill='white')
m = Image.new('L', (cr, cr), 0); ImageDraw.Draw(m).ellipse((0, 0, cr, cr), fill=255)
im.paste(ImageOps.fit(img('circ.jpg'), (cr, cr)), (cx, cy), m)
k = cr / 300
d.ellipse((cx + 118 * k, cy + 112 * k, cx + 186 * k, cy + 180 * k), outline=(255, 214, 0), width=5)
lab = 'จุดหมุนบานพับ'; fl = font('SemiBold', 28); lw = d.textlength(lab, font=fl)
d.rounded_rectangle((cx + cr / 2 - lw / 2 - 18, cy + cr - 14, cx + cr / 2 + lw / 2 + 18, cy + cr + 36), 22, fill=RED)
T((cx + cr / 2, cy + cr + 11), lab, fl, 'white', anchor='mm')

# ── feature chips ──
y0 = 818
feats = [('พับเก็บได้', 'Foldable'), ('มีพวงกุญแจ', 'Keychain'), ('เปิดฝากระป๋องได้', 'Can opener'), ('ใส่ชื่อได้ ฟรี!', 'Free name')]
cw = (W - 104 - 3 * 14) / 4
for i, (th, en) in enumerate(feats):
    x = 52 + i * (cw + 14)
    d.rounded_rectangle((x, y0, x + cw, y0 + 92), 20, fill='white', outline=(235, 210, 205), width=2)
    T((x + cw / 2, y0 + 36), th, font('SemiBold', 26), RED, anchor='mm')
    T((x + cw / 2, y0 + 70), en, font('Regular', 20), GREY, anchor='mm')

# ── 3 steps (real photos) ──
py = 935
T((52, py), 'ใช้งานง่าย 3 ขั้นตอน', font('Bold', 38), RED)
steps = [('s1.jpg', 'พับเก็บ', 'ห้อยเป็นพวงกุญแจ'), ('s2.jpg', 'ยกแผ่นพิงขึ้น', 'จนล็อก'), ('s3.jpg', 'วางมือถือ', 'ใส่เคสได้')]
sw, sh = 320, 200; gap = (W - 104 - 3 * sw) / 2
for i, (fn, t1, t2) in enumerate(steps):
    x = 52 + i * (sw + gap); y = py + 60
    rpaste(img(fn), (x, y, sw, sh))
    d.ellipse((x + 12, y + 12, x + 60, y + 60), fill=RED); T((x + 36, y + 36), str(i + 1), font('Bold', 30), 'white', anchor='mm')
    T((x + sw / 2, y + sh + 30), t1, font('SemiBold', 28), INK, anchor='mm')
    T((x + sw / 2, y + sh + 64), t2, font('Regular', 22), GREY, anchor='mm')
    if i < 2: T((x + sw + gap / 2, y + sh / 2), '›', font('Bold', 56), RED, anchor='mm')

# ── price tiers (approved by Pricing: ฿199 / 2–3 ฿179 / 4–9 ฿169 / 10+ chat) ──
py = 1300
tiers = [('1 ชิ้น', '199', 'บาท'), ('2–3 ชิ้น', '179', 'บาท / ชิ้น'), ('4–9 ชิ้น', '169', 'บาท / ชิ้น')]
tw = (W - 104 - 2 * 16) / 3
for i, (q, p, u) in enumerate(tiers):
    x = 52 + i * (tw + 16)
    d.rounded_rectangle((x, py, x + tw, py + 130), 24, fill='white', outline=RED, width=3)
    T((x + tw / 2, py + 30), q, font('SemiBold', 28), INK, anchor='mm')
    fp = font('Bold', 62); pw = d.textlength(p, font=fp); fu = font('SemiBold', 24); uw = d.textlength(u, font=fu)
    sx = x + tw / 2 - (pw + 10 + uw) / 2
    T((sx, py + 88), p, fp, RED, anchor='lm'); T((sx + pw + 10, py + 98), u, fu, RED, anchor='lm')
T((W / 2, py + 160), 'หากสนใจ 10 ชิ้นขึ้นไป โปรดติดต่อร้าน', font('SemiBold', 28), DRED, anchor='mm')

# ── contact: QR + phone (same as other posters) ──
cy0 = 1490; qs = 120
d.rounded_rectangle((52, cy0, W - 52, cy0 + 150), 26, fill='white', outline=(235, 210, 205), width=2)
for i, (q, n1, n2) in enumerate([('qr-tiktok.png', 'TikTok', '@fixtory.studio'), ('qr-facebook.png', 'Facebook', 'fixtory.studio')]):
    x = 76 + i * 340
    im.paste(img(q).resize((qs, qs)), (x, cy0 + 15))
    T((x + qs + 16, cy0 + 58), n1, font('SemiBold', 28), INK, anchor='lm')
    T((x + qs + 16, cy0 + 94), n2, font('Regular', 22), GREY, anchor='lm')
d.line((750, cy0 + 25, 750, cy0 + 125), fill=(235, 210, 205), width=2)
T((780, cy0 + 58), 'โทร / สั่งซื้อ', font('Regular', 22), GREY, anchor='lm')
T((780, cy0 + 96), '081-336-8232', font('Bold', 34), RED, anchor='lm')

# ── footer credit (licensed design, same wording as Sip Buddy / Bloom Box) ──
T((W / 2, H - 28), 'ผลิตและจำหน่ายภายใต้ commercial license จากผู้ออกแบบ', font('Regular', 22), GREY, anchor='mm')

im.save(os.path.join(D, 'mini_phone_stand_poster_v3.jpg'), quality=92)
print('ok')

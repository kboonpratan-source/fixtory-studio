from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
D = os.path.dirname(os.path.abspath(__file__))
F = os.path.expanduser('~/.fonts/')
L = ImageFont.Layout.RAQM
def font(w, s): return ImageFont.truetype(F + 'Prompt-%s.ttf' % w, s, layout_engine=L)

W, H = 1024, 1536
RED, DRED, CREAM, INK = (214, 24, 32), (150, 10, 18), (253, 246, 238), (40, 22, 18)
im = Image.new('RGB', (W, H), CREAM)
d = ImageDraw.Draw(im)

# hero photo: top area
hero = Image.open(os.path.join(D, 'hero.jpg'))
hero = ImageOps.fit(hero, (W, 900), centering=(0.5, 0.55))
im.paste(hero, (0, 0))
# dark gradient top for title legibility
grad = Image.new('L', (1, 900))
for y in range(900): grad.putpixel((0, y), int(max(0, 210 - y * 0.55)))
shade = Image.new('RGB', (W, 900), (60, 0, 4)); im.paste(shade, (0, 0), grad.resize((W, 900)))
d = ImageDraw.Draw(im)

def text(xy, s, f, fill, anchor='la', stroke=0, sf=None):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sf)

# brand
text((48, 40), 'Fixtory Studio', font('SemiBold', 34), 'white')
# title
text((48, 100), 'Mini Phone Stand', font('Bold', 84), 'white', stroke=3, sf=DRED)
# subtitle pill
sub = 'ขาตั้งมือถือจิ๋ว พกง่าย'
fs = font('SemiBold', 44); bw = d.textlength(sub, font=fs)
d.rounded_rectangle((44, 215, 44 + bw + 48, 290), 38, fill=RED)
text((68, 252), sub, fs, 'white', anchor='lm')
text((50, 318), 'ขาตั้ง • พวงกุญแจ • ที่เปิดฝากระป๋อง ในชิ้นเดียว', font('Medium', 30), 'white', stroke=2, sf=(60, 0, 4))

# circle callout: real hinge close-up
cr = 300; cx, cy = W - 48 - cr, 560
circ = ImageOps.fit(Image.open(os.path.join(D, 'circ.jpg')), (cr, cr))
mask = Image.new('L', (cr, cr), 0); ImageDraw.Draw(mask).ellipse((0, 0, cr, cr), fill=255)
d.ellipse((cx - 8, cy - 8, cx + cr + 8, cy + cr + 8), fill='white')
im.paste(circ, (cx, cy), mask)
lab = 'จุดหมุนบานพับ'
fl = font('SemiBold', 28); lw = d.textlength(lab, font=fl)
d.rounded_rectangle((cx + cr / 2 - lw / 2 - 18, cy + cr - 14, cx + cr / 2 + lw / 2 + 18, cy + cr + 36), 22, fill=RED)
text((cx + cr / 2, cy + cr + 11), lab, fl, 'white', anchor='mm')
# arrow pointing to the round hinge disc (crop shows it lower-middle)
d.ellipse((cx + 118, cy + 112, cx + 186, cy + 180), outline=(255, 214, 0), width=5)

# feature chips (bottom band of hero)
feats = [('พับเก็บได้', 'Foldable'), ('มีพวงกุญแจ', 'Keychain'), ('เปิดฝากระป๋องได้', 'Can opener'), ('ใส่ชื่อได้ ฟรี!', 'Free name')]
y0 = 912; cw = (W - 48 * 2 - 3 * 14) / 4
for i, (th, en) in enumerate(feats):
    x = 48 + i * (cw + 14)
    d.rounded_rectangle((x, y0, x + cw, y0 + 96), 20, fill='white', outline=(235, 210, 205), width=2)
    text((x + cw / 2, y0 + 38), th, font('SemiBold', 26 if len(th) < 13 else 23), RED, anchor='mm')
    text((x + cw / 2, y0 + 72), en, font('Regular', 20), (120, 90, 85), anchor='mm')

# steps panel with real photos
py = 1030
text((48, py), 'ใช้งานง่าย 3 ขั้นตอน', font('Bold', 40), RED)
steps = [('s1.jpg', '1', 'พับเก็บ', 'ห้อยเป็นพวงกุญแจ'), ('s2.jpg', '2', 'ยกแผ่นพิงขึ้น', 'จนล็อก'), ('s3.jpg', '3', 'วางมือถือ', 'ใส่เคสได้')]
sw = 290; gap = (W - 96 - 3 * sw) / 2
for i, (fn, n, t1, t2) in enumerate(steps):
    x = 48 + i * (sw + gap); y = py + 66
    ph = ImageOps.fit(Image.open(os.path.join(D, fn)), (sw, 230))
    m = Image.new('L', (sw, 230), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sw, 230), 22, fill=255)
    im.paste(ph, (int(x), int(y)), m)
    d.ellipse((x + 12, y + 12, x + 64, y + 64), fill=RED)
    text((x + 38, y + 38), n, font('Bold', 32), 'white', anchor='mm')
    text((x + sw / 2, y + 266), t1, font('SemiBold', 30), INK, anchor='mm')
    text((x + sw / 2, y + 304), t2, font('Regular', 24), (110, 90, 85), anchor='mm')
    if i < 2:
        ax = x + sw + gap / 2; text((ax, y + 115), '›', font('Bold', 60), RED, anchor='mm')

# bottom band
d.rectangle((0, H - 104, W, H), fill=RED)
text((48, H - 52), 'ขนาดเล็ก พกติดตัวได้ทุกที่', font('SemiBold', 36), 'white', anchor='lm')
text((W - 48, H - 52), 'fixtory.studio', font('Medium', 30), 'white', anchor='rm')

im.save(os.path.join(D, 'mini_phone_stand_poster_v2.png'))
print('ok')

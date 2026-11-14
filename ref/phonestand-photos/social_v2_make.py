"""Mini Phone Stand social set v2 (Marketing) - real photos, with the shop's standard poster elements
(same as poster_v3: price tiers, 10+ line, TikTok/Facebook QR, phone, 'ผลิตและจำหน่ายโดย Fixtory Studio',
PETG pill, commercial-licence credit). Hero = 08_clean.jpg (real phone, scuffs removed).
Outputs: mini_phone_stand_1x1.png, mini_phone_stand_9x16.png, mini_phone_stand_2x3_alt.png
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import os

D = os.path.dirname(os.path.abspath(__file__))
F = os.path.expanduser('~/.fonts/')
RED, DRED, CREAM, INK, MUTED = (206, 28, 36), (140, 12, 20), (253, 246, 238), (40, 22, 18), (120, 92, 86)
LINE = (235, 210, 205)
GOLD = (255, 205, 40)

PRICES = [('1 ชิ้น', '199', 'บาท'), ('2–3 ชิ้น', '179', 'บาท / ชิ้น'), ('4–9 ชิ้น', '169', 'บาท / ชิ้น')]
FEATS = [('พับเก็บได้', 'Foldable'), ('มีพวงกุญแจ', 'Keychain'),
         ('เปิดฝากระป๋องได้', 'Can opener'), ('ใส่ชื่อได้ ฟรี!', 'Free name')]
HERO = ('08_clean.jpg', (0, 300, 1666, 1900))
HINGE = ('13.jpg', (560, 840, 1140, 1420)); HINGE_DOT = (438 / 580, 312 / 580)
STEPS = [('crop_s1.jpg', None, 'พับเก็บ', 'ห้อยเป็นพวงกุญแจ'),
         ('crop_s2.jpg', None, 'ยกแผ่นพิงขึ้น', 'จนล็อก'),
         ('08_clean.jpg', (0, 560, 1500, 1560), 'วางมือถือ', 'ใส่เคสได้')]


def font(w, s):
    return ImageFont.truetype(F + 'Prompt-%s.ttf' % w, s, layout_engine=ImageFont.Layout.RAQM)


def photo(name, box=None):
    im = Image.open(os.path.join(D, name)).convert('RGB')
    if box:
        im = im.crop(box)
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    im = ImageEnhance.Brightness(im).enhance(1.04)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return ImageEnhance.Color(im).enhance(1.04)


def fit(im, size, centering=(0.5, 0.5)):
    return ImageOps.fit(im, size, Image.LANCZOS, centering=centering).filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=3))


class Poster:
    def __init__(self, w, h):
        self.W, self.H = w, h
        self.im = Image.new('RGB', (w, h), CREAM)
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, f, fill, anchor='la'):
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor)

    def fitfont(self, s, w, size, maxw):
        while self.d.textlength(s, font=font(w, size)) > maxw:
            size -= 1
        return font(w, size)

    def header(self, y0, y1, title=84, center=False, pad=52):
        W, d = self.W, self.d
        d.rectangle((0, y0, W, y1), fill=RED)
        d.rectangle((0, y1 - 8, W, y1), fill=DRED)
        h = y1 - y0 - 8
        x = W / 2 if center else pad
        a = 'm' if center else 'l'
        s = title / 84
        self.text((x, y0 + h * 0.09), 'fixtory.studio', font('SemiBold', int(30 * s)), 'white', a + 'm')
        self.text((x, y0 + h * 0.18), 'ผลิตและจำหน่ายโดย Fixtory Studio', font('Regular', int(20 * s)), (255, 220, 215), a + 'm')
        self.text((x, y0 + h * 0.36), 'Mini Phone Stand', font('Bold', title), 'white', a + 'm')
        # subtitle pill + PETG pill on one row
        fs, fm = font('SemiBold', int(38 * s)), font('SemiBold', int(28 * s))
        sub, mat = 'ขาตั้งมือถือจิ๋ว พกง่าย', 'วัสดุ PETG'
        sw, mw = d.textlength(sub, font=fs), d.textlength(mat, font=fm)
        ph, gap = 34 * s, 16
        total = sw + 48 + gap + mw + 40
        bx = W / 2 - total / 2 if center else pad - 4
        yc = y0 + h * 0.60
        d.rounded_rectangle((bx, yc - ph, bx + sw + 48, yc + ph), ph, fill='white')
        self.text((bx + 24, yc), sub, fs, RED, 'lm')
        mx = bx + sw + 48 + gap
        d.rounded_rectangle((mx, yc - ph * 0.8, mx + mw + 40, yc + ph * 0.8), ph, fill=DRED, outline='white', width=2)
        self.text((mx + 20, yc), mat, fm, 'white', 'lm')
        self.text((x, y0 + h * 0.85), 'ขาตั้ง • พวงกุญแจ • ที่เปิดฝากระป๋อง ในชิ้นเดียว',
                  font('Medium', int(27 * s)), 'white', a + 'm')

    def hero(self, y0, h, centering=(0.6, 0.45)):
        name, box = HERO
        self.im.paste(fit(photo(name, box), (self.W, h), centering), (0, y0))

    def hinge(self, cx, cy, r, ls=22):
        c = fit(photo(*HINGE), (2 * r, 2 * r))
        m = Image.new('L', c.size, 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        self.d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill='white')
        self.im.paste(c, (cx - r, cy - r), m)
        dx, dy = cx - r + HINGE_DOT[0] * 2 * r, cy - r + HINGE_DOT[1] * 2 * r
        rr = r * 0.2
        self.d.ellipse((dx - rr, dy - rr, dx + rr, dy + rr), outline=GOLD, width=max(3, r // 40))
        lab = 'จุดหมุนบานพับ'; fl = font('SemiBold', ls); lw = self.d.textlength(lab, font=fl)
        ly = cy + r + 2
        self.d.rounded_rectangle((cx - lw / 2 - 16, ly - ls * 0.85, cx + lw / 2 + 16, ly + ls * 0.85), ls,
                                 fill=RED, outline='white', width=3)
        self.text((cx, ly), lab, fl, 'white', 'mm')

    def chips(self, y0, h=84, pad=52, gap=12, th=24, en=18):
        cw = (self.W - 2 * pad - 3 * gap) / 4
        for i, (t, e) in enumerate(FEATS):
            x = pad + i * (cw + gap)
            self.d.rounded_rectangle((x, y0, x + cw, y0 + h), 18, fill='white', outline=LINE, width=2)
            self.text((x + cw / 2, y0 + h * 0.40), t, self.fitfont(t, 'SemiBold', th, cw - 16), RED, 'mm')
            self.text((x + cw / 2, y0 + h * 0.76), e, font('Regular', en), MUTED, 'mm')

    def steps(self, y0, ph=190, pad=52, head=34, t1=26, t2=21):
        W, d = self.W, self.d
        self.text((pad, y0), 'ใช้งานง่าย 3 ขั้นตอน', font('Bold', head), RED)
        sw = int((W - 2 * pad - 2 * 40) / 3); gap = (W - 2 * pad - 3 * sw) / 2
        y = y0 + int(head * 1.5)
        for i, (fn, box, a, b) in enumerate(STEPS):
            x = int(pad + i * (sw + gap))
            ph_im = fit(photo(fn, box), (sw, ph))
            m = Image.new('L', (sw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, ph - 1), 20, fill=255)
            self.im.paste(ph_im, (x, y), m)
            d.ellipse((x + 10, y + 10, x + 56, y + 56), fill=RED, outline='white', width=3)
            self.text((x + 33, y + 33), str(i + 1), font('Bold', 28), 'white', 'mm')
            self.text((x + sw / 2, y + ph + t1 * 1.1), a, font('SemiBold', t1), INK, 'mm')
            self.text((x + sw / 2, y + ph + t1 * 1.1 + t2 * 1.35), b, font('Regular', t2), MUTED, 'mm')
            if i < 2:
                self.text((x + sw + gap / 2, y + ph / 2), '›', font('Bold', 52), RED, 'mm')

    def prices(self, y0, h=120, pad=52, gap=14, big=58):
        W, d = self.W, self.d
        tw = (W - 2 * pad - 2 * gap) / 3
        for i, (q, p, u) in enumerate(PRICES):
            x = pad + i * (tw + gap)
            d.rounded_rectangle((x, y0, x + tw, y0 + h), 22, fill='white', outline=RED, width=3)
            self.text((x + tw / 2, y0 + h * 0.24), q, font('SemiBold', int(big * 0.45)), INK, 'mm')
            fp, fu = font('Bold', big), font('SemiBold', int(big * 0.38))
            pw, uw = d.textlength(p, font=fp), d.textlength(u, font=fu)
            sx = x + tw / 2 - (pw + 8 + uw) / 2
            self.text((sx, y0 + h * 0.66), p, fp, RED, 'lm')
            self.text((sx + pw + 8, y0 + h * 0.66 + big * 0.16), u, fu, RED, 'lm')
        self.text((W / 2, y0 + h + 30), 'หากสนใจ 10 ชิ้นขึ้นไป โปรดติดต่อร้าน', font('SemiBold', 26), DRED, 'mm')

    def contact(self, y0, h=140, pad=52, qs=110):
        W, d = self.W, self.d
        d.rounded_rectangle((pad, y0, W - pad, y0 + h), 24, fill='white', outline=LINE, width=2)
        col = (W - 2 * pad) / 3
        for i, (q, n1, n2) in enumerate([('qr-tiktok.png', 'TikTok', '@fixtory.studio'),
                                         ('qr-facebook.png', 'Facebook', 'fixtory.studio')]):
            x = int(pad + 18 + i * col)
            qr = Image.open(os.path.join(D, q)).convert('RGB').resize((qs, qs), Image.NEAREST)
            self.im.paste(qr, (x, int(y0 + (h - qs) / 2)))
            self.text((x + qs + 12, y0 + h * 0.40), n1, font('SemiBold', 25), INK, 'lm')
            self.text((x + qs + 12, y0 + h * 0.66), n2, self.fitfont(n2, 'Regular', 19, col - qs - 40), MUTED, 'lm')
        x = pad + 2 * col + 14
        d.line((x - 14, y0 + 22, x - 14, y0 + h - 22), fill=LINE, width=2)
        self.text((x + 6, y0 + h * 0.36), 'โทร / สั่งซื้อ', font('Regular', 21), MUTED, 'lm')
        self.text((x + 6, y0 + h * 0.66), '081-336-8232', self.fitfont('081-336-8232', 'Bold', 32, col - 30), RED, 'lm')

    def credit(self, y):
        self.text((self.W / 2, y), 'ผลิตและจำหน่ายภายใต้ commercial license จากผู้ออกแบบ', font('Regular', 20), MUTED, 'mm')

    def save(self, name):
        self.im.save(os.path.join(D, name), optimize=True)
        print('saved', name, self.im.size)


# 1) Square 1:1 (1080) - feed: header, hero, prices, contact, credit
s = Poster(1080, 1080)
s.header(0, 290, title=76)
s.hero(290, 380, centering=(0.6, 0.66))
s.hinge(915, 465, 92, 19)
s.prices(688, h=110, big=54)
s.contact(850, h=130, qs=100)
s.credit(1050)
s.save('mini_phone_stand_1x1.png')

# 2) Story 9:16 (1080x1920) - top ~180 px left for the app bar
t = Poster(1080, 1920)
t.d.rectangle((0, 0, 1080, 190), fill=RED)
t.header(180, 520, title=88, center=True)
t.hero(520, 470, centering=(0.6, 0.61))
t.hinge(905, 735, 110, 21)
t.chips(1006)
t.steps(1110, ph=170)
t.prices(1442, h=118, big=56)
t.contact(1612, h=140)
t.credit(1780)
t.d.rectangle((0, 1820, 1080, 1920), fill=RED)
t.save('mini_phone_stand_9x16.png')

# 3) Portrait 2:3 (1024x1536) - title in a solid band, not over the phone
p = Poster(1024, 1536)
p.header(0, 320, title=80)
p.hero(320, 440, centering=(0.6, 0.61))
p.hinge(855, 525, 100, 20)
p.chips(774)
p.steps(876, ph=170)
p.prices(1196, h=112, big=54)
p.contact(1368, h=130, qs=100)
p.credit(1516)
p.save('mini_phone_stand_2x3_alt.png')

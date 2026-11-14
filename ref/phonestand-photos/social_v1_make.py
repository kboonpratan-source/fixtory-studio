"""Mini Phone Stand social set v1 (Marketing) — real photos only (no AI renders).
Outputs: mini_phone_stand_2x3_alt.png (2:3), _1x1.png (IG/FB feed), _9x16.png (story).
Fonts: Prompt (Thai+Latin) in ~/.fonts, Pillow with RAQM.
Rules: no price, no slogan, no (R) until AU confirms; draft until the mgm86 licence is bought.
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import os

D = os.path.dirname(os.path.abspath(__file__))
F = os.path.expanduser('~/.fonts/')
RED, DRED, CREAM, INK, MUTED = (206, 28, 36), (140, 12, 20), (253, 246, 238), (40, 22, 18), (120, 92, 86)
GOLD = (255, 205, 40)


def font(w, s):
    return ImageFont.truetype(F + 'Prompt-%s.ttf' % w, s, layout_engine=ImageFont.Layout.RAQM)


def photo(name, box=None):
    """Open a real photo, crop, and tidy it up: levels, a touch of colour, sharpen."""
    im = Image.open(os.path.join(D, name)).convert('RGB')
    if box:
        im = im.crop(box)
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    im = ImageEnhance.Brightness(im).enhance(1.04)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.04)
    return im


def sharpen(im):
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=3))


def fit(im, size, centering=(0.5, 0.5)):
    return sharpen(ImageOps.fit(im, size, Image.LANCZOS, centering=centering))


def rounded(canvas, im, xy, r):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255)
    canvas.paste(im, xy, m)


# Source crops (full-res originals; bottom ~12% of each photo holds the camera watermark, kept out)
HERO = ('08_newphone.jpg', (0, 300, 1666, 1900))          # phone leaning on the stand, Santa face visible
HINGE = ('13.jpg', (560, 840, 1140, 1420))       # flat round pivot disc set in the side wall + FIXTORY
HINGE_DOT = (438 / 580, 312 / 580)                # disc centre inside that crop
STEPS = [('16.jpg', (230, 380, 1530, 1480), 'พับเก็บ', 'ห้อยเป็นพวงกุญแจ'),
         ('crop_s2.jpg', None, 'ยกแผ่นพิงขึ้น', 'จนล็อก'),
         ('08_newphone.jpg', (0, 560, 1500, 1560), 'วางมือถือ', 'ใส่เคสได้')]
FEATS = [('พับเก็บได้', 'Foldable'), ('มีพวงกุญแจ', 'Keychain'),
         ('เปิดฝากระป๋องได้', 'Can opener'), ('ใส่ชื่อได้ ฟรี!', 'Free name')]


class Poster:
    def __init__(self, w, h):
        self.W, self.H = w, h
        self.im = Image.new('RGB', (w, h), CREAM)
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, f, fill, anchor='la', stroke=0, sf=None):
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sf)

    def header(self, y0, y1, title=84, sub=42, line=28, pad=56, center=False):
        """Solid red band, so the title never sits on top of the phone in the photo."""
        W = self.W
        self.d.rectangle((0, y0, W, y1), fill=RED)
        # thin darker strip at the bottom edge of the band
        self.d.rectangle((0, y1 - 8, W, y1), fill=DRED)
        x = W / 2 if center else pad
        a = 'm' if center else 'l'
        gap = (y1 - y0 - 8)
        yb = y0 + gap * 0.17
        self.text((x, yb), 'Fixtory Studio', font('SemiBold', int(title * 0.38)), (255, 225, 220), anchor=a + 'm')
        yt = y0 + gap * 0.42
        self.text((x, yt), 'Mini Phone Stand', font('Bold', title), 'white', anchor=a + 'm')
        fs = font('SemiBold', sub)
        s = 'ขาตั้งมือถือจิ๋ว พกง่าย'
        bw = self.d.textlength(s, font=fs)
        ys = y0 + gap * 0.70
        bx = W / 2 - bw / 2 - 26 if center else pad - 4
        self.d.rounded_rectangle((bx, ys - sub * 0.8, bx + bw + 52, ys + sub * 0.8), sub * 0.8, fill='white')
        self.text((bx + 26, ys), s, fs, RED, anchor='lm')
        self.text((x, y0 + gap * 0.91), 'ขาตั้ง • พวงกุญแจ • ที่เปิดฝากระป๋อง ในชิ้นเดียว',
                  font('Medium', line), 'white', anchor=a + 'm')

    def hero(self, y0, h, centering=(0.55, 0.5)):
        name, box = HERO
        self.im.paste(fit(photo(name, box), (self.W, h), centering), (0, y0))

    def hinge(self, cx, cy, r, label_size=26):
        """Circle close-up of the real pivot disc (flush, not a protruding axle)."""
        name, box = HINGE
        c = fit(photo(name, box), (2 * r, 2 * r))
        m = Image.new('L', c.size, 0)
        ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        self.d.ellipse((cx - r - 7, cy - r - 7, cx + r + 7, cy + r + 7), fill='white')
        self.im.paste(c, (cx - r, cy - r), m)
        dx, dy = cx - r + HINGE_DOT[0] * 2 * r, cy - r + HINGE_DOT[1] * 2 * r
        rr = r * 0.2
        self.d.ellipse((dx - rr, dy - rr, dx + rr, dy + rr), outline=GOLD, width=max(3, r // 40))
        lab = 'จุดหมุนบานพับ'
        fl = font('SemiBold', label_size)
        lw = self.d.textlength(lab, font=fl)
        ly = cy + r + 4
        self.d.rounded_rectangle((cx - lw / 2 - 18, ly - label_size * 0.85, cx + lw / 2 + 18, ly + label_size * 0.85),
                                 label_size, fill=RED, outline='white', width=3)
        self.text((cx, ly), lab, fl, 'white', anchor='mm')

    def chips(self, y0, pad=48, h=96, gap=14, cols=4, th=26, en=20):
        W = self.W
        rows = (len(FEATS) + cols - 1) // cols
        cw = (W - pad * 2 - (cols - 1) * gap) / cols
        for i, (t, e) in enumerate(FEATS):
            x = pad + (i % cols) * (cw + gap)
            y = y0 + (i // cols) * (h + gap)
            self.d.rounded_rectangle((x, y, x + cw, y + h), 20, fill='white', outline=(235, 210, 205), width=2)
            size = th
            while self.d.textlength(t, font=font('SemiBold', size)) > cw - 20:
                size -= 1
            self.text((x + cw / 2, y + h * 0.40), t, font('SemiBold', size), RED, anchor='mm')
            self.text((x + cw / 2, y + h * 0.75), e, font('Regular', en), MUTED, anchor='mm')
        return y0 + rows * h + (rows - 1) * gap

    def steps(self, y0, pad=48, ph=230, head=40, t1=30, t2=24):
        W = self.W
        self.text((pad, y0), 'ใช้งานง่าย 3 ขั้นตอน', font('Bold', head), RED)
        sw = int((W - 2 * pad - 2 * 44) / 3)
        gap = (W - 2 * pad - 3 * sw) / 2
        y = y0 + int(head * 1.6)
        for i, (fn, box, a, b) in enumerate(STEPS):
            x = int(pad + i * (sw + gap))
            rounded(self.im, fit(photo(fn, box), (sw, ph)), (x, y), 22)
            self.d.ellipse((x + 12, y + 12, x + 64, y + 64), fill=RED, outline='white', width=3)
            self.text((x + 38, y + 38), str(i + 1), font('Bold', 32), 'white', anchor='mm')
            self.text((x + sw / 2, y + ph + t1 * 1.2), a, font('SemiBold', t1), INK, anchor='mm')
            self.text((x + sw / 2, y + ph + t1 * 1.2 + t2 * 1.4), b, font('Regular', t2), MUTED, anchor='mm')
            if i < 2:
                self.text((x + sw + gap / 2, y + ph / 2), '›', font('Bold', 60), RED, anchor='mm')
        return y + ph + t1 * 1.2 + t2 * 2

    def footer(self, h=104, size=36, pad=48):
        W, H = self.W, self.H
        self.d.rectangle((0, H - h, W, H), fill=RED)
        self.text((pad, H - h / 2), 'ขนาดเล็ก พกติดตัวได้ทุกที่', font('SemiBold', size), 'white', anchor='lm')
        self.text((W - pad, H - h / 2), 'fixtory.studio', font('Medium', int(size * 0.85)), 'white', anchor='rm')

    def save(self, name):
        self.im.save(os.path.join(D, name), optimize=True)
        print('saved', name, self.im.size)


# 1) Portrait 2:3 (1024x1536) — alternative layout: title in a solid band, not over the phone
p = Poster(1024, 1536)
p.header(0, 330)
p.hero(330, 570, centering=(0.5, 0.5))
p.hinge(850, 520, 125, 24)
p.chips(918)
p.steps(1036)
p.footer()
p.save('mini_phone_stand_2x3_alt.png')

# 2) Square 1:1 (1080x1080) — IG/FB feed
s = Poster(1080, 1080)
s.header(0, 300, title=80, sub=38, line=26)
s.hero(300, 560, centering=(0.5, 0.5))
s.hinge(905, 500, 118, 22)
s.chips(876, h=90, th=25, en=19)
s.footer(h=96, size=32)
s.save('mini_phone_stand_1x1.png')

# 3) Story 9:16 (1080x1920) — keep text out of the top ~220 px / bottom ~260 px app overlays
t = Poster(1080, 1920)
t.d.rectangle((0, 0, 1080, 220), fill=RED)
t.header(200, 560, title=92, sub=44, line=30, center=True)
t.hero(560, 640, centering=(0.5, 0.5))
t.hinge(890, 790, 130, 24)
t.chips(1226, cols=2, h=88, th=30, en=20)
t.steps(1428, ph=190, head=36, t1=28, t2=22)
t.footer(h=150, size=34)
t.save('mini_phone_stand_9x16.png')

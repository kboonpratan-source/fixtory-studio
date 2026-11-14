"""Retouch scuffs/smudges on the demo phone's metal side in 08.jpg (the phone, not the product).
Clone-stamp: each spot is covered with a patch taken further up the phone's long axis, where the
side is clean and the shading across the band is the same. Patches stay inside the phone band.
Output: 08_clean.jpg (used by social_v1_make.py).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math, os

D = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(D, '08.jpg')).convert('RGB')
W, H = src.size

# phone side band, full-res coords: inner screen edge and outer edge (axis dx/dy ~ -0.68)
def line_x(p, q, y): return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
L0, L1 = (540, 950), (252, 1380)       # just inside the dark screen edge
R0, R1 = (648, 995), (376, 1395)       # just inside the outer edge
ys = (700, 1460)
band = Image.new('L', (W, H), 0)
ImageDraw.Draw(band).polygon([(line_x(L0, L1, ys[0]), ys[0]), (line_x(R0, R1, ys[0]), ys[0]),
                              (line_x(R0, R1, ys[1]), ys[1]), (line_x(L0, L1, ys[1]), ys[1])], fill=255)
band = band.filter(ImageFilter.MinFilter(5))

ux, uy = 0.68 / math.hypot(0.68, 1), -1 / math.hypot(0.68, 1)   # unit vector up the axis
SPOTS = [  # (cx, cy, radius, shift up the axis)
    (512, 1103, 18, 52),    # small scratch
    (430, 1195, 32, 150),   # smudge
    (378, 1246, 24, 70),    # smudge
    (326, 1388, 44, 118),   # big scuff near the bottom
]  # top-down order: later patches may sample areas already cleaned
out = src.copy()
for cx, cy, r, d in SPOTS:
    sx, sy = round(ux * d), round(uy * d)
    shifted = ImageChops.offset(out, -sx, -sy)          # pixel at (x,y) now = out(x+sx, y+sy)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    m = ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(5)), band)
    out = Image.composite(shifted, out, m)
out.save(os.path.join(D, '08_clean.jpg'), quality=95)
print('saved 08_clean.jpg')

"""Swap the demo phone in 08_clean.jpg for the clean phone from the AI poster (phone only; the product stays the real photo)."""
import numpy as np, cv2, sys
from PIL import Image
AI, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ai = cv2.cvtColor(cv2.imread(AI), cv2.COLOR_BGR2RGB)
H, W = ai.shape[:2]

# --- phone mask in the AI image (edges measured on the image) ---
xl = lambda y: 832 - 0.528 * y          # left outer edge
xr = lambda y: 1007 - 0.508 * y         # right outer edge (frame)
yt = lambda x: 113 - 0.169 * (x - 771)  # top edge
yb = lambda x: 930 + 0.377 * (x - 467)  # bottom edge
def inter(fx, fy):
    y = 500.0
    for _ in range(60): x = fx(y); y = fy(x)
    return (fx(y), y)
TL, TR, BR, BL = inter(xl, yt), inter(xr, yt), inter(xr, yb), inter(xl, yb)
m = np.zeros((H, W), np.uint8)
cv2.fillPoly(m, [np.array([TL, TR, BR, BL], np.int32)], 255)
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)              # round the corners
m = cv2.erode(m, np.ones((3, 3), np.uint8))
# red hooks in front of the phone's bottom-left: repaint those pixels as phone
# (frame colour near the outline, screen black inside), sampled from the visible bottom of the phone
r, g, b = [ai[..., i].astype(int) for i in range(3)]
ys0 = np.mgrid[0:H, 0:W][0]
occ = ((r - g > 10) & (r - b > 8)) & (m > 0) & (ys0 > 780) & (ys0 > 1.45 * (np.mgrid[0:H, 0:W][1]) + 100)
dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
ys, xs = np.mgrid[0:H, 0:W]
zone = (ys > 780) & (ys > 1.45 * xs + 100) & (xs < 470) & (m > 0)
occ |= zone  # repaint the whole hidden corner
occ = cv2.dilate(occ.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & (m > 0)
near_bottom = (ys > 820) & (m > 0) & ~occ
FR = 14
FRx = 5 + 9 * np.clip((xs - 400) / 70, 0, 1)
frame_c = np.median(ai[near_bottom & (dist > 2) & (dist < FR)], 0)
screen_c = np.median(ai[near_bottom & (dist > FR + 12)], 0)
t = np.clip((dist - FRx) / 3, 0, 1)[..., None]
# frame: a little lighter at the outer rim, like the visible frame
rim = np.clip(1 - dist / 6, 0, 1)[..., None] * 18
fill = (frame_c + rim) * (1 - t) + screen_c * t
phone = ai.copy()
oa = np.clip(cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 6) * 1.6, 0, 1)[..., None]
oa = np.where(occ[..., None], np.maximum(oa, 0.85), oa)
phone = (ai * (1 - oa) + cv2.GaussianBlur(fill.astype(np.float32), (0, 0), 1.0) * oa).astype(np.uint8)
ring = (cv2.dilate(m, np.ones((15, 15), np.uint8)) > 0) & (m == 0)
phone = cv2.inpaint(phone, ring.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)

# --- place it on the real photo: AI bottom-right corner -> old phone bottom-right corner ---
src = cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB)
SH, SW = src.shape[:2]
sr, sg, sb = [src[..., i].astype(int) for i in range(3)]
tip = np.zeros((SH, SW), bool); tip[1370:1495, 200:370] = True
tip &= (sb > sr + 2)
tip = cv2.dilate(tip.astype(np.uint8), np.ones((9, 9), np.uint8))
tipm = cv2.GaussianBlur(tip.astype(np.float32), (0, 0), 3)[..., None]
src = (src * (1 - tipm) + np.roll(src, 190, axis=1) * tipm).astype(np.uint8)
S = float(sys.argv[4]) if len(sys.argv) > 4 else 1.85
a_ai, a_old = np.degrees(np.arctan(0.508)), np.degrees(np.arctan(0.663))
A = cv2.getRotationMatrix2D(BR, -(a_old - a_ai), S)
tgt = (335, 1466)
A[:, 2] += np.array(tgt) - np.array(BR)
ph = cv2.warpAffine(phone, A, (SW, SH), flags=cv2.INTER_LANCZOS4)
pm = cv2.warpAffine(m, A, (SW, SH), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
pm = cv2.GaussianBlur(pm, (0, 0), 0.8)
# soften to the photo's sharpness, add a little grain, match warmth slightly
ph = cv2.GaussianBlur(ph, (0, 0), 0.7).astype(np.float32)
ph += np.random.default_rng(3).normal(0, 2.2, ph.shape)
ph *= np.array([1.02, 1.0, 0.97])
# contact shadow under the bottom edge
sh = np.zeros((SH, SW), np.float32)
bl_w = A @ np.array([BL[0], BL[1], 1]); br_w = A @ np.array([BR[0], BR[1], 1])
cv2.line(sh, tuple(int(v) for v in bl_w + (0, 8)), tuple(int(v) for v in br_w + (0, 8)), 1.0, 26)
sh = cv2.GaussianBlur(sh, (0, 0), 14) * 0.45
base = src.astype(np.float32) * (1 - sh[..., None])
out = base * (1 - pm[..., None]) + ph * pm[..., None]

Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT, quality=95)
np.save(OUT + '.mask.npy', pm)
print('corners AI', [tuple(round(v) for v in c) for c in (TL, TR, BR, BL)], 'placed bottom', bl_w, br_w)

"""Mini Phone Stand reel (9:16, ~14 s) from the real clip video_use.mp4 + Thai captions for the 3 steps.
Captions are rendered with Pillow/RAQM (correct Thai shaping) and overlaid with ffmpeg.
Timeline of the source clip: 0-1 s folded, 1-4 s lifting the back rest, 5-13 s phone on the stand.
The first second is slowed 2x so step 1 stays on screen long enough to read.
"""
from PIL import Image, ImageDraw, ImageFont
import os, subprocess

D = os.path.dirname(os.path.abspath(__file__))
T = '/tmp/reel_ovl'
os.makedirs(T, exist_ok=True)
F = os.path.expanduser('~/.fonts/')
RED, DRED = (206, 28, 36), (140, 12, 20)
W, H = 720, 1280


def font(w, s):
    return ImageFont.truetype(F + 'Prompt-%s.ttf' % w, s, layout_engine=ImageFont.Layout.RAQM)


def layer(name, draw_fn):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im))
    p = os.path.join(T, name + '.png')
    im.save(p)
    return p


def title(d):
    d.rounded_rectangle((60, 150, W - 60, 330), 28, fill=RED + (240,))
    d.text((W / 2, 205), 'Mini Phone Stand', font=font('Bold', 58), fill='white', anchor='mm')
    d.text((W / 2, 283), 'ขาตั้งมือถือจิ๋ว พกง่าย', font=font('SemiBold', 36), fill='white', anchor='mm')


def step(n, a, b):
    def f(d):
        y0, y1 = 860, 1010
        d.rounded_rectangle((50, y0, W - 50, y1), 30, fill=(255, 255, 255, 240))
        d.ellipse((74, y0 + 30, 164, y0 + 120), fill=RED)
        d.text((119, y0 + 75), str(n), font=font('Bold', 52), fill='white', anchor='mm')
        d.text((192, y0 + 58), a, font=font('Bold', 44), fill=RED, anchor='lm')
        d.text((192, y0 + 108), b, font=font('Medium', 30), fill=(90, 70, 65), anchor='lm')
    return f


def end(d):
    d.rounded_rectangle((50, 820, W - 50, 1030), 30, fill=RED + (240,))
    d.text((W / 2, 880), 'ขาตั้ง • พวงกุญแจ • ที่เปิดฝากระป๋อง', font=font('SemiBold', 34), fill='white', anchor='mm')
    d.text((W / 2, 935), 'ในชิ้นเดียว', font=font('SemiBold', 34), fill='white', anchor='mm')
    d.text((W / 2, 995), 'fixtory.studio', font=font('Medium', 28), fill=(255, 225, 220), anchor='mm')


# (png, start, end) in OUTPUT time (after the 2x slow-down of the first second)
ovl = [
    (layer('title', title), 0.0, 3.0),
    (layer('s1', step(1, 'พับเก็บ', 'ห้อยเป็นพวงกุญแจ')), 0.0, 2.2),
    (layer('s2', step(2, 'ยกแผ่นพิงขึ้น', 'จนล็อก')), 2.2, 5.8),
    (layer('s3', step(3, 'วางมือถือ', 'ใส่เคสได้')), 5.8, 10.5),
    (layer('end', end), 10.5, 14.0),
]

grade = 'eq=contrast=1.06:saturation=1.05:brightness=0.01,unsharp=5:5:0.6'
fc = ('[0:v]trim=0:1,setpts=2*(PTS-STARTPTS)[a];'
      '[0:v]trim=1:13,setpts=PTS-STARTPTS[b];'
      '[a][b]concat=n=2:v=1,fps=30,' + grade + ',format=yuv420p[v0];')
inputs = ['-i', os.path.join(D, 'video_use.mp4')]
last = 'v0'
for i, (p, s, e) in enumerate(ovl, start=1):
    inputs += ['-i', p]
    fc += f"[{last}][{i}:v]overlay=0:0:enable='between(t,{s},{e})'[v{i}];"
    last = f'v{i}'
fc = fc.rstrip(';')
out = os.path.join(D, 'mini_phone_stand_reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', f'[{last}]',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', '-an', out], check=True)
print('saved', out)

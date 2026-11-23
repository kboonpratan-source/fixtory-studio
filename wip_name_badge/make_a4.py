# วางโปสเตอร์ (สัดส่วน 2:3) กลางหน้า A4 2480x3508 px @300dpi พื้นขอบสีเดียวกับโปสเตอร์
import os
from PIL import Image
d = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(d, 'poster_a4_src.png')).convert('RGB')
W, H = 2480, 3508
if src.height != H:
    src = src.resize((round(src.width * H / src.height), H), Image.LANCZOS)
page = Image.new('RGB', (W, H), (24, 25, 28))
page.paste(src, ((W - src.width) // 2, 0))
page.save(os.path.join(d, '..', 'name_pop_poster_a4.pdf'), 'PDF', resolution=300, quality=95)
print('A4', page.size, 'poster', src.size)

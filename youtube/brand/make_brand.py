# 채널 꾸미기 이미지 생성: banner.png(2560x1440), profile.png(800x800)
import glob, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
def fp(b): return glob.glob(f"/usr/share/fonts/**/NotoSansCJK-{'Bold' if b else 'Regular'}.ttc", recursive=True)[0]
def F(s, b=True): return ImageFont.truetype(fp(b), int(s), index=1)
BG0, BG1 = (12, 20, 38), (26, 42, 76)
INK, MUTED, ACC, UP, DOWN = (240, 244, 250), (150, 165, 190), (255, 196, 70), (240, 72, 72), (70, 140, 250)

def grad(w, h):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        p = y / h; g.putpixel((0, y), tuple(int(BG0[i] + (BG1[i] - BG0[i]) * p) for i in range(3)))
    return g.resize((w, h))

def ctext(d, cx, y, s, f, fill):
    d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)

# ---- 배너 ----
W, H = 2560, 1440
im = grad(W, H); d = ImageDraw.Draw(im)
for x in range(0, W, 80): d.line([(x, 0), (x, H)], fill=(18, 28, 50))
for y in range(0, H, 80): d.line([(0, y), (W, y)], fill=(18, 28, 50))
# 바깥쪽 장식: 오르는 꺾은선
pts = [(0, 1120), (300, 1060), (520, 1090), (760, 960), (980, 1000), (1200, 880)]
d.line(pts, fill=(90, 40, 50), width=10)
pts2 = [(1360, 560), (1600, 520), (1820, 560), (2060, 430), (2300, 470), (2560, 340)]
d.line(pts2, fill=(90, 40, 50), width=10)
# 가격표 장식(안전영역 밖)
for (x, y, t, c) in [(180, 300, "▲ 배추 +79%", UP), (2120, 1000, "▲ 휘발유 +6%", UP), (2140, 300, "▼ 계란 -8%", DOWN), (160, 1180, "▲ 삼겹살 +22%", UP)]:
    f = F(56); tw = d.textlength(t, font=f)
    d.rounded_rectangle([x, y, x + tw + 60, y + 96], radius=48, fill=(30, 40, 66), outline=c, width=4)
    d.text((x + 30, y + 12), t, font=f, fill=c)
# 안전 영역(1546x423, 가운데) 안에 핵심 문구
cx, top = W // 2, (H - 423) // 2
t1, t2 = "오늘의 경제 ", "1분"; f1 = F(150)
w1, w2 = d.textlength(t1, font=f1), d.textlength(t2, font=f1)
x0 = cx - (w1 + w2) / 2
d.text((x0, top - 10), t1, font=f1, fill=INK)
d.text((x0 + w1, top - 10), t2, font=f1, fill=ACC)
ctext(d, cx, top + 200, "내 지갑에 닿는 생활 경제, 매일 아침 1분", F(72, False), INK)
ctext(d, cx, top + 310, "기름값 · 장바구니 · 금리 · 공공요금 · 제도 변경", F(54, False), MUTED)
im.save("brand/banner.png")

# ---- 프로필 ----
S = 800
p = grad(S, S); d = ImageDraw.Draw(p)
d.ellipse([40, 40, S - 40, S - 40], outline=ACC, width=18)
ctext(d, S / 2, 170, "경제", F(150), INK)
ctext(d, S / 2, 320, "1분", F(260), ACC)
# 작은 상승 화살표 포인트
d.polygon([(625, 190), (675, 270), (575, 270)], fill=UP)
p.save("brand/profile.png")
print("ok")

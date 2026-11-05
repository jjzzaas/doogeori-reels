# 경제 브리핑 영상 렌더러 (쇼츠 1080x1920 / 롱폼 1920x1080)
# usage: python3 render_brief.py config.json   -> out_dir/silent.mp4, out_dir/thumb.jpg, out_dir/timeline.json
import json, math, os, subprocess, sys, glob
from PIL import Image, ImageDraw, ImageFont

CFG = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = CFG["out_dir"]; os.makedirs(OUT, exist_ok=True)
LONG = CFG.get("format", "short") == "long"
W, H = (1920, 1080) if LONG else (1080, 1920)
FPS = 30
U = W / 1080 if not LONG else H / 1080  # 기준 단위(짧은 변 1080 기준)

BG0, BG1 = (12, 20, 38), (22, 36, 66)
INK, MUTED, GRID = (240, 244, 250), (150, 165, 190), (40, 56, 90)
ACC = (255, 196, 70)
UP, DOWN, FLAT = (240, 72, 72), (70, 140, 250), (180, 186, 200)  # 한국 관례: 상승 빨강, 하락 파랑

def _font_path(bold):
    names = ["NotoSansCJK-Bold.ttc", "NotoSansCJK-Black.ttc"] if bold else ["NotoSansCJK-Regular.ttc", "NotoSansCJK-Medium.ttc"]
    for n in names:
        hit = glob.glob(f"/usr/share/fonts/**/{n}", recursive=True)
        if hit: return hit[0]
    raise SystemExit("Noto CJK 폰트가 없습니다: apt-get install -y fonts-noto-cjk")
FB, FR = _font_path(True), _font_path(False)
_fc = {}
def F(size, bold=True):
    k = (int(size), bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(FB if bold else FR, int(size), index=1)  # index 1 = KR
    return _fc[k]

def ease(t): t = max(0., min(1., t)); return t * t * (3 - 2 * t)
def eout(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3

def fit(d, s, size, maxw, bold=True):
    while size > 20 and d.textlength(s, font=F(size, bold)) > maxw: size -= 2
    return F(size, bold)

def wrap(d, s, f, maxw):
    lines, cur = [], ""
    for word in s.split(" "):
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def ctext(d, cx, y, s, f, fill):
    d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)

# ---------- 배경 ----------
def make_bg():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        p = y / H
        g.putpixel((0, y), tuple(int(BG0[i] + (BG1[i] - BG0[i]) * p) for i in range(3)))
    im = g.resize((W, H))
    d = ImageDraw.Draw(im)
    step = int(90 * U)
    for x in range(0, W, step): d.line([(x, 0), (x, H)], fill=(*BG0,), width=1)
    for y in range(0, H, step): d.line([(0, y), (W, y)], fill=(*BG0,), width=1)
    # 상단 채널 바
    pad = int(60 * U)
    d.text((pad, int(50 * U)), CFG["channel"], font=F(40 * U), fill=ACC)
    dl = CFG["date_label"]; f = F(34 * U, False)
    d.text((W - pad - d.textlength(dl, font=f), int(56 * U)), dl, font=f, fill=MUTED)
    return im
BG = make_bg()

# ---------- 장면 타이밍 ----------
items = CFG["items"]
timing = {}
tp = os.path.join(OUT, "tts", "durations.json")
if os.path.exists(tp): timing = json.load(open(tp, encoding="utf-8"))
def dur_of(key, default):
    return max(default, timing[key] + 0.7) if key in timing else default
scenes = [("intro", None, dur_of("intro", 3.2))]
default_item = 12.0 if LONG else 6.5
for i, it in enumerate(items): scenes.append(("item", it, dur_of(f"item{i}", it.get("sec", default_item))))
scenes.append(("outro", None, dur_of("outro", 3.0)))
starts, t = [], 0.0
for s in scenes: starts.append(t); t += s[2]
TOTAL = t
if not LONG and TOTAL > 59.5:
    print(f"경고: 쇼츠 길이 {TOTAL:.1f}s — 항목이나 대본을 줄이세요(60초 이하 권장)")
json.dump({"total": TOTAL, "scenes": [{"kind": k, "start": s, "dur": d} for (k, _, d), s in zip(scenes, starts)]},
          open(os.path.join(OUT, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 그리기 ----------
def progress(d, t):
    p = t / TOTAL; y = int(130 * U); pad = int(60 * U)
    d.rounded_rectangle([pad, y, W - pad, y + int(8 * U)], radius=int(4 * U), fill=GRID)
    d.rounded_rectangle([pad, y, pad + max(int(8 * U), int((W - 2 * pad) * p)), y + int(8 * U)], radius=int(4 * U), fill=ACC)

def subtitle(d, text, lt, dur):
    if not text or not CFG.get("subtitles", True): return
    import re
    sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip()]
    if not sents: return
    tot = sum(len(s) for s in sents); acc = 0; cur = sents[-1]
    span = max(dur - 0.7, 0.5)
    for s in sents:
        acc += len(s)
        if lt <= span * acc / tot: cur = s; break
    f = F(40 * U if not LONG else 38 * U, True)
    maxw = W - int(160 * U)
    lines = wrap(d, cur, f, maxw)[:2]
    lh = int(56 * U)
    y0 = (H - int(330 * U)) if not LONG else (H - int(150 * U))
    for k, ln in enumerate(lines):
        w = d.textlength(ln, font=f); x = (W - w) / 2; y = y0 + k * lh
        d.rounded_rectangle([x - 18 * U, y - 6 * U, x + w + 18 * U, y + lh - 4 * U], radius=int(10 * U), fill=(0, 0, 0))
        d.text((x, y), ln, font=f, fill=INK)

def sparkline(d, box, series, p, col):
    x0, y0, x1, y1 = box
    lo, hi = min(series), max(series); rng = (hi - lo) or 1
    pts = [(x0 + (x1 - x0) * i / (len(series) - 1), y1 - (y1 - y0) * (v - lo) / rng) for i, v in enumerate(series)]
    n = max(2, int(len(pts) * p + 0.999))
    seg = pts[:n]
    if p < 1 and n < len(pts):  # 마지막 구간 보간
        fr = len(pts) * p - (n - 1)
        a, b = pts[n - 1], pts[min(n, len(pts) - 1)]
        seg = pts[:n - 1] + [(a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr)] if n > 1 else seg
    for gy in range(4):
        yy = y0 + (y1 - y0) * gy / 3; d.line([(x0, yy), (x1, yy)], fill=GRID, width=1)
    if len(seg) >= 2: d.line(seg, fill=col, width=int(7 * U), joint="curve")
    ex, ey = seg[-1]; r = int(12 * U)
    d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col)

def count_up(val, p):
    # "1,398.5원" 같은 문자열의 숫자 부분만 카운트업
    import re
    m = re.search(r"[-+]?[\d,]*\.?\d+", val)
    if not m or p >= 1: return val
    raw = m.group(0); num = float(raw.replace(",", ""))
    dec = len(raw.split(".")[1]) if "." in raw else 0
    cur = num * eout(p)
    s = f"{cur:,.{dec}f}" if "," in raw else f"{cur:.{dec}f}"
    return val[:m.start()] + s + val[m.end():]

def draw_item(im, it, lt, dur, idx):
    d = ImageDraw.Draw(im)
    a = ease(lt / 0.45)
    col = {"up": UP, "down": DOWN}.get(it.get("dir"), FLAT)
    arrow = {"up": "▲", "down": "▼"}.get(it.get("dir"), "■")
    pad = int(80 * U)
    if LONG:
        lx, cy_top = pad, int(220 * U); colw = int(W * 0.46)
    else:
        lx, cy_top = pad, int(300 * U); colw = W - 2 * pad
    rise = int((1 - a) * 40 * U)
    # 태그 + 순번
    tag = f"{idx}/{len(items)}  ·  {it['tag']}"
    f = F(36 * U); tw_ = d.textlength(tag, font=f)
    d.rounded_rectangle([lx, cy_top + rise, lx + tw_ + 44 * U, cy_top + rise + 64 * U], radius=int(32 * U), fill=col)
    d.text((lx + 22 * U, cy_top + rise + 8 * U), tag, font=f, fill=(255, 255, 255))
    # 라벨
    y = cy_top + int(100 * U) + rise
    d.text((lx, y), it["label"], font=fit(d, it["label"], 58 * U, colw), fill=MUTED)
    # 큰 숫자
    p = ease((lt - 0.3) / 1.1)
    v = count_up(it["value"], p)
    fv = fit(d, it["value"], (150 if not LONG else 130) * U, colw)
    y += int(90 * U)
    d.text((lx, y), v, font=fv, fill=INK)
    # 변동
    y += int(fv.size * 1.35)
    if it.get("change"):
        pc = ease((lt - 1.1) / 0.4)
        if pc > 0:
            ch = f"{arrow} {it['change']}"
            d.text((lx - (1 - pc) * 30 * U, y), ch, font=F(64 * U), fill=col)
    y += int(110 * U)
    # 설명 두 줄
    for k, key in enumerate(("note1", "note2")):
        if not it.get(key): continue
        pn = ease((lt - 1.6 - 0.35 * k) / 0.45)
        if pn <= 0: continue
        fnt = F(46 * U, k == 0)
        for ln in wrap(d, it[key], fnt, colw):
            d.text((lx, y + (1 - pn) * 24 * U), ln, font=fnt, fill=INK if k == 0 else MUTED)
            y += int(64 * U)
        y += int(14 * U)
    # 미니 차트
    if it.get("series") and len(it["series"]) >= 2:
        ps = ease((lt - 0.6) / 2.0)
        if LONG: box = (int(W * 0.56), int(260 * U), W - pad, int(760 * U))
        else: box = (lx, max(y + int(40 * U), int(1060 * U)), W - pad, int(1440 * U))
        sparkline(d, box, it["series"], ps, col)
        if it.get("series_label"):
            d.text((box[0], box[3] + 14 * U), it["series_label"], font=F(30 * U, False), fill=MUTED)
    subtitle(d, it.get("say", ""), lt, dur)

def draw_intro(im, lt, dur):
    d = ImageDraw.Draw(im); a = ease(lt / 0.5)
    cx = W // 2; y = int(H * (0.33 if not LONG else 0.30))
    ctext(d, cx, y - (1 - a) * 30 * U, CFG.get("kicker", "오늘의 경제 한눈에"), F(48 * U), ACC)
    f = F(96 * U); maxw = W - int(160 * U)
    yy = y + int(110 * U)
    for k, ln in enumerate(wrap(d, CFG["title"], f, maxw)[:3]):
        pk = ease((lt - 0.25 - 0.2 * k) / 0.5)
        if pk > 0: ctext(d, cx, yy + (1 - pk) * 40 * U, ln, f, INK)
        yy += int(124 * U)
    pc = ease((lt - 1.0) / 0.5)
    if pc > 0:
        chips = "  ·  ".join(it["tag"] for it in items)
        ctext(d, cx, yy + int(40 * U), chips, fit(d, chips, 40 * U, maxw, False), MUTED)
    subtitle(d, CFG.get("intro_say", ""), lt, dur)

def draw_outro(im, lt, dur):
    d = ImageDraw.Draw(im); a = ease(lt / 0.5); cx = W // 2; y = int(H * 0.38)
    ctext(d, cx, y + (1 - a) * 30 * U, CFG.get("outro", "내일도 핵심만 정리해 드릴게요"), fit(d, CFG.get("outro", ""), 64 * U, W - 160 * U), INK)
    src = "출처: " + ", ".join(CFG.get("sources", []))
    fs = F(30 * U, False); yy = y + int(130 * U)
    for ln in wrap(d, src, fs, W - int(160 * U)):
        ctext(d, cx, yy, ln, fs, MUTED); yy += int(44 * U)
    ctext(d, cx, yy + int(30 * U), "투자 권유가 아닌 정보 제공 목적입니다", F(30 * U, False), MUTED)
    subtitle(d, CFG.get("outro_say", ""), lt, dur)

def frame(t):
    i = max(k for k in range(len(scenes)) if t >= starts[k])
    kind, it, dur = scenes[i]; lt = t - starts[i]
    im = BG.copy()
    if kind == "intro": draw_intro(im, lt, dur)
    elif kind == "outro": draw_outro(im, lt, dur)
    else: draw_item(im, it, lt, dur, i)
    progress(ImageDraw.Draw(im), t)
    # 장면 전환: 끝 0.25초 페이드
    fo = ease((lt - (dur - 0.25)) / 0.25)
    if fo > 0 and i < len(scenes) - 1: im = Image.blend(im, BG, fo)
    return im

def render():
    path = os.path.join(OUT, "silent.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)): pr.stdin.write(frame(k / FPS).tobytes())
    pr.stdin.close(); pr.wait()

def thumbnail():
    # 썸네일: 첫 항목의 숫자를 크게
    im = BG.copy(); d = ImageDraw.Draw(im); it = items[0]
    col = {"up": UP, "down": DOWN}.get(it.get("dir"), FLAT)
    cx = W // 2; maxw = W - int(140 * U)
    y = int(H * (0.22 if not LONG else 0.18))
    for ln in wrap(d, CFG.get("thumb_text", CFG["title"]), F(110 * U), maxw)[:3]:
        ctext(d, cx, y, ln, F(110 * U), INK); y += int(140 * U)
    ctext(d, cx, y + int(40 * U), it["value"], fit(d, it["value"], 170 * U, maxw), col)
    im.save(os.path.join(OUT, "thumb.jpg"), quality=95)

if __name__ == "__main__":
    thumbnail(); render(); print(f"done {TOTAL:.1f}s {W}x{H}")

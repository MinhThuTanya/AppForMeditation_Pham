"""Декоративные элементы интерфейса (временные — потом заменяются своими артами
с теми же именами файлов). Запуск из папки проекта: python tools/make_deco.py

assets/images/deco/    — персонажи-дудлы, пузыри, облака, рыбки, волны, круги на воде, стрелки
assets/images/buttons/ — фоны кнопок: овал со стрелками, каракули, облачко в горошек, рваная бумага
assets/images/moods/   — смайлики настроений для календаря
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

S = 3                                     # сглаживание: рисуем крупнее, потом уменьшаем
BLUE = (61, 111, 214)
BLUE_L = (127, 166, 240)
NAVY = (27, 31, 75)
random.seed(7)


def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def save(img, path, w, h):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.resize((w, h), Image.LANCZOS).save(path)


def wobble(points, amp=1.2):
    return [(x + random.uniform(-amp, amp), y + random.uniform(-amp, amp)) for x, y in points]


def stroke(d, pts, color, width, passes=2, amp=1.0, alpha=255):
    """Линия «от руки»: несколько чуть смещённых проходов."""
    for _ in range(passes):
        p = [(x * S, y * S) for x, y in wobble(pts, amp)]
        d.line(p, fill=color + (alpha,), width=int(width * S), joint="curve")


def ellipse_pts(cx, cy, rx, ry, start=0, end=360, n=80, rot=0):
    pts = []
    for i in range(n + 1):
        a = math.radians(start + (end - start) * i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        r = math.radians(rot)
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return pts


# ---------------- персонажи-дудлы ----------------
def face(kind, path):
    W = H = 180
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    cx, cy = 90, 98
    # голова
    stroke(d, ellipse_pts(cx, cy, 52, 50, -10, 352), BLUE, 3.2, amp=0.8)
    if kind == "spiky":           # колючая чёлка
        pts = [(40, 80)]
        for i in range(6):
            pts += [(48 + i * 16, 40 + (i % 2) * 6), (56 + i * 16, 70)]
        stroke(d, pts, BLUE, 3, amp=0.6)
        eyes, mouth = "angry", "grin"
    elif kind == "curly":         # кудряшки
        for i in range(7):
            a = math.radians(200 + i * 23)
            stroke(d, ellipse_pts(cx + 50 * math.cos(a), cy - 8 + 46 * math.sin(a), 13, 13), BLUE, 3, amp=0.5)
        eyes, mouth = "dots", "smile"
    elif kind == "glasses":       # очки и пробор
        stroke(d, [(48, 70), (70, 52), (100, 48), (134, 66)], BLUE, 3)
        for x in (72, 108):
            stroke(d, ellipse_pts(x, 96, 14, 12), BLUE, 2.6, amp=0.4)
        stroke(d, [(86, 96), (94, 96)], BLUE, 2.6)
        eyes, mouth = "dots", "o"
    else:                         # sleepy: шапочка и «zz»
        stroke(d, ellipse_pts(cx, 62, 48, 26, 180, 360), BLUE, 3)
        stroke(d, [(140, 34), (152, 34), (140, 46), (152, 46)], BLUE, 2.4)
        stroke(d, [(156, 18), (164, 18), (156, 26), (164, 26)], BLUE, 2)
        eyes, mouth = "closed", "small"
    ex = (74, 108)
    for x in ex:
        if eyes == "dots" and kind != "glasses":
            d.ellipse([(x - 4) * S, (92) * S, (x + 4) * S, (101) * S], fill=BLUE + (255,))
        elif eyes == "dots":
            d.ellipse([(x - 3) * S, 93 * S, (x + 3) * S, 99 * S], fill=BLUE + (255,))
        elif eyes == "angry":
            stroke(d, [(x - 9, 88 + (4 if x < 90 else 0)), (x + 9, 88 + (0 if x < 90 else 4))], BLUE, 2.6)
            d.ellipse([(x - 3) * S, 95 * S, (x + 3) * S, 101 * S], fill=BLUE + (255,))
        else:
            stroke(d, ellipse_pts(x, 94, 9, 6, 20, 160), BLUE, 2.6, amp=0.3)
    if mouth == "grin":
        stroke(d, ellipse_pts(cx, 112, 18, 12, 10, 170), BLUE, 3)
        stroke(d, [(73, 115), (107, 115)], BLUE, 2.4)
    elif mouth == "smile":
        stroke(d, ellipse_pts(cx, 114, 14, 9, 20, 160), BLUE, 3)
    elif mouth == "o":
        stroke(d, ellipse_pts(cx, 120, 6, 7), BLUE, 2.6, amp=0.3)
    else:
        stroke(d, ellipse_pts(cx, 120, 7, 4, 20, 160), BLUE, 2.6, amp=0.3)
    # румянец
    for x in (62, 118):
        d.ellipse([(x - 8) * S, 106 * S, (x + 8) * S, 114 * S], fill=(240, 150, 160, 110))
    save(img, path, W, H)


# ---------------- пузыри ----------------
def bubble(path, size=160):
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    r = size / 2 - 4
    c = size / 2
    body = Image.new("L", img.size, 0)
    ImageDraw.Draw(body).ellipse([4 * S, 4 * S, (size - 4) * S, (size - 4) * S], fill=55)
    tint = Image.new("RGBA", img.size, (170, 200, 250, 0))
    tint.putalpha(body)
    img = Image.alpha_composite(img, tint)
    d = ImageDraw.Draw(img)
    d.ellipse([4 * S, 4 * S, (size - 4) * S, (size - 4) * S], outline=(150, 185, 245, 200), width=3 * S)
    # радужная кромка
    d.arc([10 * S, 10 * S, (size - 10) * S, (size - 10) * S], 200, 300, fill=(240, 200, 230, 150), width=4 * S)
    d.arc([10 * S, 10 * S, (size - 10) * S, (size - 10) * S], 20, 110, fill=(180, 230, 220, 140), width=4 * S)
    # блик
    d.ellipse([(c - r * 0.55) * S, (c - r * 0.65) * S, (c - r * 0.15) * S, (c - r * 0.35) * S],
              fill=(255, 255, 255, 220))
    save(img.filter(ImageFilter.GaussianBlur(S * 0.6)), path, size, size)


# ---------------- облака (акварель) ----------------
def clouds(path, W=720, H=180):
    img = canvas(W, H)
    layers = [((176, 200, 240), 0.65, 70), ((120, 160, 230), 0.75, 105), ((80, 125, 215), 0.85, 140)]
    for color, alpha, base in layers:
        lay = Image.new("L", img.size, 0)
        ld = ImageDraw.Draw(lay)
        x = -20
        while x < W + 40:
            r = random.randint(34, 56)
            ld.ellipse([(x - r) * S, (base - r) * S, (x + r) * S, (base + r) * S], fill=255)
            x += r * 1.3
        ld.rectangle([0, base * S, W * S, H * S], fill=255)
        lay = lay.filter(ImageFilter.GaussianBlur(S * 1.5))
        # «зернистость» акварели
        grain = Image.effect_noise(img.size, 40).point(lambda v: 200 + v // 5)
        alpha_l = Image.composite(lay.point(lambda v: int(v * alpha)), Image.new("L", img.size, 0), lay)
        alpha_l = Image.composite(alpha_l, Image.new("L", img.size, 0), lay)
        col = Image.new("RGBA", img.size, color + (0,))
        col.putalpha(Image.blend(alpha_l, Image.composite(grain, alpha_l, lay), 0.15))
        img = Image.alpha_composite(img, col)
        # белые «завитки» на гребнях
        d = ImageDraw.Draw(img)
        x = 10
        while x < W:
            r = random.randint(16, 26)
            d.arc([(x - r) * S, (base - r + 12) * S, (x + r) * S, (base + r + 12) * S], 200, 340,
                  fill=(255, 255, 255, 140), width=2 * S)
            x += random.randint(60, 90)
    save(img, path, W, H)


# ---------------- круги на воде ----------------
def ripple(path, size=220):
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    c = size / 2
    for i, r in enumerate(range(18, int(c) - 4, 16)):
        a = max(40, 200 - i * 22)
        stroke(d, ellipse_pts(c, c, r, r * 0.96, n=90), (120, 190, 220), 3.2 - i * 0.2, passes=2, amp=0.7, alpha=a)
    img = img.filter(ImageFilter.GaussianBlur(S * 0.8))
    save(img, path, size, size)


# ---------------- рыбка ----------------
def fish(path, W=220, H=110):
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    body = ellipse_pts(95, 55, 72, 30, n=80)
    poly = [(x * S, y * S) for x, y in body]
    d.polygon(poly, fill=(150, 185, 240, 255))
    # штриховка «карандашом»
    for i in range(140):
        x = random.uniform(30, 160)
        y = random.uniform(32, 78)
        if ((x - 95) / 72) ** 2 + ((y - 55) / 30) ** 2 < 0.85:
            d.line([x * S, y * S, (x + 6) * S, (y - 3) * S], fill=(110, 150, 225, 160), width=S)
    stroke(d, body, BLUE, 3, amp=0.6)
    stroke(d, [(165, 55), (205, 28), (198, 55), (205, 82), (165, 55)], BLUE, 3, amp=0.6)
    d.polygon([(167 * S, 55 * S), (203 * S, 31 * S), (196 * S, 55 * S), (203 * S, 79 * S)], fill=(150, 185, 240, 255))
    stroke(d, ellipse_pts(48, 50, 9, 9), BLUE, 2.6, amp=0.3)
    d.ellipse([45 * S, 47 * S, 51 * S, 53 * S], fill=NAVY + (255,))
    for x in (90, 110, 130):
        stroke(d, ellipse_pts(x, 55, 6, 10, -80, 80, n=20), BLUE, 2.4, amp=0.3)
    # белая обводка-наклейка
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    mask = img.split()[3].filter(ImageFilter.MaxFilter(13))
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    out.paste(white, mask=mask)
    out = Image.alpha_composite(out, img)
    save(out, path, W, H)


# ---------------- волна-завиток ----------------
def swirl(path, W=240, H=160):
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(160):
        t = i / 159 * 3.4 * math.pi
        r = 8 + 9 * t
        pts.append((150 + r * math.cos(-t), 80 + r * math.sin(-t)))
    pts = pts[::-1] + [(60, 120), (20, 110)]
    for w, col in ((16, (190, 215, 235)), (9, (140, 185, 225)), (3, (90, 140, 200))):
        stroke(d, pts, col, w, passes=1, amp=0.3)
    for i in range(0, 160, 12):
        x, y = pts[i]
        d.ellipse([(x - 2.5) * S, (y - 2.5) * S, (x + 2.5) * S, (y + 2.5) * S], fill=(255, 255, 255, 230))
    save(img, path, W, H)


# ---------------- стрелка ----------------
def arrow(path, W=160, H=120):
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    pts = [(14, 96), (40, 70), (34, 46), (58, 40), (78, 66), (120, 30)]
    stroke(d, pts, (232, 112, 106), 7, passes=1, amp=0.4)
    stroke(d, [(100, 26), (124, 26), (120, 50)], (232, 112, 106), 7, passes=1, amp=0.3)
    save(img, path, W, H)


# ---------------- фоны кнопок ----------------
def btn_oval(path, W=360, H=200):
    """Овал от руки со стрелками сверху."""
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    stroke(d, ellipse_pts(W / 2, 128, W / 2 - 12, 62, -5, 365, n=120, rot=-2), (12, 74, 170), 4.5, passes=1, amp=0.5)
    stroke(d, ellipse_pts(W / 2 + 6, 70, 54, 6, 200, 330, n=30), (12, 74, 170), 4, passes=1, amp=0.3)
    for x, ang in ((70, -25), (W / 2, 0), (W - 70, 25)):
        a = math.radians(90 + ang)
        x2, y2 = x + 34 * math.cos(a) * 0.4, 58
        x1, y1 = x - 34 * math.cos(a), 18
        stroke(d, [(x1, y1), (x2, y2)], (12, 74, 170), 4, passes=1, amp=0.3)
        stroke(d, [(x2 - 10, y2 - 12), (x2, y2), (x2 + 10, y2 - 10)], (12, 74, 170), 4, passes=1, amp=0.3)
    save(img, path, W, H)


def btn_scribble(path, W=360, H=200):
    """Заливка «каракулями» с точками."""
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    for i in range(70):
        rx = random.uniform(W / 2 - 50, W / 2 - 24)
        ry = random.uniform(56, 72)
        stroke(d, ellipse_pts(W / 2 + random.uniform(-6, 6), H / 2 + random.uniform(-4, 4), rx, ry,
                              random.uniform(0, 40), random.uniform(320, 380), n=50),
               (222, 230, 240), random.uniform(5, 9), passes=1, amp=1.6)
    d.rectangle([60 * S, 50 * S, (W - 60) * S, (H - 50) * S], fill=(228, 235, 244, 255))
    for i in range(12):
        stroke(d, ellipse_pts(W / 2, H / 2, W / 2 - 18 + random.uniform(-6, 6), 74 + random.uniform(-6, 6),
                              random.uniform(0, 60), random.uniform(200, 330), n=50),
               (200, 214, 232), 1.6, passes=1, amp=1.2)
    stroke(d, ellipse_pts(W / 2, H / 2, W / 2 - 8, 84, 190, 230, n=12), (150, 185, 225), 4, passes=1)
    stroke(d, ellipse_pts(W / 2, H / 2, W / 2 - 8, 84, 10, 50, n=12), (150, 185, 225), 4, passes=1)
    for x, y, r in ((W - 64, 22, 7), (W - 46, 22, 7), (W - 28, 26, 7), (40, H - 24, 7), (58, H - 22, 7), (76, H - 20, 8)):
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(170, 195, 230, 230))
    save(img, path, W, H)


def btn_cloud(path, W=260, H=230):
    """Облачко-реплика в горошек с пунктирной обводкой."""
    img = canvas(W, H)
    shape = Image.new("L", img.size, 0)
    sd = ImageDraw.Draw(shape)
    for cx, cy, r in ((90, 80, 58), (160, 70, 56), (200, 130, 50), (150, 170, 54), (80, 160, 56), (60, 120, 50), (130, 120, 70)):
        sd.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=255)
    sd.polygon([(36 * S, 192 * S), (8 * S, 214 * S), (62 * S, 196 * S)], fill=255)
    fill = Image.new("RGBA", img.size, (222, 240, 252, 255))
    d = ImageDraw.Draw(fill)
    for y in range(10, H, 22):
        for x in range(10 + (y // 22 % 2) * 11, W, 22):
            d.ellipse([(x - 5) * S, (y - 5) * S, (x + 5) * S, (y + 5) * S], fill=(200, 228, 248, 255))
    img.paste(fill, mask=shape)
    edge = shape.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
    inner = shape.filter(ImageFilter.MinFilter(25))
    dash = Image.new("L", img.size, 0)
    dd = ImageDraw.Draw(dash)
    for x in range(0, W * S, 9 * S):
        dd.rectangle([x, 0, x + 4 * S, H * S], fill=255)
    ring = inner.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
    ring = Image.composite(ring, Image.new("L", img.size, 0), dash)
    blue = Image.new("RGBA", img.size, (140, 190, 225, 255))
    img.paste(blue, mask=ring)
    soft = Image.new("RGBA", img.size, (190, 220, 240, 255))
    img.paste(soft, mask=edge)
    save(img, path, W, H)


def btn_paper(path, W=360, H=220):
    """Рваная бумага на клетчатой ткани."""
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    # клетка
    gx0, gy0, gx1, gy1 = 4, 46, W - 40, H - 4
    cell = 14
    for i, x in enumerate(range(gx0, gx1, cell)):
        d.rectangle([x * S, gy0 * S, (x + cell / 2) * S, gy1 * S], fill=(110, 150, 215, 150))
    for j, y in enumerate(range(gy0, gy1, cell)):
        d.rectangle([gx0 * S, y * S, gx1 * S, (y + cell / 2) * S], fill=(110, 150, 215, 150))
    # бумага с рваным краем
    pts = []
    x0, y0, x1, y1 = 40, 8, W - 8, H - 40
    for x in range(x0, x1, 6):
        pts.append((x, y0 + random.uniform(-3, 4)))
    for y in range(y0, y1, 6):
        pts.append((x1 + random.uniform(-4, 3), y))
    for x in range(x1, x0, -6):
        pts.append((x, y1 + random.uniform(-4, 4)))
    for y in range(y1, y0, -6):
        pts.append((x0 + random.uniform(-3, 4), y))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([((x + 3) * S, (y + 4) * S) for x, y in pts], fill=(0, 0, 0, 60))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(4 * S)))
    d = ImageDraw.Draw(img)
    d.polygon([(x * S, y * S) for x, y in pts], fill=(246, 246, 244, 255))
    grain = Image.effect_noise(img.size, 18).point(lambda v: 240 + (v - 128) // 12)
    paper = Image.new("L", img.size, 0)
    ImageDraw.Draw(paper).polygon([(x * S, y * S) for x, y in pts], fill=255)
    tex = Image.merge("RGBA", (grain, grain, grain.point(lambda v: min(255, v + 2)), paper.point(lambda v: v // 6)))
    img = Image.alpha_composite(img, tex)
    d = ImageDraw.Draw(img)
    stroke(d, pts + [pts[0]], (215, 215, 212), 1.4, passes=1, amp=0.2)
    save(img, path, W, H)


# ---------------- смайлики настроений ----------------
MOODS = {"joy": (110, 200, 120), "calm": (120, 165, 240), "tired": (185, 165, 232),
         "anxious": (240, 160, 90), "sad": (150, 168, 200)}


def smiley(kind, path, size=96):
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    c = size / 2
    col = MOODS[kind]
    d.ellipse([4 * S, 4 * S, (size - 4) * S, (size - 4) * S], fill=col + (255,))
    stroke(d, ellipse_pts(c, c, c - 5, c - 5), tuple(max(0, v - 50) for v in col), 2.4, passes=1, amp=0.3)
    ink = NAVY
    if kind == "tired":
        for x in (34, 62):
            stroke(d, ellipse_pts(x, 42, 8, 5, 20, 160), ink, 3, passes=1, amp=0.2)
    elif kind == "anxious":
        for x in (34, 62):
            d.ellipse([(x - 6) * S, 34 * S, (x + 6) * S, 47 * S], fill=(255, 255, 255, 255))
            d.ellipse([(x - 3) * S, 38 * S, (x + 3) * S, 44 * S], fill=ink + (255,))
    else:
        for x in (34, 62):
            d.ellipse([(x - 5) * S, 34 * S, (x + 5) * S, 46 * S], fill=ink + (255,))
    if kind == "joy":
        d.chord([28 * S, 46 * S, 68 * S, 76 * S], 0, 180, fill=ink + (255,))
        d.chord([36 * S, 62 * S, 60 * S, 76 * S], 0, 180, fill=(235, 110, 120, 255))
    elif kind == "calm":
        stroke(d, ellipse_pts(c, 56, 13, 9, 20, 160), ink, 3.2, passes=1, amp=0.2)
    elif kind == "tired":
        d.ellipse([42 * S, 60 * S, 54 * S, 70 * S], fill=ink + (255,))
    elif kind == "anxious":
        pts = [(30 + i * 4, 66 + (4 if i % 2 else -2)) for i in range(10)]
        stroke(d, pts, ink, 3, passes=1, amp=0.1)
    else:
        stroke(d, ellipse_pts(c, 74, 13, 9, 200, 340), ink, 3.2, passes=1, amp=0.2)
        d.ellipse([66 * S, 44 * S, 74 * S, 56 * S], fill=(170, 210, 255, 255))
    if kind in ("joy", "calm"):
        for x in (24, 72):
            d.ellipse([(x - 7) * S, 52 * S, (x + 7) * S, 59 * S], fill=(245, 150, 160, 150))
    save(img, path, size, size)


if __name__ == "__main__":
    for k in ("spiky", "curly", "glasses", "sleepy"):
        face(k, f"assets/images/deco/face_{k}.png")
    bubble("assets/images/deco/bubble.png")
    clouds("assets/images/deco/clouds.png")
    ripple("assets/images/deco/ripple.png")
    fish("assets/images/deco/fish.png")
    swirl("assets/images/deco/swirl.png")
    arrow("assets/images/deco/arrow.png")
    btn_oval("assets/images/buttons/oval.png")
    btn_scribble("assets/images/buttons/scribble.png")
    btn_cloud("assets/images/buttons/cloud.png")
    btn_paper("assets/images/buttons/paper.png")
    for k in MOODS:
        smiley(k, f"assets/images/moods/{k}.png")
    print("ok")

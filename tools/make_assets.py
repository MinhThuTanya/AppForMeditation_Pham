"""Генерация спрайтов Аватара и иконки приложения (запускать из папки проекта)."""
from PIL import Image, ImageDraw, ImageFilter
import math

S = 4            # сглаживание: рисуем в 4 раза крупнее
W = H = 512

def blank(): return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
def P(*v): return [x * S for x in v]

def body_mask():
    m = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(m)
    # «капля»: эллипс сверху уже, снизу шире
    pts = []
    cx, cy = 256, 270
    for i in range(360):
        a = math.radians(i)
        rx = 150 + 18 * math.sin(a)          # чуть шире внизу
        ry = 175
        pts.append(((cx + rx * math.cos(a)) * S, (cy + ry * math.sin(a)) * S))
    d.polygon(pts, fill=255)
    return m

def gradient(c1, c2):
    g = Image.new("RGBA", (W * S, H * S))
    d = ImageDraw.Draw(g)
    for y in range(H * S):
        t = y / (H * S)
        d.line([(0, y), (W * S, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,))
    return g

def eye(d, x, y, kind):
    navy = (27, 31, 75, 255)
    if kind == "open":
        d.ellipse(P(x - 13, y - 17, x + 13, y + 17), fill=navy)
        d.ellipse(P(x - 4, y - 11, x + 4, y - 3), fill=(255, 255, 255, 255))
    elif kind == "happy":
        d.arc(P(x - 18, y - 10, x + 18, y + 22), 200, 340, fill=navy, width=7 * S)
    elif kind == "sleepy":
        d.line(P(x - 16, y + 4, x + 16, y + 4), fill=navy, width=7 * S)
        d.arc(P(x - 16, y - 8, x + 16, y + 16), 20, 160, fill=navy, width=6 * S)
    elif kind == "wide":
        d.ellipse(P(x - 16, y - 20, x + 16, y + 20), fill=(255, 255, 255, 255))
        d.ellipse(P(x - 9, y - 10, x + 9, y + 10), fill=navy)

def make(state):
    img = blank()
    d = ImageDraw.Draw(img)
    # тень
    d.ellipse(P(150, 452, 362, 482), fill=(27, 31, 75, 40))
    if state == "glowing":
        a = Image.new("L", (W * S, H * S), 0)
        ImageDraw.Draw(a).ellipse(P(60, 60, 452, 480), fill=170)
        a = a.filter(ImageFilter.GaussianBlur(28 * S))
        aura = Image.new("RGBA", (W * S, H * S), (245, 214, 120, 0)); aura.putalpha(a)
        img = Image.alpha_composite(img, aura); d = ImageDraw.Draw(img)
    colors = {"calm": ((126, 166, 242), (61, 111, 214)),
              "glowing": ((140, 180, 250), (70, 120, 225)),
              "sad": ((140, 160, 205), (82, 104, 170)),
              "anxious": ((130, 160, 235), (70, 100, 200)),
              "tired": ((150, 170, 215), (95, 118, 180))}[state]
    body = gradient(*colors); body.putalpha(body_mask())
    img = Image.alpha_composite(img, body); d = ImageDraw.Draw(img)
    # блик
    d.ellipse(P(170, 130, 230, 175), fill=(255, 255, 255, 70))
    # щёчки
    if state in ("calm", "glowing", "tired"):
        for x in (186, 326):
            d.ellipse(P(x - 22, 300, x + 22, 322), fill=(240, 140, 150, 150))
    navy = (27, 31, 75, 255)
    ex = (210, 302); ey = 262
    kind = {"calm": "open", "glowing": "happy", "sad": "open",
            "anxious": "wide", "tired": "sleepy"}[state]
    for x in ex: eye(d, x, ey, kind)
    if state == "sad":                    # брови домиком
        d.line(P(190, 236, 226, 224), fill=navy, width=5 * S)
        d.line(P(322, 236, 286, 224), fill=navy, width=5 * S)
    # рот
    if state in ("calm", "glowing"):
        r = 26 if state == "calm" else 34
        d.arc(P(256 - r, 290 - r // 2, 256 + r, 300 + r), 20, 160, fill=navy, width=7 * S)
    elif state == "sad":
        d.arc(P(232, 318, 280, 350), 200, 340, fill=navy, width=7 * S)
        d.ellipse(P(296, 286, 312, 312), fill=(150, 200, 255, 230))    # слеза
    elif state == "anxious":
        pts = [((236 + i * 4) * S, (322 + (5 if i % 2 else -5)) * S) for i in range(11)]
        d.line(pts, fill=navy, width=6 * S, joint="curve")
        d.ellipse(P(360, 190, 378, 216), fill=(170, 215, 255, 230))    # капелька пота
    elif state == "tired":
        d.ellipse(P(246, 316, 266, 334), fill=navy)
        for i, (x, y, r) in enumerate([(360, 170, 12), (385, 140, 9), (405, 115, 7)]):
            d.line(P(x - r, y - r, x + r, y - r, x - r, y + r, x + r, y + r), fill=(27, 31, 75, 200), width=4 * S)
    out = img.resize((W, H), Image.LANCZOS)
    out.save(f"assets/images/avatar/{state}.png")

def icon():
    s = 1024
    img = Image.new("RGBA", (s, s), (230, 238, 249, 255)); d = ImageDraw.Draw(img)
    d.ellipse([262, 170, 762, 670], fill=(242, 217, 122, 255))
    d.pieslice([-200, 560, 1224, 1400], 180, 360, fill=(143, 180, 236, 255))
    d.pieslice([-100, 700, 1124, 1500], 180, 360, fill=(91, 141, 239, 255))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=230, fill=255)
    img.putalpha(mask)
    img.save("assets/icons/icon.png")
    img.resize((512, 512), Image.LANCZOS).save("assets/icons/icon_512.png")

if __name__ == "__main__":
    for st in ("calm", "glowing", "sad", "anxious", "tired"):
        make(st)
    icon()
    print("ok")

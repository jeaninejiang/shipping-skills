#!/usr/bin/env python3
"""Build App Store screenshots from raw device captures.

Takes the screenshots you grabbed on a phone or in the Simulator and
composites each into a branded panel: gradient field, headline, optional
category pills, and the screen in a device frame.

    pip install pillow numpy
    python3 scripts/store-screenshots.py

Reads from screenshots/, writes to screenshots/store/. Edit PANELS below
to change which capture goes with which headline — the layout handles the
rest, so re-running after a UI change costs nothing.

The frame is a plain dark bezel, drawn rather than a photoreal iPhone:
App Review is touchier about screenshots depicting specific hardware, and
a generic rounded frame avoids the question entirely.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import sys

from brandkit import CREAM, SAND, background, device, sans

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
OUT = SHOTS / "store"

# App Store Connect asks for a specific pixel size per device slot and
# rejects anything else, so emit each one it accepts. 1179x2556 is the
# "iPhone with Dynamic Island (medium display)" slot; 1320x2868 is the
# 6.9" one. Every measurement below is expressed against REF_W and
# scaled, so adding a size here needs no other change.
SIZES = [(1179, 2556), (1320, 2868)]
REF_W = 1320
W, H = SIZES[0]


def s(v):
    """Scale a reference-width measurement to the current canvas."""
    return int(round(v * W / REF_W))

PANELS = [
    {
        "out": "01-home.png",
        "shot": "home.png",
        "headline": ["Know each", "other better."],
        "sub": "A private app for two.",
    },
    {
        "out": "02-together.png",
        "shot": "couple-reading.png",
        "headline": ["Where you fit.", "Where it grinds."],
        "sub": "Written about the two of you, never scored.",
    },
    {
        "out": "03-charts.png",
        "shot": "chart-reading.png",
        "headline": ["Know yourself.", "Know them better."],
        "sub": "Read from both your birth charts.",
        "pills": [["Love language", "Communication"], ["In conflict", "What to try"]],
    },
    {
        "out": "04-desire-map.png",
        "shot": "desire-map.png",
        "headline": ["Find where", "you meet."],
        "sub": "318 questions, answered privately.",
        "pills": [["Relationships", "General", "Manual"],
                  ["Oral", "Intercourse", "Bondage"],
                  ["Roleplay", "Toys", "+ 15 more"]],
    },
]


def pill(text, size=None):
    f = sans(size or s(46), 600)
    b = ImageDraw.Draw(Image.new("RGB", (10, 10))).textbbox((0, 0), text, font=f)
    px, py = s(38), s(24)
    w, h = b[2] - b[0] + px * 2, b[3] - b[1] + py * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w, h], h // 2, fill=(247, 241, 232, 38))
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, outline=(247, 241, 232, 110), width=2)
    d.text((px - b[0], py - b[1]), text, font=f, fill=CREAM)
    return img


def build(spec):
    src = SHOTS / spec["shot"]
    if not src.exists():
        print(f"  SKIP {spec['out']} — missing {src.relative_to(ROOT)}")
        return False

    canvas = background(W, H)
    d = ImageDraw.Draw(canvas)

    y = int(H * 0.065)
    f = sans(s(104), 700)
    for line in spec["headline"]:
        b = d.textbbox((0, 0), line, font=f)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], y - b[1]), line, font=f, fill=CREAM)
        y += s(126)

    if spec.get("sub"):
        fs = sans(s(60), 400)
        b = d.textbbox((0, 0), spec["sub"], font=fs)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], y + s(26) - b[1]), spec["sub"], font=fs, fill=SAND)
        y += s(26) + (b[3] - b[1])

    if spec.get("pills"):
        y += s(56)
        for row in spec["pills"]:
            imgs = [pill(t) for t in row]
            total = sum(i.size[0] for i in imgs) + s(18) * (len(imgs) - 1)
            x = (W - total) // 2
            for i in imgs:
                canvas.paste(i, (x, y), i)
                x += i.size[0] + s(18)
            y += imgs[0].size[1] + s(18)

    # Size the device to the space left over, so the tab bar stays in
    # frame rather than bleeding off the bottom edge.
    dy = y + s(70)
    avail = H - s(70) - dy
    ratio = Image.open(src).size[1] / Image.open(src).size[0]
    dev = device(src, int(min(W * 0.70, avail / (ratio + 0.044))))
    x = (W - dev.size[0]) // 2

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x + s(8), dy + s(26), x + dev.size[0] + s(8), dy + dev.size[1] + s(26)],
        int(W * 0.07), fill=(0, 0, 0, 130))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(s(46))))
    canvas.paste(dev, (x, dy), dev)

    dest = OUT / f"{W}x{H}"
    dest.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(dest / spec["out"], quality=92)
    return True


if __name__ == "__main__":
    if not SHOTS.exists():
        sys.exit(f"No {SHOTS.relative_to(ROOT)}/ — put your captures there first.")
    for size in SIZES:
        W, H = size
        globals()["W"], globals()["H"] = W, H
        built = sum(build(p) for p in PANELS)
        print(f"  {W}x{H}: {built}/{len(PANELS)} panels")

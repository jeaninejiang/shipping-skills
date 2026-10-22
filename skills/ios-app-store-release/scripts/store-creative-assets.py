#!/usr/bin/env python3
"""Build the App Store product-page header and search-results assets.

These are the landscape "creative assets" — the banner across the top of
the product page, and the image beside the app in search. Both are
optional and only render on iOS 27+, so nothing here blocks a
submission.

    pip install pillow numpy
    python3 scripts/store-creative-assets.py

Reads captures from screenshots/, writes to screenshots/creative/.

Sizes come straight from Apple's creative-assets spec: the header takes
21:9 at 3840x1646 or 16:9 at 5244x2950 (PNG only), and search results
takes 3:2 between 1920x1280 and 3840x2560. The 16:9 file is accepted in
both slots, which is what the "Use header asset in search results"
option in App Store Connect wants.

Apple crops these differently across devices, so everything is laid out
in fractions of the canvas and nothing load-bearing goes near an edge.
Transparency is not allowed, hence the flatten on save.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import sys

from brandkit import CREAM, SAND, background, centred_text, device, sans, wordmark

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
OUT = SHOTS / "creative"

ASSETS = [
    {
        "out": "header-21x9-3840x1646.png",
        "size": (3840, 1646),
        "layout": "banner",
        "headline": ["Find where your", "desires meet."],
        "sub": "A private app for two.",
        "shots": ["desire-map.png", "home.png"],
    },
    {
        "out": "header-16x9-5244x2950.png",
        "size": (5244, 2950),
        "layout": "banner",
        "headline": ["Find where your", "desires meet."],
        "sub": "A private app for two.",
        "shots": ["desire-map.png", "home.png"],
    },
    {
        # Small on screen, so it carries less: the mark, one line, and
        # enough of the app to show what kind of thing it is.
        "out": "search-3x2-3840x2560.png",
        "size": (3840, 2560),
        "layout": "centred",
        "headline": ["Know each other better."],
        "sub": "Desire maps and birth charts, for two.",
        "shots": ["home.png", "desire-map.png", "chart-reading.png"],
    },
]


def shadow_under(canvas, box, radius, blur):
    """A soft drop shadow behind a device, composited into `canvas`."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=(0, 0, 0, 130))
    return Image.alpha_composite(canvas, layer.filter(ImageFilter.GaussianBlur(blur)))


def place(canvas, path, width, right=None, left=None, bottom=None):
    """Drop a framed capture on the canvas, anchored by edge rather than
    by top-left, so a device can bleed off the bottom without the caller
    doing the arithmetic. Returns its frame box."""
    dev = device(path, width)
    x = (right - dev.size[0]) if right is not None else left
    y = bottom - dev.size[1]
    canvas = shadow_under(
        canvas,
        [x + width * 0.012, y + width * 0.035,
         x + dev.size[0] + width * 0.012, y + dev.size[1] + width * 0.035],
        int(width * 0.105), int(width * 0.062),
    )
    canvas.paste(dev, (int(x), int(y)), dev)
    return canvas, (x, y, dev.size[0], dev.size[1])


def text_block(canvas, spec, w, h, left, centre_y, col_w):
    """Wordmark, headline, sub — stacked and vertically centred on
    `centre_y`. Measured first so the block centres as a unit."""
    mark = wordmark(int(h * 0.105))
    f_head, f_sub = sans(int(h * 0.075), 700), sans(int(h * 0.042), 400)
    rule = ImageDraw.Draw(canvas)

    line_h = int(h * 0.075 * 1.18)
    total = mark.size[1] + int(h * 0.036) + line_h * len(spec["headline"])
    if spec.get("sub"):
        total += int(h * 0.024) + (rule.textbbox((0, 0), spec["sub"], font=f_sub)[3]
                                   - rule.textbbox((0, 0), spec["sub"], font=f_sub)[1])

    y = int(centre_y - total / 2)
    canvas.paste(mark, (left, y), mark)
    y += mark.size[1] + int(h * 0.036)

    for line in spec["headline"]:
        b = rule.textbbox((0, 0), line, font=f_head)
        rule.text((left - b[0], y - b[1]), line, font=f_head, fill=CREAM)
        y += line_h

    if spec.get("sub"):
        y += int(h * 0.024) - line_h + int(h * 0.075 * 1.0)
        b = rule.textbbox((0, 0), spec["sub"], font=f_sub)
        rule.text((left - b[0], y - b[1]), spec["sub"], font=f_sub, fill=SAND)
    return canvas


def banner(spec, w, h):
    """Wide and short: type on the left, two devices bleeding off the
    bottom right. The shape the product-page header is cropped to."""
    canvas = background(w, h)
    pad = int(w * 0.068)

    # Sized off the HEIGHT, not the width. A phone is tall, so scaling it
    # by canvas width leaves a taller canvas (16:9 beside 21:9) with a
    # band of dead purple under the type and devices that look undersized.
    front_w, back_w = int(h * 0.44), int(h * 0.37)
    front_x = w - pad - int(front_w * 1.044)

    canvas, back = place(canvas, SHOTS / spec["shots"][1], back_w,
                         right=front_x + int(back_w * 1.044 * 0.38),
                         bottom=h + h * 0.035)
    canvas, _ = place(canvas, SHOTS / spec["shots"][0], front_w,
                      right=w - pad, bottom=h + h * 0.10)

    return text_block(canvas, spec, w, h, pad, h * 0.5, back[0] - pad - int(w * 0.02))


def centred(spec, w, h):
    """Squarer: type across the top, a row of devices bleeding off the
    bottom. Reads better than a side-by-side at search-result size."""
    canvas = background(w, h)
    rule = ImageDraw.Draw(canvas)
    cx = w // 2

    mark = wordmark(int(h * 0.085))
    canvas.paste(mark, (cx - mark.size[0] // 2, int(h * 0.085)), mark)
    y = int(h * 0.085) + mark.size[1] + int(h * 0.055)

    f_head = sans(int(h * 0.062), 700)
    for line in spec["headline"]:
        y = centred_text(rule, line, f_head, cx, y, CREAM) + int(h * 0.018)

    if spec.get("sub"):
        y = centred_text(rule, spec["sub"], sans(int(h * 0.034), 400), cx,
                         y + int(h * 0.012), SAND)

    n = len(spec["shots"])
    dev_w, gap = int(w * 0.215), int(w * 0.018)
    span = n * (dev_w + int(dev_w * 0.044)) + gap * (n - 1)
    x = (w - span) // 2
    for shot in spec["shots"]:
        canvas, box = place(canvas, SHOTS / shot, dev_w, left=x, bottom=h + h * 0.14)
        x += box[2] + gap
    return canvas


def build(spec):
    missing = [s for s in spec["shots"] if not (SHOTS / s).exists()]
    if missing:
        print(f"  SKIP {spec['out']} — missing {', '.join(missing)}")
        return False

    w, h = spec["size"]
    canvas = (banner if spec["layout"] == "banner" else centred)(spec, w, h)

    # Apple rejects an alpha channel on these, so flatten rather than
    # just dropping the band.
    flat = Image.new("RGB", canvas.size, (0, 0, 0))
    flat.paste(canvas, (0, 0), canvas)

    OUT.mkdir(parents=True, exist_ok=True)
    flat.save(OUT / spec["out"])
    print(f"  {spec['out']}  {w}x{h}")
    return True


if __name__ == "__main__":
    if not SHOTS.exists():
        sys.exit(f"No {SHOTS.relative_to(ROOT)}/ — put your captures there first.")
    built = sum(build(a) for a in ASSETS)
    print(f"  {built}/{len(ASSETS)} assets → {OUT.relative_to(ROOT)}/")

"""Shared brand drawing for the App Store image scripts.

`store-screenshots.py` makes the portrait screenshot panels;
`store-creative-assets.py` makes the landscape header and search-result
assets. Both need the same gradient, the same type and the same device
frame, and the two had started to diverge — hence this module.

Everything here takes explicit sizes rather than reading globals, so a
caller can render at any canvas size.

    pip install pillow numpy
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

HERE = Path(__file__).resolve().parent

# ── Everything in this block is yours to change ───────────────────────
#
# Palette. Lift these from wherever your app's colours actually live —
# a Colors.swift, a tailwind config — rather than eyedropping a
# screenshot, so the store imagery cannot drift from the product.
PURPLE_DEEP, PURPLE_LIGHT = (59, 31, 94), (168, 125, 212)
EMERALD_DEEP = (26, 74, 58)
CREAM, SAND = (247, 241, 232), (200, 184, 162)

# Fonts. BODY_FONT sets headlines and labels. DISPLAY_FONT is the face
# your wordmark is set in, which is often licensed and not
# redistributable — so point at your own copy rather than committing
# one here. Either can be overridden without editing this file:
#
#   BRANDKIT_BODY_FONT=/path/to/Body.ttf \
#   BRANDKIT_DISPLAY_FONT=/path/to/Display.otf \
#   python3 store-screenshots.py
#
# No fonts configured at all still renders, via Pillow's default — ugly,
# but it proves the pipeline before you go hunting for files.
BODY_FONT = Path(os.environ.get("BRANDKIT_BODY_FONT", HERE / "DMSans.ttf"))
_display = os.environ.get("BRANDKIT_DISPLAY_FONT", "")
DISPLAY_FONT = Path(_display) if _display else None

# The wordmark text, and the OpenType stylistic set that selects its
# alternate glyphs if the face has any. Empty list = plain rendering.
WORDMARK_TEXT = "YourApp"
WORDMARK_FEATURES = ["ss01"]
# ──────────────────────────────────────────────────────────────────────


def _truetype(path, size):
    """Load a font, falling back to Pillow's default rather than raising
    — a missing font should degrade the look, not stop the run."""
    try:
        return ImageFont.truetype(str(path), size)
    except (OSError, TypeError):
        return ImageFont.load_default(size)


def sans(size, weight=700):
    f = _truetype(BODY_FONT, size)
    try:
        f.set_variation_by_axes([14, weight])   # opsz, wght
    except Exception:
        pass                                    # static cut or default, fine
    return f


def wordmark(height, color=CREAM, text=None, features=None):
    """Your wordmark as RGBA, `height` pixels of actual ink tall.

    Stylistic sets (`ss01` and friends) are what make a wordmark the
    brand mark rather than just the font — a swash capital, say. They
    need Pillow built with Raqm; check `PIL.features.check("raqm")`,
    and if it is False the text still renders, just without the
    alternates.

    Sizing is the fiddly part. A display glyph routinely reaches
    outside its layout box — in the face this was written for, at 200pt
    the advance was 421px while the bounding box ran from -36 to 173.
    Measure by the advance and you clip the flourish; measure by the
    box and position by the advance and you get a gap. So: size the
    canvas from the bounding box, then draw at its negated origin.
    """
    text = text if text is not None else WORDMARK_TEXT
    features = features if features is not None else WORDMARK_FEATURES
    face = DISPLAY_FONT or BODY_FONT

    rule = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    probe = _truetype(face, 200)

    # Stylistic sets need the Raqm layout engine, and the test that
    # matters is per-FONT, not per-installation: Pillow may well be
    # built with Raqm while this particular face is not using it —
    # `load_default()`, our no-font fallback, pins itself to BASIC. Ask
    # the font, and pass `features` only if it can honour them;
    # otherwise Pillow raises rather than ignoring them.
    kw = {}
    if features and getattr(probe, "layout_engine", None) == ImageFont.Layout.RAQM:
        kw = {"features": features}

    b = rule.textbbox((0, 0), text, font=probe, **kw)
    size = max(8, round(200 * height / max(1, b[3] - b[1])))

    font = _truetype(face, size)
    b = rule.textbbox((0, 0), text, font=font, **kw)
    pad = 2
    img = Image.new("RGBA", (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text(
        (pad - b[0], pad - b[1]), text, font=font, fill=color, **kw
    )
    return img


def background(w, h):
    """Purple.deep under two soft radial washes — the same treatment the
    a marketing site hero uses, so the listing and the site read as one
    brand rather than two."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    base = np.zeros((h, w, 3), np.float32) + np.array(PURPLE_DEEP, np.float32)
    for cx, cy, rad, col, strength in [
        (0.18 * w, 0.72 * h, 0.80 * w, PURPLE_LIGHT, 0.40),
        (0.90 * w, 0.18 * h, 0.62 * w, EMERALD_DEEP, 0.42),
    ]:
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / rad
        base += (np.clip(1 - d, 0, 1) ** 2 * strength)[..., None] * (
            np.array(col, np.float32) - base)
    return Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *img.size], radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def device(path, width):
    """A screen capture in a plain dark bezel.

    Drawn rather than a photoreal iPhone on purpose: App Review is
    touchier about screenshots depicting specific hardware, and a generic
    rounded frame avoids the question entirely.
    """
    shot = Image.open(path).convert("RGB")
    h = int(width * shot.size[1] / shot.size[0])
    shot = rounded(shot.resize((width, h), Image.LANCZOS), int(width * 0.085))
    bez = int(width * 0.022)
    frame = Image.new("RGBA", (width + bez * 2, h + bez * 2), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        [0, 0, *frame.size], int(width * 0.105), fill=(18, 14, 24, 255))
    frame.paste(shot, (bez, bez), shot)
    return frame


def centred_text(draw, text, font, cx, top, fill):
    """Draw `text` horizontally centred on `cx`, its ink starting at `top`.
    Returns the y the next line should start at."""
    b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (b[2] - b[0]) // 2 - b[0], top - b[1]), text, font=font, fill=fill)
    return top + (b[3] - b[1])

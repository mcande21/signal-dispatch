#!/usr/bin/env python3
"""
Signal Dispatch -- Profile Picture Final
Signal Pulse concept, research-driven refinement:
  - 3 arcs max (fewer survives small sizes)
  - Heavy stroke weight (8-12px at 512px master, scaled)
  - Strong center dot with amber glow/bloom
  - Amber gradient: inner brightest, outer fades
  - Origin at bottom-left quadrant (~37%, 62%)
  - Dark navy circular background (#0A0F1A)
  - No text
  - 512px master, scaled to 256/96/48/32 test sizes
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MASTER_SIZE = 512
RENDER_SIZE = 1024  # 2x supersampling for anti-alias

# Colors
NAVY = (10, 15, 26)          # #0A0F1A background
AMBER = (212, 133, 58)       # #D4853A arc color (alpha varies)
DOT_WHITE = (240, 237, 232)  # #F0EDE8 center dot

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Arc geometry
# ---------------------------------------------------------------------------

# Origin point as fractions of the render canvas
ORIGIN_X_FRAC = 0.37
ORIGIN_Y_FRAC = 0.62

# Arc sweep: start angle (degrees), sweep span (degrees)
# 0 = east, -90 = north; we want arcs sweeping upper-right
ARC_START = -140   # starts slightly past north going clockwise
ARC_SPAN  = 120    # covers upper-right quadrant sweep

# Three arcs: (radius_frac_of_W, alpha_0_to_255)
# Inner brightest, outer fades
ARCS = [
    (0.20, 255),   # inner -- full amber
    (0.38, 178),   # middle -- ~70% opacity
    (0.58, 102),   # outer  -- ~40% opacity
]

# Stroke weight: 3% of render canvas -- thick enough to survive 32px
STROKE_WEIGHT_FRAC = 0.045

# Center dot
DOT_RADIUS_FRAC   = 0.030   # crisp white dot
GLOW_RADIUS_FRAC  = 0.075   # soft amber glow behind dot
GLOW_BLUR_FRAC    = 0.040   # gaussian blur radius for glow
GLOW_ALPHA        = 140     # glow intensity

# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


def build_image() -> Image.Image:
    W = RENDER_SIZE

    # Base canvas: solid navy
    base = Image.new("RGBA", (W, W), (*NAVY, 255))

    ox = int(W * ORIGIN_X_FRAC)
    oy = int(W * ORIGIN_Y_FRAC)

    stroke = max(1, int(W * STROKE_WEIGHT_FRAC))

    # --- Layer: arcs ---
    arc_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    arc_draw = ImageDraw.Draw(arc_layer)

    for r_frac, alpha in ARCS:
        r = int(W * r_frac)
        bbox = (ox - r, oy - r, ox + r, oy + r)
        arc_draw.arc(
            bbox,
            start=ARC_START,
            end=ARC_START + ARC_SPAN,
            fill=(*AMBER, alpha),
            width=stroke,
        )

    base = Image.alpha_composite(base, arc_layer)

    # --- Layer: glow bloom behind center dot ---
    glow_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    gr = int(W * GLOW_RADIUS_FRAC)
    glow_draw.ellipse(
        (ox - gr, oy - gr, ox + gr, oy + gr),
        fill=(*AMBER, GLOW_ALPHA),
    )
    blur_r = int(W * GLOW_BLUR_FRAC)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=blur_r))
    base = Image.alpha_composite(base, glow_layer)

    # --- Layer: crisp white center dot ---
    dot_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dot_draw = ImageDraw.Draw(dot_layer)
    dr = int(W * DOT_RADIUS_FRAC)
    dot_draw.ellipse(
        (ox - dr, oy - dr, ox + dr, oy + dr),
        fill=(*DOT_WHITE, 255),
    )
    base = Image.alpha_composite(base, dot_layer)

    return base


def apply_circle_mask(img: Image.Image) -> Image.Image:
    """Hard circle mask -- everything outside is transparent."""
    W = img.size[0]
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, W - 1, W - 1), fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def scale_to(img: Image.Image, size: int) -> Image.Image:
    """Downscale from RENDER_SIZE to target size with LANCZOS."""
    return img.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"Rendering at {RENDER_SIZE}x{RENDER_SIZE} (2x supersampling)...")
    render = build_image()

    # Apply circle mask at render resolution for clean edges
    render_masked = apply_circle_mask(render)

    # Scale to master (512) and test sizes
    outputs = [
        (MASTER_SIZE, "profile-final.png"),
        (256,         "profile-final-256.png"),
        (96,          "profile-final-96.png"),
        (48,          "profile-final-48.png"),
        (32,          "profile-final-32.png"),
    ]

    for size, filename in outputs:
        img = scale_to(render_masked, size)
        path = os.path.join(OUT_DIR, filename)
        img.save(path, "PNG")
        print(f"  Saved {size}x{size}: {path}")

    print("\nDone. Open profile-final-32.png and squint -- bright dot with arc hints = pass.")


if __name__ == "__main__":
    main()

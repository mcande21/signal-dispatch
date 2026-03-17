#!/usr/bin/env python3
"""
Signal Dispatch -- Profile Picture v2
Redesigned with frontend-design critique applied:
  - Differentiate from WiFi icon (varying arc spans, staggered spacing)
  - Background radial gradient for depth
  - Stronger glow bloom
  - Progressive arc spacing (inner tighter, outer wider)
  - Rounded arc ends via overlapping circles at endpoints
  - Subtle noise texture
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

MASTER_SIZE = 512
RENDER_SIZE = 2048  # 4x supersampling for premium anti-alias

# Colors
NAVY_CENTER = (14, 20, 36)     # Slightly lighter center for radial gradient
NAVY_EDGE = (8, 12, 22)        # Darker edges
AMBER = (212, 133, 58)         # #D4853A
AMBER_HOT = (235, 155, 70)     # Brighter variant for inner arc
DOT_WHITE = (240, 237, 232)    # #F0EDE8

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Origin point
ORIGIN_X_FRAC = 0.36
ORIGIN_Y_FRAC = 0.63

# Three arcs with PROGRESSIVE spacing (inner tight, outer wide)
# and VARYING sweep angles (inner shorter, outer longer -- more dynamic)
ARCS = [
    # (radius_frac, alpha, sweep_start, sweep_span, color)
    (0.13, 255, -120, 85, AMBER_HOT),     # innermost -- tight to dot, short punch
    (0.23, 240, -130, 100, AMBER_HOT),    # inner -- builds outward
    (0.35, 200, -140, 115, AMBER),         # middle
    (0.48, 140, -148, 130, AMBER),         # outer-mid
    (0.62, 80, -155, 142, AMBER),          # outer -- widest, most faded
]

STROKE_WEIGHT_FRAC = 0.038

# Center dot
DOT_RADIUS_FRAC = 0.032
GLOW_RADIUS_FRAC = 0.10     # Bigger glow
GLOW_BLUR_FRAC = 0.055      # More blur spread
GLOW_ALPHA = 200             # Much stronger glow

# Second glow layer -- wide, faint amber wash
WASH_RADIUS_FRAC = 0.22
WASH_BLUR_FRAC = 0.12
WASH_ALPHA = 50


def draw_radial_gradient(img, center, color_center, color_edge, radius):
    """Draw a radial gradient from center color to edge color."""
    draw = ImageDraw.Draw(img)
    cx, cy = center
    for r in range(radius, 0, -1):
        t = r / radius  # 1.0 at edge, 0.0 at center
        color = tuple(
            int(color_center[i] + (color_edge[i] - color_center[i]) * t)
            for i in range(3)
        )
        draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            fill=(*color, 255)
        )


def draw_rounded_arc(draw, center, radius, start_deg, span_deg, color, width):
    """Draw an arc -- clean termination, no endpoint caps."""
    ox, oy = center
    bbox = (ox - radius, oy - radius, ox + radius, oy + radius)
    draw.arc(bbox, start=start_deg, end=start_deg + span_deg,
             fill=color, width=width)


def add_noise_texture(img, intensity=8, opacity=0.03):
    """Add subtle film grain / noise texture."""
    W = img.size[0]
    noise = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    pixels = noise.load()
    random.seed(42)  # Reproducible
    for y in range(0, W, 2):  # Every other pixel for performance
        for x in range(0, W, 2):
            v = random.randint(-intensity, intensity)
            a = int(abs(v) * opacity * 255)
            c = 128 + v
            pixels[x, y] = (c, c, c, a)
    return Image.alpha_composite(img, noise)


def build_image() -> Image.Image:
    W = RENDER_SIZE

    # --- Background: radial gradient for depth ---
    base = Image.new("RGBA", (W, W), (*NAVY_EDGE, 255))
    ox = int(W * ORIGIN_X_FRAC)
    oy = int(W * ORIGIN_Y_FRAC)

    # Radial gradient centered on origin point
    gradient_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw_radial_gradient(gradient_layer, (ox, oy), NAVY_CENTER, NAVY_EDGE,
                         int(W * 0.7))
    base = Image.alpha_composite(base, gradient_layer)

    stroke = max(1, int(W * STROKE_WEIGHT_FRAC))

    # --- Layer: arcs with rounded ends ---
    arc_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    arc_draw = ImageDraw.Draw(arc_layer)

    for r_frac, alpha, start, span, color in ARCS:
        r = int(W * r_frac)
        draw_rounded_arc(arc_draw, (ox, oy), r, start, span,
                         (*color, alpha), stroke)

    base = Image.alpha_composite(base, arc_layer)

    # --- Layer: wide ambient wash ---
    wash_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash_layer)
    wr = int(W * WASH_RADIUS_FRAC)
    wash_draw.ellipse(
        (ox - wr, oy - wr, ox + wr, oy + wr),
        fill=(*AMBER, WASH_ALPHA),
    )
    wash_blur = int(W * WASH_BLUR_FRAC)
    wash_layer = wash_layer.filter(ImageFilter.GaussianBlur(radius=wash_blur))
    base = Image.alpha_composite(base, wash_layer)

    # --- Layer: glow bloom behind center dot ---
    glow_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    gr = int(W * GLOW_RADIUS_FRAC)
    glow_draw.ellipse(
        (ox - gr, oy - gr, ox + gr, oy + gr),
        fill=(*AMBER_HOT, GLOW_ALPHA),
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

    # --- Noise texture for depth ---
    base = add_noise_texture(base, intensity=10, opacity=0.025)

    return base


def apply_circle_mask(img: Image.Image) -> Image.Image:
    W = img.size[0]
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, W - 1, W - 1), fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def scale_to(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.LANCZOS)


def main():
    print(f"Rendering at {RENDER_SIZE}x{RENDER_SIZE} (4x supersampling)...")
    render = build_image()
    render_masked = apply_circle_mask(render)

    outputs = [
        (MASTER_SIZE, "profile-final.png"),
        (256, "profile-final-256.png"),
        (96, "profile-final-96.png"),
        (48, "profile-final-48.png"),
        (32, "profile-final-32.png"),
    ]

    for size, filename in outputs:
        img = scale_to(render_masked, size)
        path = os.path.join(OUT_DIR, filename)
        img.save(path, "PNG")
        print(f"  Saved {size}x{size}: {path}")

    print("\nDone.")


if __name__ == "__main__":
    main()

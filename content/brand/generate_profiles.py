#!/usr/bin/env python3
"""
Signal Dispatch -- Profile Picture Generator
Produces three 256x256 brand profile images for Substack.
"""

import math
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIZE = 256
NAVY = (10, 15, 26)
OFF_WHITE = (240, 237, 232)
AMBER = (212, 133, 58)
AMBER_DIM = (212, 133, 58, 80)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(OUT_DIR, "BebasNeue-Regular.ttf")
FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
)

# ---------------------------------------------------------------------------
# Font download
# ---------------------------------------------------------------------------


def ensure_font() -> str:
    if not os.path.exists(FONT_PATH):
        print(f"Downloading Bebas Neue from GitHub...")
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        print(f"Saved to {FONT_PATH}")
    else:
        print(f"Font already present: {FONT_PATH}")
    return FONT_PATH


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def make_canvas(bg=NAVY) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """4x supersampled canvas for anti-aliasing; caller scales down."""
    scale = 4
    w = SIZE * scale
    img = Image.new("RGBA", (w, w), (*bg, 255))
    draw = ImageDraw.Draw(img)
    return img, draw, scale


def apply_circle_mask(img: Image.Image) -> Image.Image:
    """Crop to a soft circle so nothing bleeds outside the Substack crop."""
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, img.size[0] - 1, img.size[1] - 1), fill=255)
    img.putalpha(mask)
    return img


def finalise(img: Image.Image, scale: int) -> Image.Image:
    """Downscale with LANCZOS, then apply circle mask."""
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img = apply_circle_mask(img)
    return img


# ---------------------------------------------------------------------------
# V1 -- "SD" Monogram
# ---------------------------------------------------------------------------


def make_v1(font_path: str) -> Image.Image:
    scale = 4
    W = SIZE * scale
    img = Image.new("RGBA", (W, W), (*NAVY, 255))
    draw = ImageDraw.Draw(img)

    # Amber accent ring (thin, just inside edge)
    ring_pad = int(W * 0.04)
    ring_w = max(2, int(W * 0.012))
    draw.ellipse(
        (ring_pad, ring_pad, W - ring_pad, W - ring_pad),
        outline=(*AMBER, 200),
        width=ring_w,
    )

    # Load font at large size
    font_size = int(W * 0.52)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "SD"

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Center with slight upward nudge for optical balance
    cx = (W - tw) // 2 - bbox[0]
    cy = (W - th) // 2 - bbox[1] - int(W * 0.02)

    # Drop shadow (subtle)
    shadow_offset = int(W * 0.012)
    draw.text(
        (cx + shadow_offset, cy + shadow_offset),
        text,
        font=font,
        fill=(0, 0, 0, 120),
    )

    # Main lettermark
    draw.text((cx, cy), text, font=font, fill=(*OFF_WHITE, 255))

    # Amber underline accent bar
    bar_y = cy + th + int(W * 0.02)
    bar_w = int(tw * 0.55)
    bar_h = max(3, int(W * 0.018))
    bar_x = cx + (tw - bar_w) // 2
    draw.rectangle(
        (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
        fill=(*AMBER, 255),
    )

    return finalise(img, scale)


# ---------------------------------------------------------------------------
# V2 -- Signal Pulse
# ---------------------------------------------------------------------------


def make_v2() -> Image.Image:
    scale = 4
    W = SIZE * scale
    img = Image.new("RGBA", (W, W), (*NAVY, 255))

    # Work on a separate RGBA layer for compositing arcs
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    cx = W // 2
    # Anchor point slightly left of center and down for dynamic feel
    ox = int(W * 0.35)
    oy = int(W * 0.62)

    # Arc parameters: (radius_fraction_of_W, alpha, arc_degrees_span, start_angle)
    arcs = [
        (0.10, 230, 110, -100),
        (0.18, 190, 110, -100),
        (0.27, 150, 110, -100),
        (0.37, 110, 110, -100),
        (0.48, 75,  110, -100),
        (0.60, 45,  110, -100),
    ]

    arc_width = max(4, int(W * 0.022))

    for r_frac, alpha, span, start in arcs:
        r = int(W * r_frac)
        x0, y0 = ox - r, oy - r
        x1, y1 = ox + r, oy + r
        draw.arc(
            (x0, y0, x1, y1),
            start=start,
            end=start + span,
            fill=(*AMBER, alpha),
            width=arc_width,
        )

    # Origin dot
    dot_r = int(W * 0.025)
    draw.ellipse(
        (ox - dot_r, oy - dot_r, ox + dot_r, oy + dot_r),
        fill=(*OFF_WHITE, 255),
    )

    # Bright inner halo on dot
    halo_r = int(W * 0.045)
    halo_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo_layer)
    halo_draw.ellipse(
        (ox - halo_r, oy - halo_r, ox + halo_r, oy + halo_r),
        fill=(*AMBER, 60),
    )
    halo_layer = halo_layer.filter(ImageFilter.GaussianBlur(radius=int(W * 0.02)))

    img = Image.alpha_composite(img, halo_layer)
    img = Image.alpha_composite(img, layer)

    return finalise(img, scale)


# ---------------------------------------------------------------------------
# V3 -- Data Grid / Crosshair
# ---------------------------------------------------------------------------


def make_v3(font_path: str) -> Image.Image:
    scale = 4
    W = SIZE * scale
    img = Image.new("RGBA", (W, W), (*NAVY, 255))

    # --- Background grid dots ---
    grid_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid_layer)
    spacing = int(W * 0.08)
    dot_r = max(1, int(W * 0.008))
    for gx in range(0, W + spacing, spacing):
        for gy in range(0, W + spacing, spacing):
            gdraw.ellipse(
                (gx - dot_r, gy - dot_r, gx + dot_r, gy + dot_r),
                fill=(*OFF_WHITE, 22),
            )
    img = Image.alpha_composite(img, grid_layer)

    draw = ImageDraw.Draw(img)
    cx = W // 2
    cy = W // 2

    line_w = max(2, int(W * 0.014))
    amber_full = (*AMBER, 255)
    amber_dim = (*AMBER, 140)

    # -- Outer circle --
    outer_r = int(W * 0.40)
    draw.ellipse(
        (cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r),
        outline=amber_full,
        width=line_w,
    )

    # -- Inner circle --
    inner_r = int(W * 0.22)
    draw.ellipse(
        (cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r),
        outline=amber_dim,
        width=max(1, line_w - 1),
    )

    # -- Cross lines (H & V), gap in the center for the text --
    gap = int(W * 0.16)
    cross_extend = outer_r + int(W * 0.06)

    # Horizontal
    draw.line((cx - cross_extend, cy, cx - gap, cy), fill=amber_full, width=line_w)
    draw.line((cx + gap, cy, cx + cross_extend, cy), fill=amber_full, width=line_w)
    # Vertical
    draw.line((cx, cy - cross_extend, cx, cy - gap), fill=amber_full, width=line_w)
    draw.line((cx, cy + gap, cx, cy + cross_extend), fill=amber_full, width=line_w)

    # -- Tick marks on outer circle at cardinal points --
    tick_len = int(W * 0.05)
    tick_w = max(2, int(W * 0.01))
    for angle_deg in (0, 90, 180, 270):
        angle = math.radians(angle_deg)
        ix = cx + int(outer_r * math.cos(angle))
        iy = cy + int(outer_r * math.sin(angle))
        ox2 = cx + int((outer_r + tick_len) * math.cos(angle))
        oy2 = cy + int((outer_r + tick_len) * math.sin(angle))
        draw.line((ix, iy, ox2, oy2), fill=amber_full, width=tick_w)

    # -- Center dot --
    dot_r = max(3, int(W * 0.018))
    draw.ellipse(
        (cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r),
        fill=(*AMBER, 255),
    )

    # -- "SD" text centered --
    font_size = int(W * 0.24)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "SD"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = cx - tw // 2 - bbox[0]
    ty = cy - th // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=(*OFF_WHITE, 255))

    return finalise(img, scale)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    font_path = ensure_font()

    print("Generating V1 -- SD Monogram...")
    v1 = make_v1(font_path)
    v1_path = os.path.join(OUT_DIR, "profile-v1.png")
    v1.save(v1_path, "PNG")
    print(f"  Saved: {v1_path}")

    print("Generating V2 -- Signal Pulse...")
    v2 = make_v2()
    v2_path = os.path.join(OUT_DIR, "profile-v2.png")
    v2.save(v2_path, "PNG")
    print(f"  Saved: {v2_path}")

    print("Generating V3 -- Data Grid / Crosshair...")
    v3 = make_v3(font_path)
    v3_path = os.path.join(OUT_DIR, "profile-v3.png")
    v3.save(v3_path, "PNG")
    print(f"  Saved: {v3_path}")

    print("\nAll three profiles generated.")


if __name__ == "__main__":
    main()

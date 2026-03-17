#!/usr/bin/env python3
"""
Signal Dispatch -- Fractal Profile Concepts

Three fractal-based profile picture concepts:
  V1: Golden Spiral -- Fibonacci spiral emanating from origin, mathematical elegance
  V2: Julia Set -- Organic fractal structure in amber on navy, alien intelligence feel
  V3: Phyllotaxis -- Sunflower seed pattern, data-as-nature, dots radiating outward
"""

import math
import os
import random
import colorsys

from PIL import Image, ImageDraw, ImageFilter

RENDER_SIZE = 2048
MASTER_SIZE = 512

NAVY_CENTER = (14, 20, 36)
NAVY_EDGE = (8, 12, 22)
AMBER = (212, 133, 58)
AMBER_HOT = (235, 155, 70)
AMBER_BRIGHT = (255, 180, 90)
DOT_WHITE = (240, 237, 232)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio


def apply_circle_mask(img):
    W = img.size[0]
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, W - 1, W - 1), fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def scale_to(img, size):
    return img.resize((size, size), Image.LANCZOS)


def add_noise(img, intensity=8, opacity=0.025):
    W = img.size[0]
    noise = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    pixels = noise.load()
    random.seed(42)
    for y in range(0, W, 3):
        for x in range(0, W, 3):
            v = random.randint(-intensity, intensity)
            a = int(abs(v) * opacity * 255)
            c = 128 + v
            pixels[x, y] = (c, c, c, a)
    return Image.alpha_composite(img, noise)


# ---------------------------------------------------------------------------
# V1: Golden Spiral
# ---------------------------------------------------------------------------

def build_golden_spiral():
    W = RENDER_SIZE
    base = Image.new("RGBA", (W, W), (*NAVY_EDGE, 255))

    # Radial gradient background
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = int(W * 0.42), int(W * 0.55)
    for r in range(int(W * 0.6), 0, -2):
        t = r / (W * 0.6)
        c = tuple(int(NAVY_CENTER[i] + (NAVY_EDGE[i] - NAVY_CENTER[i]) * t) for i in range(3))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, 255))
    base = Image.alpha_composite(base, grad)

    # Draw golden spiral as a series of connected points
    spiral_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spiral_layer)

    # Spiral parameters -- emanating from slightly off-center
    origin_x, origin_y = int(W * 0.42), int(W * 0.55)
    a = 8.0       # initial radius
    b = 0.18      # growth rate (logarithmic spiral: r = a * e^(b*theta))

    points = []
    for i in range(800):
        theta = i * 0.04
        r = a * math.exp(b * theta)
        if r > W * 0.48:
            break
        x = origin_x + r * math.cos(theta)
        y = origin_y - r * math.sin(theta)
        points.append((x, y, theta, r))

    # Draw spiral with varying thickness and opacity
    for i in range(1, len(points)):
        x1, y1, t1, r1 = points[i - 1]
        x2, y2, t2, r2 = points[i]

        # Progress along spiral (0 to 1)
        progress = i / len(points)

        # Thickness increases outward
        width = max(2, int(4 + progress * 35))

        # Alpha: bright in the middle, fade at both ends
        if progress < 0.15:
            alpha = int(255 * (progress / 0.15))
        elif progress > 0.8:
            alpha = int(255 * ((1 - progress) / 0.2))
        else:
            alpha = 255

        # Color: hotter near center, standard amber outward
        if progress < 0.3:
            color = AMBER_BRIGHT
        elif progress < 0.6:
            color = AMBER_HOT
        else:
            color = AMBER

        sd.line([(x1, y1), (x2, y2)], fill=(*color, alpha), width=width)

    base = Image.alpha_composite(base, spiral_layer)

    # Glow at origin
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(W * 0.08)
    gd.ellipse((origin_x - gr, origin_y - gr, origin_x + gr, origin_y + gr),
               fill=(*AMBER_HOT, 180))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W * 0.045)))
    base = Image.alpha_composite(base, glow)

    # Center dot
    dot = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    dr = int(W * 0.025)
    dd.ellipse((origin_x - dr, origin_y - dr, origin_x + dr, origin_y + dr),
               fill=(*DOT_WHITE, 255))
    base = Image.alpha_composite(base, dot)

    base = add_noise(base)
    return base


# ---------------------------------------------------------------------------
# V2: Julia Set
# ---------------------------------------------------------------------------

def build_julia_set():
    W = RENDER_SIZE
    base = Image.new("RGBA", (W, W), (*NAVY_EDGE, 255))

    # Julia set parameters -- choose c for an interesting shape
    # c = -0.7 + 0.27015j gives a nice connected fractal
    c = complex(-0.7, 0.27015)
    max_iter = 120

    # Render Julia set
    fractal = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    pixels = fractal.load()

    # Map pixel coordinates to complex plane
    x_range = (-1.5, 1.5)
    y_range = (-1.5, 1.5)

    for py in range(0, W, 2):  # Step by 2 for speed, we're downscaling anyway
        for px in range(0, W, 2):
            zx = x_range[0] + (x_range[1] - x_range[0]) * px / W
            zy = y_range[0] + (y_range[1] - y_range[0]) * py / W
            z = complex(zx, zy)

            iteration = 0
            while abs(z) < 4 and iteration < max_iter:
                z = z * z + c
                iteration += 1

            if iteration < max_iter:
                # Color based on escape speed
                t = iteration / max_iter
                # Smooth coloring
                t = math.sqrt(t)

                if t < 0.3:
                    # Deep amber glow near the set boundary
                    alpha = int(255 * (t / 0.3))
                    r = int(AMBER_HOT[0] * (t / 0.3))
                    g = int(AMBER_HOT[1] * (t / 0.3))
                    b = int(AMBER_HOT[2] * (t / 0.3))
                elif t < 0.6:
                    # Full amber
                    alpha = 255
                    blend = (t - 0.3) / 0.3
                    r = int(AMBER_HOT[0] + (AMBER[0] - AMBER_HOT[0]) * blend)
                    g = int(AMBER_HOT[1] + (AMBER[1] - AMBER_HOT[1]) * blend)
                    b = int(AMBER_HOT[2] + (AMBER[2] - AMBER_HOT[2]) * blend)
                else:
                    # Fade to navy
                    fade = (t - 0.6) / 0.4
                    alpha = int(255 * (1 - fade * 0.9))
                    r = int(AMBER[0] * (1 - fade * 0.7))
                    g = int(AMBER[1] * (1 - fade * 0.7))
                    b = int(AMBER[2] * (1 - fade * 0.7))

                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                alpha = max(0, min(255, alpha))

                pixels[px, py] = (r, g, b, alpha)
                # Fill the 2x2 block
                if px + 1 < W:
                    pixels[px + 1, py] = (r, g, b, alpha)
                if py + 1 < W:
                    pixels[px, py + 1] = (r, g, b, alpha)
                if px + 1 < W and py + 1 < W:
                    pixels[px + 1, py + 1] = (r, g, b, alpha)

    base = Image.alpha_composite(base, fractal)
    base = add_noise(base)
    return base


# ---------------------------------------------------------------------------
# V3: Phyllotaxis (Fibonacci Dots)
# ---------------------------------------------------------------------------

def build_phyllotaxis():
    W = RENDER_SIZE
    base = Image.new("RGBA", (W, W), (*NAVY_EDGE, 255))

    # Radial gradient
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = W // 2, W // 2
    for r in range(int(W * 0.5), 0, -2):
        t = r / (W * 0.5)
        c = tuple(int(NAVY_CENTER[i] + (NAVY_EDGE[i] - NAVY_CENTER[i]) * t) for i in range(3))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, 255))
    base = Image.alpha_composite(base, grad)

    # Phyllotaxis: each dot placed at angle = n * golden_angle
    golden_angle = 2 * math.pi / (PHI * PHI)  # ~137.508 degrees
    n_dots = 300
    max_radius = W * 0.44

    dots_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots_layer)

    for n in range(1, n_dots + 1):
        theta = n * golden_angle
        r = max_radius * math.sqrt(n / n_dots)  # Vogel's model

        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)

        # Progress from center (0) to edge (1)
        progress = n / n_dots

        # Dot size: larger near center, smaller at edge
        dot_r = max(2, int(18 - progress * 14))

        # Color: hot amber center, fading outward
        if progress < 0.2:
            color = AMBER_BRIGHT
            alpha = 255
        elif progress < 0.5:
            color = AMBER_HOT
            alpha = int(255 - (progress - 0.2) * 100)
        else:
            color = AMBER
            alpha = int(200 - (progress - 0.5) * 300)
            alpha = max(30, alpha)

        dd.ellipse(
            (int(x - dot_r), int(y - dot_r), int(x + dot_r), int(y + dot_r)),
            fill=(*color, alpha)
        )

    base = Image.alpha_composite(base, dots_layer)

    # Center glow
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(W * 0.1)
    gd.ellipse((cx - gr, cy - gr, cx + gr, cy + gr), fill=(*AMBER_HOT, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W * 0.06)))
    base = Image.alpha_composite(base, glow)

    # Bright center dot
    dot = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dtd = ImageDraw.Draw(dot)
    dr = int(W * 0.028)
    dtd.ellipse((cx - dr, cy - dr, cx + dr, cy + dr), fill=(*DOT_WHITE, 255))
    base = Image.alpha_composite(base, dot)

    base = add_noise(base)
    return base


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    builders = [
        ("fractal-v1-spiral", build_golden_spiral),
        ("fractal-v2-julia", build_julia_set),
        ("fractal-v3-phyllotaxis", build_phyllotaxis),
    ]

    for name, builder in builders:
        print(f"Rendering {name}...")
        render = builder()
        masked = apply_circle_mask(render)

        for size, suffix in [(MASTER_SIZE, ""), (48, "-48")]:
            img = scale_to(masked, size)
            path = os.path.join(OUT_DIR, f"{name}{suffix}.png")
            img.save(path, "PNG")
            print(f"  {size}x{size}: {path}")

    print("\nDone. Three fractal concepts ready.")


if __name__ == "__main__":
    main()

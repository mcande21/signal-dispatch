#!/usr/bin/env python3
"""
Signal Dispatch -- 3D Sierpinski Tetrahedron Profile Picture

Renders a 3D Sierpinski tetrahedron (Tetrix) with:
  - Perspective projection
  - Amber wireframe on dark navy
  - Ambient glow at vertices
  - Rotated to an interesting viewing angle
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

RENDER_SIZE = 2048
MASTER_SIZE = 512

NAVY_EDGE = (8, 12, 22)
NAVY_CENTER = (14, 20, 36)
AMBER = (212, 133, 58)
AMBER_HOT = (235, 155, 70)
AMBER_BRIGHT = (255, 180, 90)
DOT_WHITE = (240, 237, 232)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 3D Math
# ---------------------------------------------------------------------------

def rotate_x(point, angle):
    x, y, z = point
    c, s = math.cos(angle), math.sin(angle)
    return (x, y * c - z * s, y * s + z * c)


def rotate_y(point, angle):
    x, y, z = point
    c, s = math.cos(angle), math.sin(angle)
    return (x * c + z * s, y, -x * s + z * c)


def rotate_z(point, angle):
    x, y, z = point
    c, s = math.cos(angle), math.sin(angle)
    return (x * c - y * s, x * s + y * c, z)


def project(point, W, fov=2.5, camera_z=4.0):
    """Perspective projection from 3D to 2D."""
    x, y, z = point
    # Translate so object is in front of camera
    z_shifted = z + camera_z
    if z_shifted <= 0.1:
        z_shifted = 0.1
    # Perspective divide
    scale = fov / z_shifted
    px = int(W / 2 + x * scale * W / 2)
    py = int(W / 2 - y * scale * W / 2)  # Flip Y for screen coords
    return (px, py, z_shifted)


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)


# ---------------------------------------------------------------------------
# Sierpinski Tetrahedron Generation
# ---------------------------------------------------------------------------

def tetrahedron_vertices():
    """Regular tetrahedron centered at origin, edge length ~2."""
    # Vertices of a regular tetrahedron
    a = (1, 1, 1)
    b = (1, -1, -1)
    c = (-1, 1, -1)
    d = (-1, -1, 1)
    return [a, b, c, d]


def tetrahedron_edges():
    """Edge pairs for a tetrahedron (indices into vertex list)."""
    return [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def sierpinski_tetrahedron(vertices, depth):
    """
    Recursively generate Sierpinski tetrahedron.
    Returns list of (vertices, edges) for each sub-tetrahedron at the leaf level.
    """
    if depth == 0:
        return [vertices]

    a, b, c, d = vertices
    # Midpoints of all 6 edges
    ab = midpoint(a, b)
    ac = midpoint(a, c)
    ad = midpoint(a, d)
    bc = midpoint(b, c)
    bd = midpoint(b, d)
    cd = midpoint(c, d)

    # 4 sub-tetrahedra (corners of the original)
    results = []
    results.extend(sierpinski_tetrahedron([a, ab, ac, ad], depth - 1))
    results.extend(sierpinski_tetrahedron([b, ab, bc, bd], depth - 1))
    results.extend(sierpinski_tetrahedron([c, ac, bc, cd], depth - 1))
    results.extend(sierpinski_tetrahedron([d, ad, bd, cd], depth - 1))

    return results


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def build_sierpinski_3d():
    W = RENDER_SIZE
    base = Image.new("RGBA", (W, W), (*NAVY_EDGE, 255))

    # Subtle radial gradient
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = W // 2, W // 2
    for r in range(int(W * 0.55), 0, -3):
        t = r / (W * 0.55)
        c = tuple(int(NAVY_CENTER[i] + (NAVY_EDGE[i] - NAVY_CENTER[i]) * t) for i in range(3))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, 255))
    base = Image.alpha_composite(base, grad)

    # Generate TWO Sierpinski tetrahedra stacked -- one upright, one inverted on top
    base_verts = tetrahedron_vertices()
    depth = 4
    edges_idx = tetrahedron_edges()

    # First tetrahedron: standard orientation, shifted down
    verts_bottom = [(v[0], v[1] - 0.55, v[2]) for v in base_verts]
    # Second tetrahedron: inverted (flip Y), shifted up
    verts_top = [(v[0], -v[1] + 0.55, v[2]) for v in base_verts]

    sub_tetras = []
    sub_tetras.extend(sierpinski_tetrahedron(verts_bottom, depth))
    sub_tetras.extend(sierpinski_tetrahedron(verts_top, depth))

    # Rotation angles for an interesting viewing angle
    rx = math.radians(25)    # Tilt forward
    ry = math.radians(35)    # Rotate right
    rz = math.radians(10)    # Slight roll

    # Collect all edges with their depth (z) for painter's algorithm
    all_edges_2d = []

    for verts in sub_tetras:
        # Rotate each vertex
        rotated = []
        for v in verts:
            v = rotate_x(v, rx)
            v = rotate_y(v, ry)
            v = rotate_z(v, rz)
            rotated.append(v)

        # Project and collect edges
        projected = [project(v, W, fov=2.2, camera_z=5.0) for v in rotated]

        for i, j in edges_idx:
            p1 = projected[i]
            p2 = projected[j]
            avg_z = (p1[2] + p2[2]) / 2
            all_edges_2d.append(((p1[0], p1[1]), (p2[0], p2[1]), avg_z))

    # Sort by z (back to front -- painter's algorithm)
    all_edges_2d.sort(key=lambda e: -e[2])

    # Find z range for depth-based coloring
    z_values = [e[2] for e in all_edges_2d]
    z_min, z_max = min(z_values), max(z_values)
    z_range = z_max - z_min if z_max > z_min else 1

    # Draw edges
    edge_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge_layer)

    for (x1, y1), (x2, y2), avg_z in all_edges_2d:
        # Depth-based properties
        depth_t = (avg_z - z_min) / z_range  # 0 = far, 1 = near

        # Near edges: brighter, thicker
        # Far edges: dimmer, thinner
        alpha = int(40 + depth_t * 215)
        width = max(1, int(1 + depth_t * 4))

        # Color: far = muted amber, near = hot amber
        r = int(AMBER[0] + (AMBER_HOT[0] - AMBER[0]) * depth_t)
        g = int(AMBER[1] + (AMBER_HOT[1] - AMBER[1]) * depth_t)
        b = int(AMBER[2] + (AMBER_HOT[2] - AMBER[2]) * depth_t)

        ed.line([(x1, y1), (x2, y2)], fill=(r, g, b, alpha), width=width)

    base = Image.alpha_composite(base, edge_layer)

    # Vertex glow layer -- add subtle glow at the brightest (nearest) vertices
    glow_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Collect unique projected vertices with their z
    vertex_set = {}
    for (x1, y1), (x2, y2), avg_z in all_edges_2d:
        for vx, vy in [(x1, y1), (x2, y2)]:
            key = (vx // 8, vy // 8)  # Deduplicate nearby points
            if key not in vertex_set or avg_z > vertex_set[key][2]:
                vertex_set[key] = (vx, vy, avg_z)

    # Draw small glows at the nearest vertices
    for key, (vx, vy, vz) in vertex_set.items():
        depth_t = (vz - z_min) / z_range
        if depth_t > 0.6:  # Only glow on nearest vertices
            gr = int(6 + depth_t * 12)
            ga = int((depth_t - 0.6) / 0.4 * 80)
            glow_draw.ellipse(
                (vx - gr, vy - gr, vx + gr, vy + gr),
                fill=(*AMBER_BRIGHT, ga)
            )

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=int(W * 0.008)))
    base = Image.alpha_composite(base, glow_layer)

    # Noise texture
    noise = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    pixels = noise.load()
    random.seed(42)
    for y in range(0, W, 3):
        for x in range(0, W, 3):
            v = random.randint(-8, 8)
            a = int(abs(v) * 0.025 * 255)
            c = 128 + v
            pixels[x, y] = (c, c, c, a)
    base = Image.alpha_composite(base, noise)

    return base


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


def main():
    print("Rendering 3D Sierpinski Tetrahedron...")
    render = build_sierpinski_3d()
    masked = apply_circle_mask(render)

    outputs = [
        (MASTER_SIZE, "sierpinski-3d.png"),
        (256, "sierpinski-3d-256.png"),
        (96, "sierpinski-3d-96.png"),
        (48, "sierpinski-3d-48.png"),
        (32, "sierpinski-3d-32.png"),
    ]

    for size, filename in outputs:
        img = scale_to(masked, size)
        path = os.path.join(OUT_DIR, filename)
        img.save(path, "PNG")
        print(f"  {size}x{size}: {path}")

    print("\nDone.")


if __name__ == "__main__":
    main()

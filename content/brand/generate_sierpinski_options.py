#!/usr/bin/env python3
"""
Signal Dispatch -- Four Sierpinski Profile Concepts

1. Wireframe glow -- edges only, depth fog, no filled faces
2. 2D flat geometric mark -- clean Sierpinski triangle, logo-appropriate
3. Hybrid signal pulse -- 2D Sierpinski at center with radar arcs
4. Minimal mark -- single level of voids, bold and iconic
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

RENDER_SIZE = 2048
MASTER_SIZE = 512

BG_DARK = (6, 9, 18)
BG_MID = (12, 17, 30)
AMBER_DEEP = (140, 80, 25)
AMBER = (212, 133, 58)
AMBER_HOT = (240, 165, 75)
AMBER_BRIGHT = (255, 200, 120)
DOT_WHITE = (240, 237, 232)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def apply_circle_mask(img):
    W = img.size[0]
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, W-1, W-1), fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out

def scale_to(img, size):
    return img.resize((size, size), Image.LANCZOS)

def make_bg(W):
    base = Image.new("RGBA", (W, W), (*BG_DARK, 255))
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = W//2, W//2
    for r in range(int(W*0.5), 0, -3):
        t = r / (W*0.5)
        c = tuple(int(BG_MID[i] + (BG_DARK[i]-BG_MID[i])*t) for i in range(3))
        gd.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*c, 255))
    return Image.alpha_composite(base, grad)

def add_noise(img):
    W = img.size[0]
    noise = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    px = noise.load()
    random.seed(42)
    for y in range(0, W, 3):
        for x in range(0, W, 3):
            v = random.randint(-6, 6)
            a = int(abs(v) * 0.02 * 255)
            px[x, y] = (128+v, 128+v, 128+v, a)
    return Image.alpha_composite(img, noise)


# ---------------------------------------------------------------------------
# 3D math (for wireframe option)
# ---------------------------------------------------------------------------

def rot_x(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0], p[1]*c - p[2]*s, p[1]*s + p[2]*c)

def rot_y(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0]*c + p[2]*s, p[1], -p[0]*s + p[2]*c)

def rot_z(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0]*c - p[1]*s, p[0]*s + p[1]*c, p[2])

def proj(p, W, fov=2.4, cz=4.0):
    z = p[2] + cz
    if z < 0.1: z = 0.1
    s = fov / z
    return (int(W/2 + p[0]*s*W/2), int(W/2 - p[1]*s*W/2), z)

def mid3(a, b):
    return ((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2)


# ---------------------------------------------------------------------------
# Sierpinski generators
# ---------------------------------------------------------------------------

def sierpinski_3d(verts, depth):
    if depth == 0:
        return [verts]
    a, b, c, d = verts
    ab, ac, ad = mid3(a,b), mid3(a,c), mid3(a,d)
    bc, bd, cd = mid3(b,c), mid3(b,d), mid3(c,d)
    r = []
    r.extend(sierpinski_3d([a, ab, ac, ad], depth-1))
    r.extend(sierpinski_3d([b, ab, bc, bd], depth-1))
    r.extend(sierpinski_3d([c, ac, bc, cd], depth-1))
    r.extend(sierpinski_3d([d, ad, bd, cd], depth-1))
    return r

def sierpinski_2d(v0, v1, v2, depth):
    """Generate 2D Sierpinski triangle -- returns list of filled triangles."""
    if depth == 0:
        return [(v0, v1, v2)]
    m01 = ((v0[0]+v1[0])/2, (v0[1]+v1[1])/2)
    m12 = ((v1[0]+v2[0])/2, (v1[1]+v2[1])/2)
    m02 = ((v0[0]+v2[0])/2, (v0[1]+v2[1])/2)
    r = []
    r.extend(sierpinski_2d(v0, m01, m02, depth-1))
    r.extend(sierpinski_2d(m01, v1, m12, depth-1))
    r.extend(sierpinski_2d(m02, m12, v2, depth-1))
    return r


# ---------------------------------------------------------------------------
# OPTION 1: Wireframe Glow
# ---------------------------------------------------------------------------

def build_wireframe():
    W = RENDER_SIZE
    base = make_bg(W)

    tetras = sierpinski_3d([(1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)], 4)
    edges_idx = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]

    rx, ry, rz = math.radians(30), math.radians(40), math.radians(5)

    all_edges = []
    for verts in tetras:
        rotated = [rot_z(rot_y(rot_x(v, rx), ry), rz) for v in verts]
        projected = [proj(v, W) for v in rotated]
        for i, j in edges_idx:
            p1, p2 = projected[i], projected[j]
            all_edges.append(((p1[0],p1[1]), (p2[0],p2[1]), (p1[2]+p2[2])/2))

    all_edges.sort(key=lambda e: -e[2])
    z_vals = [e[2] for e in all_edges]
    z_min, z_max = min(z_vals), max(z_vals)
    z_range = z_max - z_min if z_max > z_min else 1

    # Glow layer -- draw edges thick and blurred
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for (x1,y1), (x2,y2), z in all_edges:
        t = (z - z_min) / z_range
        alpha = int(20 + t * 80)
        gd.line([(x1,y1),(x2,y2)], fill=(*AMBER, alpha), width=max(1, int(2 + t*8)))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W*0.006)))
    base = Image.alpha_composite(base, glow)

    # Sharp edge layer
    edge_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge_layer)
    for (x1,y1), (x2,y2), z in all_edges:
        t = (z - z_min) / z_range
        alpha = int(30 + t * 225)
        width = max(1, int(1 + t * 3))
        r = int(AMBER[0] + (AMBER_BRIGHT[0]-AMBER[0]) * t)
        g = int(AMBER[1] + (AMBER_BRIGHT[1]-AMBER[1]) * t)
        b = int(AMBER[2] + (AMBER_BRIGHT[2]-AMBER[2]) * t)
        ed.line([(x1,y1),(x2,y2)], fill=(r,g,b,alpha), width=width)
    base = Image.alpha_composite(base, edge_layer)

    return add_noise(base)


# ---------------------------------------------------------------------------
# OPTION 2: 2D Flat Geometric Mark
# ---------------------------------------------------------------------------

def build_flat_mark():
    W = RENDER_SIZE
    base = make_bg(W)

    # Equilateral triangle centered, filling most of the circle
    cx, cy = W//2, W//2
    size = W * 0.38
    # Vertices of equilateral triangle (point up)
    v0 = (cx, cy - size * 1.0)                          # top
    v1 = (cx - size * math.cos(math.radians(30)),
          cy + size * math.sin(math.radians(30)) * 1.0)  # bottom-left
    v2 = (cx + size * math.cos(math.radians(30)),
          cy + size * math.sin(math.radians(30)) * 1.0)  # bottom-right

    # Shift down slightly to visually center (triangles look top-heavy)
    shift = W * 0.04
    v0 = (v0[0], v0[1] + shift)
    v1 = (v1[0], v1[1] + shift)
    v2 = (v2[0], v2[1] + shift)

    depth = 5
    triangles = sierpinski_2d(v0, v1, v2, depth)

    # Glow behind the shape
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    glow_d = ImageDraw.Draw(glow)
    gr = int(W * 0.28)
    glow_d.ellipse((cx-gr, cy-gr+int(shift), cx+gr, cy+gr+int(shift)),
                    fill=(*AMBER, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W*0.07)))
    base = Image.alpha_composite(base, glow)

    # Draw filled triangles with subtle variation
    tri_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    td = ImageDraw.Draw(tri_layer)

    for i, (t0, t1, t2) in enumerate(triangles):
        # Slight color variation based on position (lighter toward top)
        avg_y = (t0[1] + t1[1] + t2[1]) / 3
        t_val = 1.0 - (avg_y - (cy - size)) / (size * 2)  # 0=bottom, 1=top
        t_val = max(0, min(1, t_val))

        r = int(AMBER[0] + (AMBER_BRIGHT[0]-AMBER[0]) * t_val * 0.6)
        g = int(AMBER[1] + (AMBER_BRIGHT[1]-AMBER[1]) * t_val * 0.6)
        b = int(AMBER[2] + (AMBER_BRIGHT[2]-AMBER[2]) * t_val * 0.6)

        poly = [(int(t0[0]),int(t0[1])), (int(t1[0]),int(t1[1])), (int(t2[0]),int(t2[1]))]
        td.polygon(poly, fill=(r, g, b, 240))

    base = Image.alpha_composite(base, tri_layer)

    # Draw edges on top for definition
    edge_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    eld = ImageDraw.Draw(edge_layer)
    for t0, t1, t2 in triangles:
        poly = [(int(t0[0]),int(t0[1])), (int(t1[0]),int(t1[1])), (int(t2[0]),int(t2[1]))]
        for k in range(3):
            m = (k+1) % 3
            eld.line([poly[k], poly[m]], fill=(*AMBER_HOT, 60), width=1)
    base = Image.alpha_composite(base, edge_layer)

    return add_noise(base)


# ---------------------------------------------------------------------------
# OPTION 3: Hybrid -- 2D Sierpinski + Signal Arcs
# ---------------------------------------------------------------------------

def build_hybrid():
    W = RENDER_SIZE
    base = make_bg(W)

    # Smaller triangle with arcs emanating
    cx, cy = int(W * 0.38), int(W * 0.58)
    size = W * 0.20

    v0 = (cx, cy - size)
    v1 = (cx - size * math.cos(math.radians(30)), cy + size * 0.5)
    v2 = (cx + size * math.cos(math.radians(30)), cy + size * 0.5)

    depth = 4
    triangles = sierpinski_2d(v0, v1, v2, depth)

    # Signal arcs emanating from the triangle
    arc_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc_layer)

    arcs = [
        (int(W*0.18), 240, -130, 95),
        (int(W*0.30), 180, -140, 115),
        (int(W*0.43), 100, -148, 130),
    ]
    stroke = int(W * 0.032)
    for r, alpha, start, span in arcs:
        bbox = (cx-r, cy-r, cx+r, cy+r)
        ad.arc(bbox, start=start, end=start+span, fill=(*AMBER, alpha), width=stroke)

    base = Image.alpha_composite(base, arc_layer)

    # Glow at origin
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx-int(W*0.1), cy-int(W*0.08),
                                   cx+int(W*0.1), cy+int(W*0.08)),
                                  fill=(*AMBER, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W*0.05)))
    base = Image.alpha_composite(base, glow)

    # Draw the Sierpinski triangle
    tri_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    td = ImageDraw.Draw(tri_layer)
    for t0, t1, t2 in triangles:
        poly = [(int(t0[0]),int(t0[1])), (int(t1[0]),int(t1[1])), (int(t2[0]),int(t2[1]))]
        td.polygon(poly, fill=(*AMBER_HOT, 230))
        for k in range(3):
            m = (k+1) % 3
            td.line([poly[k], poly[m]], fill=(*AMBER_BRIGHT, 100), width=1)

    base = Image.alpha_composite(base, tri_layer)

    return add_noise(base)


# ---------------------------------------------------------------------------
# OPTION 4: Minimal Mark -- bold, iconic, fewer recursions
# ---------------------------------------------------------------------------

def build_minimal():
    W = RENDER_SIZE
    base = make_bg(W)

    cx, cy = W//2, W//2
    size = W * 0.36
    shift = W * 0.04

    v0 = (cx, cy - size + shift)
    v1 = (cx - size * math.cos(math.radians(30)), cy + size * 0.5 + shift)
    v2 = (cx + size * math.cos(math.radians(30)), cy + size * 0.5 + shift)

    # Only depth 3 -- bold, readable, iconic
    depth = 3
    triangles = sierpinski_2d(v0, v1, v2, depth)

    # Strong glow
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(W * 0.25)
    gd.ellipse((cx-gr, cy-gr+int(shift), cx+gr, cy+gr+int(shift)),
               fill=(*AMBER, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W*0.08)))
    base = Image.alpha_composite(base, glow)

    # Draw triangles -- solid amber, no gradient, bold
    tri_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    td = ImageDraw.Draw(tri_layer)
    for t0, t1, t2 in triangles:
        poly = [(int(t0[0]),int(t0[1])), (int(t1[0]),int(t1[1])), (int(t2[0]),int(t2[1]))]
        td.polygon(poly, fill=(*AMBER_HOT, 255))

    base = Image.alpha_composite(base, tri_layer)

    # Thin edge outlines for definition
    edge_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    eld = ImageDraw.Draw(edge_layer)

    # Draw the outer triangle outline
    outer = [(int(v0[0]),int(v0[1])), (int(v1[0]),int(v1[1])), (int(v2[0]),int(v2[1]))]
    for k in range(3):
        m = (k+1) % 3
        eld.line([outer[k], outer[m]], fill=(*AMBER_BRIGHT, 180), width=int(W*0.004))

    # Draw void outlines (the removed triangles)
    def get_voids(v0, v1, v2, d):
        if d == 0:
            return []
        m01 = ((v0[0]+v1[0])/2, (v0[1]+v1[1])/2)
        m12 = ((v1[0]+v2[0])/2, (v1[1]+v2[1])/2)
        m02 = ((v0[0]+v2[0])/2, (v0[1]+v2[1])/2)
        voids = [(m01, m12, m02)]  # The center void
        voids.extend(get_voids(v0, m01, m02, d-1))
        voids.extend(get_voids(m01, v1, m12, d-1))
        voids.extend(get_voids(m02, m12, v2, d-1))
        return voids

    voids = get_voids(v0, v1, v2, depth)
    for vt0, vt1, vt2 in voids:
        vpoly = [(int(vt0[0]),int(vt0[1])), (int(vt1[0]),int(vt1[1])), (int(vt2[0]),int(vt2[1]))]
        for k in range(3):
            m = (k+1) % 3
            eld.line([vpoly[k], vpoly[m]], fill=(*AMBER_BRIGHT, 80), width=max(1, int(W*0.002)))

    base = Image.alpha_composite(base, edge_layer)

    return add_noise(base)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    builders = [
        ("opt1-wireframe", build_wireframe),
        ("opt2-flat-mark", build_flat_mark),
        ("opt3-hybrid", build_hybrid),
        ("opt4-minimal", build_minimal),
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

    print("\nDone. Four options ready.")


if __name__ == "__main__":
    main()

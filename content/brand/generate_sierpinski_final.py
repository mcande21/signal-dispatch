#!/usr/bin/env python3
"""
Signal Dispatch -- Sierpinski Pyramid Profile Picture
Ground-up redesign with frontend-design principles.

Design direction: A single Sierpinski tetrahedron rendered with intention.
Not a wireframe dump -- a composed, lit, atmospheric piece.

Key design decisions:
  - Single tetrahedron (not stacked) -- clarity over complexity
  - Filled faces with transparency, not just wireframe -- gives solidity
  - Dramatic lighting: one face bright, others in shadow -- 3D reads instantly
  - The fractal voids are the design -- the negative space IS the pattern
  - Amber-to-white gradient on the lit face, deep amber on shadow faces
  - Atmospheric glow behind the shape -- it floats, doesn't sit
  - Viewing angle chosen for maximum visual interest (see the void structure)
  - Generous padding -- the shape breathes inside the circle
  - Background: deep navy with subtle radial gradient, not flat
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

RENDER_SIZE = 2048
MASTER_SIZE = 512

# Palette
BG_DARK = (6, 9, 18)           # Deepest navy
BG_MID = (12, 17, 30)          # Subtle gradient center
AMBER_DEEP = (160, 95, 30)     # Shadow faces
AMBER = (212, 133, 58)         # Mid tone
AMBER_HOT = (240, 165, 75)     # Lit face
AMBER_PEAK = (255, 200, 120)   # Hottest highlights
WHITE_WARM = (245, 235, 220)   # Edge highlights

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 3D Math
# ---------------------------------------------------------------------------

def rotate_x(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0], p[1]*c - p[2]*s, p[1]*s + p[2]*c)

def rotate_y(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0]*c + p[2]*s, p[1], -p[0]*s + p[2]*c)

def rotate_z(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0]*c - p[1]*s, p[0]*s + p[1]*c, p[2])

def project(p, W, fov=2.6, cam_z=3.8):
    z = p[2] + cam_z
    if z < 0.1: z = 0.1
    scale = fov / z
    return (int(W/2 + p[0]*scale*W/2), int(W/2 - p[1]*scale*W/2), z)

def midpoint(a, b):
    return ((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2)

def face_normal(v0, v1, v2):
    """Compute face normal via cross product."""
    ux, uy, uz = v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]
    vx, vy, vz = v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]
    nx = uy*vz - uz*vy
    ny = uz*vx - ux*vz
    nz = ux*vy - uy*vx
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length < 1e-10: return (0, 0, 1)
    return (nx/length, ny/length, nz/length)

def dot_product(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def centroid(verts):
    n = len(verts)
    return (sum(v[0] for v in verts)/n, sum(v[1] for v in verts)/n, sum(v[2] for v in verts)/n)


# ---------------------------------------------------------------------------
# Sierpinski Generation
# ---------------------------------------------------------------------------

def tetra_verts():
    """Regular tetrahedron centered at origin."""
    return [(1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1)]

def sierpinski(verts, depth):
    if depth == 0:
        return [verts]
    a, b, c, d = verts
    ab, ac, ad = midpoint(a,b), midpoint(a,c), midpoint(a,d)
    bc, bd, cd = midpoint(b,c), midpoint(b,d), midpoint(c,d)
    result = []
    result.extend(sierpinski([a, ab, ac, ad], depth-1))
    result.extend(sierpinski([b, ab, bc, bd], depth-1))
    result.extend(sierpinski([c, ac, bc, cd], depth-1))
    result.extend(sierpinski([d, ad, bd, cd], depth-1))
    return result


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def build():
    W = RENDER_SIZE
    base = Image.new("RGBA", (W, W), (*BG_DARK, 255))

    # Radial gradient background -- glow from center
    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = W//2, W//2
    for r in range(int(W*0.5), 0, -3):
        t = r / (W*0.5)
        c = tuple(int(BG_MID[i] + (BG_DARK[i]-BG_MID[i])*t) for i in range(3))
        gd.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(*c, 255))
    base = Image.alpha_composite(base, grad)

    # Generate fractal -- depth 5 for more recursion detail
    depth = 5
    sub_tetras = sierpinski(tetra_verts(), depth)

    # Rotation -- chosen for maximum void visibility
    rx = math.radians(30)
    ry = math.radians(40)
    rz = math.radians(5)

    # Light direction (normalized) -- coming from upper-left-front
    light_dir = (0.4, 0.7, 0.5)
    ln = math.sqrt(sum(x*x for x in light_dir))
    light_dir = tuple(x/ln for x in light_dir)

    # Tetrahedron faces: 4 faces per tetrahedron
    face_indices = [(0,1,2), (0,1,3), (0,2,3), (1,2,3)]

    # Collect all faces with their properties for depth sorting
    all_faces = []

    for verts in sub_tetras:
        # Rotate
        rotated = []
        for v in verts:
            v = rotate_x(v, rx)
            v = rotate_y(v, ry)
            v = rotate_z(v, rz)
            rotated.append(v)

        for fi in face_indices:
            v0, v1, v2 = rotated[fi[0]], rotated[fi[1]], rotated[fi[2]]

            # Face normal for lighting
            normal = face_normal(v0, v1, v2)

            # Backface culling -- skip faces pointing away from camera
            face_center = centroid([v0, v1, v2])
            view_dir = (0, 0, -1)  # Camera looks down -Z
            if dot_product(normal, view_dir) > 0:
                # Flip normal if it points away
                normal = (-normal[0], -normal[1], -normal[2])

            # Lighting intensity
            intensity = max(0, dot_product(normal, light_dir))
            # Add ambient so shadow faces aren't invisible
            intensity = 0.15 + intensity * 0.85

            # Project vertices
            p0 = project(v0, W)
            p1 = project(v1, W)
            p2 = project(v2, W)

            avg_z = (p0[2] + p1[2] + p2[2]) / 3
            all_faces.append(([(p0[0],p0[1]), (p1[0],p1[1]), (p2[0],p2[1])],
                             avg_z, intensity))

    # Sort back to front (painter's algorithm)
    all_faces.sort(key=lambda f: -f[1])

    # Draw filled faces
    face_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    fd = ImageDraw.Draw(face_layer)

    for poly, z, intensity in all_faces:
        # Color based on lighting intensity
        if intensity > 0.7:
            # Bright face -- hot amber to peak
            t = (intensity - 0.7) / 0.3
            r = int(AMBER_HOT[0] + (AMBER_PEAK[0]-AMBER_HOT[0]) * t)
            g = int(AMBER_HOT[1] + (AMBER_PEAK[1]-AMBER_HOT[1]) * t)
            b = int(AMBER_HOT[2] + (AMBER_PEAK[2]-AMBER_HOT[2]) * t)
        elif intensity > 0.4:
            # Mid face -- amber
            t = (intensity - 0.4) / 0.3
            r = int(AMBER[0] + (AMBER_HOT[0]-AMBER[0]) * t)
            g = int(AMBER[1] + (AMBER_HOT[1]-AMBER[1]) * t)
            b = int(AMBER[2] + (AMBER_HOT[2]-AMBER[2]) * t)
        else:
            # Shadow face -- deep amber
            t = intensity / 0.4
            r = int(AMBER_DEEP[0] * 0.5 + AMBER_DEEP[0] * 0.5 * t)
            g = int(AMBER_DEEP[1] * 0.5 + AMBER_DEEP[1] * 0.5 * t)
            b = int(AMBER_DEEP[2] * 0.5 + AMBER_DEEP[2] * 0.5 * t)

        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Semi-transparent fill + opaque edge
        fill_alpha = int(180 + intensity * 75)
        fd.polygon(poly, fill=(r, g, b, fill_alpha))

        # Edge lines -- slightly brighter than face
        edge_r = min(255, r + 30)
        edge_g = min(255, g + 20)
        edge_b = min(255, b + 10)
        edge_alpha = int(100 + intensity * 155)
        width = max(1, int(1 + intensity * 2))

        for i in range(len(poly)):
            j = (i + 1) % len(poly)
            fd.line([poly[i], poly[j]], fill=(edge_r, edge_g, edge_b, edge_alpha), width=width)

    base = Image.alpha_composite(base, face_layer)

    # Atmospheric glow behind the shape
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    glow_d = ImageDraw.Draw(glow)
    gr = int(W * 0.22)
    glow_d.ellipse((cx-gr, cy-gr-int(W*0.02), cx+gr, cy+gr-int(W*0.02)),
                    fill=(*AMBER, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(W*0.08)))
    # Composite glow BEHIND the face layer
    base_with_glow = Image.new("RGBA", (W, W), (*BG_DARK, 255))
    base_with_glow = Image.alpha_composite(base_with_glow, grad)
    base_with_glow = Image.alpha_composite(base_with_glow, glow)
    base_with_glow = Image.alpha_composite(base_with_glow, face_layer)

    # Subtle noise
    noise = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    pixels = noise.load()
    random.seed(42)
    for y in range(0, W, 3):
        for x in range(0, W, 3):
            v = random.randint(-6, 6)
            a = int(abs(v) * 0.02 * 255)
            pixels[x, y] = (128+v, 128+v, 128+v, a)
    base_with_glow = Image.alpha_composite(base_with_glow, noise)

    return base_with_glow


def apply_circle_mask(img):
    W = img.size[0]
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, W-1, W-1), fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def scale_to(img, size):
    return img.resize((size, size), Image.LANCZOS)


def main():
    print("Rendering Sierpinski Pyramid (ground-up redesign)...")
    render = build()
    masked = apply_circle_mask(render)

    outputs = [
        (MASTER_SIZE, "sierpinski-final.png"),
        (256, "sierpinski-final-256.png"),
        (96, "sierpinski-final-96.png"),
        (48, "sierpinski-final-48.png"),
        (32, "sierpinski-final-32.png"),
    ]

    for size, filename in outputs:
        img = scale_to(masked, size)
        path = os.path.join(OUT_DIR, filename)
        img.save(path, "PNG")
        print(f"  {size}x{size}: {path}")

    print("\nDone.")


if __name__ == "__main__":
    main()

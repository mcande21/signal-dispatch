"""
Signal Dispatch OG Image Generator
Issue #10: "The Shotgun" -- DEEP DIVE style
Output: 1200 x 630 px PNG

Deep dive treatment: dark, dramatic, minimal.
- Dark navy background
- "SIGNAL DISPATCH" with dashes, amber/orange, top left with horizontal rule
- Large bold condensed title (white, dominant)
- Subtitle below in lighter weight
- "DEEP DIVE | DATE" at bottom left in small spaced caps
- Subtle "#10" watermark bottom right
- Signal arc texture bottom right
- NO framing bars (top/bottom) -- no pill badges
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_PATH = "/path/to/home/projects/signal-dispatch/content/drafts/10-og-image.png"
FONT_DIR = "/tmp/sd-og-fonts"
WIDTH, HEIGHT = 1200, 630

# Colors -- exact match to SD #5 deep dive
BG_TOP    = (10, 15, 26)       # #0A0F1A  deep navy top
BG_BOTTOM = (14, 20, 36)       # #0E1424  slightly lighter navy bottom
ACCENT    = (212, 133, 58)     # #D4853A  signal orange/amber
TEXT_PRI  = (240, 237, 232)    # #F0EDE8  off-white primary
TEXT_SEC  = (180, 175, 165)    # #B4AFA5  muted secondary
GRID_COL  = (30, 42, 60)       # #1E2A3C  faint grid lines

PADDING_X = 72
PADDING_Y = 60

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

BEBAS_PATH   = os.path.join(FONT_DIR, "BebasNeue-Regular.ttf")
JAKARTA_PATH = os.path.join(FONT_DIR, "PlusJakartaSans.ttf")


def load_font(path, size):
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for candidate in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    return ImageFont.load_default()


font_title_lg = load_font(BEBAS_PATH, 130)
font_pubname  = load_font(JAKARTA_PATH, 17)
font_subtitle = load_font(JAKARTA_PATH, 26)
font_meta     = load_font(JAKARTA_PATH, 15)
font_issue_wm = load_font(BEBAS_PATH, 200)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def draw_tracked_text(draw, pos, text, font, fill, tracking=3):
    """Draw text with additional letter spacing (tracking)."""
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = font.getbbox(ch)
        x += (bbox[2] - bbox[0]) + tracking
    return x


def tracked_text_width(text, font, tracking=3):
    w = 0
    for ch in text:
        bbox = font.getbbox(ch)
        w += (bbox[2] - bbox[0]) + tracking
    return w


def wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        bbox = font.getbbox(test)
        if (bbox[2] - bbox[0]) > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines

# ---------------------------------------------------------------------------
# Canvas + background gradient
# ---------------------------------------------------------------------------

img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
draw = ImageDraw.Draw(img)

for y in range(HEIGHT):
    t = y / HEIGHT
    r = int(BG_TOP[0] + t * (BG_BOTTOM[0] - BG_TOP[0]))
    g = int(BG_TOP[1] + t * (BG_BOTTOM[1] - BG_TOP[1]))
    b = int(BG_TOP[2] + t * (BG_BOTTOM[2] - BG_TOP[2]))
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# ---------------------------------------------------------------------------
# Texture: subtle dot grid
# ---------------------------------------------------------------------------

texture = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(texture)
GRID_STEP = 32
DOT_RADIUS = 1

random.seed(42)
for gx in range(0, WIDTH + GRID_STEP, GRID_STEP):
    for gy in range(0, HEIGHT + GRID_STEP, GRID_STEP):
        jx = random.randint(-2, 2)
        jy = random.randint(-2, 2)
        cx, cy = gx + jx, gy + jy
        tdraw.ellipse(
            [(cx - DOT_RADIUS, cy - DOT_RADIUS),
             (cx + DOT_RADIUS, cy + DOT_RADIUS)],
            fill=(GRID_COL[0], GRID_COL[1], GRID_COL[2], 35),
        )

img = Image.alpha_composite(img.convert("RGBA"), texture).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Texture: horizontal scan lines (every 4px, very faint)
# ---------------------------------------------------------------------------

scan_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(scan_layer)
for sy in range(0, HEIGHT, 4):
    sdraw.line([(0, sy), (WIDTH, sy)], fill=(0, 0, 0, 12))
img = Image.alpha_composite(img.convert("RGBA"), scan_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Background: radar / signal pulse motif (concentric arcs, bottom-right)
# ---------------------------------------------------------------------------

PULSE_CX = WIDTH + 80
PULSE_CY = HEIGHT + 60
PULSE_STEPS = 7
PULSE_STEP_SIZE = 110
PULSE_ALPHA_START = 18
PULSE_ALPHA_DECAY = 2

pulse_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
pdraw = ImageDraw.Draw(pulse_layer)

for i in range(PULSE_STEPS):
    radius = 120 + i * PULSE_STEP_SIZE
    alpha = max(0, PULSE_ALPHA_START - i * PULSE_ALPHA_DECAY)
    for thickness_offset in range(2):
        r = radius + thickness_offset
        bbox = [(PULSE_CX - r, PULSE_CY - r), (PULSE_CX + r, PULSE_CY + r)]
        pdraw.arc(
            bbox, start=180, end=270,
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha),
            width=1,
        )

img = Image.alpha_composite(img.convert("RGBA"), pulse_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

TOP_ROW_Y  = PADDING_Y
TITLE_Y    = 130
SUBTITLE_Y = 380
DIVIDER_Y  = 460
META_Y     = 490

# ---------------------------------------------------------------------------
# 1. Publication name row
#    "── SIGNAL DISPATCH ──────────────────────────────"
# ---------------------------------------------------------------------------

PUB_TEXT = "SIGNAL DISPATCH"
PUB_TRACKING = 5

DASH_LEFT_W = 28
DASH_GAP    = 12
DASH_Y_OFFSET = 10

pub_x  = PADDING_X
dash_y = TOP_ROW_Y + DASH_Y_OFFSET

# Left dash
draw.line(
    [(pub_x, dash_y), (pub_x + DASH_LEFT_W, dash_y)],
    fill=ACCENT, width=2,
)

pub_text_x = pub_x + DASH_LEFT_W + DASH_GAP
final_x = draw_tracked_text(
    draw,
    (pub_text_x, TOP_ROW_Y),
    PUB_TEXT,
    font_pubname,
    ACCENT,
    tracking=PUB_TRACKING,
)

# Right accent line extending to right edge minus padding
RIGHT_LINE_X = WIDTH - PADDING_X
if final_x + 20 < RIGHT_LINE_X:
    draw.line(
        [(final_x + DASH_GAP, dash_y), (RIGHT_LINE_X, dash_y)],
        fill=ACCENT, width=2,
    )

# ---------------------------------------------------------------------------
# 2. Main title: "THE SHOTGUN"
#    Bebas Neue, large, auto-scale to fit canvas width
# ---------------------------------------------------------------------------

TITLE_TEXT = "THE SHOTGUN"

title_bbox = font_title_lg.getbbox(TITLE_TEXT)
title_w = title_bbox[2] - title_bbox[0]
max_title_w = WIDTH - PADDING_X * 2

if title_w > max_title_w:
    scale = max_title_w / title_w
    font_title_use = load_font(BEBAS_PATH, int(130 * scale))
else:
    font_title_use = font_title_lg

draw.text((PADDING_X, TITLE_Y), TITLE_TEXT, font=font_title_use, fill=TEXT_PRI)

# ---------------------------------------------------------------------------
# 3. Subtitle
# ---------------------------------------------------------------------------

SUBTITLE_TEXT = "Who actually loses voters when you require proof of citizenship"

subtitle_lines = wrap_text(SUBTITLE_TEXT, font_subtitle, WIDTH - PADDING_X * 2)
sub_line_h = font_subtitle.getbbox("Ag")[3] - font_subtitle.getbbox("Ag")[1]
sub_spacing = 8

for i, line in enumerate(subtitle_lines):
    draw.text(
        (PADDING_X, SUBTITLE_Y + i * (sub_line_h + sub_spacing)),
        line,
        font=font_subtitle,
        fill=TEXT_SEC,
    )

# ---------------------------------------------------------------------------
# 4. Thin accent divider line
# ---------------------------------------------------------------------------

draw.line(
    [(PADDING_X, DIVIDER_Y), (PADDING_X + 200, DIVIDER_Y)],
    fill=ACCENT, width=1,
)

# ---------------------------------------------------------------------------
# 5. Metadata row: "DEEP DIVE  |  MARCH 21, 2026"
# ---------------------------------------------------------------------------

META_TEXT = "DEEP DIVE  |  MARCH 21, 2026"
draw_tracked_text(
    draw,
    (PADDING_X, META_Y),
    META_TEXT,
    font_meta,
    TEXT_SEC,
    tracking=2,
)

# ---------------------------------------------------------------------------
# 6. Subtle right-side vertical accent bar
# ---------------------------------------------------------------------------

bar_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
bdraw = ImageDraw.Draw(bar_layer)
bdraw.line(
    [(WIDTH - PADDING_X, PADDING_Y), (WIDTH - PADDING_X, HEIGHT - PADDING_Y)],
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 55),
    width=1,
)
img = Image.alpha_composite(img.convert("RGBA"), bar_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# 7. Issue number watermark -- very faint, bottom-right
# ---------------------------------------------------------------------------

issue_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
idraw = ImageDraw.Draw(issue_layer)

issue_text = "#10"
ibbox = font_issue_wm.getbbox(issue_text)
iw = ibbox[2] - ibbox[0]
ih = ibbox[3] - ibbox[1]
issue_x = WIDTH - PADDING_X - iw - 10
issue_y = HEIGHT - ih - PADDING_Y + 20

idraw.text(
    (issue_x, issue_y),
    issue_text,
    font=font_issue_wm,
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 18),
)
img = Image.alpha_composite(img.convert("RGBA"), issue_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

img.save(OUTPUT_PATH, "PNG", optimize=True)
print(f"\nSaved: {OUTPUT_PATH}")
print(f"Size:  {img.size[0]} x {img.size[1]} px")

"""
Signal Dispatch OG Image Generator
Issue #9: "The Pipeline" -- Weekly Brief
Output: 1200 x 630 px PNG

Weekly brief treatment: lighter, more bulletin-energy vs deep dive's dramatic darkness.
- Slightly lighter navy background
- Prominent "WEEKLY BRIEF" pill/tag label
- Horizontal rule motif (full-width, more architectural)
- Wider breathing room / more whitespace
- Issue number watermark still present but subtler
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_PATH = "content/drafts/9-og-image.png"
FONT_DIR = "/tmp/sd-og-fonts"
WIDTH, HEIGHT = 1200, 630

# Weekly brief palette -- slightly lighter/warmer than deep dive
# Deep dive: BG_TOP=(10, 15, 26), BG_BOTTOM=(14, 20, 36)
# Weekly brief: a touch brighter, more "alive"
BG_TOP    = (12, 18, 32)       # #0C1220  navy top
BG_MID    = (16, 24, 42)       # #10182A  mid (3-stop gradient for more depth)
BG_BOTTOM = (11, 17, 30)       # slightly pulled back at bottom

ACCENT      = (212, 133, 58)   # #D4853A  signal orange/amber (same as deep dive)
ACCENT_LIGHT = (225, 152, 80)  # slightly lighter orange for the pill bg

TEXT_PRI  = (240, 237, 232)    # #F0EDE8  off-white primary
TEXT_SEC  = (175, 170, 160)    # muted secondary
TEXT_DIM  = (100, 98, 90)      # very dim
GRID_COL  = (28, 40, 62)       # faint grid dot color

# Weekly brief label colors -- pill style
PILL_BG   = (40, 28, 12)       # very dark amber background for pill
PILL_BORDER = ACCENT

PADDING_X = 72
PADDING_Y = 56

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

font_pubname   = load_font(JAKARTA_PATH, 15)
font_label     = load_font(JAKARTA_PATH, 13)   # "WEEKLY BRIEF" pill text
font_title_lg  = load_font(BEBAS_PATH, 220)
font_subtitle  = load_font(JAKARTA_PATH, 26)
font_meta      = load_font(JAKARTA_PATH, 14)
font_issue_wm  = load_font(BEBAS_PATH, 200)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def draw_tracked_text(draw, pos, text, font, fill, tracking=3):
    """Draw text with extra letter-spacing."""
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = font.getbbox(ch)
        x += (bbox[2] - bbox[0]) + tracking
    return x  # returns the x after last char

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
# Canvas + background gradient (3-stop, slightly lighter than deep dive)
# ---------------------------------------------------------------------------

img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
draw = ImageDraw.Draw(img)

mid_stop = int(HEIGHT * 0.55)

for y in range(HEIGHT):
    if y <= mid_stop:
        t = y / mid_stop
        r = int(BG_TOP[0] + t * (BG_MID[0] - BG_TOP[0]))
        g = int(BG_TOP[1] + t * (BG_MID[1] - BG_TOP[1]))
        b = int(BG_TOP[2] + t * (BG_MID[2] - BG_TOP[2]))
    else:
        t = (y - mid_stop) / (HEIGHT - mid_stop)
        r = int(BG_MID[0] + t * (BG_BOTTOM[0] - BG_MID[0]))
        g = int(BG_MID[1] + t * (BG_BOTTOM[1] - BG_MID[1]))
        b = int(BG_MID[2] + t * (BG_BOTTOM[2] - BG_MID[2]))
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# ---------------------------------------------------------------------------
# Texture: subtle dot grid
# ---------------------------------------------------------------------------

texture = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(texture)
GRID_STEP = 36
DOT_RADIUS = 1
random.seed(99)
for gx in range(0, WIDTH + GRID_STEP, GRID_STEP):
    for gy in range(0, HEIGHT + GRID_STEP, GRID_STEP):
        jx = random.randint(-3, 3)
        jy = random.randint(-3, 3)
        cx, cy = gx + jx, gy + jy
        tdraw.ellipse(
            [(cx - DOT_RADIUS, cy - DOT_RADIUS),
             (cx + DOT_RADIUS, cy + DOT_RADIUS)],
            fill=(GRID_COL[0], GRID_COL[1], GRID_COL[2], 28),
        )
img = Image.alpha_composite(img.convert("RGBA"), texture).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Texture: horizontal scan lines (every 5px, very faint)
# Weekly brief: slightly less dense scan lines = lighter feel
# ---------------------------------------------------------------------------

scan_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(scan_layer)
for sy in range(0, HEIGHT, 5):
    sdraw.line([(0, sy), (WIDTH, sy)], fill=(0, 0, 0, 10))
img = Image.alpha_composite(img.convert("RGBA"), scan_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Background signal pulse -- bottom-right corner, very subtle
# ---------------------------------------------------------------------------

pulse_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
pdraw = ImageDraw.Draw(pulse_layer)
PULSE_CX = WIDTH + 100
PULSE_CY = HEIGHT + 80
for i in range(6):
    radius = 150 + i * 120
    alpha = max(0, 14 - i * 2)
    for t in range(2):
        r = radius + t
        bbox = [(PULSE_CX - r, PULSE_CY - r), (PULSE_CX + r, PULSE_CY + r)]
        pdraw.arc(bbox, start=180, end=270,
                  fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha), width=1)
img = Image.alpha_composite(img.convert("RGBA"), pulse_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
# Weekly brief layout (top to bottom):
#   PADDING_Y=56        top margin
#   TOP_RULE_Y=56       full-width top horizontal rule (orange) -- hallmark of the brief
#   PUBNAME_Y=76        "SIGNAL DISPATCH" label row
#   PILL_Y=72           "WEEKLY BRIEF" pill, right-aligned to pubname row
#   SECOND_RULE_Y       thin separator below pubname row
#   TITLE_Y             Big title: "The Pipeline" (computed to center block)
#   SUBTITLE_Y          Subtitle text (computed from title bottom)
#   DIVIDER_Y           Short accent rule
#   META_Y              "SD #9 | MARCH 21, 2026"
#   BOTTOM_RULE_Y=574   Full-width bottom rule (matches top)
# ---------------------------------------------------------------------------

TOP_RULE_Y    = PADDING_Y
PUBNAME_Y     = TOP_RULE_Y + 20
META_GAP      = 18
BOTTOM_RULE_Y = HEIGHT - PADDING_Y

# ---------------------------------------------------------------------------
# 1. Full-width top horizontal rule (the distinctive weekly brief element)
#    Two lines: thick accent + thin separator beneath pubname
# ---------------------------------------------------------------------------

# Top rule: orange accent line, full width minus padding
draw.line(
    [(PADDING_X, TOP_RULE_Y), (WIDTH - PADDING_X, TOP_RULE_Y)],
    fill=ACCENT, width=2,
)

# ---------------------------------------------------------------------------
# 2. Publication name row: "── SIGNAL DISPATCH" with dashes
# ---------------------------------------------------------------------------

PUB_TEXT = "SIGNAL DISPATCH"
PUB_TRACKING = 5

DASH_W   = 22
DASH_GAP = 10
dash_y   = PUBNAME_Y + 9  # vertically center with font cap height

# Left short dash
draw.line(
    [(PADDING_X, dash_y), (PADDING_X + DASH_W, dash_y)],
    fill=ACCENT, width=2,
)

pub_text_x = PADDING_X + DASH_W + DASH_GAP
end_pub_x = draw_tracked_text(
    draw,
    (pub_text_x, PUBNAME_Y),
    PUB_TEXT,
    font_pubname,
    ACCENT,
    tracking=PUB_TRACKING,
)

# ---------------------------------------------------------------------------
# 3. "WEEKLY BRIEF" pill -- right-aligned, same row as pubname
# ---------------------------------------------------------------------------

PILL_TEXT = "WEEKLY BRIEF"
PILL_TRACKING = 3
PILL_PAD_X = 12
PILL_PAD_Y = 5
PILL_RADIUS = 4

pill_text_w = tracked_text_width(PILL_TEXT, font_label, tracking=PILL_TRACKING)
pill_h = font_label.getbbox("Ag")[3] - font_label.getbbox("Ag")[1]

pill_w = pill_text_w + PILL_PAD_X * 2
pill_box_h = pill_h + PILL_PAD_Y * 2

pill_right = WIDTH - PADDING_X
pill_top   = PUBNAME_Y - 2
pill_left  = pill_right - pill_w
pill_bottom = pill_top + pill_box_h

# Draw pill background (dark amber, very subtle)
pill_bg_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
pbdraw = ImageDraw.Draw(pill_bg_layer)
pbdraw.rounded_rectangle(
    [(pill_left, pill_top), (pill_right, pill_bottom)],
    radius=PILL_RADIUS,
    fill=(PILL_BG[0], PILL_BG[1], PILL_BG[2], 200),
    outline=(ACCENT[0], ACCENT[1], ACCENT[2], 180),
    width=1,
)
img = Image.alpha_composite(img.convert("RGBA"), pill_bg_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# Draw pill text
pill_text_x = pill_left + PILL_PAD_X
pill_text_y = pill_top + PILL_PAD_Y
draw_tracked_text(
    draw,
    (pill_text_x, pill_text_y),
    PILL_TEXT,
    font_label,
    ACCENT,
    tracking=PILL_TRACKING,
)

# ---------------------------------------------------------------------------
# 4. Thin rule below pubname/pill row (secondary separator)
# ---------------------------------------------------------------------------

SECOND_RULE_Y = PUBNAME_Y + pill_box_h + 10
draw.line(
    [(PADDING_X, SECOND_RULE_Y), (WIDTH - PADDING_X, SECOND_RULE_Y)],
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 60),
    width=1,
)

# The second rule line requires RGBA for alpha -- use a layer
rule2_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
r2draw = ImageDraw.Draw(rule2_layer)
r2draw.line(
    [(PADDING_X, SECOND_RULE_Y), (WIDTH - PADDING_X, SECOND_RULE_Y)],
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 55),
    width=1,
)
img = Image.alpha_composite(img.convert("RGBA"), rule2_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# 5. Main title: "The Pipeline"
#    Bebas Neue all-caps, size chosen to not exceed canvas width
# ---------------------------------------------------------------------------

TITLE_TEXT = "THE PIPELINE"

title_bbox_raw = font_title_lg.getbbox(TITLE_TEXT)
title_w = title_bbox_raw[2] - title_bbox_raw[0]
max_title_w = WIDTH - PADDING_X * 2

if title_w > max_title_w:
    scale = max_title_w / title_w
    font_title_use = load_font(BEBAS_PATH, int(220 * scale))
else:
    font_title_use = font_title_lg

title_bbox_use = font_title_use.getbbox(TITLE_TEXT)
title_h = title_bbox_use[3] - title_bbox_use[1]
title_glyph_bottom = title_bbox_use[3]  # actual rendered bottom = TITLE_Y + this

# ---------------------------------------------------------------------------
# 6. Subtitle & metadata -- measure heights so we can center the block
# ---------------------------------------------------------------------------

SUBTITLE_TEXT = "How voter rolls became an enforcement tool"
subtitle_lines = wrap_text(SUBTITLE_TEXT, font_subtitle, WIDTH - PADDING_X * 2)
sub_line_h = font_subtitle.getbbox("Ag")[3] - font_subtitle.getbbox("Ag")[1]
sub_block_h = len(subtitle_lines) * (sub_line_h + 8) - 8  # last line has no trailing gap

meta_h = font_meta.getbbox("Ag")[3] - font_meta.getbbox("Ag")[1]

# Total block: title glyph bottom + gap + subtitle + gap + divider + meta_gap + meta
# Use title_glyph_bottom (bbox y1) for offset, not visual title_h, for accurate layout
TITLE_TO_SUB_GAP = 22
SUB_TO_DIVIDER_GAP = 26
DIVIDER_H = 1
total_block_h = title_glyph_bottom + TITLE_TO_SUB_GAP + sub_block_h + SUB_TO_DIVIDER_GAP + DIVIDER_H + META_GAP + meta_h

# Usable zone: SECOND_RULE_Y to BOTTOM_RULE_Y
usable_h = BOTTOM_RULE_Y - SECOND_RULE_Y
# Place block slightly above center (upper 45% of usable zone) for visual weight
TITLE_Y = SECOND_RULE_Y + int((usable_h - total_block_h) * 0.38)

# Draw title
draw.text((PADDING_X, TITLE_Y), TITLE_TEXT, font=font_title_use, fill=TEXT_PRI)

# Draw subtitle -- anchor to actual glyph bottom (TITLE_Y + title_glyph_bottom)
subtitle_y_base = TITLE_Y + title_glyph_bottom + TITLE_TO_SUB_GAP

for i, line in enumerate(subtitle_lines):
    draw.text(
        (PADDING_X, subtitle_y_base + i * (sub_line_h + 8)),
        line,
        font=font_subtitle,
        fill=TEXT_SEC,
    )

# ---------------------------------------------------------------------------
# 7. Short accent divider + metadata row
# ---------------------------------------------------------------------------

divider_y = subtitle_y_base + sub_block_h + 8 + SUB_TO_DIVIDER_GAP  # +8 for last line spacing

draw.line(
    [(PADDING_X, divider_y), (PADDING_X + 180, divider_y)],
    fill=ACCENT, width=1,
)

meta_y = divider_y + META_GAP
META_TEXT = "SD #9  |  MARCH 21, 2026"
draw_tracked_text(
    draw,
    (PADDING_X, meta_y),
    META_TEXT,
    font_meta,
    TEXT_SEC,
    tracking=2,
)

# ---------------------------------------------------------------------------
# 8. Full-width bottom horizontal rule (mirrors the top -- bulletin feel)
# ---------------------------------------------------------------------------

bottom_rule_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
brdraw = ImageDraw.Draw(bottom_rule_layer)
brdraw.line(
    [(PADDING_X, BOTTOM_RULE_Y), (WIDTH - PADDING_X, BOTTOM_RULE_Y)],
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 90),
    width=1,
)
img = Image.alpha_composite(img.convert("RGBA"), bottom_rule_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# 9. Right-side subtle vertical bar (brand constant)
# ---------------------------------------------------------------------------

bar_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
bdraw = ImageDraw.Draw(bar_layer)
bdraw.line(
    [(WIDTH - PADDING_X, PADDING_Y), (WIDTH - PADDING_X, HEIGHT - PADDING_Y)],
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 40),
    width=1,
)
img = Image.alpha_composite(img.convert("RGBA"), bar_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# 10. Issue number watermark -- very faint bottom-right
# ---------------------------------------------------------------------------

issue_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
idraw = ImageDraw.Draw(issue_layer)
issue_text = "#9"
ibbox = font_issue_wm.getbbox(issue_text)
# ibbox = (x0, y0, x1, y1) -- y0 is the top bearing offset
# To anchor glyph bottom at BOTTOM_RULE_Y + 30 (bleeding below the rule):
# issue_y + ibbox[3] = BOTTOM_RULE_Y + 30  =>  issue_y = BOTTOM_RULE_Y + 30 - ibbox[3]
iw = ibbox[2] - ibbox[0]
issue_x = WIDTH - PADDING_X - iw - 15
issue_y = BOTTOM_RULE_Y + 30 - ibbox[3]
idraw.text(
    (issue_x, issue_y),
    issue_text,
    font=font_issue_wm,
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 22),
)
img = Image.alpha_composite(img.convert("RGBA"), issue_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

img.save(OUTPUT_PATH, "PNG", optimize=True)
print(f"Saved: {OUTPUT_PATH}")
print(f"Size:  {img.size[0]} x {img.size[1]} px")

"""
Signal Dispatch OG Image Generator
Issue #12: "The Gap"
Output: 1200 x 630 px PNG
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = "/path/to/home/projects/signal-dispatch/content/drafts/12-og-image.png"
BEBAS_PATH  = "/path/to/home/projects/signal-dispatch/content/brand/BebasNeue-Regular.ttf"
WIDTH, HEIGHT = 1200, 630

BG_TOP    = (10, 15, 26)
BG_BOTTOM = (14, 20, 36)
ACCENT    = (212, 133, 58)
TEXT_PRI  = (240, 237, 232)
TEXT_SEC  = (180, 175, 165)
GRID_COL  = (30, 42, 60)

PADDING_X = 72
PADDING_Y = 60


def load_font(path, size):
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for candidate in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    return ImageFont.load_default()


img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
draw = ImageDraw.Draw(img)

for y in range(HEIGHT):
    t = y / HEIGHT
    r = int(BG_TOP[0] + t * (BG_BOTTOM[0] - BG_TOP[0]))
    g = int(BG_TOP[1] + t * (BG_BOTTOM[1] - BG_TOP[1]))
    b = int(BG_TOP[2] + t * (BG_BOTTOM[2] - BG_TOP[2]))
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

GRID_STEP = 32
DOT_RADIUS = 1
DOT_ALPHA = 35

texture = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(texture)

random.seed(12)
for gx in range(0, WIDTH + GRID_STEP, GRID_STEP):
    for gy in range(0, HEIGHT + GRID_STEP, GRID_STEP):
        jx = random.randint(-2, 2)
        jy = random.randint(-2, 2)
        cx, cy = gx + jx, gy + jy
        tdraw.ellipse(
            [(cx - DOT_RADIUS, cy - DOT_RADIUS),
             (cx + DOT_RADIUS, cy + DOT_RADIUS)],
            fill=(GRID_COL[0], GRID_COL[1], GRID_COL[2], DOT_ALPHA),
        )

img = Image.alpha_composite(img.convert("RGBA"), texture).convert("RGB")
draw = ImageDraw.Draw(img)

SCAN_ALPHA = 12
scan_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(scan_layer)
for sy in range(0, HEIGHT, 4):
    sdraw.line([(0, sy), (WIDTH, sy)], fill=(0, 0, 0, SCAN_ALPHA))
img = Image.alpha_composite(img.convert("RGBA"), scan_layer).convert("RGB")
draw = ImageDraw.Draw(img)

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

font_title_lg  = load_font(BEBAS_PATH, 160)
font_pubname   = load_font(BEBAS_PATH, 17)
font_subtitle  = load_font(BEBAS_PATH, 30)
font_meta      = load_font(BEBAS_PATH, 18)


def draw_tracked_text(draw, pos, text, font, fill, tracking=3):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = font.getbbox(ch)
        x += (bbox[2] - bbox[0]) + tracking
    return x


TOP_ROW_Y  = PADDING_Y
TITLE_Y    = 120
SUBTITLE_Y = 370
DIVIDER_Y  = 450
META_Y     = 478

PUB_TEXT     = "SIGNAL DISPATCH"
PUB_TRACKING = 5

pub_x  = PADDING_X
dash_y = TOP_ROW_Y + 10

draw.line(
    [(pub_x, dash_y), (pub_x + 28, dash_y)],
    fill=ACCENT, width=2,
)

pub_text_x = pub_x + 28 + 12
final_x = draw_tracked_text(
    draw,
    (pub_text_x, TOP_ROW_Y),
    PUB_TEXT,
    font_pubname,
    ACCENT,
    tracking=PUB_TRACKING,
)

RIGHT_LINE_X = WIDTH - PADDING_X
if final_x + 20 < RIGHT_LINE_X:
    draw.line(
        [(final_x + 12, dash_y), (RIGHT_LINE_X, dash_y)],
        fill=ACCENT, width=2,
    )

TITLE_TEXT = "THE GAP"
draw.text((PADDING_X, TITLE_Y), TITLE_TEXT, font=font_title_lg, fill=TEXT_PRI)

SUBTITLE_TEXT = "How Electricity Regulation Lets Utilities"
SUBTITLE_TEXT2 = "Choose Data Centers Over Communities"
draw.text((PADDING_X, SUBTITLE_Y), SUBTITLE_TEXT, font=font_subtitle, fill=TEXT_SEC)
draw.text((PADDING_X, SUBTITLE_Y + 40), SUBTITLE_TEXT2, font=font_subtitle, fill=TEXT_SEC)

draw.line(
    [(PADDING_X, DIVIDER_Y), (PADDING_X + 200, DIVIDER_Y)],
    fill=ACCENT, width=1,
)

META_TEXT = "DEEP DIVE  |  MAY 16, 2026"
draw_tracked_text(
    draw,
    (PADDING_X, META_Y),
    META_TEXT,
    font_meta,
    TEXT_SEC,
    tracking=2,
)

BAR_X  = WIDTH - PADDING_X
bar_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
bdraw = ImageDraw.Draw(bar_layer)
bdraw.line([(BAR_X, PADDING_Y), (BAR_X, HEIGHT - PADDING_Y)], fill=(ACCENT[0], ACCENT[1], ACCENT[2], 55), width=1)
img = Image.alpha_composite(img.convert("RGBA"), bar_layer).convert("RGB")
draw = ImageDraw.Draw(img)

issue_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
idraw = ImageDraw.Draw(issue_layer)
font_issue = load_font(BEBAS_PATH, 200)
issue_text = "12"
ibbox = font_issue.getbbox(issue_text)
iw = ibbox[2] - ibbox[0]
ih = ibbox[3] - ibbox[1]
issue_x = WIDTH - PADDING_X - iw - 10
issue_y = HEIGHT - ih - PADDING_Y + 20
idraw.text(
    (issue_x, issue_y),
    issue_text,
    font=font_issue,
    fill=(ACCENT[0], ACCENT[1], ACCENT[2], 22),
)
img = Image.alpha_composite(img.convert("RGBA"), issue_layer).convert("RGB")

img.save(OUTPUT_PATH, "PNG", optimize=True)
print(f"\nSaved: {OUTPUT_PATH}")
print(f"Size:  {img.size[0]} x {img.size[1]} px")

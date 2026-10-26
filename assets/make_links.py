"""The link band between sheet 1 and sheet 2: four cells, one image each.

Each cell is a quarter of the drawing's width, so the README can make each one a
real link (links inside an image are not clickable) while the band still reads
as part of the sheet: the left and right cells carry the frame's side lines.
Built by make_profile.py.
"""
import os

from sheet import THEMES, esc, open_svg, write

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 225, 64            # four cells across the 900-wide sheet

LINKS = [
    ('website', 'WEBSITE', 'navyrobson.com', 'www'),
    ('linkedin', 'LINKEDIN', 'in/navy-robson', 'in'),
    ('upwork', 'UPWORK', 'freelancers/navyrobson', 'Up'),
    ('code', 'CODE', 'github.com/nrobson3', '</>'),
]
BADGE_FONT = "'Segoe UI', Arial, Helvetica, sans-serif"


def badge(c, x, y, glyph):
    """Solid rounded square with the glyph knocked out, in the sheet's ink."""
    s = 28
    o = ['<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="5" fill="%s"/>' % (x, y, s, s, c['ink'])]
    size = 15 if len(glyph) <= 2 else (9.5 if glyph == 'www' else 11.5)
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="%s" font-size="%.1f" font-weight="700" '
             'fill="%s">%s</text>' % (x + s / 2, y + s / 2 + size * 0.36, BADGE_FONT, size, c['bg'], esc(glyph)))
    return o


def cell(c, framed, i, label, value, glyph):
    first, last = i == 0, i == len(LINKS) - 1
    o = [open_svg(W, H, '%s: %s' % (label, value))]
    o += framed(c, W, H, open_top=True, open_bottom=True, left=first, right=last, rules=False)
    x0 = 18.5 if first else 0.0
    x1 = W - 18.5 if last else W
    if not first:      # cell divider, drawn by the cell on its right
        o.append('<line x1="0.7" y1="0" x2="0.7" y2="%d" stroke="%s" stroke-width="1.4"/>' % (H, c['ink']))
    bx = x0 + 16
    o += badge(c, bx, (H - 28) / 2, glyph)
    tx = bx + 28 + 12
    o.append('<text x="%.1f" y="%d" font-size="10" letter-spacing="2" fill="%s">%s</text>' % (tx, 27, c['accent'], esc(label)))
    room = (x1 - 30) - tx
    size = min(13.5, room / (0.6 * len(value)))
    o.append('<text x="%.1f" y="%d" font-size="%.1f" fill="%s">%s</text>' % (tx, 45, size, c['ink'], esc(value)))
    ax, ay = x1 - 18, H // 2
    o.append('<g fill="none" stroke="%s" stroke-width="1.4" stroke-linecap="square">' % c['accent'])
    o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>' % (ax - 6, ay + 6, ax + 5, ay - 5))
    o.append('<polyline points="%.1f,%d %.1f,%d %.1f,%d"/>' % (ax - 2, ay - 5, ax + 5, ay - 5, ax + 5, ay + 2))
    o.append('</g></svg>')
    return '\n'.join(o)


def build(framed):
    for i, (key, label, value, glyph) in enumerate(LINKS):
        for t, c in THEMES.items():
            write(os.path.join(HERE, 'link-%s-%s.svg' % (key, t)), cell(c, framed, i, label, value, glyph))

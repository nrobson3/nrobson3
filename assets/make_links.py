"""Link tiles under the profile card, drawn as drawing callouts.

Each tile is its own small image so the README can wrap it in a real link
(links inside an SVG shown as an image are not clickable).

    python make_links.py   ->  link-<name>-dark.svg, link-<name>-light.svg
"""
import os

from sheet import THEMES, esc, open_svg, write

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 264, 58

LINKS = [
    ('linkedin', 'LINKEDIN', 'in/navy-robson'),
    ('upwork', 'UPWORK', 'freelancers/navyrobson'),
    ('code', 'CODE', 'fusion360-parametric-parts'),
]


def tile(c, label, value):
    o = [open_svg(W, H, '%s: %s' % (label, value))]
    o.append('<rect width="%d" height="%d" rx="5" fill="%s"/>' % (W, H, c['bg']))
    o.append('<rect x="3.5" y="3.5" width="%d" height="%d" fill="none" stroke="%s" stroke-width="1.3"/>'
             % (W - 7, H - 7, c['ink']))
    # leader line from a datum dot, like a callout on a drawing
    o.append('<circle cx="17" cy="%d" r="2.6" fill="%s"/>' % (H // 2, c['ink']))
    o.append('<line x1="17" y1="%d" x2="30" y2="%d" stroke="%s" stroke-width="1"/>' % (H // 2, H // 2, c['muted']))
    o.append('<text x="38" y="24" font-size="10" letter-spacing="2" fill="%s">%s</text>' % (c['muted'], esc(label)))
    # shrink long values so they stop short of the arrow (0.6 em is a wide monospace fallback)
    size = min(13.5, (W - 38 - 40) / (0.6 * len(value)))
    o.append('<text x="38" y="42" font-size="%.1f" fill="%s">%s</text>' % (size, c['ink'], esc(value)))
    # arrow out of the sheet
    ax, ay = W - 22, H // 2
    o.append('<g fill="none" stroke="%s" stroke-width="1.4" stroke-linecap="square">' % c['ink'])
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d"/>' % (ax - 6, ay + 6, ax + 5, ay - 5))
    o.append('<polyline points="%d,%d %d,%d %d,%d"/>' % (ax - 2, ay - 5, ax + 5, ay - 5, ax + 5, ay + 2))
    o.append('</g></svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    for key, label, value in LINKS:
        for t, c in THEMES.items():
            p = os.path.join(HERE, 'link-%s-%s.svg' % (key, t))
            write(p, tile(c, label, value))
            print(p)

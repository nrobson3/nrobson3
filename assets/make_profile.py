"""Stacks the three sheets into one continuous drawing for the profile README.

    python make_profile.py    ->  profile-dark.svg, profile-light.svg

Each sheet is built by its own module; here their outer frames are dropped and
they are stacked so each sheet's bottom frame line is the next sheet's top
line, inside one frame. GitHub leaves a gap between separate images, so one
image is the only way to have no seams. The link tiles stay separate images
because a link inside an image cannot be clicked.
"""
import os

from sheet import THEMES, frame, open_svg, write
import make_card
import make_portrait
import make_stats

HERE = os.path.dirname(os.path.abspath(__file__))
W = 900
INSET = 18.5              # inner frame line, from sheet.frame()


def inner(svg, c, h):
    """Drop a sheet's <svg> wrapper and its frame, keep everything drawn inside."""
    drop = set(frame(c, W, h))
    lines = svg.split('\n')
    return [l for l in lines[1:-1] if l not in drop and not l.startswith('<style>')]


def profile(theme, g):
    c = THEMES[theme]
    sheets = [(make_card.H, make_card.card(theme)),
              (make_portrait.H, make_portrait.sheet(c)),
              (make_stats.H, make_stats.sheet(c, g))]
    total = sum(h for h, _ in sheets) - int(2 * INSET) * (len(sheets) - 1)
    o = [open_svg(W, total, 'Navy Robson: engineering student at Western University; Fusion 360 '
                  'mechanical design; portrait and spec list; Upwork and GitHub figures'),
         '<style>text, tspan { white-space: pre; }</style>']
    o += frame(c, W, total)
    off = 0
    for i, (h, svg) in enumerate(sheets):
        o.append('<g transform="translate(0 %d)">' % off)
        o += inner(svg, c, h)
        o.append('</g>')
        if i < len(sheets) - 1:   # shared edge: this sheet's bottom line is the next one's top
            y = off + h - INSET
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
                     % (INSET, y, W - INSET, y, c['ink']))
        off += h - int(2 * INSET)
    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    g = make_stats.github_numbers()
    print('repos %d, scripts %d, tests %d, last 30 days %d'
          % (g['repos'], g['scripts'], g['tests'], sum(g['series'])))
    for t in THEMES:
        p = os.path.join(HERE, 'profile-%s.svg' % t)
        write(p, profile(t, g))
        print(p, os.path.getsize(p), 'bytes')

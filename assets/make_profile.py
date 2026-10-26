"""Builds the profile drawing as three stacked pieces that read as one sheet.

    python make_profile.py    ->  profile-top-*.svg, link-*-*.svg, profile-bottom-*.svg

  top     sheet 1, frame open at the bottom
  band    four link cells, each its own image so it can be a real link; the
          outer cells carry the drawing's side frame lines
  bottom  sheets 2 and 3 sharing an edge, frame open at the top

The README puts all five images on one line with align="top" and widths of
100% / 33.333% x3 / 100%, which removes GitHub's gap under inline images, so
the pieces meet edge to edge.
"""
import os

from sheet import THEMES, esc, open_svg, write
import make_card
import make_links
import make_portrait
import make_stats

HERE = os.path.dirname(os.path.abspath(__file__))
W = 900
INSET = 18.5              # inner frame line in every sheet
EDGE = 0.7                # half the frame stroke: an open edge's shared line sits here


def inner(svg, c, h):
    """A sheet's drawing without its <svg> wrapper and its own frame."""
    from sheet import frame
    drop = set(frame(c, W, h))
    return [l for l in svg.split('\n')[1:-1] if l not in drop and not l.startswith('<style>')]


def framed(c, w, h, open_top=False, open_bottom=False, left=True, right=True, rules=True):
    """Background and frame for one piece; open edges run to the piece boundary.
    rules=False leaves out the top and bottom frame lines (the band between pieces
    uses the neighbours' lines)."""
    o = ['<rect x="0" y="%d" width="%d" height="%d" rx="6" fill="%s"/>'
         % (-10 if open_top else 0, w, h + (10 if open_top else 0) + (10 if open_bottom else 0), c['bg'])]
    for x0, ok in ((8.5, left), (w - 8.5, right)):            # outer faint border
        if ok:
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
                     % (x0, 0 if open_top else 8.5, x0, h if open_bottom else h - 8.5, c['faint']))
    for x0, ok in ((INSET, left), (w - INSET, right)):        # inner frame
        if ok:
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
                     % (x0, 0 if open_top else INSET, x0, h if open_bottom else h - INSET, c['ink']))
    if not open_top:
        o.append('<line x1="8.5" y1="8.5" x2="%.1f" y2="8.5" stroke="%s" stroke-width="1"/>' % (w - 8.5, c['faint']))
    if not open_bottom:
        o.append('<line x1="8.5" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>' % (h - 8.5, w - 8.5, h - 8.5, c['faint']))
    if not rules:
        return o
    top_y = EDGE if open_top else INSET
    bot_y = h - EDGE if open_bottom else h - INSET
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>' % (INSET, top_y, w - INSET, top_y, c['ink']))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>' % (INSET, bot_y, w - INSET, bot_y, c['ink']))
    return o


def top(theme):
    c = THEMES[theme]
    h = make_card.H - int(INSET)                      # cut just below the title block
    o = [open_svg(W, h, 'Navy Robson: engineering student at Western University; Fusion 360 mechanical design')]
    o += framed(c, W, h, open_bottom=True)
    o += inner(make_card.card(theme), c, make_card.H)
    o.append('</svg>')
    return '\n'.join(o)


def bottom(theme, g):
    c = THEMES[theme]
    sheets = [(make_portrait.H, make_portrait.sheet(c)), (make_stats.H, make_stats.sheet(c, g))]
    shift = INSET - EDGE                              # drop everything above the shared top line
    h = int(round(sum(s for s, _ in sheets) - 2 * INSET * (len(sheets) - 1) - shift))
    o = [open_svg(W, h, 'Character portrait of Navy Robson beside a spec list; Upwork and GitHub figures'),
         '<style>text, tspan { white-space: pre; }</style>']
    o += framed(c, W, h, open_top=True)
    off = -shift
    for i, (sh, svg) in enumerate(sheets):
        o.append('<g transform="translate(0 %.1f)">' % off)
        o += inner(svg, c, sh)
        o.append('</g>')
        if i < len(sheets) - 1:
            y = off + sh - INSET
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.4"/>'
                     % (INSET, y, W - INSET, y, c['ink']))
        off += sh - 2 * INSET
    o.append('</svg>')
    return '\n'.join(o)


LINK_URLS = {
    'website': ('https://navyrobson.com', 'Website: navyrobson.com'),
    'linkedin': ('https://www.linkedin.com/in/navy-robson', 'LinkedIn: in/navy-robson'),
    'upwork': ('https://www.upwork.com/freelancers/navyrobson', 'Upwork: freelancers/navyrobson'),
    'code': ('https://github.com/nrobson3?tab=repositories', 'Code: github.com/nrobson3'),
}
TOP_ALT = ('Navy Robson. Engineering student at Western University (common first year). Fusion 360 '
           'mechanical design: mechanisms, moulded-part DFM, GD&T drawings; Python and the Fusion API.')
BOTTOM_ALT = ('Character portrait of Navy Robson beside a spec list, then Upwork figures (Job Success, rating, '
              'jobs, earnings) and GitHub figures with contributions over the last 30 days.')


def readme():
    """One line, no spaces between tags: the pieces must sit edge to edge. Each image
    path carries a hash of its contents, so a changed image is never served from cache."""
    import hashlib

    def src(name):
        data = open(os.path.join(HERE, name), 'rb').read()
        return 'assets/%s?v=%s' % (name, hashlib.sha1(data).hexdigest()[:8])

    def pic(stem, alt, width):
        return ('<picture><source media="(prefers-color-scheme: dark)" srcset="%s"><img alt="%s" src="%s" '
                'width="%s" align="top"></picture>' % (src(stem + '-dark.svg'), esc(alt).replace('"', '&quot;'),
                                                       src(stem + '-light.svg'), width))
    parts = [pic('profile-top', TOP_ALT, '100%')]
    for key, (url, alt) in LINK_URLS.items():
        parts.append('<a href="%s">%s</a>' % (url, pic('link-' + key, alt, '25%')))
    parts.append(pic('profile-bottom', BOTTOM_ALT, '100%'))
    with open(os.path.join(os.path.dirname(HERE), 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(parts) + '\n')


if __name__ == '__main__':
    g = make_stats.github_numbers()
    print('repos %d, scripts %d, tests %d, last 30 days %d'
          % (g['repos'], g['scripts'], g['tests'], sum(g['series'])))
    for t in THEMES:
        write(os.path.join(HERE, 'profile-top-%s.svg' % t), top(t))
        write(os.path.join(HERE, 'profile-bottom-%s.svg' % t), bottom(t, g))
    make_links.build(framed)
    readme()
    print('wrote profile-top, link cells, profile-bottom (dark and light) and README.md')

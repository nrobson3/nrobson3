"""Sheet 2 of the profile: a neofetch-style spec list beside a character portrait.

    python make_portrait.py   ->  portrait-dark.svg, portrait-light.svg

The portrait comes from portrait.txt (made by photo_to_ascii.py). Edit SECTIONS
to change the text; values are right-aligned with dot leaders, as in neofetch.
"""
import os

from sheet import THEMES, esc, frame, open_svg, title_block, write

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 900, 540

USER = 'navy@robson'
SECTIONS = [
    (USER, [
        ('Host', 'Western University, Ontario'),
        ('Kernel', 'Engineering, common first year'),
        ('Uptime', 'Year 1 of 5, co-op included'),
        ('Shell', 'Autodesk Fusion 360'),
        ('Scripting', 'Python, Fusion 360 API'),
        ('CAD', 'Fusion 360, Onshape'),
        ('Languages.Real', 'English'),
    ]),
    ('Engineering', [
        ('Mechanisms', 'gear trains, linkages, gimbals'),
        ('Moulded.Parts', 'snap fits, draft, parting lines'),
        ('Drawings', 'GD&T, ISO first-angle'),
    ]),
    ('Currently', [
        ('Team', 'Western Formula Racing (recruit)'),
        ('Building', 'service brake, manual override'),
        ('Learning', 'FEA in SolidWorks'),
    ]),
    ('Freelance', [
        ('Platform', 'Upwork'),
        ('Clients', 'product makers, inventors'),
    ]),
]
WIDTH = 52              # characters per line on the text side
TEXT_SIZE = 13.2        # px; Consolas is 0.55 em wide, so 52 chars is about 380 px
LINE = 20.5
ART_SIZE = 12.2
ART_LINE = 13.6


def line_items():
    """Yield (kind, parts) rows: a section rule, or a key / dots / value row."""
    for i, (title, rows) in enumerate(SECTIONS):
        if i:
            yield 'gap', None
        lead = '' if i == 0 else '- '
        yield 'rule', (lead + title + ' ', '-' * max(3, WIDTH - len(lead + title) - 1))
        for key, value in rows:
            head = '. ' + key + ': '
            dots = '.' * max(2, WIDTH - len(head) - len(value) - 1) + ' '
            yield 'row', (head, dots, value)


def sheet(c):
    o = [open_svg(W, H, 'Navy Robson: ' + '; '.join('%s %s' % (k, v) for _, rows in SECTIONS for k, v in rows))]
    # keep runs of spaces: the portrait and the dot leaders are laid out in characters
    o.append('<style>text, tspan { white-space: pre; }</style>')
    o += frame(c, W, H)
    items = list(line_items())
    block = sum(LINE * (0.6 if k == 'gap' else 1) for k, _ in items) - LINE
    x0, y = 44, 19 + (H - 64 - 19 - block) / 2 + TEXT_SIZE * 0.35
    for kind, parts in items:
        if kind == 'gap':
            y += LINE * 0.6
            continue
        if kind == 'rule':
            title, dashes = parts
            o.append('<text x="%d" y="%.1f" font-size="%.1f" xml:space="preserve"><tspan fill="%s" font-weight="700">%s</tspan>'
                     '<tspan fill="%s">%s</tspan></text>' % (x0, y, TEXT_SIZE, c['ink'], esc(title), c['faint'], dashes))
        else:
            head, dots, value = parts
            key = head[2:]
            o.append('<text x="%d" y="%.1f" font-size="%.1f" xml:space="preserve"><tspan fill="%s">. </tspan>'
                     '<tspan fill="%s">%s</tspan><tspan fill="%s">%s</tspan><tspan fill="%s">%s</tspan></text>'
                     % (x0, y, TEXT_SIZE, c['faint'], c['muted'], esc(key), c['faint'], dots, c['ink'], esc(value)))
        y += LINE

    # portrait, centred in the right-hand view
    art = open(os.path.join(HERE, 'portrait.txt'), encoding='utf-8').read().rstrip('\n').split('\n')
    cols = max(len(l) for l in art)
    art_w = cols * ART_SIZE * 0.55
    ax = 668 - art_w / 2
    ay = 19 + (H - 64 - 19 - len(art) * ART_LINE) / 2 + ART_SIZE
    o.append('<g font-size="%.1f" fill="%s" xml:space="preserve">' % (ART_SIZE, c['ink']))
    for i, l in enumerate(art):
        if l.strip():
            o.append('<text x="%.1f" y="%.1f">%s</text>' % (ax, ay + i * ART_LINE, esc(l)))
    o.append('</g>')
    o.append('<line x1="476.5" y1="19" x2="476.5" y2="%d" stroke="%s" stroke-width="1"/>' % (H - 64, c['faint']))

    o += title_block(c, W, H, [('DRAWN', 'N. ROBSON'), ('DWG', 'NR-002'), ('REV', 'A'),
                               ('VIEW', 'PORTRAIT'), ('SHEET', '2 / 3')])
    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    for t, c in THEMES.items():
        p = os.path.join(HERE, 'portrait-%s.svg' % t)
        write(p, sheet(c))
        print(p, os.path.getsize(p), 'bytes')

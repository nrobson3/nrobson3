"""Shared drawing-sheet style for the profile SVGs: themes, frame, title block."""

THEMES = {
    'dark': {'bg': '#0a0a0a', 'ink': '#e8e8e8', 'muted': '#8a8a8a', 'faint': '#3a3a3a'},
    'light': {'bg': '#ffffff', 'ink': '#141414', 'muted': '#6a6a6a', 'faint': '#cfcfcf'},
}
FONT = "Consolas, 'DejaVu Sans Mono', Menlo, 'Liberation Mono', monospace"


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;')


def open_svg(w, h, label):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, esc(label)))


def frame(c, w, h):
    """Sheet background, outer border and the heavier inner frame."""
    return ['<rect width="%d" height="%d" rx="6" fill="%s"/>' % (w, h, c['bg']),
            '<rect x="8.5" y="8.5" width="%d" height="%d" fill="none" stroke="%s" stroke-width="1"/>'
            % (w - 17, h - 17, c['faint']),
            '<rect x="18.5" y="18.5" width="%d" height="%d" fill="none" stroke="%s" stroke-width="1.4"/>'
            % (w - 37, h - 37, c['ink'])]


def title_block(c, w, h, cells):
    """Strip along the bottom of the sheet: (label, value) cells, then a first-angle
    projection symbol in the last cell."""
    o = []
    ty = h - 64
    o.append('<line x1="19" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4"/>' % (ty, w - 19, ty, c['ink']))
    n = len(cells) + 1
    cw = (w - 38) / n
    for i in range(1, n):
        x = 19 + cw * i
        o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>' % (x, ty, x, h - 19, c['ink']))
    for i, (k, v) in enumerate(cells):
        x = 19 + cw * i + 8
        o.append('<text x="%.1f" y="%d" font-size="10" fill="%s">%s</text>' % (x, ty + 16, c['muted'], esc(k)))
        o.append('<text x="%.1f" y="%d" font-size="14" fill="%s">%s</text>' % (x, ty + 35, c['ink'], esc(v)))
    fx, fy = 19 + cw * (n - 1) + cw / 2, ty + 23
    o.append('<g fill="none" stroke="%s" stroke-width="1">' % c['ink'])
    o.append('<circle cx="%.1f" cy="%.1f" r="9"/><circle cx="%.1f" cy="%.1f" r="4.5"/>' % (fx + 22, fy, fx + 22, fy))
    o.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f"/>' % (
        fx - 30, fy - 4.5, fx - 6, fy - 9, fx - 6, fy + 9, fx - 30, fy + 4.5))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-dasharray="6 2 1.5 2"/>' % (
        fx - 36, fy, fx + 36, fy, c['muted']))
    o.append('</g>')
    return o


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)

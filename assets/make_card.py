"""Builds the profile card: a drawing-sheet SVG with a live planetary gear set.

The gear outlines are true involutes and the motion is the real kinematics of a
planetary stage with the ring held: sun at w, carrier at w * Ns/(Ns+Nr), planets
spinning at -(Ns/Np)(w - w_carrier) relative to the carrier. Planet tooth phases
come from the same meshing equations as fusion360-parametric-parts, so the teeth
stay in mesh for the whole loop.

    python make_card.py      ->  card-dark.svg, card-light.svg
"""
import math
import os

from sheet import THEMES, esc, frame, open_svg, title_block, write

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ gear set
M, PA = 1.25, 20.0                 # module (mm), pressure angle (deg)
NS, NP, NR, N_PLANETS = 18, 18, 54, 3
THIN = 0.2                         # tooth thinning per gear (mm), as in the gearbox
RING_OD = 80.0
SUN_PERIOD = 8.0                   # s per sun revolution; carrier takes 4x as long

# ------------------------------------------------------------------ text
NAME = 'NAVY ROBSON'
ROWS = [
    ('Program', ['Engineering, Western University', '(common first year)']),
    ('Focus', ['Mechanisms, moulded-part DFM,', 'GD&T drawings']),
    ('Tools', ['Fusion 360, Python (Fusion API),', 'Onshape']),
    ('Code', ['fusion360-parametric-parts:', 'parts that check their own math']),
    ('Freelance', ['Upwork, 100% Job Success']),
    ('Status', ['Open to co-op & internships']),
]
CAPTION = ['18 / 18 / 54 planetary, ring held', 'sun 4 : 1 carrier, true involutes']
TITLE_BLOCK = [('DRAWN', 'N. ROBSON'), ('DWG', 'NR-001'), ('REV', 'A'), ('UNITS', 'mm'), ('SHEET', '1 / 3')]

W, H = 900, 420


def inv(a):
    return math.tan(a) - a


def wrap(v, p):
    r = math.fmod(v, p)
    return r + p if r < 0 else r


def external_gear(n, phase_deg, steps=10):
    """Closed outline of a whole external gear (mm), tooth 0 centred on phase."""
    pa = math.radians(PA)
    rp = M * n / 2.0
    rb, ra, rf = rp * math.cos(pa), rp + M, rp - 1.25 * M
    psi = math.pi / (2 * n) - (THIN / 2) / rp
    r_lo = max(rf, rb)

    def th(r):
        return psi + inv(pa) - inv(math.acos(min(1.0, rb / r)) if r > rb else 0.0)

    flank = [(rf, th(r_lo))] + [(r_lo + (ra - r_lo) * i / steps, th(r_lo + (ra - r_lo) * i / steps))
                                for i in range(steps + 1)]
    pts = []
    pitch = 2 * math.pi / n
    for k in range(n):
        c = math.radians(phase_deg) + k * pitch
        pts += [(r, c - t) for r, t in flank]                    # leading flank, root to tip
        pts += [(ra, c - th(ra) + 2 * th(ra) * i / 4) for i in range(1, 4)]
        pts += [(r, c + t) for r, t in reversed(flank)]          # trailing flank, tip to root
        a0, a1 = c + th(r_lo), c + pitch - th(r_lo)
        pts += [(rf, a0 + (a1 - a0) * i / 4) for i in range(1, 4)]  # root arc to next tooth
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


def ring_inner(n, phase_deg=0.0, steps=10):
    """Inner (toothed) boundary of an internal gear, mm."""
    pa = math.radians(PA)
    rp = M * n / 2.0
    rb, ra, rf = rp * math.cos(pa), rp - M, rp + 1.25 * M
    psi = math.pi / (2 * n) - (THIN / 2) / rp
    r_lo = max(ra, rb)

    def th(r):   # half-angle of a ring tooth (material) at radius r
        return psi - inv(pa) + inv(math.acos(min(1.0, rb / r)) if r > rb else 0.0)

    flank = [(r_lo + (rf - r_lo) * i / steps, th(r_lo + (rf - r_lo) * i / steps)) for i in range(steps + 1)]
    pts = []
    pitch = 2 * math.pi / n
    for k in range(n):
        c = math.radians(phase_deg) + k * pitch
        pts += [(r_lo, c - th(r_lo) + 2 * th(r_lo) * i / 4) for i in range(0, 5)]  # tooth tip
        pts += [(r, c + t) for r, t in flank]                                    # flank out to root
        a0, a1 = c + th(rf), c + pitch - th(rf)
        pts += [(rf, a0 + (a1 - a0) * i / 4) for i in range(1, 4)]               # root arc (space)
        pts += [(r, c + pitch - t) for r, t in reversed(flank)]                  # flank back in
    return [(r * math.cos(a), r * math.sin(a)) for r, a in pts]


def solve_phases():
    """Sun and planet tooth phases (deg) that mesh with a ring at phase 0.
    Same equations as planetary_gearset.py, spur case."""
    theta = 0.0
    phi_r = 0.0
    phi_s = wrap((180.0 * NP + (NS + NR) * theta - NR * phi_r) / NS, 360.0 / NS)
    planets = []
    for k in range(N_PLANETS):
        th = theta + 360.0 * k / N_PLANETS
        php = wrap(th + 180.0 + (NS / NP) * (th - phi_s) - 180.0 / NP, 360.0 / NP)
        planets.append((th, php))
    return phi_s, planets


# ------------------------------------------------------------------ SVG
def path(pts, s, ox=0.0, oy=0.0):
    d = 'M' + ' L'.join('%.2f %.2f' % (ox + x * s, oy - y * s) for x, y in pts)
    return d + ' Z'


def spin(cx, cy, period, direction=1):
    to = 360 * direction
    return ('<animateTransform attributeName="transform" type="rotate" from="0 %.2f %.2f" '
            'to="%d %.2f %.2f" dur="%.3fs" repeatCount="indefinite"/>' % (cx, cy, to, cx, cy, period))


def card(theme):
    c = THEMES[theme]
    s = 3.05                       # px per mm
    cx, cy = 186, 172              # gear centre
    a = (NS + NP) * M / 2.0        # planet centre distance
    phi_s, planets = solve_phases()

    w_s = 360.0 / SUN_PERIOD
    w_c = w_s * NS / (NS + NR)
    w_rel = -(NS / NP) * (w_s - w_c)          # planet spin relative to the carrier
    # SVG y points down, so a positive maths angle is a negative SVG rotation
    sun_T, car_T, rel_T = 360.0 / w_s, 360.0 / w_c, 360.0 / abs(w_rel)

    o = [open_svg(W, H, 'Navy Robson, engineering student at Western University; '
                       'Fusion 360 mechanical design')]
    o += frame(c, W, H)

    # ---------------- gears
    g = ['<g fill="none" stroke="%s" stroke-width="1.15" stroke-linejoin="round">' % c['ink']]
    # centre lines and pitch circles (chain lines)
    chain = 'stroke="%s" stroke-width="0.8" stroke-dasharray="14 3 2 3"' % c['muted']
    span = (RING_OD / 2 + 8) * s
    g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" %s/>' % (cx - span, cy, cx + span, cy, chain))
    g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" %s/>' % (cx, cy - span, cx, cy + span, chain))
    g.append('<circle cx="%.1f" cy="%.1f" r="%.2f" %s fill="none"/>' % (cx, cy, a * s, chain))
    # ring (held): outer circle + toothed inner boundary, even-odd fill
    ring = path(ring_inner(NR), s, cx, cy)
    outer = 'M%.2f %.2f a%.2f %.2f 0 1 0 %.2f 0 a%.2f %.2f 0 1 0 %.2f 0 Z' % (
        cx - RING_OD / 2 * s, cy, RING_OD / 2 * s, RING_OD / 2 * s, RING_OD * s,
        RING_OD / 2 * s, RING_OD / 2 * s, -RING_OD * s)
    g.append('<path d="%s %s" fill-rule="evenodd" fill="%s" fill-opacity="0.06"/>' % (outer, ring, c['ink']))
    # sun
    g.append('<g>%s<path d="%s"/><circle cx="%.1f" cy="%.1f" r="%.2f"/></g>' % (
        spin(cx, cy, sun_T, -1), path(external_gear(NS, phi_s), s, cx, cy), cx, cy, 2.5 * s))
    # carrier: planets orbit with it and spin relative to it
    g.append('<g>%s' % spin(cx, cy, car_T, -1))
    for th, php in planets:
        px = cx + a * s * math.cos(math.radians(th))
        py = cy - a * s * math.sin(math.radians(th))
        g.append('<g>%s<path d="%s"/><circle cx="%.2f" cy="%.2f" r="%.2f"/>'
                 '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="0.8"/></g>' % (
                     spin(px, py, rel_T, 1 if w_rel < 0 else -1),
                     path(external_gear(NP, php), s, px, py), px, py, 2.7 * s,
                     px - 4 * s, py, px + 4 * s, py, c['muted']))
    g.append('</g></g>')
    o += g

    # caption under the gears
    for i, line in enumerate(CAPTION):
        o.append('<text x="%d" y="%d" text-anchor="middle" font-size="12" fill="%s">%s</text>'
                 % (cx, 315 + 15 * i, c['muted'], esc(line)))

    # divider between the view and the text
    o.append('<line x1="352.5" y1="19" x2="352.5" y2="%d" stroke="%s" stroke-width="1"/>' % (H - 64, c['faint']))

    # ---------------- text
    x0, y = 382, 66
    o.append('<text x="%d" y="%d" font-size="26" font-weight="700" letter-spacing="3" fill="%s">%s</text>'
             % (x0, y, c['ink'], NAME))
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (x0, y + 14, W - 44, y + 14, c['faint']))
    y += 46
    col = 12                                     # label column width, characters
    for label, values in ROWS:
        for j, v in enumerate(values):
            lead = (label + ' ').ljust(col, '.') + ' ' if j == 0 else ' ' * (col + 1)
            o.append('<text x="%d" y="%d" font-size="15" xml:space="preserve">'
                     '<tspan fill="%s">%s</tspan><tspan fill="%s">%s</tspan></text>'
                     % (x0, y, c['muted'], esc(lead), c['ink'], esc(v)))
            y += 21
        y += 9

    o += title_block(c, W, H, TITLE_BLOCK)
    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    for t in THEMES:
        p = os.path.join(HERE, 'card-%s.svg' % t)
        write(p, card(t))
        print(p, os.path.getsize(p), 'bytes')

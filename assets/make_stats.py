"""Sheet 2 of the profile: performance data.

GitHub numbers are fetched live with the GitHub CLI when you run this; the
Upwork figures have no public API, so they are set by hand below. Nothing runs
on a schedule: refresh with

    python make_stats.py      ->  stats-dark.svg, stats-light.svg

then commit the two SVGs when you want the profile to show the new numbers.
"""
import datetime as dt
import glob
import json
import os
import shutil
import subprocess

from sheet import THEMES, esc, frame, open_svg, title_block, write

HERE = os.path.dirname(os.path.abspath(__file__))
USER = 'nrobson3'
W, H = 900, 300

# ------------------------------------------------------------------ Upwork figures
# Kept in profile_data.json: the weekly update refreshes jobs and earnings from the
# Upwork connector; Job Success and rating are not exposed there, so they are set by hand.
_DATA = json.load(open(os.path.join(HERE, 'profile_data.json'), encoding='utf-8'))['upwork']
UPWORK = [
    (_DATA['job_success'], 'JOB SUCCESS'),
    (_DATA['rating'], 'CLIENT RATING'),
    (_DATA['jobs'], 'JOBS COMPLETED'),
    (_DATA['earned'], 'EARNED'),
]
PARTS_VERIFIED = 3        # parts built and measured in Fusion across the public repos
LOCAL_CLONES = os.path.normpath(os.path.join(HERE, '..', '..'))   # folder holding the repo clones


def gh_bin():
    for c in (shutil.which('gh'), r'C:\Program Files\GitHub CLI\gh.exe'):
        if c and os.path.exists(c):
            return c
    raise SystemExit('GitHub CLI (gh) not found')


def github_numbers():
    today = dt.date.today()
    start = today - dt.timedelta(days=29)
    q = ('query($u:String!,$f:DateTime!,$t:DateTime!){ user(login:$u){'
         ' repositories(first:100, privacy:PUBLIC, ownerAffiliations:OWNER){ totalCount nodes{ name } }'
         ' contributionsCollection(from:$f, to:$t){ contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }')
    out = subprocess.run([gh_bin(), 'api', 'graphql', '-f', 'query=' + q, '-f', 'u=' + USER,
                          '-f', 'f=%sT00:00:00Z' % start, '-f', 't=%sT23:59:59Z' % today],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit('gh api failed: ' + (out.stderr or out.stdout).strip())
    user = json.loads(out.stdout)['data']['user']
    days = {d['date']: d['contributionCount']
            for w in user['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']}
    series = [days.get(str(start + dt.timedelta(days=i)), 0) for i in range(30)]
    repos = [n['name'] for n in user['repositories']['nodes']]
    return {'repos': user['repositories']['totalCount'], 'series': series, 'start': start, 'end': today,
            'scripts': count_local(repos, '*.manifest'), 'tests': count_tests(repos)}


def count_local(repos, pattern):
    """Fusion scripts ship with a .manifest, so count those in the local clones."""
    return sum(len(glob.glob(os.path.join(LOCAL_CLONES, r, '**', pattern), recursive=True)) for r in repos)


def count_tests(repos):
    n = 0
    for r in repos:
        for f in glob.glob(os.path.join(LOCAL_CLONES, r, '**', 'test*.py'), recursive=True):
            n += sum(1 for line in open(f, encoding='utf-8') if line.lstrip().startswith('def test_'))
    return n


def sheet(c, g):
    o = [open_svg(W, H, 'Performance data: Upwork %s; GitHub %d contributions in the last 30 days'
                  % (', '.join('%s %s' % (v, k.lower()) for v, k in UPWORK), sum(g['series'])))]
    o += frame(c, W, H)
    top = 19
    bottom = H - 64

    def heading(x, text):
        o.append('<text x="%d" y="%d" font-size="11" letter-spacing="3" fill="%s">%s</text>'
                 % (x, top + 30, c['muted'], esc(text)))

    # ---------------- Upwork: 2 x 2 figures
    heading(44, 'UPWORK')
    for i, (value, label) in enumerate(UPWORK):
        x = 44 + (i % 2) * 200
        y = top + 86 + (i // 2) * 76
        o.append('<text x="%d" y="%d" font-size="30" font-weight="700" fill="%s">%s</text>' % (x, y, c['ink'], esc(value)))
        o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (x, y + 9, x + 150, y + 9, c['faint']))
        o.append('<text x="%d" y="%d" font-size="10.5" letter-spacing="1.5" fill="%s">%s</text>'
                 % (x, y + 25, c['muted'], esc(label)))

    o.append('<line x1="450.5" y1="%d" x2="450.5" y2="%d" stroke="%s" stroke-width="1"/>' % (top, bottom, c['faint']))

    # ---------------- GitHub: totals row, then the 30-day strip
    gx = 476
    heading(gx, 'GITHUB')
    totals = [(g['repos'], 'PUBLIC REPOS'), (g['scripts'], 'FUSION SCRIPTS'),
              (g['tests'], 'UNIT TESTS'), (PARTS_VERIFIED, 'PARTS VERIFIED')]
    for i, (value, label) in enumerate(totals):
        x = gx + i * 96
        o.append('<text x="%d" y="%d" font-size="24" font-weight="700" fill="%s">%s</text>' % (x, top + 80, c['ink'], value))
        for j, word in enumerate(label.split(' ', 1)):
            o.append('<text x="%d" y="%d" font-size="9.5" letter-spacing="1" fill="%s">%s</text>'
                     % (x, top + 97 + 12 * j, c['muted'], esc(word)))

    series, peak = g['series'], max(max(g['series']), 1)
    cw, gap, sy, sh = 11.0, 1.6, top + 132, 26
    for i, n in enumerate(series):
        x = gx + i * (cw + gap)
        if n:
            o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" fill-opacity="%.2f"/>'
                     % (x, sy, cw, sh, c['ink'], 0.35 + 0.65 * n / peak))
        else:
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" fill="none" stroke="%s" stroke-width="1"/>'
                     % (x + 0.5, sy + 0.5, cw - 1, sh - 1, c['faint']))
    o.append('<text x="%d" y="%d" font-size="12" fill="%s">%d contributions in the last 30 days</text>'
             % (gx, sy + sh + 22, c['muted'], sum(series)))
    o.append('<text x="%d" y="%d" font-size="10" text-anchor="end" fill="%s">%s</text>'
             % (gx + 30 * (cw + gap) - gap, sy + sh + 22, c['muted'], g['end'].strftime('%d %b').upper()))

    o += title_block(c, W, H, [('DRAWN', 'N. ROBSON'), ('DWG', 'NR-003'), ('REV', 'A'),
                               ('AS OF', g['end'].isoformat()), ('SHEET', '3 / 3')])
    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    g = github_numbers()
    print('repos %d, scripts %d, tests %d, last 30 days %d' % (g['repos'], g['scripts'], g['tests'], sum(g['series'])))
    for t, c in THEMES.items():
        p = os.path.join(HERE, 'stats-%s.svg' % t)
        write(p, sheet(c, g))
        print(p)

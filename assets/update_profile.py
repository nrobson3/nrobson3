"""Weekly refresh: rebuild the profile drawing, check it, commit and push.

    python update_profile.py --blocklist PATH [--dry-run]

profile_data.json is edited first (Upwork figures, the Currently lines); this
script then rebuilds profile-*.svg with fresh GitHub numbers and refuses to
publish if anything looks wrong:
  - a Currently value longer than the sheet has room for;
  - any word from the blocklist (kept outside this public repo);
  - a gitleaks finding, when gitleaks is installed.
Commits use a separate author address that is not linked to the account, so the
weekly refresh does not count as a contribution.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MAX_VALUE = 34                       # characters a Currently value can use on the sheet
ALLOWED_KEYS = {'Team', 'Building', 'Learning', 'Next', 'Reading', 'Testing'}
AUTHOR = 'Navy Robson (weekly refresh) <weekly-refresh@nrobson3.invalid>'


def run(cmd, **kw):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit('failed: %s\n%s' % (' '.join(cmd), (r.stderr or r.stdout).strip()))
    return r.stdout


def check_data():
    data = json.load(open(os.path.join(HERE, 'profile_data.json'), encoding='utf-8'))
    rows = data['currently']
    if not 1 <= len(rows) <= 4:
        raise SystemExit('Currently needs 1 to 4 rows, has %d' % len(rows))
    for key, value in rows:
        if key not in ALLOWED_KEYS:
            raise SystemExit('Currently key %r is not one of %s' % (key, sorted(ALLOWED_KEYS)))
        if not value.strip() or len(value) > MAX_VALUE:
            raise SystemExit('Currently value %r must be 1-%d characters' % (value, MAX_VALUE))
    return data


def blocklist_hits(path):
    words = [w.strip() for w in open(path, encoding='utf-8') if w.strip() and not w.startswith('#')]
    pattern = re.compile(r'(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])' % '|'.join(re.escape(w) for w in words), re.I)
    hits = []
    for f in [os.path.join(HERE, 'profile_data.json'), os.path.join(REPO, 'README.md')] + \
            glob.glob(os.path.join(HERE, 'profile-*.svg')):
        for m in pattern.finditer(open(f, encoding='utf-8').read()):
            hits.append('%s: %s' % (os.path.basename(f), m.group(0)))
    return hits


def gitleaks():
    exe = shutil.which('gitleaks') or next(iter(glob.glob(os.path.expandvars(
        r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gitleaks*\gitleaks.exe'))), None)
    if not exe:
        return 'gitleaks not installed, skipped'
    r = subprocess.run([exe, 'dir', REPO, '--no-banner'], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('gitleaks found something:\n' + (r.stdout + r.stderr)[-2000:])
    return 'gitleaks: no leaks found'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--blocklist', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    run(['git', 'pull', '--ff-only', '-q'])
    data = check_data()
    out = subprocess.run([sys.executable, os.path.join(HERE, 'make_profile.py')],
                         cwd=HERE, capture_output=True, text=True)
    if out.returncode:
        raise SystemExit('make_profile failed:\n' + out.stderr)
    hits = blocklist_hits(a.blocklist)
    if hits:
        raise SystemExit('blocklisted words found, nothing published:\n  ' + '\n  '.join(hits))
    print(out.stdout.strip().splitlines()[0])
    print(gitleaks())
    print('currently:', '; '.join('%s = %s' % (k, v) for k, v in data['currently']))
    print('upwork:', data['upwork'])

    images = sorted(os.path.relpath(p, REPO).replace(os.sep, '/')
                    for p in glob.glob(os.path.join(HERE, 'profile-*.svg')) + glob.glob(os.path.join(HERE, 'link-*.svg')))
    run(['git', 'add', '-A', 'assets/profile_data.json'] + images)
    if not run(['git', 'diff', '--cached', '--name-only']).strip():
        print('no changes to publish')
        return
    if a.dry_run:
        print('dry run: changes staged, not committed')
        print(run(['git', 'diff', '--cached', '--stat']))
        run(['git', 'reset', '-q'])
        return
    import datetime
    run(['git', 'commit', '-q', '--author', AUTHOR, '-m',
         'Weekly profile refresh (%s)' % datetime.date.today().isoformat()])
    run(['git', 'push', '-q', 'origin', 'main'])
    print('pushed', run(['git', 'log', '-1', '--format=%h']).strip())


if __name__ == '__main__':
    main()

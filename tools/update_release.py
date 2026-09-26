"""Update the body (and name) of an existing GitHub release.

The token comes from the same git credential helper `git push` uses and is never
printed. Pass --dry-run to only report what would change.

Usage:
    python tools/update_release.py <tag> <notes.md> [--name NAME] [--dry-run]
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = 'llxj12/goetyownedfix'


def get_token():
    env = os.environ.get('GITHUB_TOKEN')
    if env:
        return env
    p = subprocess.run(['git', 'credential', 'fill'],
                       input='protocol=https\nhost=github.com\n\n',
                       capture_output=True, text=True, cwd=os.getcwd())
    for line in p.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    raise SystemExit('could not obtain a GitHub credential from the git credential helper')


def api(url, token, method='GET', payload=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    req.add_header('User-Agent', 'goetyownedfix-release-script')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    name = None
    if '--name' in sys.argv:
        name = sys.argv[sys.argv.index('--name') + 1]
    if len(args) < 2:
        print(__doc__)
        return 2
    tag, notes_path = args[0], args[1]
    notes = open(notes_path, encoding='utf-8').read()
    payload = {'body': notes}
    if name:
        payload['name'] = name

    if dry:
        print('DRY RUN - would PATCH /repos/%s/releases/tags/%s' % (REPO, tag))
        print('new body: %d chars' % len(notes))
        if name:
            print('new name:', name)
        return 0

    token = get_token()
    status, rel = api('https://api.github.com/repos/%s/releases/tags/%s' % (REPO, tag), token)
    if status != 200:
        print('FAILED to read release: HTTP %s\n%s' % (status, rel))
        return 1
    print('updating release %s (%s)' % (rel['tag_name'], rel['html_url']))
    status, resp = api('https://api.github.com/repos/%s/releases/%d' % (REPO, rel['id']),
                       token, method='PATCH', payload=payload)
    if status != 200:
        print('FAILED to update release: HTTP %s\n%s' % (status, resp))
        return 1
    print('  name:', resp['name'])
    print('  body length now:', len(resp.get('body') or ''))
    print('  draft/prerelease:', resp['draft'], resp['prerelease'])
    return 0


if __name__ == '__main__':
    sys.exit(main())

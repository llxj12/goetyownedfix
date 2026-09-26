"""Create the GitHub release for a tag and upload the built jar.

The token is read from the git credential helper (same store `git push` uses) and
is never printed. Pass --dry-run to print the payload without calling the API.

Usage:
    python tools/publish_release.py <tag> <jar> <notes.md> [--name NAME] [--dry-run]
"""
import base64
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
    # ask the same credential helper git uses; nothing is echoed
    p = subprocess.run(
        ['git', 'credential', 'fill'],
        input='protocol=https\nhost=github.com\n\n',
        capture_output=True, text=True, cwd=os.getcwd())
    for line in p.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    raise SystemExit('could not obtain a GitHub credential from the git credential helper')


def api(url, token, method='GET', payload=None, raw=None, content_type='application/json'):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
    elif raw is not None:
        data = raw
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    req.add_header('User-Agent', 'goetyownedfix-release-script')
    if data is not None:
        req.add_header('Content-Type', content_type)
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
    if len(args) < 3:
        print(__doc__)
        return 2
    tag, jar, notes_path = args[0], args[1], args[2]
    notes = open(notes_path, encoding='utf-8').read()
    title = name or ('goetyownedfix %s (Minecraft 1.21.1 / NeoForge)' % tag)

    payload = {
        'tag_name': tag,
        'name': title,
        'body': notes,
        'draft': False,
        'prerelease': False,
    }
    if dry:
        print('DRY RUN - would POST /repos/%s/releases' % REPO)
        print('tag_name :', tag)
        print('name     :', title)
        print('body     : %d chars' % len(notes))
        print('asset    :', jar, os.path.getsize(jar), 'bytes')
        return 0

    token = get_token()
    print('creating release for tag %s ...' % tag)
    status, resp = api('https://api.github.com/repos/%s/releases' % REPO, token,
                       method='POST', payload=payload)
    if status not in (200, 201):
        print('FAILED to create release: HTTP %s\n%s' % (status, resp))
        return 1
    print('  release created:', resp['html_url'])
    upload_url = resp['upload_url'].split('{')[0]

    fname = os.path.basename(jar)
    with open(jar, 'rb') as f:
        blob = f.read()
    print('uploading %s (%d bytes) ...' % (fname, len(blob)))
    status, resp = api('%s?name=%s' % (upload_url, fname), token, method='POST',
                       raw=blob, content_type='application/java-archive')
    if status not in (200, 201):
        print('FAILED to upload asset: HTTP %s\n%s' % (status, resp))
        return 1
    print('  asset uploaded:', resp['browser_download_url'])
    print('  size:', resp['size'], 'bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())

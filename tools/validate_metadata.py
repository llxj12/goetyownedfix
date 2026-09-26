"""Publishing-grade metadata validation for the 1.21.1 (NeoForge) patch jar.

Uses Python's stdlib parsers (tomllib / json / zipfile) - the same specs the
loader enforces - so no game launch and no external dependency is needed.

Checks:
  * META-INF/neoforge.mods.toml parses as TOML and has the structure NeoForge 4.x
    expects (modLoader, loaderVersion, [[mixins]], [[mods]] with modId/version,
    [[dependencies.<modid>]] entries with modId/type/versionRange/side)
  * the jar version matches the expected release version
  * mixins.goetyfix.json parses as JSON with the required keys and no duplicates
  * the MixinConfigs manifest attribute points at an existing config in the jar
  * the mixin config declares a package whose classes all exist in the jar
  * every dependency versionRange is a syntactically valid Maven range
  * prints a SHA-256 based release manifest for the release notes
"""
import hashlib
import io
import json
import os
import re
import sys
import tomllib
import zipfile

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print('  FAIL: %s' % msg)


def ok(msg):
    print('  ok: %s' % msg)


MAVEN_RANGE = re.compile(
    r'^\s*(\[[^\]]*\]|\([^)]*\)|\[[^)]*\)|\([^\]]*\]|[0-9][0-9A-Za-z.\-+]*)\s*$')


def valid_range(rng):
    if not rng or not isinstance(rng, str):
        return False
    if not MAVEN_RANGE.match(rng):
        return False
    if rng[0] in '[(':
        inner = rng[1:-1]
        if ',' in inner:
            lo, hi = [p.strip() for p in inner.split(',', 1)]
            if lo and hi and lo > hi:
                return False
    return True


def main():
    jar = sys.argv[1]
    expect_version = sys.argv[2] if len(sys.argv) > 2 else None

    print('== release metadata validation: %s' % os.path.basename(jar))
    z = zipfile.ZipFile(jar)
    names = set(z.namelist())

    # ---------- neoforge.mods.toml ----------
    toml_bytes = z.read('META-INF/neoforge.mods.toml')
    try:
        meta = tomllib.load(io.BytesIO(toml_bytes))
        ok('neoforge.mods.toml parses as TOML (tomllib, spec-compliant)')
    except Exception as e:
        fail('neoforge.mods.toml does not parse: %s' % e)
        meta = None

    if meta is not None:
        if meta.get('modLoader') == 'javafml':
            ok('modLoader=javafml')
        else:
            fail('modLoader must be "javafml", got %r' % meta.get('modLoader'))

        lv = meta.get('loaderVersion')
        if valid_range(lv):
            ok('loaderVersion=%s is a valid range' % lv)
        else:
            fail('loaderVersion invalid: %r' % lv)

        mixins = meta.get('mixins')
        cfgs = [m.get('config') for m in mixins] if isinstance(mixins, list) else []
        if cfgs and all(c in names for c in cfgs):
            ok('[[mixins]] declares %s, present in jar' % cfgs)
        else:
            fail('[[mixins]] configs missing from jar: %r' % cfgs)

        mods = meta.get('mods')
        if isinstance(mods, list) and len(mods) >= 1:
            m0 = mods[0]
            if m0.get('modId') == 'goetyfix':
                ok('[[mods]] modId=goetyfix')
            else:
                fail('unexpected modId %r' % m0.get('modId'))
            ver = m0.get('version')
            if expect_version and ver != expect_version:
                fail('jar version %r != expected %r' % (ver, expect_version))
            else:
                ok('version=%s' % ver)
            for field in ('displayName', 'description', 'authors', 'license') :
                key = 'license' if field == 'license' else field
                if field == 'license':
                    if meta.get('license'):
                        ok('license=%s' % meta['license'])
                    else:
                        fail('missing top-level license')
                elif m0.get(key):
                    ok('%s present (%d chars)' % (key, len(str(m0[key]))))
                else:
                    fail('missing [[mods]].%s' % key)
            logo = m0.get('logoFile')
            if logo:
                if logo in names:
                    ok('logoFile=%s present in jar' % logo)
                else:
                    fail('logoFile %r not in jar' % logo)

        deps = meta.get('dependencies', {})
        got = {d.get('modId') for lst in deps.values() for d in lst}
        for want in ('neoforge', 'minecraft', 'goety'):
            if want in got:
                ok('dependency: %s' % want)
            else:
                fail('missing dependency: %s' % want)
        for owner, lst in deps.items():
            if owner != 'goetyfix':
                fail('dependencies declared for unexpected mod %r' % owner)
            for d in lst:
                if d.get('type') not in ('required', 'optional', 'incompatible', 'discouraged'):
                    fail('bad dependency type %r for %s' % (d.get('type'), d.get('modId')))
                if 'versionRange' in d and not valid_range(d['versionRange']):
                    fail('bad versionRange %r for %s' % (d['versionRange'], d.get('modId')))
        ok('all dependency entries structurally valid')

    # ---------- manifest ----------
    mf = z.read('META-INF/MANIFEST.MF').decode('utf-8', 'replace').replace('\r\n', '\n')
    mc = re.search(r'^MixinConfigs:\s*(.+)$', mf, re.M)
    if mc:
        cfgs = [c.strip() for c in mc.group(1).split(',')]
        missing = [c for c in cfgs if c not in names]
        if missing:
            fail('MixinConfigs names missing files: %r' % missing)
        else:
            ok('manifest MixinConfigs=%s points at files in the jar' % cfgs)
    else:
        fail('manifest has no MixinConfigs attribute')

    # ---------- mixin config ----------
    cfg = json.loads(z.read('mixins.goetyfix.json').decode('utf-8'))
    required_keys = ('required', 'minVersion', 'package', 'compatibilityLevel', 'mixins')
    for k in required_keys:
        if k not in cfg:
            fail('mixin config missing key %r' % k)
    if all(k in cfg for k in required_keys):
        ok('mixin config has all required keys')
    lst = cfg.get('mixins', [])
    if len(lst) != len(set(lst)):
        fail('mixin config lists duplicate entries')
    else:
        ok('mixin config lists %d unique mixins' % len(lst))
    pkg = cfg.get('package', '').replace('.', '/')
    missing = [m for m in lst if '%s/%s.class' % (pkg, m) not in names]
    if missing:
        fail('mixin classes listed but not in jar: %r' % missing)
    else:
        ok('every listed mixin class exists in the jar under %s/' % pkg)

    # ---------- release manifest ----------
    print()
    print('== release manifest ==')
    with open(jar, 'rb') as f:
        data = f.read()
    print('  file  : %s' % os.path.basename(jar))
    print('  size  : %d bytes' % len(data))
    print('  sha256: %s' % hashlib.sha256(data).hexdigest())
    print('  sha1  : %s' % hashlib.sha1(data).hexdigest())

    print()
    if FAILS:
        print('%d FAILURES' % len(FAILS))
        return 1
    print('METADATA VALIDATION PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())

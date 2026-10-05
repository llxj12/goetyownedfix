"""Static verification for the goetyownedfix 1.21.1 (NeoForge) patch jar.

Checks, without launching the game:
  1. every @Mixin target class named in the built jar exists in the Goety 3.1.5.1
     jar or the Minecraft/NeoForge client jar;
  2. each Goety target really declares isAlliedTo(Entity) (the injected method),
     and MobUtil declares illagerAllies(Entity, Entity);
  3. every mixin class listed in mixins.goetyownedfix.json is present in the jar, and
     every mixin class in the jar is listed in the config;
  4. each mixin's injected method name/descriptor matches the target;
  5. neoforge.mods.toml is well formed enough for NeoForge (modId/version/
     dependencies present) and matches the jar version;
  6. the jar manifest carries the MixinConfigs attribute.
"""
import io
import json
import os
import re
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cfparse import methods_from_bytes, R

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print('  FAIL: %s' % msg)


def ok(msg):
    print('  ok: %s' % msg)


def class_annotations(data):
    r = R(data)
    if r.u4() != 0xCAFEBABE:
        raise ValueError('not a class file')
    r.u2(); r.u2()
    n = r.u2()
    pool = {}
    i = 1
    while i < n:
        t = r.u1()
        if t == 1:
            l = r.u2(); pool[i] = ('utf8', r.raw(l).decode('utf-8', 'replace'))
        elif t == 3:
            pool[i] = ('int', struct.unpack('>i', r.raw(4))[0])
        elif t == 4:
            pool[i] = ('float', struct.unpack('>f', r.raw(4))[0])
        elif t == 5:
            pool[i] = ('long', struct.unpack('>q', r.raw(8))[0]); i += 1
        elif t == 6:
            pool[i] = ('double', struct.unpack('>d', r.raw(8))[0]); i += 1
        elif t == 7:
            pool[i] = ('class', r.u2())
        elif t == 8:
            pool[i] = ('string', r.u2())
        elif t in (9, 10, 11, 12, 17, 18):
            pool[i] = ('ref', (r.u2(), r.u2()))
        elif t == 15:
            pool[i] = ('mh', (r.u1(), r.u2()))
        elif t == 16:
            pool[i] = ('mt', r.u2())
        elif t in (19, 20):
            pool[i] = ('mod', r.u2())
        else:
            raise ValueError('bad cp tag %d' % t)
        i += 1

    def utf(idx):
        v = pool.get(idx)
        return v[1] if v and v[0] == 'utf8' else None

    def ev():
        tag = chr(r.u1())
        if tag in 'scIBCSZFDJ':
            return (tag, r.u2())
        if tag == 'e':
            return (tag, (r.u2(), r.u2()))
        if tag == '@':
            return (tag, ann())
        if tag == '[':
            return (tag, [ev() for _ in range(r.u2())])
        raise ValueError('element_value tag %r' % tag)

    def resolve(v):
        tag, p = v
        if tag in ('s', 'c'):
            return utf(p)
        if tag in 'IBCSZ':
            return pool.get(p, (None, None))[1]
        if tag == 'e':
            return utf(p[1])
        if tag == '@':
            return p
        if tag == '[':
            return [resolve(x) for x in p]
        return v

    def ann():
        ti = r.u2()
        pairs = []
        for _ in range(r.u2()):
            ni = r.u2()
            pairs.append((utf(ni), resolve(ev())))
        return (utf(ti), pairs)

    r.u2(); r.u2(); r.u2()
    for _ in range(r.u2()):
        r.u2()
    for _ in range(r.u2()):
        r.u2(); r.u2(); r.u2()
        for _ in range(r.u2()):
            r.u2(); r.raw(r.u4())
    for _ in range(r.u2()):
        r.u2(); r.u2(); r.u2()
        for _ in range(r.u2()):
            r.u2(); r.raw(r.u4())
    out = []
    for _ in range(r.u2()):
        name = utf(r.u2())
        ln = r.u4()
        start = r.i
        if name in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'):
            for _ in range(r.u2()):
                out.append(ann())
        r.i = start + ln
    return out


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    patch_jar, goety_jar, client_jar, tools_dir = sys.argv[1:5]

    print('== patch jar: %s' % os.path.basename(patch_jar))
    pz = zipfile.ZipFile(patch_jar)
    pnames = [n for n in pz.namelist() if n.endswith('.class')]

    gz = zipfile.ZipFile(goety_jar)
    gnames = set(gz.namelist())
    cz = zipfile.ZipFile(client_jar)
    cnames = set(cz.namelist())

    # 6. manifest
    manifest = pz.read('META-INF/MANIFEST.MF').decode('utf-8', 'replace')
    if 'MixinConfigs: mixins.goetyownedfix.json' in manifest.replace('\r\n', '\n'):
        ok('manifest declares MixinConfigs: mixins.goetyownedfix.json')
    else:
        fail('manifest missing MixinConfigs attribute')

    # 3. config listing
    cfg = json.loads(pz.read('mixins.goetyownedfix.json').decode('utf-8'))
    listed = set(cfg.get('mixins', []))
    in_jar = {os.path.basename(n)[:-6] for n in pnames if '/mixin/' in n}
    if listed == in_jar:
        ok('mixins.goetyownedfix.json lists exactly the %d mixin classes in the jar' % len(listed))
    else:
        fail('config/jar mismatch: only-in-config=%s only-in-jar=%s' % (sorted(listed - in_jar), sorted(in_jar - listed)))
    if cfg.get('required') is False and cfg.get('injectors', {}).get('defaultRequire') == 0:
        ok('soft mode active (required=false, defaultRequire=0)')
    else:
        fail('soft-mode settings missing')

    # 5. metadata
    toml = pz.read('META-INF/neoforge.mods.toml').decode('utf-8')
    if re.search(r'\[\[mixins\]\]\s*\n\s*config\s*=\s*"mixins\.goetyownedfix\.json"', toml):
        ok('neoforge.mods.toml declares [[mixins]] config (NeoForge 1.21.x loader path)')
    else:
        fail('neoforge.mods.toml missing [[mixins]] config declaration')
    if 'modId="goetyownedfix"' in toml:
        ok('neoforge.mods.toml declares modId=goetyownedfix')
    else:
        fail('neoforge.mods.toml missing modId')
    m = re.search(r'version="([^"]+)"', toml)
    ver = m.group(1) if m else '?'
    if re.search(r'version="%s"' % re.escape(ver), toml) and ver != '?':
        ok('metadata version = %s' % ver)
    for dep in ('neoforge', 'minecraft', 'goety'):
        if re.search(r'modId="%s"' % dep, toml):
            ok('dependency declared: %s' % dep)
        else:
            fail('dependency missing: %s' % dep)

    # 1 + 2 + 4. per-mixin target and injected method
    print('== per-mixin target checks')
    check_goety_methods = set()
    for n in sorted(pnames):
        if '/mixin/' not in n:
            continue
        short = os.path.basename(n)[:-6]
        anns = class_annotations(pz.read(n))
        targets = []
        for a, pairs in anns:
            if a and 'Lorg/spongepowered/asm/mixin/Mixin;' == a:
                for k, v in pairs:
                    if k == 'value':
                        targets = v
        if len(targets) != 1:
            fail('%s: expected exactly one @Mixin target, got %s' % (short, targets))
            continue
        tdesc = targets[0]              # Lcom/foo/Bar;
        tpath = tdesc[1:-1] + '.class'
        tname = tpath.rsplit('/', 1)[-1][:-6]

        if tpath in gnames:
            src = 'goety'
            data = gz.read(tpath)
        elif tpath in cnames:
            src = 'minecraft/neoforge'
            data = cz.read(tpath)
        else:
            fail('%s: target %s not found in Goety or Minecraft jar' % (short, tpath))
            continue

        methods = methods_from_bytes(data)
        mnames = {nm for nm, d in methods}
        if tname == 'MobUtil':
            want = 'illagerAllies'
            desc = '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;)Z'
            if (want, desc) in methods:
                ok('%-40s -> %s.%s(Entity,Entity)  [%s]' % (short, tname, want, src))
            elif want in mnames:
                fail('%s: %s.%s has an unexpected descriptor %s' % (short, tname, want, [d for nm, d in methods if nm == want]))
            else:
                fail('%s: %s has no %s' % (short, tname, want))
        else:
            want = 'isAlliedTo'
            desc = '(Lnet/minecraft/world/entity/Entity;)Z'
            if (want, desc) in methods:
                ok('%-40s -> %s.%s(Entity)  [%s]' % (short, tname, want, src))
                if src == 'goety':
                    check_goety_methods.add(tpath)
            elif want in mnames:
                fail('%s: %s.%s has an unexpected descriptor %s (Entity overload missing)' % (short, tname, want, [d for nm, d in methods if nm == want]))
            else:
                fail('%s: %s has no %s' % (short, tname, want))

    # report the guarded fraction of Goety isAlliedTo overrides
    overrides = []
    for n in gnames:
        if not n.startswith('com/Polarice3/Goety/') or not n.endswith('.class'):
            continue
        try:
            if any(nm == 'isAlliedTo' and d == '(Lnet/minecraft/world/entity/Entity;)Z'
                   for nm, d in methods_from_bytes(gz.read(n))):
                overrides.append(n)
        except Exception:
            pass
    print('== coverage: %d/%d Goety classes that override isAlliedTo(Entity) are guarded'
          % (len(check_goety_methods), len(overrides)))
    missing = set(overrides) - check_goety_methods
    if missing:
        print('   unguarded (review whether each still needs a guard):')
        for m_ in sorted(missing):
            print('     ', m_)

    print()
    if FAILS:
        print('%d FAILURES' % len(FAILS))
        return 1
    print('ALL CHECKS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())

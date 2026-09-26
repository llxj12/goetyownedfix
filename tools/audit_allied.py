"""Audit every Goety isAlliedTo(Entity) override for null-safety.

For each class that overrides isAlliedTo(Entity) this script:
  * decodes the method body and reports the first calls it makes,
  * classifies it as:
      - "DIRECT-FIRST": the argument is dereferenced (getType/getTeam/...) before
        any null check on it -> would NPE on a null argument,
      - "PASS-THROUGH": the argument is only forwarded to super/another override,
        so the crash lands in vanilla Entity.isAlliedTo -> would NPE as well,
      - "GUARDED": contains a null check on the argument first,
  * also audits MobUtil.illagerAllies / areAllies.

Usage:
    python audit_allied.py <goety.jar> [client.jar]
"""
import sys
import zipfile

sys.path.insert(0, __file__.rsplit('\\', 1)[0])
from bytecode_probe import find_code, analyse  # noqa: E402

TARGETS = [
    'com/Polarice3/Goety/common/entities/neutral/Owned.class',
    'com/Polarice3/Goety/common/entities/boss/Apostle.class',
    'com/Polarice3/Goety/common/entities/boss/Vizier.class',
    'com/Polarice3/Goety/common/entities/hostile/servants/VizierClone.class',
    'com/Polarice3/Goety/common/entities/hostile/BoneLord.class',
    'com/Polarice3/Goety/common/entities/hostile/SkullLord.class',
    'com/Polarice3/Goety/common/entities/hostile/BroodMother.class',
    'com/Polarice3/Goety/common/entities/hostile/cultists/Cultist.class',
    'com/Polarice3/Goety/common/entities/hostile/cultists/Heretic.class',
    'com/Polarice3/Goety/common/entities/hostile/Irk.class',
    'com/Polarice3/Goety/common/entities/hostile/illagers/Ripper.class',
    'com/Polarice3/Goety/common/entities/ally/golem/SquallGolem.class',
    'com/Polarice3/Goety/common/entities/hostile/WitherNecromancer.class',
    'com/Polarice3/Goety/common/entities/hostile/HostileDrownedNecromancer.class',
    'com/Polarice3/Goety/common/entities/hostile/illagers/HostileRedstoneGolem.class',
    'com/Polarice3/Goety/common/entities/hostile/illagers/HostileRedstoneMonstrosity.class',
    'com/Polarice3/Goety/common/entities/hostile/illagers/HuntingIllagerEntity.class',
    'com/Polarice3/Goety/common/entities/neutral/ender/AbstractEnderling.class',
    'com/Polarice3/Goety/common/entities/ally/spider/AbstractSpiderServant.class',
]
DESC = '(Lnet/minecraft/world/entity/Entity;)Z'
ARG_DEREF = ('.getType(', '.getTeam(', '.getUUID(', '.blockPosition(', '.position(',
             '.level(', '.getStringUUID(', '.getName(', '.getScoreboardName(',
             '.isSpectator(', '.getTags(')


def classify(refs, branches):
    """Decide whether the null Entity argument can reach a dereference.

    KEY INSIGHT used here: several overrides DO contain ifnull/ifnonnull branches,
    but those check *other* values (getTrueOwner()'s result, or the Team returned
    by getTeam()). A branch only protects the Entity ARGUMENT when it tests the
    argument itself. We therefore look for an argument dereference (a call on the
    Entity parameter, e.g. Entity.getTeam() / Entity.getType()) that is not
    dominated by a null check of that same value.

    Since the argument flows in unmodified, the simple and safe criterion is:
        does the body dereference the argument at a point reachable with null?
    Which is the case unless an early branch returns before every such deref.
    """
    derefs = [r for r in refs if any(k in r[2] for k in ARG_DEREF)]
    passthru = [r for r in refs if '.isAlliedTo(' in r[2]]
    # an argument guard = null check whose skip target jumps past a dereference
    arg_guard = None
    for pc, op, target in branches:
        if op not in ('ifnull', 'ifnonnull'):
            continue
        if any(pc < d[0] < target for d in derefs):
            arg_guard = pc
            break
    guarded_derefs = [d for d in derefs if arg_guard is not None and d[0] > arg_guard]
    # dereferences that are NOT protected by such a branch
    unguarded = [d for d in derefs if arg_guard is None or d[0] < arg_guard]

    if unguarded:
        return 'ARG-DEREF', unguarded[0]
    if derefs and not unguarded:
        return 'ARG-CHECKED', 'null-check @%d guards the argument deref' % arg_guard
    if passthru:
        return 'PASS-THROUGH', passthru[0]
    return 'NO-ARG-USE', refs[0] if refs else None


def main():
    goety = sys.argv[1]
    z = zipfile.ZipFile(goety)
    names = set(z.namelist())
    print('== auditing isAlliedTo(Entity) overrides in %s' % goety.rsplit('\\', 1)[-1])
    counts = {}
    rows = []
    for cls in TARGETS:
        if cls not in names:
            rows.append((cls.rsplit('/', 1)[-1][:-6], 'MISSING', ''))
            counts['MISSING'] = counts.get('MISSING', 0) + 1
            continue
        hits = find_code(z.read(cls), 'isAlliedTo', DESC)
        if not hits:
            rows.append((cls.rsplit('/', 1)[-1][-6:], 'NO-OVERRIDE', ''))
            continue
        desc, code, pool = hits[0]
        refs, branches = analyse(code, pool)
        kind, detail = classify(refs, branches)
        counts[kind] = counts.get(kind, 0) + 1
        if isinstance(detail, tuple):
            text = '@%d %s %s' % detail
        elif isinstance(detail, list):
            text = '; '.join('@%d %s %s' % d for d in detail)
        else:
            text = str(detail)
        rows.append((cls.rsplit('/', 1)[-1][:-6], kind, text))
    width = max(len(r[0]) for r in rows)
    for name, kind, detail in rows:
        print('  %-*s  %-13s %s' % (width, name, kind, detail))
    print()
    print('  summary: %s' % counts)

    mob = 'com/Polarice3/Goety/utils/MobUtil.class'
    if mob in names:
        print()
        print('== MobUtil helpers')
        if True:
            pass
    # MobUtil: decode the two helpers
    if mob in names:
        for helper, hdesc in (('illagerAllies', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;)Z'),
                              ('areAllies', '(Lnet/minecraft/world/entity/Entity;Lnet/minecraft/world/entity/Entity;)Z')):
            hits = find_code(z.read(mob), helper, hdesc)
            if not hits:
                print('  %s: not found' % helper)
                continue
            desc, code, pool = hits[0]
            refs, branches = analyse(code, pool)
            nulls = [b for b in branches if b[1] in ('ifnull', 'ifnonnull')]
            first_null = nulls[0][0] if nulls else None
            first_deref = None
            for pc, op, target in refs:
                if any(k in target for k in ARG_DEREF):
                    first_deref = (pc, target)
                    break
            verdict = 'NONE-FOUND'
            if first_deref:
                verdict = 'UNSAFE' if (first_null is None or first_deref[0] < first_null) else 'GUARDED'
            print('  %-14s refs=%d nullchecks=%d verdict=%s  first-deref=%s' % (
                helper, len(refs), len(nulls), verdict, first_deref))


if __name__ == '__main__':
    main()

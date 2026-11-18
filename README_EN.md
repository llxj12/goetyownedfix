# Goety Summon Crash Fix (goetyownedfix)

[中文版 Chinese](README.md)

> **This branch is the Forge 1.20.1 build (modId `goetyownedfix` since v1.1.2; since v1.2.0 the HellBlast fix from `goetyhellblastfix` is merged in, so that jar is no longer needed).**
> Playing **Minecraft 1.21.1 (NeoForge)**? Grab the matching release from [Releases](https://github.com/llxj12/goetyownedfix/releases); the sources live on the `neoforge-1.21.1` branch.
> The two builds target different game versions — pick one. This mod **can be installed alongside the "Goety Fix" memory-leak mod** (which uses the modId `goetyfix`), verified in-game since 1.1.2.

A minimal Forge 1.20.1 patch mod that fixes **two `Ticking entity` NullPointerException families** in **Goety**:

1. `isAlliedTo` (v1.1.x): the target AI passes a null entity into `isAlliedTo` when a summon takes damage;
2. `HellBlast` (v1.2.0, merged from `goetyhellblastfix`): an **ownerless** HellBlast calls the ignite method on its null owner while exploding.

## Symptoms

The game crashes when entering a world / the Nether, with one of these two typical signatures:

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_5647_()" because "p_20355_" is null
    at Entity.m_7307_ (Entity.java:2236)
    at Goety...Owned.m_7307_ (Owned.java:186)
```

or (newly covered in v1.1.0):

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_6095_()" because "entityIn" is null
    at Goety...Apostle.m_7307_ (Apostle.java:399)
```

Common triggers: **Goety summons (Inferno, Zombie Servants, ...) taking damage** (especially in the Nether, or when several summons of the same kind are around), and **fights involving the Apostle boss**. One verified real-world chain: in the Nether, a **RevelationFix HereticServant taking damage** → `HurtByTargetGoal.alertOthers` → `HereticServant.isAlliedTo(null)` → `Apostle.isAlliedTo(null)` → NPE at line 399.

## Root Cause

Multiple Goety entity classes override `isAlliedTo` (SRG: `m_7307_`). When the target AI `HurtByTargetGoal.alertOthers` passes a null `getLastHurtByMob()` into it:

- Vanilla 1.20.1 `Entity.isAlliedTo` performs **no null check** on the argument and calls `p.getTeam()` directly → NPE (Entity.java:2236);
- Some Goety overrides (e.g. `Apostle`) dereference the argument (`entityIn.getType()`, Apostle.java:399) **before** calling super → also NPE.

After scanning the entity classes in Goety 2.5.49.3 / 2.5.55.4 / 2.5.56.x / 2.5.57.0 (905 classes checked exhaustively in 2.5.56.x), **19 classes override `isAlliedTo`, and all of them share this hazard** (three patterns: direct dereference / pass-through to vanilla / via the `MobUtil.illagerAllies` helper).

## What's Fixed (v1.1)

Entry-level null guards are injected into **all 19 overrides** (a null argument returns false immediately), plus a safety net on **vanilla `Entity.isAlliedTo`** (covers pass-through paths and the same kind of calls from other mods):

- `Owned` (kept from v1.0)
- `Apostle`, `Vizier`, `VizierClone`, `BoneLord`, `SkullLord`, `BroodMother`, `Cultist`, `Heretic`, `Irk`, `Ripper`, `SquallGolem`, `WitherNecromancer`, `HostileDrownedNecromancer`, `HostileRedstoneGolem`, `HostileRedstoneMonstrosity`, `HuntingIllagerEntity`, `AbstractEnderling`, `AbstractSpiderServant`
- vanilla `Entity` (safety net)
- `MobUtil.illagerAllies` (the helper itself dereferences its arguments without a null check; guarded as well)
- `HereticServant` (v1.1.1: RevelationFix's cultist — the verified real-world crash caller, see below)
- `MaverickServant`, `ApostleServant` (v1.2.1: the other two RevelationFix servants with the same shape; `MaverickServant` is reachable through the inherited Cultist alertSameType goal, `ApostleServant` is currently unreachable and guarded defensively)
- `IfritClone`, `MurmurServant`, `MurmurServantHead` (v1.2.1: entry guards for the optional goety_supreme / goetyominous add-ons; all three are currently unreachable and guarded defensively. They use string targets, so there is no compile-time add-on dependency — if an add-on is absent, soft mode only logs a warning)

A null entity can never be an ally, so returning false is safe and correct; **checks on valid entities are completely unaffected — zero side effects**. Mixin-only, contains no Goety code.

### Addon compatibility (verified class-by-class)

GoetyAwaken (4 classes) and GoetyLadder (1 class) overrides are pass-through implementations that resolve to already-guarded Goety classes or the vanilla `Entity` safety net — **no extra patches needed**. GoetyRevelation and goetygrae declare no overrides.

**RevelationFix (v1.1.1)**: verified from a real crash report — `HereticServant` (the "异教徒" cultist, a RevelationFix class normally loaded via GoetyRevelation's JarJar bundle) forwards a null entity into Goety's `Apostle.isAlliedTo`, crashing at Apostle.java:399. v1.1.1 adds an entry guard on `HereticServant.m_7307_` (caller-side safety net). If RevelationFix is not installed, soft mode skips this mixin with a warning and the game still starts. v1.2.1 adds the same entry guard to the other two same-shaped classes, `MaverickServant` (reachable) and `ApostleServant` (currently unreachable).

## Second Defect: Ownerless HellBlast (v1.2.0, merged from goetyhellblastfix)

### Symptoms

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_20254_(int)" because "this.val$entity" is null
    at Goety...HellBlast$1.explodeHurt (HellBlast.java:177)
    at Goety...SpellExplosion.<init> (SpellExplosion.java:72)
    at Goety...HellBlast$1.<init> (HellBlast.java:171)
    at Goety...HellBlast.m_6532_ (HellBlast.java:171)
```

Trigger: the **HellBlast has no owner** (`/summon goety:hell_blast`, accidental spell spawns, or the owner dying/unloading), `Fiery > 0`, and **a living entity is caught in the explosion**. Exploding over empty air or `Fiery = 0` never triggers it, which is why it can stay hidden for a long time.

### Root Cause

`HellBlast.m_6532_` captures its `getOwner()` into the anonymous explosion class `HellBlast$1`; `explodeHurt` applies the explosion damage first and then calls `setRemainingFireTicks` (`Entity.m_20254_`) on the captured owner. With a null owner that is an NPE, killing the server tick.

### Fix

Redirects the **single** `Entity.m_20254_(I)` call in `HellBlast$1.explodeHurt` and skips it when the owner is null; explosion damage and every owned-HellBlast path are untouched.

- **Why not an `@At("RETURN")` guard on the constructor**: `SpellExplosion`'s constructor itself calls `explodeHurt` (line 72), so the NPE is thrown from inside the constructor and the constructor never reaches RETURN — exactly why `goetyhellblastfix` 0.0.1 did nothing.
- **Why the class name is stable**: the real stack says `HellBlast$1`; mixin renames only anonymous classes generated inside other mods' mixins (`Class$Anonymous$hash`), not Goety's.
- Call site verified identical across 2.5.25.0 / 2.5.36.1 / 2.5.55.4 / 2.5.56.0 / 2.5.56.4 / 2.5.57.0 / **2.5.58.4** (1.21.1's 3.1.5.1 uses Mojang names and is out of scope for this branch).

## Installation

- Requires **Forge 1.20.1 (47.x)** + **Goety 2.5.49+** (all 28 patch targets verified on 2.5.49.3 / 2.5.55.4 / 2.5.57.0 / 2.5.58.4; real-machine tested on 2.5.55.4 and 2.5.57.0)
- Drop the release jar (see Releases) into the `mods` folder (**replace the old goetyownedfix-1.0.0 / 1.1.0 / 1.1.1 / 1.1.2 — do not install both**)
- v1.2.0 already includes `goetyhellblastfix`: **delete `goetyhellblastfix-0.0.2.jar` if you had it installed**
- Install on **both client and server** (for integrated servers, the machine hosting the save must have it)
- Coexists with RevelationFix / Goety:Revelation / GoetyAwaken and other Goety addons without conflicts

## Crash Resistance

- **Soft mode**: mixin config is `required=false` + `defaultRequire=0` — if a future Goety update removes a class or renames a method, the affected mixin is skipped with a warning log and **the game starts normally instead of crashing**. The vanilla `Entity.isAlliedTo` safety net always anchors to a method that exists in 1.20.1, so pass-through classes stay covered even if an individual class mixin goes stale. The HellBlast redirect is soft too (`require = 0`) — a missing call site only logs a warning.
- **Cost of soft mode**: a successful and a failed injection look identical in-game. To confirm the HellBlast guard, search `logs/debug.log` for `HellBlastExplosionNullGuardMixin` — no `Injection error` / `target was not found` warning means it applied.
- **Dependency protection**: `mods.toml` declares goety as `mandatory=true` with `>=2.5.49` — installing it without Goety (or with an outdated Goety) makes FML refuse to load at startup with a clear error, instead of crashing later in-game.
- **Conflict-free design**: all injections are additive `@Inject` / `@Redirect`s (no method bodies replaced) and never conflict with other mods' overrides.

## Compatibility

- Mixin-only: applies null guards at runtime, contains no Goety code
- If Goety officially fixes this issue later, simply delete this mod

## Build

Requires JDK 17 and the Forge 47.4.22 libraries (standard local paths are baked into the script and can be overridden):

```powershell
# the version is read from META-INF/mods.toml, so the file name can never drift from the metadata
.\build.ps1

# other Goety jar / JDK:
.\build.ps1 -GoetyJar '修改目标MOD\[诡厄巫法] goety-2.5.57.0.jar' -Jdk 'E:\.minecraft\jdk-17.0.18+8'
```

The script compiles `llxj/**/*.java`, assembles `META-INF/MANIFEST.MF` (with `MixinConfigs: mixins.goetyownedfix.json`), `pack.mcmeta`, the mixin config and `mods.toml`, then writes `goetyownedfix-<version>.jar` in the repository root and prints its SHA-256.

Compile classpath (assembled by the script): `mixin-0.8.5.jar`, `javafmllanguage-1.20.1-47.4.22.jar`, `forge-1.20.1-47.4.22-universal.jar`, `client-1.20.1-...-srg.jar` and a 1.20.1 goety jar (defaults to the newest 2.x in `修改目标MOD`).

When packaging: `META-INF/MANIFEST.MF` must contain `MixinConfigs: mixins.goetyownedfix.json`, and `pack.mcmeta` (pack_format 15) must be present.

## Changelog

- **1.2.1**: added entry guards for the other two same-shaped RevelationFix servants — `MaverickServant` (inherits the Cultist `HurtByTargetGoal` with alertSameType enabled, so the same NPE is reproducible) and `ApostleServant` (currently unreachable, guarded defensively); string-target guards were also added for the optional add-ons — `IfritClone` (goety_supreme) and `MurmurServant` / `MurmurServantHead` (goetyominous) — with no compile-time dependency and a warning-only skip when absent; 28 patch targets in total
- **1.2.0**: merged the HellBlast fix from `goetyhellblastfix` 0.0.2 (null-owner guard in `HellBlast$1.explodeHurt`), 23 patch targets in total; added `build.ps1` (version read from `mods.toml`, no more file-name/metadata drift)
- **1.1.2**: **modId changed from `goetyfix` to `goetyownedfix`** (mixin config renamed to `mixins.goetyownedfix.json`) — resolves a modId conflict with the unrelated "Goety Fix" memory-leak mod, so both can now load together; the Goety dependency floor was also lowered from 2.5.56 to **2.5.49** (all patch targets verified on 2.5.49.3 / 2.5.55.4)
- **1.1.1**: added RevelationFix `HereticServant` caller-side entry guard (verified real-world crash path from a live crash report — double safety net)
- **1.1.0**: all 19 `isAlliedTo` overrides + vanilla `Entity.isAlliedTo` safety net + `MobUtil.illagerAllies` guard + soft-mode crash resistance (fixes Apostle.java:399 and the rest of the family)
- **1.0.0**: only `Owned.isAlliedTo` fixed

## Coexistence with other mods

- **Goety Fix (memory-leak fix)**: it uses the same modId `goetyfix`; since 1.1.2 this mod uses `goetyownedfix` instead, so both can be installed together (tested in-game on Goety 2.5.55.4: both mods load, both mixin configs apply, zero conflicts)
- Coexists with RevelationFix / Goety:Revelation / GoetyAwaken / goety_ladder / goetygrae without conflicts

## License

MIT License. Thanks to [Polarice3's Goety](https://github.com/Polarice3/Goety-2).

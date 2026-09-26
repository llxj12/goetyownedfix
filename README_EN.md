# Goety Summon Crash Patch (goetyownedfix) — 1.21.1 / NeoForge

[中文说明](README.md)

A tiny **NeoForge 1.21.1** patch that fixes the **`isAlliedTo` NullPointerException family in Goety**.

> This directory is the 1.21.1 port of the original Forge 1.20.1 mod. The 1.20.1 sources are kept in `legacy-forge-1.20.1/`. Both jars use the same modId (`goetyfix`) — **install only one of them**.

## Symptom

The game crashes while entering a world / the Nether or during Apostle fights:

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_6095_()" because "entityIn" is null
    at net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal.m_26047_(HurtByTargetGoal.java:95)
```

Typical triggers: **whenever a Goety summon or cultist takes damage** (especially in the Nether, with several of the same mob nearby), and during **Apostle** encounters.

## Cause

Several Goety entity classes override `isAlliedTo(Entity)`. When the target AI `HurtByTargetGoal.alertOthers` forwards a null `getLastHurtByMob()` into it:

- vanilla `Entity.isAlliedTo(Entity)` performs **no null check** on the argument and dereferences it → NPE;
- some Goety overrides (e.g. `Apostle`) dereference the argument (`entityIn.getType()`) even before calling super → NPE as well.

A scan of **all 3090 Goety classes in Goety 3.1.5.1 (the NeoForge 1.21.1 port)** shows **19 classes override `isAlliedTo(Entity)`, all of them sharing the same hazard**.

## Fix (v2.0.0)

A null check is injected at the `isAlliedTo` entry point of all 19 overriding classes (a null argument returns `false`), plus two extra safety nets:

- **19 Goety 3.1.5.1 overrides**: `Owned`, `Apostle`, `Vizier`, `VizierClone`, `BoneLord`, `SkullLord`, `BroodMother`, `Cultist`, `Heretic`, `Irk`, `Ripper`, `SquallGolem`, `WitherNecromancer`, `HostileDrownedNecromancer`, `HostileRedstoneGolem`, `HostileRedstoneMonstrosity`, `HuntingIllagerEntity`, `AbstractEnderling`, `AbstractSpiderServant`
- **vanilla `Entity.isAlliedTo(Entity)`**: covers every "pass-through to super" caller, including same-shaped overrides from other mods
- **`MobUtil.illagerAllies`**: the helper dereferences both arguments without a null check, so it is guarded too

A null entity can never be an ally, so returning `false` is safe and correct; **judgements for non-null arguments are completely unaffected** (zero side effects). Mixin-only — it contains no Goety code.

### Differences from the 1.20.1 build

| Item | 1.20.1 / Forge | 1.21.1 / NeoForge (this build) |
| --- | --- | --- |
| Injected method name | SRG `m_7307_` | official `isAlliedTo` (NeoForge 1.21.1 no longer uses SRG runtime names) |
| Metadata file | `META-INF/mods.toml` (`mandatory=`, depends on modId `forge`) | `META-INF/neoforge.mods.toml` (`type="required"`, depends on modId `neoforge`) |
| Mixin config loading | manifest `MixinConfigs` | manifest `MixinConfigs` **and** `[[mixins]] config=` declaration (NeoForge 1.21.x uses the latter) |
| Target Goety | 2.5.56+ | 3.1.5+ (1.21.1 port) |
| Mixin count | 22 (incl. RevelationFix `HereticServant`) | 21 (RevelationFix has no 1.21.1 build; can be added back later) |

## Installation

- Requires **NeoForge 1.21.1 (21.1.x)** and **Goety 3.1.5+ (1.21.1 port)**
- Drop `dist/goetyownedfix-2.0.0-neoforge-1.21.1.jar` into your `mods` folder
- **Do not install it next to the 1.20.1/Forge build** (same modId, different loader)
- Install on **both client and server** (for a single-player world, the machine hosting the world)

## Compatibility

- Runtime-only mixin patch; contains no Goety code
- If Goety fixes this upstream, simply delete this mod
- Add-on mods that override `isAlliedTo` by forwarding to super are covered automatically by the `Entity.isAlliedTo` safety net

## Crash resistance

- **Soft mode**: the mixin config uses `required=false` + `defaultRequire=0`. If a future Goety update removes a target class or renames a method, the affected mixin is **skipped with a warning instead of crashing the game**. The vanilla `Entity.isAlliedTo` safety net is anchored to a vanilla method that never disappears, so pass-through classes stay covered even if a per-class mixin stops applying.
- **Dependency guard**: `neoforge.mods.toml` declares `goety` as `type="required"` with `>=3.1.5`, so installing it without Goety fails loudly at **startup** instead of misbehaving in-game.
- **Conflict-free**: every injection is an additive `@Inject`; no other mod's override is replaced.

## Building

Requires **JDK 21** (NeoForge 1.21.1 and Goety 3.1.5.1 are Java 21 bytecode; this mod itself is compiled with `--release 17` for wider compatibility).

```powershell
.\build.ps1                    # finds the toolchain and packs dist\
.\build.ps1 -Javac "C:\path\to\jdk21\bin\javac.exe" -Version 2.0.0
```

Classpath jars (read from `..\_mc1211_tools\deps\`, falling back to the local launcher library folder):

| jar | Purpose |
| --- | --- |
| `neoforge-21.1.219-client.jar` | NeoForge-patched Minecraft (official names) |
| `client-1.21.1-20240808.144430-srg.jar` | vanilla 1.21.1 client |
| `sponge-mixin-0.15.2+mixin.0.8.7.jar` | Mixin (shipped with NeoForge 1.21.1) |
| `loader-4.0.42.jar` | FancyModLoader, provides the `@Mod` annotation |
| `goety-3.1.5.1.jar` | the mixin target (Goety 1.21.1 port) |

Packaging notes: `META-INF/MANIFEST.MF` must contain `MixinConfigs: mixins.goetyfix.json`, and the jar must contain `META-INF/neoforge.mods.toml`, `mixins.goetyfix.json` and `pack.mcmeta`.

## Static verification

`verify.ps1` checks the built jar **without launching the game**:

1. every `@Mixin` target really exists in Goety 3.1.5.1 / Minecraft 1.21.1;
2. each target really declares the injected `isAlliedTo(Entity)` (exact descriptor match) / `MobUtil.illagerAllies(Entity,Entity)`;
3. the classes listed in `mixins.goetyfix.json` and the mixin classes inside the jar match exactly;
4. `neoforge.mods.toml` carries modId, version, all three dependencies and the `[[mixins]]` declaration;
5. the manifest carries `MixinConfigs`;
6. coverage: how many of Goety's `isAlliedTo(Entity)` overrides are guarded (currently **19/19**).

```powershell
.\verify.ps1
```

A second, **release-metadata validator** checks the packaged jar with spec-compliant parsers (Python's stdlib `tomllib` for TOML, `json` for JSON):

```powershell
python .\tools\validate_metadata.py .\dist\goetyownedfix-2.0.0-neoforge-1.21.1.jar 2.0.0
```

It verifies that `neoforge.mods.toml` parses as TOML, that `modLoader` / `loaderVersion` / `[[mixins]]` / `[[mods]]` (modId, version, displayName, description, authors, license, logoFile) are all present, that the three dependencies carry valid types and version ranges, that the manifest `MixinConfigs` entries exist in the jar, that every mixin class listed in the config is packaged, and finally prints the artifact size with its SHA-256/SHA-1.

Exact dependency versions, sources and reproduction steps are in `BUILD-MANIFEST.md`.

## Version history

- **2.0.0** (this build, 1.21.1 / NeoForge): ported to NeoForge 1.21.1 with official `isAlliedTo` injection instead of SRG `m_7307_`; covers all 19 Goety 3.1.5.1 overrides + vanilla `Entity` safety net + `MobUtil.illagerAllies`; adds the `[[mixins]]` metadata declaration and a static verifier
- **1.1.1** (1.20.1 / Forge): caller-side guard for RevelationFix `HereticServant`
- **1.1.0** (1.20.1 / Forge): all 19 `isAlliedTo` overrides + vanilla `Entity.isAlliedTo` safety net + `MobUtil.illagerAllies` guard + soft mode
- **1.0.0** (1.20.1 / Forge): only `Owned.isAlliedTo`

## License

MIT License. Thanks to [Polarice3's Goety](https://github.com/Polarice3/Goety-2).

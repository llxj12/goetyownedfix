# Goety Summon Crash Patch (goetyownedfix) — 1.21.1 / NeoForge

[中文说明](README.md)

A tiny **NeoForge 1.21.1** patch that fixes the **`isAlliedTo` NullPointerException family in Goety**.

## Symptom

The game crashes while entering a world / the Nether or during Apostle fights:

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getType()" because "entityIn" is null
    at net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal.alertOthers (HurtByTargetGoal.java:95)
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

## Installation

- Requires **NeoForge 1.21.1 (21.1.x)** and **Goety 3.1.5+ (1.21.1 port)**
- Drop `dist/goetyownedfix-2.0.0-neoforge-1.21.1.jar` into your `mods` folder
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

Entry timestamps of the staged files are pinned to `SOURCE_DATE_EPOCH` (default `1790432400` = 2026-09-26T14:20:00Z), so a rebuild from the same sources is **byte-identical**. A different epoch yields an equivalent jar with a different hash, so only one parameter set should be advertised per release.

Classpath jars (read from `..\_mc1211_tools\deps\`, falling back to the local launcher library folder):

| jar | Purpose |
| --- | --- |
| `neoforge-21.1.219-client.jar` | NeoForge-patched Minecraft (official names) |
| `client-1.21.1-20240808.144430-srg.jar` | vanilla 1.21.1 client |
| `sponge-mixin-0.15.2+mixin.0.8.7.jar` | Mixin (shipped with NeoForge 1.21.1) |
| `loader-4.0.42.jar` | FancyModLoader, provides the `@Mod` annotation |
| `goety-3.1.5.1.jar` | the mixin target (Goety 1.21.1 port) |

Packaging notes: `META-INF/MANIFEST.MF` must contain `MixinConfigs: mixins.goetyfix.json`, and the jar must contain `META-INF/neoforge.mods.toml` and `mixins.goetyfix.json` (a 1.21.1 mod jar does not need `pack.mcmeta`).

## Version history

- **2.0.0**: ported to Minecraft 1.21.1 / NeoForge; covers all 19 `isAlliedTo` overrides in Goety 3.1.5.1 + vanilla `Entity.isAlliedTo` safety net + `MobUtil.illagerAllies` guard + soft-mode crash resistance

## License

MIT License. Thanks to [Polarice3's Goety](https://github.com/Polarice3/Goety-2).

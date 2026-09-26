# Changelog

## v2.0.0 — Minecraft 1.21.1 / NeoForge

**Updated to Minecraft 1.21.1 (NeoForge).**

- Updated the mod to Minecraft 1.21.1 and NeoForge 21.1.x
- The injection target is now the official `isAlliedTo` name, since NeoForge 1.21.1 no longer uses SRG runtime names
- Null guards on all 19 classes that override `isAlliedTo` in Goety 3.1.5.1
- Vanilla `Entity.isAlliedTo` safety net, covering every caller that passes the argument through to super
- `MobUtil.illagerAllies` guard, since the helper dereferences its arguments without a null check
- Soft-mode mixin config (`required=false`, `defaultRequire=0`): if a future Goety update removes a class or renames a method, the affected mixin is skipped with a warning and the game still starts
- Requires NeoForge 21.1.x (or a newer 21.1) and Goety 3.1.5+ (the 1.21.1 build)
- Install on both client and server

### Short version

Updated to Minecraft 1.21.1 / NeoForge. Null guards on all 19 Goety classes that
override `isAlliedTo`, plus a vanilla `Entity.isAlliedTo` safety net and a
`MobUtil.illagerAllies` guard. Requires NeoForge 21.1.x and Goety 3.1.5+.

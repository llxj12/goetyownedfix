# goetyownedfix v2.0.0 —— 诡厄巫法召唤物崩溃补丁

修复 **诡厄巫法 (Goety)** 因 `isAlliedTo` 收到 null 实体而导致的「Ticking entity」崩溃家族。NeoForge 1.21.1 迷你补丁，纯 Mixin 实现，不含任何 Goety 代码。

## 本次更新（v2.0.0）

- **适配 Minecraft 1.21.1 / NeoForge 21.1.x**
- 依据 **Goety 3.1.5.1（1.21.1 版）**的实体类扫描结果，其中**重写 `isAlliedTo` 的 19 个类全部入口空判断**
- NeoForge 1.21.1 使用官方方法名，因此本版的注入目标由 SRG 名 `m_7307_` 改为官方名 `isAlliedTo`（无需 refmap）

## 症状

进世界 / 下界时游戏崩溃，崩溃报告为：

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getType()" because "entityIn" is null
    at net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal.alertOthers (HurtByTargetGoal.java:95)
```

或（透传路径）：

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getTeam()" because "p_20355_" is null
    at Entity.isAlliedTo (Entity.java)
```

常见触发场景：**狱焰、僵尸仆从等 Goety 召唤物受伤时**（尤其下界、多只同类召唤物在场时），以及 **Apostle（亚波伦）相关战斗**。

## 原因

Goety 的多个实体类重写了 `isAlliedTo`。当目标 AI `HurtByTargetGoal.alertOthers` 把为 null 的 `getLastHurtByMob()` 传进来时：

- 原版 `Entity.isAlliedTo` 对参数**不做空判断**，直接对参数取队伍（`p.getTeam()`）→ NPE；
- 部分 Goety 重写（如 `Apostle`）在调 super **之前**就解引用参数（`entityIn.getType()`）→ 同样 NPE。

经对 Goety 3.1.5.1 全部实体类扫描，**重写 `isAlliedTo` 的类共 19 个，全部存在同类隐患**（直接解引用 / 透传 vanilla / 经 `MobUtil.illagerAllies` 工具类三种模式）。

## 修复内容（v2.0.0）

- **19 个 `isAlliedTo` 重写类全部入口空判断**：参数为 null 直接返回 false（null 不可能是盟友），对有效实体的判断完全不受影响，零副作用
- **原版 `Entity.isAlliedTo` 兜底**：覆盖透传 super 的路径及其它 mod 的同类调用
- **`MobUtil.illagerAllies` 工具类防护**：工具类内部对参数无空判断，一并覆盖
- **软模式抗崩溃**：mixin 配置 `required=false` + `defaultRequire=0`，未来 Goety 更新导致某个类被删除/方法改名时，对应 mixin 跳过并打警告日志，**游戏照常启动**，不会崩溃

## 安装

- 需要 **Minecraft 1.21.1** + **NeoForge 21.1.x** + **Goety 3.1.5+**（1.21.1 版）
- 把 jar 放入 `mods` 文件夹即可
- 客户端和服务端**都要装**（集成服务器 = 开存档的那台机器必须装）

## 兼容性

- 仅以 Mixin 方式在运行时打空判断补丁，不含任何 Goety 代码
- 若 Goety 官方后续修复了此问题，删除本 mod 即可
- 全部为 `@Inject` 叠加式注入，不与其它 mod 的重写冲突

## 版本历史

- **2.0.0**：适配 Minecraft 1.21.1 / NeoForge；覆盖 Goety 3.1.5.1 全部 19 个 `isAlliedTo` 重写类 + 原版 `Entity.isAlliedTo` 兜底 + `MobUtil.illagerAllies` 防护 + 软模式抗崩溃

## 许可

MIT License

---

# goetyownedfix v2.0.0 — Goety Summon Crash Fix

Fixes the "Ticking entity" crash family in **Goety** caused by `isAlliedTo` receiving a null entity. A minimal NeoForge 1.21.1 patch mod, implemented purely with Mixins, containing no Goety code.

## What's New (v2.0.0)

- **Ported to Minecraft 1.21.1 / NeoForge 21.1.x**
- Based on a scan of Goety 3.1.5.1 (the 1.21.1 build), **entry-level null guards on all 19 classes that override `isAlliedTo`**
- NeoForge 1.21.1 uses Mojang official names, so the injection target moved from the SRG name `m_7307_` to the official name `isAlliedTo` (no refmap needed)

## Symptoms

The game crashes while entering a world / the Nether, with a report like:

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getType()" because "entityIn" is null
    at net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal.alertOthers (HurtByTargetGoal.java:95)
```

or, on a pass-through path:

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getTeam()" because "p_20355_" is null
    at Entity.isAlliedTo (Entity.java)
```

Common triggers: **Goety summons taking damage** (especially in the Nether, or when several summons of the same kind are around), and **fights involving the Apostle boss**.

## Root Cause

Multiple Goety entity classes override `isAlliedTo`. When the target AI `HurtByTargetGoal.alertOthers` passes a null `getLastHurtByMob()` into it:

- Vanilla `Entity.isAlliedTo` performs **no null check** on the argument and reads the team from it (`p.getTeam()`) → NPE;
- Some Goety overrides (e.g. `Apostle`) dereference the argument (`entityIn.getType()`) **before** calling super → also NPE.

After scanning every entity class in Goety 3.1.5.1, **19 classes override `isAlliedTo`, and all of them share this hazard** (three patterns: direct dereference / pass-through to vanilla / via the `MobUtil.illagerAllies` helper).

## What's Fixed (v2.0.0)

- **Entry-level null guard on all 19 `isAlliedTo` overrides**: a null argument returns false immediately (a null entity can never be an ally); checks on valid entities are completely unaffected — zero side effects
- **Vanilla `Entity.isAlliedTo` safety net**: covers super pass-through paths and the same kind of calls from other mods
- **`MobUtil.illagerAllies` guard**: the helper dereferences its arguments without a null check; now covered as well
- **Soft-mode crash resistance**: mixin config `required=false` + `defaultRequire=0` — if a future Goety update removes a class or renames a method, the affected mixin is skipped with a warning log and **the game starts normally instead of crashing**

## Installation

- Requires **Minecraft 1.21.1** + **NeoForge 21.1.x** + **Goety 3.1.5+** (the 1.21.1 build)
- Drop the jar into the `mods` folder
- Install on **both client and server** (for integrated servers, the machine hosting the save must have it)

## Compatibility

- Mixin-only: applies null guards at runtime, contains no Goety code
- If Goety officially fixes this issue later, simply delete this mod
- All injections are additive `@Inject`s; they never conflict with other mods' overrides

## Changelog

- **2.0.0**: ported to Minecraft 1.21.1 / NeoForge; covers all 19 `isAlliedTo` overrides in Goety 3.1.5.1 + vanilla `Entity.isAlliedTo` safety net + `MobUtil.illagerAllies` guard + soft-mode crash resistance

## License

MIT License

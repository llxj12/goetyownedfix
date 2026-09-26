# 诡厄巫法召唤物崩溃补丁 (goetyownedfix) — 1.21.1 / NeoForge 版

[English README](README_EN.md)

一个 **NeoForge 1.21.1** 迷你补丁，修复 **诡厄巫法 (Goety) 的 `isAlliedTo` 空指针崩溃家族**。

## 症状

进世界/下界或与亚波伦系列战斗时游戏崩溃，崩溃报告为：

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.getType()" because "entityIn" is null
    at net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal.alertOthers (HurtByTargetGoal.java:95)
```

常见触发场景：**召唤物/信徒受伤时**（尤其下界、多只同类在场时），以及 **Apostle（亚波伦）相关战斗**。

## 原因

Goety 的多个实体类重写了 `isAlliedTo(Entity)`。当目标 AI `HurtByTargetGoal.alertOthers` 把为 null 的 `getLastHurtByMob()` 传进来时：

- 原版 `Entity.isAlliedTo(Entity)` 对参数**不做空判断**，直接取参数队伍 → NPE；
- 部分 Goety 重写（如 `Apostle`）在调 super **之前**就解引用参数（`entityIn.getType()`）→ 同样 NPE。

对 **Goety 3.1.5.1（NeoForge 1.21.1 移植版）全部 3090 个 Goety 类扫描结果：重写 `isAlliedTo(Entity)` 的类共 19 个，全部存在同类隐患**。

## 修复方式（v2.0.0）

在全部 19 个重写类的 `isAlliedTo` 入口注入空判断（参数为 null 直接返回 false），并额外做两层兜底：

- **19 个 Goety 3.1.5.1 重写类**：`Owned`、`Apostle`、`Vizier`、`VizierClone`、`BoneLord`、`SkullLord`、`BroodMother`、`Cultist`、`Heretic`、`Irk`、`Ripper`、`SquallGolem`、`WitherNecromancer`、`HostileDrownedNecromancer`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity`、`AbstractEnderling`、`AbstractSpiderServant`
- **原版 `Entity.isAlliedTo(Entity)`**：兜底，覆盖所有"透传 super"的调用方（含其它 mod 的同名重写）
- **`MobUtil.illagerAllies`**：工具类内部对参数同样无空判断，一并防护

null 不可能是盟友，返回 false 安全且正确；**对有效实体（非 null 参数）的判断完全不受影响**，零副作用。mixin-only，不含任何 Goety 代码。

## 安装

- 需要 **NeoForge 1.21.1（21.1.x）** + **Goety 3.1.5+（1.21.1 移植版）**
- 把 `dist/goetyownedfix-2.0.0-neoforge-1.21.1.jar` 丢进 `mods` 文件夹即可
- 客户端和服务端**都要装**（集成服务器 = 开存档的那台机器必须装）

## 兼容性

- 仅以 mixin 方式在运行时打空判断补丁，不含任何 Goety 代码
- 若 Goety 官方后续修复了此问题，删除本 mod 即可
- 附属 mod 若也以"透传 super"方式重写 `isAlliedTo`，会被 `Entity.isAlliedTo` 兜底 mixin 自动覆盖

## 抗崩溃性说明

- **软模式**：mixin 配置为 `required=false` + `defaultRequire=0`——若未来 Goety 更新导致某个类被删除/方法改名，对应的 mixin 会被**跳过并打警告日志，游戏照常启动**，而不是崩溃。原版 `Entity.isAlliedTo` 兜底始终锚定在原版方法上，透传类即使某个 per-class mixin 失效也仍被覆盖。
- **依赖保护**：`neoforge.mods.toml` 中 `goety` 依赖为 `type="required"` 且要求 `>=3.1.5`——若误装在没有 Goety 或版本过低的整合包里，加载器会在**启动阶段**给出明确报错并拒绝加载。
- **无冲突设计**：全部为 `@Inject` 叠加式注入，不与其它 mod 的重写冲突。

## 编译 / Build

需要 **JDK 21**（NeoForge 1.21.1 与 Goety 3.1.5.1 均为 Java 21 字节码；本 mod 自身以 `--release 17` 编译，兼容性更好）。

```powershell
.\build.ps1                    # 自动查找工具链并编译打包到 dist\
.\build.ps1 -Javac "C:\path\to\jdk21\bin\javac.exe" -Version 2.0.0
```

打包时会把暂存文件的**时间戳固定**到 `SOURCE_DATE_EPOCH`（默认 `1790432400` = 2026-09-26T14:20:00Z），因此同源重建产物**字节级一致**；换个 epoch 会得到内容等价但哈希不同的产物，发布时请只声明一种参数。

需要的 classpath jar（默认从 `..\_mc1211_tools\deps\` 读取，缺失时回退到本机启动器库目录）：

| jar | 用途 |
| --- | --- |
| `neoforge-21.1.219-client.jar` | NeoForge 补丁后的 Minecraft（官方名） |
| `client-1.21.1-20240808.144430-srg.jar` | 原版 1.21.1 客户端 |
| `sponge-mixin-0.15.2+mixin.0.8.7.jar` | Mixin（随 NeoForge 1.21.1 分发） |
| `loader-4.0.42.jar` | FancyModLoader 的 `@Mod` 注解 |
| `goety-3.1.5.1.jar` | mixin 目标（Goety 1.21.1 移植版） |

打包要点：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyfix.json`，且包含 `META-INF/neoforge.mods.toml` 与 `mixins.goetyfix.json`（1.21.1 的 mod jar 不需要 `pack.mcmeta`）。

## 版本历史

- **2.0.0**：适配 Minecraft 1.21.1 / NeoForge；覆盖 Goety 3.1.5.1 全部 19 个 `isAlliedTo` 重写类 + 原版 `Entity.isAlliedTo` 兜底 + `MobUtil.illagerAllies` 防护 + 软模式抗崩溃

## 许可

MIT License。感谢 [Polarice3 的 Goety](https://github.com/Polarice3/Goety-2)。

# 诡厄巫法召唤物崩溃补丁 (goetyownedfix)

[English README](README_EN.md)

> **本分支是 Forge 1.20.1 版。**
> 如果你玩的是 **Minecraft 1.21.1（NeoForge）**，请到 [Releases 下载 v2.0.0](https://github.com/llxj12/goetyownedfix/releases/tag/v2.0.0)，源码在 `neoforge-1.21.1` 分支。
> 两个版本的 modId 都是 `goetyfix`，**不要同时安装**。

一个 Forge 1.20.1 迷你补丁，修复 **诡厄巫法 (Goety) 的 `isAlliedTo` 空指针崩溃家族**。

## 症状

进世界/下界时游戏崩溃，崩溃报告为：

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_5647_()" because "p_20355_" is null
    at Entity.m_7307_ (Entity.java:2236)
    at Goety...Owned.m_7307_ (Owned.java:186)
```

或（v1.1 新增覆盖的 Apostle 路径）：

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_6095_()" because "entityIn" is null
    at Goety...Apostle.m_7307_ (Apostle.java:399)
```

常见触发场景：**狱焰、僵尸仆从等 Goety 召唤物受伤时**（尤其下界、多只同类召唤物在场时），以及 **Apostle（亚波伦）相关战斗**。已按真实崩溃日志核实的一条完整链路：下界中 **RevelationFix 的异教徒 (HereticServant) 受伤** → `HurtByTargetGoal.alertOthers` → `HereticServant.isAlliedTo(null)` → `Apostle.isAlliedTo(null)` → 399 行 NPE。

## 原因

Goety 的多个实体类重写了 `isAlliedTo(Entity)`（SRG: `m_7307_`）。当目标 AI `HurtByTargetGoal.alertOthers` 把为 null 的 `getLastHurtByMob()` 传进来时：

- 原版 1.20.1 `Entity.isAlliedTo` 对参数**不做空判断**，直接 `p.getTeam()` → NPE（Entity.java:2236）；
- 部分 Goety 重写（如 `Apostle`）在调 super **之前**就解引用参数（`entityIn.getType()`，Apostle.java:399）→ 同样 NPE。

经对 Goety 2.5.56.x / 2.5.57.0 全部 905 个实体类扫描，**重写 `isAlliedTo` 的类共 19 个，全部存在同类隐患**（直接解引用 / 透传 vanilla / 经 `MobUtil.illagerAllies` 工具类三种模式）。

## 修复方式（v1.1）

在**全部 19 个重写类**的 `isAlliedTo` 方法入口注入空判断（参数为 null 直接返回 false），并额外在**原版 `Entity.isAlliedTo` 入口**加一层兜底（覆盖透传路径与其它 mod 的同类调用）：

- `Owned`（v1.0 原有，保留）
- `Apostle`、`Vizier`、`VizierClone`、`BoneLord`、`SkullLord`、`BroodMother`、`Cultist`、`Heretic`、`Irk`、`Ripper`、`SquallGolem`、`WitherNecromancer`、`HostileDrownedNecromancer`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity`、`AbstractEnderling`、`AbstractSpiderServant`
- 原版 `Entity`（兜底）
- `MobUtil.illagerAllies`（工具类内部对参数无空判断，一并防护）
- `HereticServant`（v1.1.1 新增：RevelationFix 的异教徒，实际崩溃调用方，见下）

null 不可能是盟友，返回 false 安全且正确；**对有效实体的判断完全不受影响**，零副作用。mixin-only，不含任何 Goety 代码。

### 附属 mod 兼容性（已逐一扫描验证）

- GoetyAwaken、GoetyLadder、GoetyRevelation、goetygrae 等附属中重写 `isAlliedTo` 的类（Awaken 4 个 + Ladder 1 个）均为「透传 super」实现，最终会落到本补丁已覆盖的 Goety 类或原版 `Entity`，由兜底 mixin 自动覆盖。
- **RevelationFix（v1.1.1）**：经真实崩溃日志核实，`HereticServant`（异教徒，RevelationFix 的类，通常经 GoetyRevelation 的 JarJar 内嵌加载）会把 null 透传进 Goety `Apostle.isAlliedTo` 导致 399 行崩溃——v1.1.1 已为 `HereticServant.m_7307_` 入口新增空判断（调用方侧兜底）。若未装 RevelationFix，软模式会自动跳过该 mixin，不影响使用。

## 安装

- 需要 **Forge 1.20.1 (47.x)** + **Goety 2.5.49+**（22 个补丁目标已在 2.5.49.3 / 2.5.55.4 / 2.5.57.0 上逐一核对；实机验证于 2.5.55.4 与 2.5.57.0）
- 把发布版 jar 丢进 `mods` 文件夹即可（**替换旧版 goetyownedfix-1.0.0 / 1.1.0 / 1.1.1，不要同时装**）
- 与 RevelationFix / Goety:Revelation / Goety 各附属共存，无冲突
- 客户端和服务端**都要装**（集成服务器 = 开存档的那台机器必须装）

## 兼容性

- 仅以 mixin 方式在运行时打空判断补丁，不含任何 Goety 代码
- 若 Goety 官方后续修复了此问题，删除本 mod 即可

## 抗崩溃性说明

- **软模式**：mixin 配置为 `required=false` + `defaultRequire=0`——若未来 Goety 更新导致某个类被删除/方法改名，对应的 mixin 会被**跳过并打警告日志，游戏照常启动**，而不是崩溃。原版 `Entity.isAlliedTo` 兜底始终锚定在 1.20.1 原版方法上（该方法永不缺席），透传类即使某个 per-class mixin 失效也仍被覆盖。
- **依赖保护**：`mods.toml` 中 goety 依赖为 `mandatory=true` 且要求 `>=2.5.49`——若误装在没有 Goety 或版本过低的整合包里，FML 会在**启动阶段**给出明确报错并拒绝加载（不会进游戏后莫名崩溃）。
- **无冲突设计**：全部为 `@Inject` 叠加式注入，不与其它 mod 的重写冲突。

## 编译 / Build

需要 JDK 17，并准备以下 jar 作为 classpath：
`mixin-0.8.5.jar`、`javafmllanguage-1.20.1-47.4.22.jar`、`forge-1.20.1-47.4.22-universal.jar`、`client-1.20.1-...-srg.jar`、`goety-2.5.57.0.jar`（或对应的 2.5.56.x）

```bash
javac -encoding UTF-8 -proc:none -source 17 -target 17 \
  -cp "<上述 jar 以分号连接>" -d out \
  llxj/goetyfix/GoetyOwnedFixMod.java llxj/goetyfix/mixin/*.java
```

打包时注意：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyownedfix.json`，且包含 `pack.mcmeta`（pack_format 15）。

## 版本历史

- **1.1.2**：**modId 由 `goetyfix` 改为 `goetyownedfix`**（mixin 配置同步改名为 `mixins.goetyownedfix.json`）——解决与「Goety Fix」内存修复模组的 modId 冲突，两者现在可以同时加载；同时把 Goety 依赖下限从 2.5.56 放宽到 **2.5.49**（补丁目标已在 2.5.49.3 / 2.5.55.4 上逐一核对）
- **1.1.1**：新增 RevelationFix `HereticServant` 调用方入口守卫（经群友真实崩溃日志核实为实际崩溃路径，双保险）
- **1.1.0**：覆盖全部 19 个 `isAlliedTo` 重写类 + 原版 `Entity.isAlliedTo` 兜底 + `MobUtil.illagerAllies` 防护 + 软模式抗崩溃
- **1.0.0**：仅修复 `Owned.isAlliedTo`

## 与其它 mod 共存

- **Goety Fix（诡厄巫法内存修复）**：其 modId 同为 `goetyfix`，1.1.2 起本 mod 改用 `goetyownedfix`，两者可同时安装（已在 Goety 2.5.55.4 环境实测：两个 mod 均正常加载、mixin 各自应用、零冲突）
- 与 RevelationFix / Goety:Revelation / GoetyAwaken / goety_ladder / goetygrae 等附属共存无冲突

## 许可

MIT License。感谢 [Polarice3 的 Goety](https://github.com/Polarice3/Goety-2)。

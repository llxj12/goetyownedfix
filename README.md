# 诡厄巫法召唤物崩溃补丁 (goetyownedfix)

[English README](README_EN.md)

> **本分支是 Forge 1.20.1 版（v1.1.2 起 modId 为 `goetyownedfix`；v1.2.0 起已合并原 `goetyhellblastfix` 的狱焰修复，不再需要单独安装它）。**
> 如果你玩的是 **Minecraft 1.21.1（NeoForge）**，请到 [Releases](https://github.com/llxj12/goetyownedfix/releases) 下载对应版本，源码在 `neoforge-1.21.1` 分支。
> 两者面向不同游戏版本，按需择一安装；本 mod 与 modId 为 `goetyfix` 的「Goety Fix」内存修复 mod **可以同时安装**（1.1.2 起已实测共存）。

一个 Forge 1.20.1 迷你补丁，修复诡厄巫法 (Goety) 的**两类 `Ticking entity` 空指针崩溃**：

1. `isAlliedTo` 家族（v1.1.x）：召唤物受伤时目标 AI 把 null 传进 `isAlliedTo`；
2. 狱焰 `HellBlast` 家族（v1.2.0，合并自 `goetyhellblastfix`）：**无主**狱焰爆炸时对 null 归属者调用点燃方法。

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

经对 Goety 2.5.49.3 / 2.5.55.4 / 2.5.56.x / 2.5.57.0 的实体类扫描（2.5.56.x 全量 905 个逐一核对），**重写 `isAlliedTo` 的类共 19 个，全部存在同类隐患**（直接解引用 / 透传 vanilla / 经 `MobUtil.illagerAllies` 工具类三种模式）。

## 修复方式（v1.1）

在**全部 19 个重写类**的 `isAlliedTo` 方法入口注入空判断（参数为 null 直接返回 false），并额外在**原版 `Entity.isAlliedTo` 入口**加一层兜底（覆盖透传路径与其它 mod 的同类调用）：

- `Owned`（v1.0 原有，保留）
- `Apostle`、`Vizier`、`VizierClone`、`BoneLord`、`SkullLord`、`BroodMother`、`Cultist`、`Heretic`、`Irk`、`Ripper`、`SquallGolem`、`WitherNecromancer`、`HostileDrownedNecromancer`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity`、`AbstractEnderling`、`AbstractSpiderServant`
- 原版 `Entity`（兜底）
- `MobUtil.illagerAllies`（工具类内部对参数无空判断，一并防护）
- `HereticServant`（v1.1.1 新增：RevelationFix 的异教徒，实际崩溃调用方，见下）
- `MaverickServant`、`ApostleServant`（v1.2.1 新增：RevelationFix 另外两个同构仆从，入口判空；`MaverickServant` 经 Cultist 的 alertSameType 目标可达，`ApostleServant` 当前不可达，属防御性对齐）
- `IfritClone`、`MurmurServant`、`MurmurServantHead`（v1.2.1 新增：可选附属 goety_supreme / goetyominous 的入口判空；三者当前均不可达，属防御性对齐。用字符串 target 编写，不引入附属编译依赖，未安装时软模式只留一条告警）

null 不可能是盟友，返回 false 安全且正确；**对有效实体的判断完全不受影响**，零副作用。mixin-only，不含任何 Goety 代码。

### 附属 mod 兼容性（已逐一扫描验证）

- GoetyAwaken、GoetyLadder、GoetyRevelation、goetygrae 等附属中重写 `isAlliedTo` 的类（Awaken 4 个 + Ladder 1 个）均为「透传 super」实现，最终会落到本补丁已覆盖的 Goety 类或原版 `Entity`，由兜底 mixin 自动覆盖。
- **RevelationFix（v1.1.1）**：经真实崩溃日志核实，`HereticServant`（异教徒，RevelationFix 的类，通常经 GoetyRevelation 的 JarJar 内嵌加载）会把 null 透传进 Goety `Apostle.isAlliedTo` 导致 399 行崩溃——v1.1.1 已为 `HereticServant.m_7307_` 入口新增空判断（调用方侧兜底）。若未装 RevelationFix，软模式会自动跳过该 mixin，不影响使用。v1.2.1 又对另外两个同构类 `MaverickServant`（可达）与 `ApostleServant`（暂不可达）加了同样的入口守卫。

## 第二个缺陷：无主狱焰 HellBlast（v1.2.0，合并自 goetyhellblastfix）

### 症状

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_20254_(int)" because "this.val$entity" is null
    at Goety...HellBlast$1.explodeHurt (HellBlast.java:177)
    at Goety...SpellExplosion.<init> (SpellExplosion.java:72)
    at Goety...HellBlast$1.<init> (HellBlast.java:171)
    at Goety...HellBlast.m_6532_ (HellBlast.java:171)
```

触发条件：**狱焰没有归属者**（`/summon goety:hell_blast`、法术意外生成、发射者死亡/卸载区块导致 owner 丢失），且 `Fiery > 0`，且爆炸范围内**有生物被伤到**。炸空气、`Fiery = 0` 都不会触发，所以平时不一定暴露。

### 原因

`HellBlast.m_6532_` 把自己的 `getOwner()` 捕获进匿名爆炸类 `HellBlast$1`；`explodeHurt` 先结算爆炸伤害，随后对捕获的归属者调用 `setRemainingFireTicks`（`Entity.m_20254_`）。归属者为 null 时即 NPE，直接把服务端 tick 打崩。

### 修复

只重定向 `HellBlast$1.explodeHurt` 里**唯一一处** `Entity.m_20254_(I)`，归属者为 null 时跳过点燃；爆炸伤害与有主狱焰的行为完全不变。

- **为什么不能挂在构造函数 `@At("RETURN")`**：`SpellExplosion` 构造函数内部（第 72 行）就会调用 `explodeHurt`，NPE 从构造函数里抛出，构造函数永远走不到 RETURN——这正是 `goetyhellblastfix` 0.0.1 失效的原因。
- **为什么类名稳定**：真实崩溃栈里就是 `HellBlast$1`；被 mixin 改名的是其它 mod mixin 自己生成的匿名类（`Class$Anonymous$hash`），不是 Goety 的。
- 调用点已逐版本核对一致：2.5.25.0 / 2.5.36.1 / 2.5.55.4 / 2.5.56.0 / 2.5.56.4 / 2.5.57.0 / **2.5.58.4**（1.21.1 的 3.1.5.1 使用 Mojang 名，不在本分支适用范围）。

## 安装

- 需要 **Forge 1.20.1 (47.x)** + **Goety 2.5.49+**（28 个补丁目标已在 2.5.49.3 / 2.5.55.4 / 2.5.57.0 / 2.5.58.4 上逐一核对；实机验证于 2.5.55.4 与 2.5.57.0）
- 把发布版 jar 丢进 `mods` 文件夹即可（**替换旧版 goetyownedfix-1.0.0 / 1.1.0 / 1.1.1 / 1.1.2，不要同时装**）
- v1.2.0 已合并 `goetyhellblastfix`，**装过 `goetyhellblastfix-0.0.2.jar` 的请删掉它**，避免重复加载
- 与 RevelationFix / Goety:Revelation / Goety 各附属共存，无冲突
- 客户端和服务端**都要装**（集成服务器 = 开存档的那台机器必须装）

## 兼容性

- 仅以 mixin 方式在运行时打空判断补丁，不含任何 Goety 代码
- 若 Goety 官方后续修复了此问题，删除本 mod 即可

## 抗崩溃性说明

- **软模式**：mixin 配置为 `required=false` + `defaultRequire=0`——若未来 Goety 更新导致某个类被删除/方法改名，对应的 mixin 会被**跳过并打警告日志，游戏照常启动**，而不是崩溃。原版 `Entity.isAlliedTo` 兜底始终锚定在 1.20.1 原版方法上（该方法永不缺席），透传类即使某个 per-class mixin 失效也仍被覆盖。狱焰重定向同理（`require = 0`），失效只打警告。
- **软模式的代价**：注入成功与失败在游戏里表现一样。确认狱焰补丁是否生效，请在 `logs/debug.log` 里搜 `HellBlastExplosionNullGuardMixin`——没有 `Injection error` / `target was not found` 一类告警即为已生效。
- **依赖保护**：`mods.toml` 中 goety 依赖为 `mandatory=true` 且要求 `>=2.5.49`——若误装在没有 Goety 或版本过低的整合包里，FML 会在**启动阶段**给出明确报错并拒绝加载（不会进游戏后莫名崩溃）。
- **无冲突设计**：全部为 `@Inject` / `@Redirect` 叠加式注入（不替换方法体），不与其它 mod 的重写冲突。

## 编译 / Build

需要 JDK 17，并备好 Forge 47.4.22 的库（脚本内已写死本机标准路径，可用参数覆盖）：

```powershell
# 版本号自动从 META-INF/mods.toml 读取，不会出现「文件名 1.1.0、元数据 0.0.2」这类漂移
.\build.ps1

# 指定其它 Goety 版本 / JDK：
.\build.ps1 -GoetyJar '修改目标MOD\[诡厄巫法] goety-2.5.57.0.jar' -Jdk 'E:\.minecraft\jdk-17.0.18+8'
```

脚本流程：`javac` 编译 `llxj/**/*.java` → 组装 `META-INF/MANIFEST.MF`（含 `MixinConfigs: mixins.goetyownedfix.json`）、`pack.mcmeta`、mixin 配置与 `mods.toml` → 输出根目录 `goetyownedfix-<版本>.jar` 并打印 SHA-256。

编译 classpath 由脚本自动拼装，需要的原件是：`mixin-0.8.5.jar`、`javafmllanguage-1.20.1-47.4.22.jar`、`forge-1.20.1-47.4.22-universal.jar`、`client-1.20.1-...-srg.jar`，以及一个 1.20.1 的 goety jar（默认取 `修改目标MOD` 里最新的 2.x）。

打包注意：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyownedfix.json`，且包含 `pack.mcmeta`（pack_format 15）。

## 版本历史

- **1.2.1**：补齐 RevelationFix 另两个同构仆从的入口守卫——`MaverickServant`（经继承的 Cultist `HurtByTargetGoal` 开启 alertSameType，可复现同类 NPE）与 `ApostleServant`（当前不可达，防御性对齐）；另为可选附属 goety_supreme 的 `IfritClone` 与 goetyominous 的 `MurmurServant` / `MurmurServantHead` 加了字符串 target 守卫（无编译期依赖、未装只告警），补丁目标总数 28
- **1.2.0**：合并 `goetyhellblastfix` 0.0.2 的狱焰修复（`HellBlast$1.explodeHurt` 空归属者守卫），补丁目标总数 23；新增 `build.ps1`（版本号从 `mods.toml` 读取，杜绝文件名与元数据版本漂移）
- **1.1.2**：**modId 由 `goetyfix` 改为 `goetyownedfix`**（mixin 配置同步改名为 `mixins.goetyownedfix.json`）——解决与「Goety Fix」内存修复模组的 modId 冲突，两者现在可以同时加载；同时把 Goety 依赖下限从 2.5.56 放宽到 **2.5.49**（补丁目标已在 2.5.49.3 / 2.5.55.4 上逐一核对）
- **1.1.1**：新增 RevelationFix `HereticServant` 调用方入口守卫（经群友真实崩溃日志核实为实际崩溃路径，双保险）
- **1.1.0**：覆盖全部 19 个 `isAlliedTo` 重写类 + 原版 `Entity.isAlliedTo` 兜底 + `MobUtil.illagerAllies` 防护 + 软模式抗崩溃
- **1.0.0**：仅修复 `Owned.isAlliedTo`

## 与其它 mod 共存

- **Goety Fix（诡厄巫法内存修复）**：其 modId 同为 `goetyfix`，1.1.2 起本 mod 改用 `goetyownedfix`，两者可同时安装（已在 Goety 2.5.55.4 环境实测：两个 mod 均正常加载、mixin 各自应用、零冲突）
- 与 RevelationFix / Goety:Revelation / GoetyAwaken / goety_ladder / goetygrae 等附属共存无冲突

## 许可

MIT License。感谢 [Polarice3 的 Goety](https://github.com/Polarice3/Goety-2)。

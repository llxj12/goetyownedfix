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

打包要点：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyfix.json`，且包含 `META-INF/neoforge.mods.toml`、`mixins.goetyfix.json`、`pack.mcmeta`。

## 静态验证

`verify.ps1` 会对打好的 jar 做**不开游戏**的逐项校验：

1. 每个 `@Mixin` 目标类是否真的存在于 Goety 3.1.5.1 / Minecraft 1.21.1 中；
2. 目标类是否真的声明了被注入的 `isAlliedTo(Entity)`（描述符精确匹配）/ `MobUtil.illagerAllies(Entity,Entity)`；
3. `mixins.goetyfix.json` 列出的类与 jar 内的 mixin 类是否**完全一致**；
4. `neoforge.mods.toml` 的 modId/版本/三个依赖/`[[mixins]]` 声明是否齐全；
5. manifest 是否带 `MixinConfigs`；
6. 覆盖率统计：Goety 中重写 `isAlliedTo(Entity)` 的类有多少个被本补丁覆盖（当前 **19/19**）。

```powershell
.\verify.ps1            # 目标类/描述符 + 覆盖率
.\verify.ps1 -Audit     # 额外做字节码审计：证明 Goety 3.1.5.1 里的 bug 依然存在
```

**字节码级审计**（`tools/audit_allied.py`、`tools/bytecode_probe.py`）会反汇编 Goety 3.1.5.1 里全部 19 个 `isAlliedTo` 重写与 `MobUtil` 辅助方法，判定**参数为 null 时是否会被解引用**。当前结论（详见 `GOETY-3.1.5.1-AUDIT.md`）：

| 分类 | 数量 | 后果 |
| --- | --- | --- |
| 直接解引用参数（如 `Apostle` 第 1 条指令就是 `Entity.getType()`） | 8 | 参数为 null 立即 NPE |
| 透传给 super（最终落到原版 `Entity.isAlliedTo`，其方法体仅 9 字节且零判空） | 3 | 在原版处 NPE |
| 交给 `MobUtil.illagerAllies`（其 @8 处 `Entity.getTeam()`） | 7 | 在工具方法内 NPE |
| 参数被真正判空（`AbstractEnderling`） | 1 | 返回 false，不崩（保留 mixin 作为未来保险） |

也就是说：**官方在 1.21.1 上没有修这个问题，19 个类的防护全部有必要。**

另有一个**发布元数据校验**脚本，用规范级解析器检查打包结果（TOML 用 Python 标准库 `tomllib`，JSON 用 `json`）：

```powershell
python .\tools\validate_metadata.py .\dist\goetyownedfix-2.0.0-neoforge-1.21.1.jar 2.0.0
```

它会校验：`neoforge.mods.toml` 能否按 TOML 规范解析、`modLoader`/`loaderVersion`/`[[mixins]]`/`[[mods]]`（modId、version、displayName、description、authors、license、logoFile）是否齐全、三个依赖的类型与版本区间语法是否合法、manifest 的 `MixinConfigs` 指向的文件是否存在、mixin 配置列出的类是否都在 jar 内，最后打印产物大小与 SHA-256/SHA-1。

构建依赖的确切版本与来源、以及复现步骤见 `BUILD-MANIFEST.md`。

## 版本历史

- **2.0.0**：适配 Minecraft 1.21.1 / NeoForge；覆盖 Goety 3.1.5.1 全部 19 个 `isAlliedTo` 重写类 + 原版 `Entity.isAlliedTo` 兜底 + `MobUtil.illagerAllies` 防护 + 软模式抗崩溃

## 许可

MIT License。感谢 [Polarice3 的 Goety](https://github.com/Polarice3/Goety-2)。

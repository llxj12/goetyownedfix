## 诡厄巫法召唤物崩溃补丁 v2.0.0 — Minecraft 1.21.1 / NeoForge

修复 Goety 的 **`isAlliedTo` 空指针崩溃家族**（`Ticking entity` 崩溃）在 **1.21.1 / NeoForge** 上的版本。

### 安装

| 项目 | 要求 |
| --- | --- |
| 游戏 | Minecraft **1.21.1** |
| 加载器 | **NeoForge 21.1.x**（或更高 21.1） |
| 前置 | **Goety 3.1.5+**（1.21.1 移植版） |
| 安装位置 | 客户端与服务端**都要装**（单人存档 = 存档所在的那台机器） |

⚠️ 本版 modId 与 1.20.1 / Forge 版同为 `goetyfix`，**不要同时安装**。玩 1.20.1 请用 [v1.1.1](https://github.com/llxj12/goetyownedfix/releases/tag/v1.1.1)。

### 本版变化

- **移植到 NeoForge 1.21.1**：注入的方法名从 SRG `m_7307_` 改为官方名 `isAlliedTo`（NeoForge 1.21.1 不再使用 SRG 运行时名，因此也不需要 refmap）
- 依据 **Goety 3.1.5.1（1.21.1 移植版）全量扫描**，覆盖其中**全部 19 个**重写 `isAlliedTo(Entity)` 的实体类
- 保留原版 `Entity.isAlliedTo(Entity)` 兜底（覆盖所有"透传 super"的调用方，含其它 mod）
- 保留 `MobUtil.illagerAllies` 工具类防护
- 元数据迁移为 `META-INF/neoforge.mods.toml`，并新增 `[[mixins]] config=` 声明（NeoForge 1.21.x 的 mixin 配置加载路径）
- 依赖声明：`neoforge >= 21.1` / `minecraft [1.21.1,1.21.2)` / `goety >= 3.1.5`
- 未包含 RevelationFix `HereticServant` 守卫：RevelationFix 暂无 1.21.1 版本

### 覆盖范围

| 分类 | 数量 | 类 |
| --- | --- | --- |
| 直接解引用参数 | 8 | `Apostle`、`BoneLord`、`SkullLord`、`BroodMother`、`Cultist`、`Heretic`、`WitherNecromancer`、`HostileDrownedNecromancer` |
| 透传给 super | 3 | `Owned`、`SquallGolem`、`AbstractSpiderServant` |
| 经 `MobUtil.illagerAllies` | 7 | `Vizier`、`VizierClone`、`Irk`、`Ripper`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity` |
| 官方已自行判空 | 1 | `AbstractEnderling`（保留 mixin 作未来保险） |

以上分类来自对 Goety 3.1.5.1 发布字节码的反汇编（`tools/audit_allied.py`），证据见仓库 `GOETY-3.1.5.1-AUDIT.md`：其中 `Apostle.isAlliedTo` 的**第 1 条指令**就是 `Entity.getType()`，而原版 `Entity.isAlliedTo(Entity)` 方法体仅 9 字节、**零判空**。

### 抗崩溃设计

- **软模式**：mixin 配置 `required=false` + `defaultRequire=0`，若未来 Goety 更新删类/改名，对应 mixin 只跳过并打警告，**不会崩游戏**
- **依赖保护**：缺 Goety 或版本过低时，加载器在启动阶段直接报错拒绝加载
- 全部为 `@Inject` 叠加式注入，不与其它 mod 的重写冲突

### 校验值

```
文件    goetyownedfix-2.0.0-neoforge-1.21.1.jar
大小    31634 字节
SHA-256 e9b97ee0551868c2de240a59eb24d9e3baf8becd8bdd413fa860607759273a29
SHA-1   4f6f36446355cb7fa0cb3465f71fcbab8e2892f8
```

### 验证状态

已完成**静态验证**：21 个 mixin 的目标类与方法描述符全部命中 Goety 3.1.5.1、覆盖率 19/19、元数据经规范级解析器校验、构建可复现（固定时间戳后连续两次构建哈希一致）。

**尚未进行实机验证**（没有 1.21.1 游戏实例）。如果你遇到了问题，请在 [Issues](https://github.com/llxj12/goetyownedfix/issues) 附上 `logs/debug.log` 里 `goetyfix` 相关的行。

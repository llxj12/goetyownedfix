# Goety 3.1.5.1 `isAlliedTo` 崩溃面审计（字节码级证据）

本文件记录**为什么这个补丁在 1.21.1 上仍然必要**：不是「照着 1.20.1 抄一遍」，而是对 **Goety 3.1.5.1（NeoForge 1.21.1 移植版）真实发布的字节码**逐类反汇编得出的结论。

复现命令（无需启动游戏，纯静态分析）：

```powershell
python .\tools\audit_allied.py ..\_mc1211_tools\deps\goety-3.1.5.1.jar
python .\tools\bytecode_probe.py ..\_mc1211_tools\deps\goety-3.1.5.1.jar <类路径> isAlliedTo "(Lnet/minecraft/world/entity/Entity;)Z"
```

## 1. 崩溃链的两个必要环节都成立

**环节 A — 原版 `Entity.isAlliedTo(Entity)` 不判空**（`client-1.21.1-...-srg.jar`，方法体仅 9 字节）：

```
@2  invokevirtual  Entity.getTeam()                   <- 直接对参数取队伍
@5  invokevirtual  Entity.isAlliedTo(Team)
null-check branches: NONE
```

**环节 B — Goety 的重写照样会踩**，例如 `Apostle.isAlliedTo`（方法体 39 字节，**第 1 条指令**就是解引用参数）：

```
@1  invokevirtual  Entity.getType()                   <- entityIn.getType()，参数为 null 立即 NPE
@4  getstatic      ModTags$EntityTypes.APOSTLE_OTHER_ALLIES
@7  invokevirtual  EntityType.is(TagKey)
...
@35 invokespecial  SpellCastingCultist.isAlliedTo(Entity)
```

这与 1.20.1 时代真实崩溃日志里的 `Apostle.java:399 —— Cannot invoke "Entity.m_6095_()" because "entityIn" is null` 完全同源（`m_6095_` 即 `getType()`）。

## 2. 19 个重写类的完整分类

判定标准：**参数 `entityIn` 是否可能在为 null 的情况下被解引用**。注意——很多重写里**确实存在** `ifnull/ifnonnull` 分支，但它们判的是**别的值**（`getTrueOwner()` 的返回值，或 `getTeam()` 返回的 `PlayerTeam`），**并不保护参数本身**。

| 分类 | 数量 | 类 | 参数为 null 时的后果 |
| --- | --- | --- | --- |
| **直接解引用参数** | 8 | `Apostle`(@1 `getType`)、`BoneLord`(@33 `getTeam`)、`SkullLord`(@33)、`BroodMother`(@25)、`Cultist`(@18)、`Heretic`(@8)、`WitherNecromancer`(@25)、`HostileDrownedNecromancer`(@18) | 参数为 null 时**在解引用处立即 NPE** |
| **透传给 super** | 3 | `Owned`(@14 `LivingEntity.isAlliedTo`)、`SquallGolem`(@15 `AbstractGolemServant.isAlliedTo`)、`AbstractSpiderServant`(@14) | null 继续流入原版 `Entity.isAlliedTo` → 环节 A 处 NPE |
| **交给 `MobUtil.illagerAllies`** | 7 | `Vizier`、`VizierClone`、`Irk`、`Ripper`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity`（均在 @2 调用） | 进入工具方法，其 @8 `getTeam()` 处 NPE（见下） |
| **参数被真正判空** | 1 | `AbstractEnderling`（@4 `ifnonnull` 跳过全部参数解引用） | **返回 false，不崩**（该 mixin 为无害冗余/未来保险） |

### `MobUtil` 工具方法

| 方法 | 判定 | 证据 |
| --- | --- | --- |
| `illagerAllies(Entity, Entity)` | **UNSAFE** | 6 个 `ifnull/ifnonnull` 分支全部晚于首次解引用：@8 `Entity.getTeam()` 处 NPE |
| `areAllies(Entity, Entity)` | 未发现参数解引用 | 新增方法，本次未纳入防护（无必要） |

## 3. 结论

- **19 个类全部纳入防护是正确且必要的**：其中 18 个在参数为 null 时确实会走到 NPE，第 19 个（`AbstractEnderling`）虽已安全，但保留 HEAD 注入是无害的（且能在官方未来改动时继续兜底）。
- **`Entity.isAlliedTo` 兜底 mixin 是真正兜住「透传」类的那一层**：仅靠 19 个 per-class mixin 也能拦住，但任何**其它 mod**（或未被扫描到的第三方继承者）以同样方式透传 null 时，只有原版入口的兜底能救。
- 补丁的注入点是 `@At("HEAD")` + `cancellable`，**先于方法体任何一条指令执行**，因此在上述所有路径上都能拦下 null。

## 4. 与 1.20.1 分支的差异

- 1.20.1 的 `Apostle` 是「先 `entityIn.getType()` 再 super」，1.21.1 的 `Apostle` 同样是第 1 条指令解引用 —— **官方在这两个版本上都没有修**。
- 1.21.1 的 `Vizier`、`VizierClone`、`Irk`、`Ripper`、`HostileRedstoneGolem`、`HostileRedstoneMonstrosity`、`HuntingIllagerEntity` 经由 `MobUtil.illagerAllies`，与 1.20.1 一致；该方法在 3.1.5.1 中依然不安全。

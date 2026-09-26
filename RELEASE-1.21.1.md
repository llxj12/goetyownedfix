# 1.21.1 / NeoForge 发布清单 (v2.0.0)

## 构建产物

```
dist/goetyownedfix-2.0.0-neoforge-1.21.1.jar
```

| 项 | 值 |
| --- | --- |
| 大小 | 31634 字节 |
| SHA-256 | `4c6b086b04b985e828cbd883d1854e8773b93bacea34159598c2fc807bb5a25d` |
| SHA-1 | `1650712df7dcad4af45cba16ee38eac4dcd3d879` |

构建：`.\build.ps1`（同源重建字节级可复现）
验证：`.\verify.ps1`（目标类/描述符 + 19/19 覆盖率）· `python tools\validate_metadata.py <jar> 2.0.0`（TOML/JSON/元数据）
依赖与复现细节见 `BUILD-MANIFEST.md`。

## 发布前检查清单

- [x] 22 个源文件用 JDK 21 编译通过（`--release 17` 字节码）
- [x] jar 结构正确：`META-INF/neoforge.mods.toml`、`META-INF/MANIFEST.MF`(MixinConfigs)、`mixins.goetyfix.json`、图标
- [x] 静态验证：21 个 mixin（19 Goety + Entity + MobUtil）目标类与方法描述符全部命中 Goety 3.1.5.1，覆盖率 19/19
- [x] 元数据验证：TOML 用规范级解析器（tomllib）解析通过；`[[mixins]]` 声明、modId/版本/logoFile/三个依赖、版本区间语法全部校验通过
- [x] 构建可复现：两次独立构建产物 SHA-256 一致
- [ ] **实机验证（尚未做）**：需要 NeoForge 1.21.1 + Goety 3.1.5.1 的游戏实例
  - 验证方法：进入游戏后打开 `logs/debug.log`，搜索 `goetyfix`，应看到 21 行
    `Mixing XxxAlliedGuardMixin from mixins.goetyfix.json into ...`
  - 若某行缺失，说明该 mixin 未生效（软模式下只打警告，不崩溃）
  - 触发场景：在 Goety 召唤物/信徒附近战斗，尤其是下界多只同类在场时

## 平台发布字段

| 字段 | 值 |
| --- | --- |
| 名称 | 诡厄巫法召唤物崩溃补丁 (goetyownedfix) |
| 英文名 | Goety Summon Crash Patch |
| 版本 | 2.0.0 |
| modId | goetyfix |
| 加载器 | NeoForge |
| 游戏版本 | 1.21.1 |
| 依赖 | Goety 3.1.5+ (1.21.1 移植版)，必须与本体同时安装于客户端与服务端 |
| 许可 | MIT |
| 作者 | LLXJ |
| 分类建议 | Bug Fixes / Utility（Modrinth: `neoforge`, `1.21.1`；CurseForge: `Bug Fixes`, `Mobs`） |

## 更新日志（可直接粘贴）

### 2.0.0 — 1.21.1 / NeoForge 移植

- 移植到 **NeoForge 1.21.1**：注入的方法名由 SRG `m_7307_` 改为官方名 `isAlliedTo`（NeoForge 1.21.1 不再使用 SRG 运行时名，因此也不需要 refmap）
- 依据 **Goety 3.1.5.1（1.21.1 移植版）** 全量扫描结果，覆盖其中**全部 19 个**重写 `isAlliedTo(Entity)` 的实体类
- 保留原版 `Entity.isAlliedTo(Entity)` 兜底 mixin（覆盖所有"透传 super"的调用方，含其它 mod）
- 保留 `MobUtil.illagerAllies` 工具类空判断防护
- 元数据迁移为 `META-INF/neoforge.mods.toml`，并新增 `[[mixins]] config=` 声明（NeoForge 1.21.x 的 mixin 配置加载路径）
- 依赖声明改为 `neoforge >= 21.1` / `minecraft [1.21.1,1.21.2)` / `goety >= 3.1.5`
- 新增 `build.ps1`（一键编译打包）与 `verify.ps1`（不开游戏的目标类/方法描述符静态校验，含覆盖率统计）
- **未包含** RevelationFix `HereticServant` 守卫：RevelationFix 暂无 1.21.1 版本；若后续发布，可照 1.20.1 分支的写法加回

## 已知限制

1. **尚未实机验证**：本版本只做了静态校验（目标类存在、方法描述符匹配、元数据完整），未在 1.21.1 游戏里跑过。
2. **仅支持 NeoForge**：不适用于 Fabric/Quilt；1.20.1 请用 `legacy-forge-1.20.1/` 里的 Forge 版。
3. **不能与 Forge 版共存**：modId 同为 `goetyfix`（不同加载器本也不会装在一起，但别把两个 jar 丢进同一个 mods 目录）。
4. **RevelationFix 相关路径未覆盖**：若将来 1.21.1 上有 RevelationFix，且其异教徒仍把 null 透传进 Goety，需要补一个 `HereticServant` 守卫 mixin。

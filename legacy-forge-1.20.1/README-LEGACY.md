# 已归档：1.20.1 / Forge 版源码

本目录是 **goetyownedfix 的 1.20.1 / Forge 版**，完整保留，供历史版本维护与对照。仓库根目录现在是 **1.21.1 / NeoForge 版**。

## 内容

| 路径 | 说明 |
| --- | --- |
| `llxj/goetyfix/` | 1.20.1 源码：1 个 Mod 主类 + 22 个 mixin（19 个 Goety 重写类 + 原版 `Entity` 兜底 + `MobUtil` + RevelationFix `HereticServant`） |
| `META-INF/mods.toml` | Forge 版元数据（`mandatory=`、依赖 `forge`/`minecraft`/`goety`） |
| `mixins.goetyfix.json` | Forge 版 mixin 配置（注入 SRG 名 `m_7307_`） |
| `pack.mcmeta` | Forge 版需要；1.21.1 的 mod jar 不再需要 |
| `test/GoetyFixTest.java` | 原静态自检程序（toml/json/类加载与 `@Mixin` 目标解析） |
| `goetyownedfix-*.jar` | 历史发布产物 1.0.0 / 1.1.0 / 1.1.1 |

## 该版的要点

- 注入的方法是 **SRG 名 `m_7307_`**（1.20.1 Forge 生产环境的运行时方法名）
- 元数据文件是 **`META-INF/mods.toml`**，依赖 modId 为 `forge`
- mixin 配置通过 **manifest 的 `MixinConfigs`** 加载
- 目标 Goety：**2.5.56+**（已在 2.5.56.5 / 2.5.57.0 / 2.5.58.4 上核对）
- 比 1.21.1 版多一个 **RevelationFix `HereticServant`** 守卫（RevelationFix 目前没有 1.21.1 版本）

## 编译（与 1.20.1/Forge 一致）

需要 JDK 17，以及以下 jar 作为 classpath：
`mixin-0.8.5.jar`、`javafmllanguage-1.20.1-47.4.22.jar`、`forge-1.20.1-47.4.22-universal.jar`、`client-1.20.1-...-srg.jar`、`goety-2.5.57.0.jar`

```bash
javac -encoding UTF-8 -proc:none -source 17 -target 17 \
  -cp "<上述 jar 以分号连接>" -d out \
  llxj/goetyfix/GoetyOwnedFixMod.java llxj/goetyfix/mixin/*.java
```

打包要点：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyfix.json`，且包含 `pack.mcmeta`（pack_format 15）。

## 注意

两个版本的 **modId 都是 `goetyfix`**（同一项目的不同游戏版本），**不要同时安装**。

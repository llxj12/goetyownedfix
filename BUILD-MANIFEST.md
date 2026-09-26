# 1.21.1 / NeoForge 构建清单 (v2.0.0)

本文件记录构建该 jar 所需的**确切依赖版本与来源**，以及产物的校验值，便于他人复现与比对。

## 产物

| 项 | 值 |
| --- | --- |
| 文件 | `dist/goetyownedfix-2.0.0-neoforge-1.21.1.jar` |
| 大小 | 31634 字节 |
| SHA-256 | `e9b97ee0551868c2de240a59eb24d9e3baf8becd8bdd413fa860607759273a29` |
| SHA-1 | `4f6f36446355cb7fa0cb3465f71fcbab8e2892f8` |
| 字节码 | Java 17（`javac --release 17`，JDK 21 编译） |
| 内容 | 22 个类（1 个 Mod 主类 + 21 个 mixin）、`mixins.goetyfix.json`、`META-INF/neoforge.mods.toml`、图标 |

## 构建依赖（classpath）

| jar | 版本 | 来源 |
| --- | --- | --- |
| `neoforge-21.1.219-client.jar` | 21.1.219 | `maven.neoforged.net/releases/net/neoforged/neoforge/21.1.219/` |
| `client-1.21.1-20240808.144430-srg.jar` | 1.21.1 | 启动器库 `libraries/net/minecraft/client/`（官方名，非混淆） |
| `sponge-mixin-0.15.2+mixin.0.8.7.jar` | mixin 0.8.7 | 随 NeoForge 21.1.219 分发 |
| `loader-4.0.42.jar` | FML 4.0.42 | `maven.neoforged.net/releases/net/neoforged/fancymodloader/loader/4.0.42/`（提供 `@Mod`） |
| `goety-3.1.5.1.jar` | 3.1.5.1 | Goety 官方 NeoForge 1.21.1 移植版（mixin 目标） |

编译命令（由 `build.ps1` 生成）：

```
javac -encoding UTF-8 -proc:none --release 17 -nowarn \
  -cp "<上述 5 个 jar 以 ; 连接>" -d build/classes <22 个 java 源文件>
```

打包要点：
- `META-INF/MANIFEST.MF` 含 `MixinConfigs: mixins.goetyfix.json`
- 含 `META-INF/neoforge.mods.toml`（其中 `[[mixins]] config="mixins.goetyfix.json"` 是 NeoForge 1.21.x 的加载路径）
- 1.21.1 的 mod jar **不需要** `pack.mcmeta`（Minecraft 1.21 起 mod 资源包自动生成 `pack.mcmeta`）

## 开发环境（本次构建实际使用的工具链）

| 项 | 值 |
| --- | --- |
| JDK | Zulu 21.52+203-CA（OpenJDK 21.0.12.1 LTS），解压于 `..\_mc1211_tools\jdk\` |
| 依赖缓存目录 | `..\_mc1211_tools\deps\` |
| 构建脚本 | `build.ps1`（自动发现 JDK，缺依赖时回退到本机启动器库） |
| 验证脚本 | `verify.ps1`（目标类/方法描述符 + 覆盖率）· `tools/validate_metadata.py`（TOML/JSON/清单元数据） |

## 复现步骤

```powershell
# 1) 准备 classpath 依赖到 ..\_mc1211_tools\deps\（见上表）
# 2) 构建
.\build.ps1
# 3) 双重验证
.\verify.ps1
python tools\validate_metadata.py dist\goetyownedfix-2.0.0-neoforge-1.21.1.jar 2.0.0
```

`build.ps1` 在打包前会把暂存目录里所有文件的时间戳**固定**到 `SOURCE_DATE_EPOCH`（默认 `1790432400` = 2026-09-26T14:20:00Z），因此 jar 内条目时间戳不再随构建时间变化，**同源重建产物字节级一致**（已实测连续两次构建 SHA-256 相同：`e9b97ee0…`）。

> 注：早期版本未固定时间戳，每次构建的 SHA-256 都不同（内容相同、仅条目时间戳不同）。若你要核对旧哈希，请以本文件当前值为准。
>
> 更换 `SOURCE_DATE_EPOCH` 会得到不同哈希但内容等价的产物；发布时请**只声明一种**构建参数。

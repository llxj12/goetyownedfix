# 诡厄巫法召唤物崩溃补丁 (goetyownedfix)

一个 Forge 1.20.1 迷你补丁，修复 **诡厄巫法 (Goety) 召唤物反复崩溃** 的问题。

## 症状

进世界/下界时游戏崩溃，崩溃报告为：

```
Ticking entity
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.entity.Entity.m_5647_()" because "p_20355_" is null
    at Entity.m_7307_ (Entity.java:2236)
    at Goety...Owned.m_7307_ (Owned.java:186)
```

常见触发场景：**狱焰、僵尸仆从等 Goety 召唤物受伤时**（尤其下界、多只同类召唤物在场时）。

## 原因

Goety 的 `Owned.isAlliedTo(Entity)` 在参数为 null 时（目标AI `HurtByTargetGoal.alertOthers` 把已被 Goety 清空的 `getLastHurtByMob()` 传进来），把 null 透传给原版 `Entity.isAlliedTo`。原版 1.20.1 的实现对参数**不做空判断**，直接调用 `p.getTeam()` → NPE → 整个游戏崩溃。

## 修复方式

在 `Owned.isAlliedTo` 方法入口注入空判断：**参数为 null 直接返回 false**（null 不可能是盟友）。不影响任何正常游戏行为，对所有 Goety Owned 系召唤物（狱焰、僵尸仆从等）一次性生效。

## 安装

- 需要 **Forge 1.20.1 (47.x)** + **Goety 2.5.56+**
- 把发布版 jar（见 Releases 或各平台发布页）丢进 `mods` 文件夹即可
- 与 RevelationFix / Goety:Revelation / Goety 各附属共存，无冲突
- 客户端和服务端**都要装**（集成服务器 = 开存档的那台机器必须装）

## 兼容性

- 仅以 mixin 方式在运行时给 Goety 的 `Owned` 类打一个空判断补丁，不含任何 Goety 代码
- 若 Goety 官方后续修复了此问题，删除本 mod 即可

## 编译 / Build

需要 JDK 17，并准备以下 jar 作为 classpath：
`mixin-0.8.5.jar`、`javafmllanguage-1.20.1-47.4.22.jar`、`forge-1.20.1-47.4.22-universal.jar`、`client-1.20.1-...-srg.jar`、`goety-2.5.56.5.jar`

```bash
javac -encoding UTF-8 -proc:none -source 17 -target 17 \
  -cp "<上述 jar 以分号连接>" -d out \
  llxj/goetyfix/GoetyOwnedFixMod.java llxj/goetyfix/mixin/OwnedNullGuardMixin.java
```

打包时注意：jar 的 `META-INF/MANIFEST.MF` 必须包含 `MixinConfigs: mixins.goetyfix.json`，且包含 `pack.mcmeta`（pack_format 15）。

## 许可

MIT License。感谢 [Polarice3 的 Goety](https://github.com/Polarice3/Goety-2)。

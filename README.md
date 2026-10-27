# HD2 战况接口实验台（Status / GWE 抓包与合成注入）

> build `26088801` / warId 801，2026-10-27 实机。
> 与 [hd2-datamined](https://github.com/deepseekv41flash/hd2-datamined) 的分工：
> **那边只放离线数据表逆向**（`.dl_bin` 表结构、字段、命名），**这边放网络层**——
> 抓包、对表、以及对 `Status` 响应的合成改写实验。

## 这是什么

《Helldivers 2》客户端从 `api.live.prod.thehelldiversgame.com` 拉战况。本仓库记录并工具化了一条实验线：

```
本地 hosts + 自签 CA + 443 MITM  →  只改写 /api/WarSeason/801/Status  →  客户端把假战况当真
```

它起源于对一个第三方 mod（`variant_mod`）的逆向：那个 mod 的「变种玩法」不是数据表 mod，
而是一个 MITM 代理，通过给 `planetActiveEffects` 追加条目来改变星球上的敌人变种。
本仓库把这个机制拆开、量到边界。

## 结论速览（全部实机验证）

| 改写 Status 的字段 | 客户端表现 |
|---|---|
| `planetActiveEffects` | 星图效果芯片 / 部署界面**作战卡** / `COMBATANT FORCES` / **局内天气** |
| `campaigns` | 任意星球变成「前线」：**可选、可进、可开一局** |
| `planetStatus.owner` | 星球卡阵营标题 **+ 任务里刷哪一族敌人** |
| 伪造 `campaignId` 发给服务器 | 服务器照发 operation id 与 missionId，**无任何校验** |

细节与证据：[`docs/EXPERIMENTS-2026-10-27.md`](docs/EXPERIMENTS-2026-10-27.md)。

## 文档

| 文件 | 内容 |
|---|---|
| `docs/EXPERIMENTS-2026-10-27.md` | 9 组实验的完整记录：设计、判据、证据、否证、踩坑 |
| `docs/GWECAPTURE.md` | GWE（GalacticWarEffects）抓包与对表方法、effectType 解释器、实测结果 |
| `docs/EFFECT-MENU-801.md` | 310 条效果目录 × presence 种类/阵营/显示名 × 在线战况 × 证据等级 |
| `docs/E8-REACHABILITY.md` | 「能不能进入原本打不了的星球」专项实验 |

## 工具

| 文件 | 作用 |
|---|---|
| `tools/gwe_capture.py` | 给第三方 `war_proxy.py` 打只读抓包补丁（含 12 项自检，含顺序陷阱回归） |
| `tools/gwe_join.py` | GWE 条目 ↔ 本地对象表的对表工具 |
| `tools/effect_menu.py` | GWE + presence 表 + 最新 Status → 可注入效果菜单（md + csv） |

> 启动器 `run_capture.ps1` / `capture_status.ps1` 也收进来了，但它们依赖第三方 mod 目录、
> 本机证书与 hosts（换机器要改路径）；工作流见 `docs/GWECAPTURE.md` §1。
> 抓包产物（响应体）**不入库**：里面有账号 id。

## 边界与合规

这是**只读侦察 + 本机客户端侧**的实验：代理只改自己机器收到的响应，不向服务器写战况。
但「伪造 campaign 后在无战役星球上创建作战」确实向线上服务器发了它认为非法的请求
（服务器未拒绝）。这类实验应在受控、短时、可回滚的前提下进行，且不要扩散到多人对局。

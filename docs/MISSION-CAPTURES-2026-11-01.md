# 任务抓包三连（2026-11-01 夜）：伪造防守 → 城市分区 → 真实防守

> 目标：把 `Operation/Create` → `Mission/Start` → `Mission/end` 全链路、三条任务线（解放 / 事件防守 / 城市分区）
> 都抓到真实样本，并验证哪些字段能用于判读。
> 结论先说：**链路全部抓通**；伪造防守能完整打完并拿到结算，但生成的任务不是真防守任务、结算里的
> `campaignWon/othersImpact*` 是残值；城市分区与真防守拿到了干净对照组，`impact` 落点、`othersImpact` 语义、
> 目标表（game.dll 0x2CA65D0）全部解出。
>
> 字段总表与证据见 `repo-datamined/docs/tables/OPERATION-MISSION-API-26088801.md`；
> 目标名解码见 `repo-datamined/docs/tables/MISSION-OBJECTIVES-26251122.md`。

## 0. 本夜三局一览

| 轮次 | 时间（+08）| 任务线 | 星球 | 难度 | 作战 | 结果 |
|---|---|---|---|---|---|---|
| ① 伪造防守 | 21:54–22:07 | 事件防守（伪造）| CHARBAL-VII(156) | 8 | op 1237 / type 4 / jointOp 9101 | 成功撤离，`campaignWon=true(伪)` |
| ② 城市分区 | 22:19–22:55 | 城市分区 | MINTORIA(207) region 1 | 8 | op 1242 / type 8 | 成功撤离，`impact=2` → 分区 −2 |
| ③ 真防守 | 23:07–23:47 | 事件防守（真实事件 5730）| MINTORIA(207) | 8 | op 1243 / type 4 / jointOp 5730 | 成功撤离，`othersImpact=1,844` 验证 |

## 1. 环境与工具

### 1.1 启动"防守注入 rewrite"模式（新脚本，可重复执行）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  D:\mod\work\variant-net\tools\start_defense_proxy.ps1 `
  -SpecFile D:\mod\work\variant-net\out\defense_spec_20261101.json
```

脚本做四件事（全部幂等、自动备份）：
1. `stop.ps1` 停旧代理，等 443 释放；
2. 备份 `config.json` / `runtime\selection.json` / `runtime\status.json` 为 `*.bak-defense-<时间戳>`；
3. 写 `config-defense.json`（`targets=[]`、`passthrough=false`）与 `selection.json`（`enabled=false`）——
   只保留"Status 改写路径"，不叠加变种词条；
4. 带 `HD2_GWE_EXTRA`（防守 spec）/ `HD2_GWE_DUMP` / `HD2_GWE_PATHS` / `HD2_GWE_REQ_PATHS` 启动代理。

### 1.2 本夜注入 spec（五件套，目标 156 CHARBAL-VII ← 157 DURGEN）

```json
{"campaigns":[{"planet":156,"id":51990,"type":4,"count":38,"race":3}],
 "attacks":[{"source":157,"target":156}],
 "events":[{"planet":156,"id":9101,"eventType":1,"race":3,
            "health":1881000,"maxHealth":1900000,
            "startOffset":-3600,"endOffset":169200,
            "campaignId":51990,"hqNodeIndex":2}],
 "owner":{"156":1}}
```

离线自检：`defense_inject.py selftest` 7/7 PASS；再用真实 Status 走 `rewrite_status` 得 `added=4`。

### 1.3 抓包环境

```
HD2_GWE_DUMP      = D:\mod\out\gwe
HD2_GWE_PATHS     = /api/WarSeason/801/Status,/api/Operation
HD2_GWE_REQ_PATHS = /api/Operation
```

## 2. 第一局：伪造防守 156（21:54–22:07）

### 2.1 现场

- 21:54:34 Status（`23195938`）命中注入，日志 4 行 `REWRITE-EXTRA`；
- 21:56:20 `Operation/Create`（`req_419c21eb`）→ 服务器接受，op **1237**；
- 21:57:37 `Mission/Start`（`req_585875be`）→ `missionId e5acb2a0…`；
- 22:05:57 `Mission/end`（`req_be90471d` → `d0bdbe5b`）成功；
- 22:07:16 Status（`4ff62a20`）——服务器侧 156 号星球**毫无变化**（无战役/事件），伪造 campaign 从未存在过。

### 2.2 Create 请求（客户端把防守参数自己选好）

```json
{"operationSettingsId":538077316,"jointOperationId":9101,"type":4,"id":1237,
 "seed":1544323042,"race":3,"warId":801,"placementNodeIndex":9,
 "campaignId":51990,"planetIndex":156,"difficulty":8,
 "missions":[{"type":3,"state":1,"index":0},{"type":3,"state":1,"index":1},{"type":3,"state":1,"index":2}]}
```

### 2.3 结算（`d0bdbe5b`）

| 字段 | 值 | 判读 |
|---|---|---|
| XP / 影响力 / 货币 | 258 / 86 / 1,002 | 真实发放 |
| multipliers | `851354768 ×3` + `540020798 ×1` | 难度 8 ✓ |
| `campaignWon` | **true** | ✗ 残值（服务器不认识事件）|
| `othersImpactPlanetEvent` | **1,880,999** | ✗ 残值（= 注入事件血量 −1）|
| 任务目标（解码）| **ERADICATE AUTOMATON FORCES** | ⚠ 是普通清剿任务，不是真防守任务 |

⇒ **伪造防守的边界**：链路 100% 可用（建作战/开局/打完/结算），但
① 任务池退回普通任务；② `campaignWon/othersImpact*` 不可用。研究防守语义必须打真实事件。

## 3. 第二局：城市分区 207（22:19–22:55，**故意挑的城市任务**）

### 3.1 时间线（含 3 次"建了作战但没打"的真防守）

| 时刻 | 事件 |
|---|---|
| 22:19:22 | Abandon 1237（离开 156 时自动撤掉伪造作战）；Create **1238** type 8（城市）|
| 22:20:11 / 22:20:24 | Create **1239 / 1240** type 4（真防守，jointOp 5730，3×type3）|
| 22:21:43 | Start 1240 mission 0 → 22:25:42 Abandon（无结算请求）|
| 22:25:57 / 22:26:26 | Create/Start **1241** type 4 → 22:34:30 Abandon（无结算请求）|
| 22:35:11 | Create **1242** type 8（城市，region 1）|
| 22:36:02 | Start 1242 mission 2，`regionIndex=1`、`territoryIndex=148` |
| 22:36:28 | `SetMaxRewards 4` |
| 22:53:35 | `Mission/end` 1242 → 结算（`req_fca34003` → `12b9a872`）|
| 22:55:02 | Status（`8d70d101`）|

### 3.2 Create / Start 关键差异

```json
// Create（type 8 城市分区）
{"operationSettingsId":3204348594,"jointOperationId":-1,"type":8,"id":1242,
 "seed":-1176703554,"race":3,"warId":801,"placementNodeIndex":1,
 "campaignId":51752,"planetIndex":207,"difficulty":8,
 "missions":[{"type":1,...},{"type":1,...},{"type":1,...}]}
// Start：regionIndex = 1（城市分区），Mission/end 请求也带 regionIndex
```

### 3.3 本局 8 个目标（全解码）

3 个 `DESTROY AUTOMATON COMMAND BUNKER`（全成功）+ `DETECTOR TOWER`×2（1 成 1 败）+
`MORTAR EMPLACEMENT`（败）+ `GUNSHIP FACILITY`（败）+ `UPLOAD ESCAPE POD DATA`（成）。
`missionSuccess=true`（只看撤离，3 个侧目标失败不影响）。

### 3.4 结算与 Status 实测

| 项 | 值 |
|---|---|
| XP / 影响力 / 货币 | **936 / 312 / 4,434**（约为解放战的 3.5–4.3 倍）|
| badges | 9 个，含三个新解 locid：**Destroyed Light/Medium/Heavy Automaton Outpost**（影响 5/10/20）|
| `impact` | 2 |
| `campaignWon` | false |
| `othersImpact*` | 0/0/0 |
| **Status 实测** | `planetRegions[207][1].health` **200,000 → 199,998 = −2** ⇒ 城市战 impact 直接扣分区血量（1:1）|
| 同时 | `planetEvents[207].health` −705（**别人**在打事件防守，与本局无关）|

## 4. 第三局：真实防守 207（23:07–23:47，事件 5730，难度 8）

### 4.1 时间线

| 时刻 | 事件 |
|---|---|
| 23:07:54 | Create **1243**（`operationSettingsId=538077316`、`jointOperationId=5730`、type 4、diff 8、3×type3）→ 服务器接受 |
| 23:08:28 | Start：`regionIndex=-1`、missionIndex 2、territory 214 → `missionId 0a859dd6…` |
| 23:08:57 | `SetMaxRewards 8` |
| 23:40:19 | `Mission/end`（`req_4776dd8b` → `dd2350f7`）成功撤离 |
| 23:46:58 | Status（`32fad0ba`）——用于验证事件血量 |

### 4.2 本局 8 个目标（全解码）

| 目标 | 成败 |
|---|---|
| **EVACUATE PRIORITY CITIZENS**（撤离平民）| ✅ |
| **ESTABLISH COMMUNICATION UPLINK** ×2（联络被困平民）| ✅ ✅ |
| STRATAGEM JAMMER | ❌ |
| GUNSHIP FACILITY | ✅ |
| SEAF ARTILLERY | ❌ |
| LIDAR STATION | ❌ |
| DESTROY ROGUE RESEARCH STATION | ✅ |

⇒ 真防守任务的形状 = **撤离平民/高价值资产 + 中继通信**，再附带随机侧目标。

### 4.3 结算

| 项 | 值 |
|---|---|
| XP / 影响力 / 货币 | 903 / 301 / 4,602 |
| `multipliers` | `851354768 ×3` + `540020798 ×1` ✓（难度 8）|
| `campaignWon` | **false** ✓ |
| `othersImpactPlanetEvent` / `communityTarget` | **1,844 / 1,844** |
| `impact` | 2 |

### 4.4 验证 `othersImpactPlanetEvent`（本夜最后一块拼图）

| 指标 | 值 |
|---|---|
| 事件 5730 血量 @23:05:02（`7f6ae829`，即客户端开局缓存）| 2,248,348 |
| 事件 5730 血量 @23:46:58（`32fad0ba`）| **2,246,101** |
| 实际掉血 | **−2,247**（41.8 分钟，53.7/分）|
| 本局窗口（23:08:28→23:40:19，31.9 分钟）按同速率折算 | ≈1,711（期间在线 2,693→3,062，速率略升 ⇒ 1,844 合理）|
| 响应里的 `othersImpactPlanetEvent` | **1,844** ✓ |

对照 10/29：`othersImpact=4,789`，同期事件掉血速率 ≈200/分 × 21 分钟 ≈ 4,205 ✓ 同量级。
⇒ **`othersImpactPlanetEvent` = 本局期间其他玩家把事件血量打掉的量**（个人 `impact` 不计入或可忽略）。

## 5. 本夜补齐/修正的语义（速查）

| 结论 | 证据 | 详见 |
|---|---|---|
| `warTime`/`healthAtStart*` = **客户端缓存的 Status 快照**（不是服务器实时值）| 6/6 局与抓包 Status 的 `time` 逐字节一致 | API 文档 §4.2 |
| `multipliers[].id32` **按难度索引**（game.dll `0x205C578` 10 元素数组）| diff5→33707031/1.75、diff8→851354768/3.0 | API 文档 §5.3 |
| `impact` 三条落点：行星 / 事件 / **城市分区** | 城市局分区血 200000→199998 | API 文档 §5.5 |
| `othersImpactPlanetEvent` = 其他玩家的事件贡献 | 两例真防守 | API 文档 §5.6 |
| `objectives[].id` 可解码成目标名 | game.dll 0x2CA65D0 目标表（152 条）| 目标表文档 |
| 伪造防守 = 链路可用但**任务池与结算残值不可用** | 与真防守同难度对照 | API 文档 §7 |
| `operation.type`：0=解放、4=事件防守、8=城市分区 | 6 局互锁 | API 文档 §2.1 |

## 6. 回滚（本夜结束时已执行）

```powershell
# 1) 停代理
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\stop.ps1
# 2) 还原三份备份（时间戳 20261101-214549）
copy /Y D:\Downloads\variant_mod\config.json.bak-defense-20261101-214549  D:\Downloads\variant_mod\config.json
copy /Y D:\Downloads\variant_mod\runtime\selection.json.bak-defense-20261101-214549 D:\Downloads\variant_mod\runtime\selection.json
copy /Y D:\Downloads\variant_mod\runtime\status.json.bak-defense-20261101-214549    D:\Downloads\variant_mod\runtime\status.json
# 3) 想继续用代理但正常玩：passthrough 重启
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\run.ps1 -Passthrough
# 4) 想彻底撤环境（需管理员）：撤销 hosts + 证书
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\teardown.ps1
```

> 注意：hosts 仍指向本机 ⇒ 代理必须保持运行（passthrough 或 rewrite），否则游戏无法连服务器；
> 彻底停用要 `teardown.ps1`（管理员）。

## 7. 未解 / 后续

1. `889185878` / `1748229498` 等 hash 型 badge 的名字（不在 26088801 strings；部分与目标表 `+0x54` 关联）；
2. `3071768642` 在 4 局里 amount 恒为 8 的原因；
3. `SetMaxRewards` 规则（本夜见 14 / 8 / 4）；
4. 城市分区战是否也能触发事件防守结算（城市局 `othersImpact*=0`，说明城市战不挂事件）；
5. 多人与联合作战（joint op 多人）样本未抓。

## 8. 产物清单（`D:\mod\out\gwe\`）

| 轮次 | Create | Start | end 请求→响应 | Status 前/后 |
|---|---|---|---|---|
| ① 伪造防守 | `req_419c21eb` | `req_585875be` | `req_be90471d` → `d0bdbe5b` | `23195938` / `4ff62a20` |
| ② 城市 | `req_607da437`(1242)、`req_2afeaeac`(1238) | `req_a72b7f59` | `req_fca34003` → `12b9a872` | `7a647a36` / `8d70d101` |
| ③ 真防守 | `req_cdc8d894` | `req_f3f61671` | `req_4776dd8b` → `dd2350f7` | `7f6ae829` / `32fad0ba` |
| 未打的真防守 | `req_f93da49f`(1239)、`req_08e6f70e`(1240)、`req_771b5373`(1241) | `req_60899f7b`(1240)、`req_52c2aa4d`(1241) | 只有 Abandon | — |

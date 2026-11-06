# 游戏访问的 API 清单（除 GWE 以外的全部端点）

> 来源：`D:/Downloads/variant_mod/logs/proxy.log.1` + `proxy.log`（最近一段会话，共 **5638** 条请求、**59** 种端点模式）。
> 抓取方式：hosts 把 `api.live.prod.thehelldiversgame.com` 指到本机 MITM 代理（自签会话证书），**只覆盖这一个 API 主机**；Steam / CDN / PlayFab 等其它主机不经过代理，本表看不到。
> 机读版：`out/gwe/api-endpoints.csv`（本地生成，`out/` 不入库）；生成器 `tools/api_inventory.py`。

## 1. 分组总览

| 组 | 端点数 | 请求数 |
|---|---:|---:|
| 社交 | 3 | 827 |
| 战局 | 10 | 1520 |
| 大厅 | 5 | 929 |
| 消息 | 6 | 598 |
| 配置 | 1 | 118 |
| 账号 | 2 | 142 |
| 命令 | 3 | 213 |
| 任务 | 9 | 395 |
| 养成 | 16 | 788 |
| 商业化 | 1 | 90 |
| 未知 | 1 | 15 |
| 其他 | 2 | 3 |

## 2. 全量清单（按请求数降序）

| 组 | 方法 | 端点 | 次数 | 平均请求体 | 用途 |
|---|---|---|---:|---:|---|
| 社交 | GET | `/api/FriendsV2/Request?offset={n}&limit={n}` | 406 | 0 B | 好友请求/最近/拉黑 |
| 战局 | GET | `/api/Episode/{warId}/status?maxEntries=1` | 406 | 0 B | 赛季/剧集活动状态 |
| 大厅 | PUT | `/api/lobby` | 388 | 1528 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 大厅 | POST | `/api/lobby/{id}/member` | 259 | 4 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 战局 | GET | `/api/Stats/war/{warId}/summary` | 249 | 0 B | 全局战况汇总（前线/星系统计） |
| 大厅 | POST | `/api/lobby/accounts` | 227 | 2647 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 社交 | GET | `/api/FriendsV2/Block?offset={n}&limit={n}` | 214 | 0 B | 好友请求/最近/拉黑 |
| 社交 | GET | `/api/FriendsV2/Recent?offset={n}&limit={n}` | 207 | 0 B | 好友请求/最近/拉黑 |
| 消息 | GET | `/api/NewsFeed/801?maxEntries=16&fromTimeStamp={ts}` | 200 | 0 B | 新闻/公告 |
| 战局 | GET | `/api/WarSeason/{warId}/timeSinceStart` | 134 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/WarSeason/{warId}/Status` | 122 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 配置 | GET | `/api/Configuration/GameClient` | 118 | 0 B | GameClient 客户端配置 |
| 账号 | POST | `/api/Account/Login` | 114 | 437 B | Login / ReportPosition（反作弊上报） |
| 命令 | GET | `/api/v2/Assignment/War/801` | 110 | 0 B | Major Order/每日命令（War/Player） |
| 消息 | POST | `/api/Pes/GetMessages` | 105 | 127 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 战局 | GET | `/api/WarSeason/GalacticWarEffects` | 104 | 0 B | GWE 效果目录（服务器准备的内容清单） |
| 战局 | GET | `/api/WarSeason/current/WarId` | 103 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/Stats/profile/summary` | 101 | 0 B | 个人战绩汇总 |
| 战局 | GET | `/api/Stats/profile/{warId}/summary` | 101 | 0 B | 个人战绩汇总 |
| 命令 | GET | `/api/v2/Assignment/Player` | 101 | 0 B | Major Order/每日命令（War/Player） |
| 消息 | POST | `/api/Pes/GetConfiguration` | 100 | 63 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 消息 | POST | `/api/Mail/inbox` | 100 | 118 B | 邮件收件箱 |
| 战局 | GET | `/api/WarSeason/{warId}/warinfo` | 100 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/WarSeason/NewsTicker` | 100 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 任务 | GET | `/api/Mission/RewardEntries` | 91 | 0 B | 任务结算：RewardEntries / Session |
| 任务 | GET | `/api/Operation` | 90 | 0 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 养成 | GET | `/api/Progression/ItemPackages` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/ProgressionPackages` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/items` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/levelspec` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/inventory` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 商业化 | PUT | `/api/Monetization/Steam/RedeemStoreContent` | 90 | 0 B | Steam DLC/商城兑换 |
| 养成 | GET | `/api/Progression/Items/Customize/v2` | 90 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/SeasonPass` | 90 | 0 B | 战争债券页面数据 |
| 消息 | POST | `/api/Pes/GetMotd` | 90 | 63 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 任务 | POST | `/api/Operation/Mission/Start` | 73 | 166 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 任务 | POST | `/api/Operation/Mission/SetMaxRewards` | 66 | 73 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 大厅 | GET | `/api/lobby/{id}` | 47 | 0 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 养成 | PUT | `/api/Progression/Items/Customize/v2` | 41 | 99 B | 物品/背包/等级/成就/自定义 |
| 任务 | POST | `/api/Operation/Abandon` | 28 | 27 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 任务 | POST | `/api/Operation/Create` | 28 | 317 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 账号 | POST | `/api/Account/ReportPosition` | 28 | 79 B | Login / ReportPosition（反作弊上报） |
| 未知 | POST | `/api/Proxy/1621247262/577226056` | 15 | 329 B | 内部代理/中继（请求体未抓，响应 0B） |
| 养成 | POST | `/api/Progression/inventory/consume` | 11 | 253 B | 物品/背包/等级/成就/自定义 |
| 养成 | PUT | `/api/Progression/Achievements` | 11 | 141 B | 物品/背包/等级/成就/自定义 |
| 任务 | POST | `/api/Mission/Session` | 11 | 1242 B | 任务结算：RewardEntries / Session |
| 大厅 | DELETE | `/api/lobby/clear` | 8 | 4 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 任务 | POST | `/api/Operation/Mission/ActivityV2` | 5 | 108 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 任务 | POST | `/api/Operation/Mission/end` | 3 | 851 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 消息 | POST | `/api/Pes/GetIngameSurvey` | 3 | 938 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 命令 | POST | `/api/v2/Assignment/Player` | 2 | 40 B | Major Order/每日命令（War/Player） |
| 其他 | GET | `/api/StoreFront` | 2 | 0 B |  |
| 其他 | GET | `/` | 1 | 0 B |  |
| 养成 | GET | `/api/SeasonPass/1518605421` | 1 | 0 B | 战争债券页面数据 |
| 养成 | GET | `/api/SeasonPass/1859364959` | 1 | 0 B | 战争债券页面数据 |
| 养成 | GET | `/api/SeasonPass/593507300` | 1 | 0 B | 战争债券页面数据 |
| 养成 | GET | `/api/SeasonPass/1193171589` | 1 | 0 B | 战争债券页面数据 |
| 养成 | GET | `/api/SeasonPass/3978214801` | 1 | 0 B | 战争债券页面数据 |

## 3. 与实验最相关的接口

- **`GET /api/WarSeason/801/Status`**：战况板（planetStatus / planetActiveEffects / campaigns / planetAttacks / planetEvents / jointOperations）——我们唯一会**改写**的响应；
- **`GET /api/WarSeason/GalacticWarEffects`**：效果目录（312 条，含 type32/40/71/94）——只读抓包；
- **`PUT /api/lobby`**：组队 + 当前选中星球（代理从请求体里读 `player planet`，用于粘性注入）；
- **`POST /api/Operation/Create` / `Mission/Start` / `Mission/end`**：任务创建、开始、结算；Create 的请求体里带 `operationSettingsId / type / planetIndex / difficulty / missions[]`，结算请求体带 `planetEventId / healthAtStart / objectives / operationId`——都是**服务端权威**，本地伪造风险高（之前防守伪造实验已经踩过）；
- **`GET /api/Stats/war/801/summary`**：全局战况（前线 63 条攻击边等）；
- **`GET /api/v2/Assignment/War/801`**：Major Order；**`/api/Progression/*`**：解锁/背包（服务端权威）。

## 3.5 实测：`Operation` / `Mission` 响应里没有任务级 modifier 字段（2026-11-01）

响应白名单扩到 `/api/Operation`、`/api/Mission` 后，实际打两局的全文：

| 端点 | 响应大小 | 字段 | 有 modifier 吗 |
|---|---:|---|---|
| `GET /api/Operation` | 558 B | `nextOperationId` + `operations[]`：`id, seed, warId, planetIndex, placementNodeIndex, campaignId, jointOperationId, isActive, type, difficulty, race, missions[{index,type,state,missionId,participants}], rewards, operationSettingsId` | ✗ 没有 |
| `POST /api/Operation/Create` | 60 B | `{operations:[{id, rewards:[], backupRewards:[]}]}` | ✗ 没有 |
| `POST /api/Operation/Mission/Start` | 52 B | `{missionId: uuid}` | ✗ 没有 |
| `POST /api/Operation/Mission/end` | 560/1244 B | `operationId, missionIndex, missionId, experience, multipliers[], badges[], campaignWon, impact, progressionPackageUpdates[], rewards[]` | ✗ 没有（`multipliers` 是徽章/经验倍率） |

⇒ **任务级 modifier（wiki 的 Operation Modifiers）不由 API 下发**；客户端把它硬编码在 `data/game/game.dll`（偏移 `0x2CA0168`，13 条 × 0x50 B，可用 `repo-datamined/tools/opmod_scan.py` 提取）。
详见 `repo-datamined/docs/tables/OPERATION-MODIFIERS-26088801.md`。

> 2026-11-01 深夜续：三条任务线（解放/事件防守/城市分区）共 6 局已抓全，字段语义、`impact` 落点、
> `othersImpactPlanetEvent`、`multipliers`（按难度）、`objectives[].id` 解码都已完成 —— 见
> `repo-datamined/docs/tables/OPERATION-MISSION-API-26088801.md`、
> `repo-datamined/docs/tables/MISSION-OBJECTIVES-26251122.md`、本仓库 `MISSION-CAPTURES-2026-11-01.md`。

## 4. 已抓到的请求体样本（`D:/mod/out/gwe/req_*.json`）

```jsonc
// POST /api/Operation/Create
{"operations":[{"operationSettingsId":2350081063,"jointOperationId":-1,"type":0,"id":1210,
  "seed":804334477,"race":2,"warId":801,"placementNodeIndex":6,"campaignId":51999,
  "planetIndex":139,"difficulty":1,"missions":[{"type":1,"state":1,"index":0}]}]}
// POST /api/Operation/Mission/Start
{"planetIndex":156,"warId":801,"regionIndex":-1,"operationId":1221,"missionIndex":0,
  "territoryIndex":12,"participants":["11893343864225233967"]}
// POST /api/Operation/Mission/ActivityV2
{"uniqueId":2344827714,"activityId32":2140130854,"missionId":"961f1ae0-…"}
// POST /api/Operation/Mission/end（节选）
{"warSeasonId":801,"type":3,"planetEventId":5729,"planetIndex":244,"healthAtStartPlanet":1400000,
  "campaignId":51751,"objectives":[{"id":3846731770,"succeeded":true}],"operationId":1220,…}
```

## 5. 未知/待查

- **`POST /api/Proxy/{a}/{b}`**（15 次，请求体 ~325–334 B，响应 0 B）：像内部中继/转发，未抓请求体（需要把捕获白名单加上该路径才能看）；
- **`POST /api/Mission/Session`**（9 次，583–2431 B）：任务会话/结算前上报，响应 202/200 0 B；
- **`POST /api/Pes/GetIngameSurvey`**（955 B）：局后问卷；
- 其余 `Pes/*`（GetConfiguration/GetMessages/GetMotd）是 PlayFab 风格的账号侧数据。

## 6. 复现

```bash
python tools/api_inventory.py     # 重新统计日志 → CSV + 本文档
```


## 7. 战备解锁：59 个端点里没有载体（2026-11-05 排查）

有人会自然想到"既然武器能靠 inventory 注入上架，战备也一样"。**不行，原因在接口层**。

### 7.1 两个否证

| 检查 | 结果 |
|---|---|
| 951 条拥有清单里有几个 id 与 `generated_stratagem_settings` 的战备 id 相交 | **只有 2 个** ⇒ inventory 不是战备的拥有表 |
| 59 个已抓端点里有"已解锁战备数组 / 解锁位 / 领取记录"吗 | **没有**（`stratagem` 相关端点零命中）|

### 7.2 唯一真实存在的授予通道

`GET /api/WarSeason/801/Status` 的 `planetActiveEffects[]` → 指向 `effectType = 32` 的 GWE 效果
（`values[0]` = 战备 hash）。特性：

- **星球级 / 全局**（后者走 `globalEvents[].effectIds`），不是账号级；
- **临时**（跟星球/事件走），**最多同时 3 个**；
- **不进拥有列表**，也不改配装面板的永久可选集。

type32 全表 88 条、84/88 能解出战备名、官方发放实例见 `docs/TYPE32-STRATAGEMS.md`。

### 7.3 永久解锁的可能载体（未验证）

抓到的响应里唯一沾"进度/领取"的字段是 `/api/Progression` 的
`packageProgress.claimedLevels` 与 `purchasedSeasonPassItems`（战令页已领等级）。
战备解锁状态可能在这里、也可能根本不在服务端 —— 与"配件解锁"同形态（客户端本地/内存登记表）。

### 7.4 结论

- 代理**发不了**永久战备，只能做星球/全局的临时配发（type32）；
- 要真正"永久解锁 + 配装面板可选"，现有唯一可行路线是数据表 `generated_stratagem_settings +0xC8`
  的额外战备（[RECON-SHODAN-EXTRA-STRATAGEM](https://github.com/deepseekv41flash/hd2-datamined/blob/master/docs/cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md)，7 条实机）；
- 若要走代理，下一步得先抓**改装/战令页按需请求**，确认 `claimedLevels` 是否真是载体。

## 8. 配件解锁的真实端点：`AcquireUnlockableItem`（2026-11-06 发现）

此前（`repo-datamined` WEAPON-CUSTOMIZATION §15）判定"配件没有拥有层、解锁状态在客户端本地"。
**2026-11-06 17:12 的实机日志否掉了后一半** —— 在游戏里花 Requisition 解锁 CB-9 Exploding Crossbow
的 REFLEX SIGHT 时，代理完整记到了这两笔：

```
17:12:12  POST /api/Progression/ProgressionPackage/AcquireUnlockableItem   136B → 200 (119B)
17:12:34  PUT  /api/Progression/Items/Customize/v2                        160B → 200 (1705B)
```

| 端点 | 判读 |
|---|---|
| `POST /api/Progression/ProgressionPackage/AcquireUnlockableItem` | **解锁购买动作**：把"某个可解锁项"花货币买下来。附件解锁走的就是它 |
| `PUT /api/Progression/Items/Customize/v2` | 随后把选中的配件写进该武器的改装槽（我们此前已知的保存路径）|

⇒ **附件解锁是服务端动作，不是纯本地**。之前"没有拥有层"只说明它**不在**
`/api/Progression/inventory` 的 `items[]` 与 `/api/Progression/items` 目录里（那两个清单查不到任何 optionId），
并不等于服务端没有记录 —— 记录应该在"可解锁项"这套结构里，由 `AcquireUnlockableItem` 写入。

**仍缺的一环：请求体。** 当时请求白名单只有 `/api/Operation`，136 B 的 body 没落盘。已修复：

- `_gwe_capture_req` 默认白名单改为 `/api/Operation,/api/lobby,/api/Progression/Items/Customize`
  （运行时可用 `HD2_GWE_REQ_PATHS` 覆盖）；
- 请求体文件名带上方法：`req_<METHOD>_<hash>_<path>.json`，`index.txt` 记 `REQ <METHOD>\t<path>`；
- 代理于 2026-11-06 17:15:27 以 `HD2_GWE_PATHS="api/"` + `HD2_GWE_REQ_PATHS="api/Operation,api/lobby,api/Progression"` 重启。

下次再解锁任意一个配件，就能拿到 body 与 119 B 响应，从而确认：
① 解锁项用什么 id 空间（是不是 optionId `0xB7303DA1`）；② 响应里是否回传剩余货币/已解锁集合。

## 8.1 完整报文（2026-11-06 17:25 抓到 AR-23A 的 ANGLED FOREGRIP 解锁）

**解锁请求** `POST /api/Progression/ProgressionPackage/AcquireUnlockableItem`（135 B）：

```json
{ "expectedCost" : [ { "mixId" : 3608481516, "amount" : 5000}],
  "itemMixId" : 718265621, "targetLevel" : 7, "packageId32" : 2221505542}
```

**响应**（114 B）：

```json
{"packageId32":2221505542,
 "inventoryChanges":[{"mixId":3608481516,"amount":-5000},{"mixId":718265621,"amount":1}]}
```

**随后装备** `PUT /api/Progression/Items/Customize/v2`（186 B）：

```json
{ "mixId" : 1160920394, "modes" : [0,0,0,0], "activeIndex" : 0,
  "customizations" : [ { "index" : 0, "slots" : [3207983096, 3073392033, 3171207820, 209531742, 3072203841, 0,0,0]} ] }
```

## 8.2 id 模型（关键：附件的"拥有"是 inventory 里的一行）

`/api/Progression/items` 里 `progressionCategory == 2` 且带 `parentId` 的记录就是**附件解锁行**：

```json
{"itemId":3207983096, "parentId":1160920394, "mixId":718265621,
 "progressionCategory":2, "isConsumable":false, "buyPrice":[], "sellPrice":[]}
```

| 概念 | 值 | 说明 |
|---|---|---|
| 附件 optionId | `3207983096` = `0xBF35EFF8` | 写进 `customization.slots[]` 的那个 id；**就是目录行的 `itemId`** |
| 武器 mixId | `1160920394` = `0x45323D4A` | 目录行的 `parentId`（AR-23A Liberator Carbine）|
| 附件库存键 | `718265621` | 目录行的 `mixId`；**「这把枪 + 这个附件」独享的一个 id** |
| 武器包 | `2221505542` = `0x84697C06` | 请求里的 `packageId32` |
| 货币 | `3608481516` | Requisition（`isConsumable`、`progressionCategory 18`、`maxCap 50000`）|
| 等级门槛 | `targetLevel: 7` | 该枪等级要求，对应改装页的 LUL |

目录全量统计（3020 条里）：**1455 条附件行 / 57 把武器 / 247 种附件**，本账号当时已拥有 **279** 条。

### 8.2.1 为什么之前误判成"没有拥有层"

2026-11-05 那次排查是拿 **optionId（`0x…`）** 去比 inventory 的 **`mixId`** 字段 —— 但附件行的
`itemId` 才是 optionId，`mixId` 是另一套库存键。字段比错，于是得到"0 命中"。

### 8.2.2 持久化实证

| 证据 | 内容 |
|---|---|
| 17:12 解锁 CB-9 的 REFLEX SIGHT（当时没抓到 body） | — |
| 17:19 重新拉 `Progression/inventory` | **963 → 964 条**，新增 `2828694410` |
| 该行内容 | `{itemId: 3073392033 (0xB7303DA1 REFLEX SIGHT), parentId: 1942567317 (0x73C93995 CB-9), progressionCategory: 2}` |

⇒ **附件解锁会写进服务端 inventory 并持久化**；客户端按"这一行在不在"判断配件是否已解锁。

### 8.2.3 由此得到的能力（**✓✓ 实机 2026-11-06 17:35**）

"送附件" = 往 `inventory.items[]` 里塞 `{mixId: <附件库存键>, amount: 1}`，与武器上架同一条路。
代理已支持**独立的附件注入开关** `runtime/inventory_attach_inject.json`
（`_gwe_inventory_rewrite` 会与 `inventory_inject.json` 分别开关、同时开启则合并），
生成器 `tools/attach_items.py`：

```bash
python tools/attach_items.py --catalog <items抓包>.json     --weapon 0x45323D4A --inventory <inventory抓包>.json     --out runtime/inventory_attach_inject.json [--enable] [--list]
```

> ⚠ 抓包目录里 `PUT /api/lobby` 的 body **含 `connectionString`（大厅连接串）与 `memberAccountId`**，
> 属敏感数据：`out/` 必须在 `.gitignore` 里（当前已忽略），任何文档/提交都不得粘贴原值。

## 8.3 `PUT /api/lobby` 的 body 形状（已加入白名单）

1350 B，字段：`startTime / lobbyId / players[4]（sourcePlatform、memberAccountId、isHost、playerName、
playerRank、experience、hasInfo、commendRank）/ connectionString / operationProgress / gameModeProgress /
memberAccountIds / inLoadout / buildGameHash / warId / state / difficulty / hostability / privacyMode /
onboardingState / numLobbyMembers / sosBeacons / planetId / territoryId / race / crossplayMode /
preferenceGroup / regionIndex`。

进星球前 `warId = -1`、`planetId = -1`；`players[0]` 是房主，其余为占位（`sourcePlatform: 5`）。

**✓✓ 实机结果**：给 AR-23A 注入 28 条它尚未拥有的附件行后，用户回报
**「28 个全可选、装上能用」**（未花 Requisition）。

| 证据 | 值 |
|---|---|
| 代理日志 | `INV REWRITE +51 -0 items`（17:33、17:35 两次）|
| 算术核对 | 24 武器行 + 28 附件行 − 1（AR-23A 下挂已于 17:25 真买，已在清单里）= **51** ✔ |
| 同一时刻的服务端真值 | `7ea1b22a` inventory = **965 条**（964 + 新买的 718265621），其中 `2828694410`（CB-9 反射镜）与 `718265621`（AR-23A 下挂）都在 ⇒ 两笔真实购买都已持久化，而注入物（LAS-22 等）依旧 0 命中 |

⇒ **附件解锁完全由 inventory 一行决定，客户端不校验等级/货币/包进度**。
⇒ 全目录 1455 行覆盖 57 把武器 / 247 种附件，可一次性全解锁（生成器 `tools/attach_items.py`）。

**边界**：未发布武器（如 LAS-22 `0x7DE53646`）在目录里**没有任何附件行**（0 条），
所以它们的改装页仍是 CANNOT EDIT —— 这条要靠"伪造目录行 + 库存行"另行尝试，与本次能力不冲突。

## 9. 超级商店（StoreFront）：外观类解锁（2026-11-06 真实购买抓包）

用户在 19:02:52 登录后，于 **19:04:09 / 19:04:38 / 19:05:01** 连买三件外观（护甲 / 头盔 / 披风），全量抓包完整记录。

### 9.1 端点族

| 端点 | 作用 | 本次大小 |
|---|---|---|
| `GET /api/StoreFront/rotation` | 当期轮换：`{expireTime, salesPage:{id32, layoutType, layoutSize, sections:[{id32,bannerId32,items:[{salesId, mixId, position, size}]}]}}` | 617 B |
| `GET /api/StoreFront/<pageId32>` | 某个商店页（同上结构，含 banner 分组）| 14,652 B（`page=2776696735`）|
| **`POST /api/StoreFront/buy`** | **购买** | 请求 129 B / 响应 99–133 B |

### 9.2 购买报文

```jsonc
// 请求（129 B）
{"expectedCost": [{"mixId": 3481751602, "amount": 250}],
 "salesId": "38125272-1f68-4637-9fff-eeb23eb39a39", "warId": 801}

// 响应（133 B）
{"items": [{"mixId": 2556497905, "amount": 1},      // ← 授予的物品
           {"mixId": 2254107389, "amount": -200},    // ← 实扣货币 A
           {"mixId": 3422537285, "amount": -50}],    // ← 实扣货币 B
 "packageProgress": []}
```

要点：

- **`salesId` 是购买凭据**（UUID），由商店页下发；`mixId` 由页面给出 → `page[salesId].mixId == 授予的 mixId`（三次全部一致）。
- `expectedCost.mixId = 3481751602` 是**组合价 id**，不是实际扣费货币；响应里扣的是 `3422537285` / `2254107389`（均 `progressionCategory: 18`、`isConsumable`）。
- **授予方式 = `items[]` 里给该 `mixId` +1** —— 与武器上架、附件解锁**同一条 inventory 机制**。

### 9.3 三次真实购买（19:04–19:05）

| 时刻 | salesId | 售价 | 授予 mixId | 目录属性 |
|---|---|---:|---|---|
| 19:04:09 | `38125272…` | 250 | **2556497905** | `cat 3`，`itemId 2846302183`，`parentId 3622341476`（DP-8 套装）|
| 19:04:38 | `ee979cd3…` | 100 | **1233248044** | `cat 3`，`itemId 2979884042`，`parentId 3622341476`（同套装 = 头盔）|
| 19:05:01 | `add6aac6…` | 125 | **1513263450** | `cat 3`，`itemId == mixId`，无 `parentId`（披风）|

购买前那份 inventory（19:03:11，**965 条服务端真值**）里三件**都不在** ⇒ 三件都是本次新获得的拥有权。

> ⚠ 目录里的 `buyPrice`（250 / 125 / 100）与实际扣费（250 / 100 / 125）**顺序不一致**，
> 说明目录价不等于当期售价（或页面/目录的对应被我们读反）——**不要拿 `buyPrice` 当售价**。

### 9.4 由此得到的结论

**外观（护甲 / 头盔 / 披风 / 横幅……）在服务端就是 inventory 里的一行**，`progressionCategory: 3`
（横幅等为 9）。所以"解锁护甲"完全可以走和武器一样的注入路线，不需要伪造购买请求。

规模：目录 `cat 3` 共 **427 条**，本账号已拥有 **236**，**未拥有 191** ⇒ 都是可注入候选。

**注意别混两个 id 空间**：`inventory.avatarCustomization` 里的 `armor_set` / `helmet_set`
（本次为 `1773940042` / `2547476111`）是**外观变体 key**（对应 `generated_customization_armor_sets.dl_bin`），
**不是**物品 id，也永远不该出现在 `inventory.items[]` 里。

### 9.4.1 商店 UI 的"已拥有"也读 inventory（2026-11-06 19:20 实机）

把三件**尚未购买**的商店外观注入 `inventory.items[]` 后（`INV REWRITE +167`），用户回报：
军械库出现三件、可装备、模型正常，**并且商店页对这三件直接显示"已拥有"**。

⇒ 商店的"我买过没有"判定**不是**查购买记录/`salesId`，而是与军械库共享同一份
`/api/Progression/inventory` 响应。一次注入同时影响**军械库 + 超级商店**两个界面。

⇒ 反过来也说明：真买与注入的差别只在服务端记录；界面上两者无法区分
（本次同一会话服务端真值 `965 → 968`，正好是三次真实购买的 +3，注入的三件 0 命中）。

### 9.5 商店物品的**名字**从哪来（抓包里没有名字）

`StoreFront/*` 与 `Progression/items` 里**只有 id**（`mixId` / `itemId` / `salesId`），没有任何名称字段。
名字要回本地数据解：

```bash
# ① 解封护甲/外观表（422 组、453,204 B 明文）
python tools/dlbin_seal.py open-key --key refs/dlbin/keys/recipient.sk \
    --out armor_sets.plain "<game>/data/game/generated_customization_armor_sets.dl_bin"

# ② 在行内找 itemId / mixId / parentId（套装），行内有两个名称 locid（全大写 + 标题式），
#    用 refs/strings-en-26088801.json（24,834 条）解出
```

实测（2026-11-06，两次反向验证）：

| id | 在表里的键 | 解出名字 |
|---|---|---|
| `3622341476`（套装）| parentId | **DP-8 MOUNTAIN-SCALED** ✓ 与用户刚买的一致 |
| `1513263450`（披风 mixId）| mixId | **THUNDERING HOOVES OF LOYALTY** ✓ 与用户口述一致 |
| `3710087385`（套装）| parentId | **SS-500 PALE PROSECUTOR** |
| `1808786641`（披风 mixId=itemId）| mixId | **ARCTIC DECREE** |
| `186664391` / `1952614298`（两件的 itemId）| itemId | 同属 `SS-500 PALE PROSECUTOR`（护甲与头盔**共用套装名**）|

⇒ 经验：**护甲行与头盔行共用同一套名称 locid**（同套装同名），披风/横幅各自单独一行；
名字永远在本地表里，抓包只给 id，写文档/回答问题时不要凭 id 猜名字。

## 10. 战备解锁：`POST /api/SeasonPass/item/buy`（2026-11-06 20:30 真实解锁抓包）

用户 20:30:02 从 **ENTRENCHED DIVISION** 战团解锁 **GAS MORTAR SENTRY**，全量抓包完整记下。

### 10.1 端点族

| 端点 | 作用 |
|---|---|
| `GET /api/SeasonPass/<warbondId32>` | 战团详情：`seasonPassPages[].seasonPassItems[] = {seasonPassItemId, itemMixId, medalCost, gridSize, gridPosition, isPremium, isRepeatable}` ← **页内每一项 → 实际物品 id 的映射就在这里** |
| **`POST /api/SeasonPass/item/buy`** | **买单个战团项** |
| `GET /api/SeasonPass` | 26 个战团概览（`itemIds` = `seasonPassItemId` 集合，不是页号）|

### 10.2 报文

```jsonc
// 请求（102 B）—— 战团 id 3978214801，项 919，85 奖章
{"expectedCost": [{"mixId": 1276729503, "amount": 85}],
 "seasonPassItemId": 919, "warId": 801}

// 响应（130 B）
{"items": [{"mixId": 1276729503, "amount": -85},    // 奖章（medalsConsumableMixId）
           {"mixId": 3859732805, "amount": 1},      // ← 解锁的物品（+1 = 进 inventory）
           {"mixId": 905852432, "amount": 85}],     // 该战团的 medalsSpentMixId
 "packageProgress": []}
```

### 10.3 结论：**战备拥有权 = inventory 里的一行（`progressionCategory: 11`）**

| 检查 | 结果 |
|---|---|
| `seasonPassItemId 919` → `itemMixId` | **3859732805**（`medalCost 85`，与请求金额一致）|
| 该 id 在 `Progression/items` 里 | **有**：`{itemId: 3859732805, mixId: 3859732805, progressionCategory: 11, isConsumable: false}` |
| 购买前 inventory（968 条） | **不含** 3859732805 |
| 购买后 | 响应 `items[]` 给它 **+1** ⇒ inventory 加一行 |

⇒ **和武器 / 附件 / 商店外观同一条机制**：拥有权就是 inventory 行；`cat 11` 是"战备解锁物品"这一类。
⇒ 2026-11-05 那次"951 条里只有 2 个 id 与 `stratagem_settings` 相交"之所以得出"无载体"，
是因为**拿战备 hash 去比 inventory**；战备的解锁物品是另一套 mixId（`cat 11`），战备 hash 与它无关。
⇒ 目录里 `cat 11` 共 **108** 条，本次登录时已拥有 **77**、未拥有 **31** ⇒ 都是"只加一行 inventory 即可"的候选
（目录行本来就存在，因此不与"伪造目录行不被客户端接受"那条边界冲突）。




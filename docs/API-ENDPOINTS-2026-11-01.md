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


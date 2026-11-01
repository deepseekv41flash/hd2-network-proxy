# 游戏访问的 API 清单（除 GWE 以外的全部端点）

> 来源：`D:/Downloads/variant_mod/logs/proxy.log.1` + `proxy.log`（最近一段会话，共 **5436** 条请求、**53** 种端点模式）。
> 抓取方式：hosts 把 `api.live.prod.thehelldiversgame.com` 指到本机 MITM 代理（自签会话证书），**只覆盖这一个 API 主机**；Steam / CDN / PlayFab 等其它主机不经过代理，本表看不到。
> 机读版：`out/gwe/api-endpoints.csv`（本地生成，`out/` 不入库）；生成器 `tools/api_inventory.py`。

## 1. 分组总览

| 组 | 端点数 | 请求数 |
|---|---:|---:|
| 社交 | 3 | 803 |
| 战局 | 10 | 1458 |
| 大厅 | 5 | 874 |
| 消息 | 6 | 582 |
| 配置 | 1 | 116 |
| 账号 | 2 | 139 |
| 命令 | 3 | 205 |
| 任务 | 9 | 383 |
| 养成 | 11 | 771 |
| 商业化 | 1 | 89 |
| 未知 | 1 | 15 |
| 其他 | 1 | 1 |

## 2. 全量清单（按请求数降序）

| 组 | 方法 | 端点 | 次数 | 平均请求体 | 用途 |
|---|---|---|---:|---:|---|
| 社交 | GET | `/api/FriendsV2/Request?offset={n}&limit={n}` | 390 | 0 B | 好友请求/最近/拉黑 |
| 战局 | GET | `/api/Episode/{warId}/status?maxEntries=1` | 379 | 0 B | 赛季/剧集活动状态 |
| 大厅 | PUT | `/api/lobby` | 360 | 1521 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 大厅 | POST | `/api/lobby/{id}/member` | 239 | 4 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 战局 | GET | `/api/Stats/war/{warId}/summary` | 235 | 0 B | 全局战况汇总（前线/星系统计） |
| 大厅 | POST | `/api/lobby/accounts` | 223 | 2647 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 社交 | GET | `/api/FriendsV2/Block?offset={n}&limit={n}` | 210 | 0 B | 好友请求/最近/拉黑 |
| 社交 | GET | `/api/FriendsV2/Recent?offset={n}&limit={n}` | 203 | 0 B | 好友请求/最近/拉黑 |
| 消息 | GET | `/api/NewsFeed/801?maxEntries=16&fromTimeStamp={ts}` | 195 | 0 B | 新闻/公告 |
| 战局 | GET | `/api/WarSeason/{warId}/timeSinceStart` | 128 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/WarSeason/{warId}/Status` | 118 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 配置 | GET | `/api/Configuration/GameClient` | 116 | 0 B | GameClient 客户端配置 |
| 账号 | POST | `/api/Account/Login` | 113 | 437 B | Login / ReportPosition（反作弊上报） |
| 命令 | GET | `/api/v2/Assignment/War/801` | 106 | 0 B | Major Order/每日命令（War/Player） |
| 消息 | POST | `/api/Pes/GetMessages` | 103 | 127 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 战局 | GET | `/api/WarSeason/GalacticWarEffects` | 102 | 0 B | GWE 效果目录（服务器准备的内容清单） |
| 战局 | GET | `/api/WarSeason/current/WarId` | 102 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/WarSeason/{warId}/warinfo` | 99 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/WarSeason/NewsTicker` | 99 | 0 B | 战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker |
| 战局 | GET | `/api/Stats/profile/summary` | 98 | 0 B | 个人战绩汇总 |
| 战局 | GET | `/api/Stats/profile/{warId}/summary` | 98 | 0 B | 个人战绩汇总 |
| 命令 | GET | `/api/v2/Assignment/Player` | 98 | 0 B | Major Order/每日命令（War/Player） |
| 消息 | POST | `/api/Pes/GetConfiguration` | 97 | 63 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 消息 | POST | `/api/Mail/inbox` | 97 | 118 B | 邮件收件箱 |
| 任务 | GET | `/api/Mission/RewardEntries` | 90 | 0 B | 任务结算：RewardEntries / Session |
| 任务 | GET | `/api/Operation` | 89 | 0 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 养成 | GET | `/api/Progression/ItemPackages` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/ProgressionPackages` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/items` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/levelspec` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/Progression/inventory` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 商业化 | PUT | `/api/Monetization/Steam/RedeemStoreContent` | 89 | 0 B | Steam DLC/商城兑换 |
| 养成 | GET | `/api/Progression/Items/Customize/v2` | 89 | 0 B | 物品/背包/等级/成就/自定义 |
| 养成 | GET | `/api/SeasonPass` | 89 | 0 B | 战争债券页面数据 |
| 消息 | POST | `/api/Pes/GetMotd` | 89 | 63 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 任务 | POST | `/api/Operation/Mission/Start` | 71 | 166 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 任务 | POST | `/api/Operation/Mission/SetMaxRewards` | 66 | 73 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 大厅 | GET | `/api/lobby/{id}` | 44 | 0 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 养成 | PUT | `/api/Progression/Items/Customize/v2` | 41 | 99 B | 物品/背包/等级/成就/自定义 |
| 任务 | POST | `/api/Operation/Abandon` | 26 | 27 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 任务 | POST | `/api/Operation/Create` | 26 | 312 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 账号 | POST | `/api/Account/ReportPosition` | 26 | 79 B | Login / ReportPosition（反作弊上报） |
| 未知 | POST | `/api/Proxy/1621247262/577226056` | 15 | 329 B | 内部代理/中继（请求体未抓，响应 0B） |
| 养成 | POST | `/api/Progression/inventory/consume` | 9 | 270 B | 物品/背包/等级/成就/自定义 |
| 养成 | PUT | `/api/Progression/Achievements` | 9 | 141 B | 物品/背包/等级/成就/自定义 |
| 任务 | POST | `/api/Mission/Session` | 9 | 1018 B | 任务结算：RewardEntries / Session |
| 大厅 | DELETE | `/api/lobby/clear` | 8 | 4 B | 组队/当前选中星球（PUT lobby 带 planet 信息） |
| 任务 | POST | `/api/Operation/Mission/ActivityV2` | 5 | 108 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 命令 | POST | `/api/v2/Assignment/Player` | 1 | 41 B | Major Order/每日命令（War/Player） |
| 任务 | POST | `/api/Operation/Mission/end` | 1 | 930 B | 战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2 |
| 消息 | POST | `/api/Pes/GetIngameSurvey` | 1 | 955 B | PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey |
| 其他 | GET | `/` | 1 | 0 B |  |

## 3. 与实验最相关的接口

- **`GET /api/WarSeason/801/Status`**：战况板（planetStatus / planetActiveEffects / campaigns / planetAttacks / planetEvents / jointOperations）——我们唯一会**改写**的响应；
- **`GET /api/WarSeason/GalacticWarEffects`**：效果目录（312 条，含 type32/40/71/94）——只读抓包；
- **`PUT /api/lobby`**：组队 + 当前选中星球（代理从请求体里读 `player planet`，用于粘性注入）；
- **`POST /api/Operation/Create` / `Mission/Start` / `Mission/end`**：任务创建、开始、结算；Create 的请求体里带 `operationSettingsId / type / planetIndex / difficulty / missions[]`，结算请求体带 `planetEventId / healthAtStart / objectives / operationId`——都是**服务端权威**，本地伪造风险高（之前防守伪造实验已经踩过）；
- **`GET /api/Stats/war/801/summary`**：全局战况（前线 63 条攻击边等）；
- **`GET /api/v2/Assignment/War/801`**：Major Order；**`/api/Progression/*`**：解锁/背包（服务端权威）。

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


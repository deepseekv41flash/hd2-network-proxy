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

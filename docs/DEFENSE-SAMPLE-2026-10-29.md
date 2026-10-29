# 真实 DEFENSE 样本（2026-10-29，warId 801）—— 首次拿到

> 来源：本机 MITM 抓包（passthrough + 只读落盘），`D:\mod\out\gwe`，`/api/` 全端点。
> 样本文件：`8945e8dc_api_WarSeason_801_Status.json`（49,779 B，14:20Z）。
> 现场：游戏内星图显示 **DEFENSE / UVARYLIA 5 / INVASION LEVEL 38 / DEFEND 01:22:09:22**（截图 13:56Z），
> 阵营 **AUTOMATON**，词条 **THE INCINERATION CORPS**。

---

## 0. 结论：DEFENSE = 「type 4 战役 + planetEvents + jointOperations」三件套

之前三轮失败的原因不是"服务器不校验"这类猜想，而是**样本形状错了**：我们把
`campaigns[].type` 当成攻守开关（试过 1/2/3/4），把 `planetEvents` 单独伪造。
真实样本一次给全三块，而且 `type = 4` 恰恰就是那次"改了却什么都不显示"的值 ——
**它需要另外两块才能渲染**。

| 块 | 真实值（planet 244 = UVARYLIA 5） |
|---|---|
| `campaigns[]` | `{"id": 51751, "planetIndex": 244, "type": 4, "count": 21, "race": 3}` |
| `planetEvents[]` | `{"id": 5729, "planetIndex": 244, "eventType": 1, "race": 3, "health": 1883848, "maxHealth": 1900000, "startTime": 85336150, "expireTime": 85508950, "campaignId": 51751, "jointOperationIds": [5729], "potentialBuildUp": 0}` |
| `jointOperations[]` | `{"id": 5729, "planetIndex": 244, "hqNodeIndex": 2}` |
| `planetStatus[244]` | `{"index": 244, "owner": 1, "health": 1400000, "regenPerSecond": 0, "players": 7350, …}` |

**UI 标签的对应关系**（与截图逐项对上）：

| 界面文字 | 字段 |
|---|---|
| DEFENSE | `campaigns[].type = 4` **且** `planetEvents` 与 `jointOperations` 同 id 齐备 |
| AUTOMATON | `campaigns[].race = 3`（不是 attacker 阵营，而是**本战役的敌方种族**） |
| INVASION LEVEL | `campaigns[].count`（截图 38 → 抓包时已降到 21：玩家在防守中把它打下来了） |
| DEFEND 01:22:09:22 | `planetEvents.expireTime − Status.time`（抓包读数 165,650 s = **46.01 h**，与截图 46.16 h 吻合） |
| 防守进度 | `planetEvents.health / maxHealth`（99.15%；**不是** `planetStatus.health`，后者满值 1.4 M） |
| 战线位置 | `planetAttacks` 里 `{source: 242, target: 244}` 等（63–64 条恒定，是**adjacency/前线邻接表**，不是"当前被攻击列表"） |

> ⚠ 两个此前记错的点：
> 1. **`planetAttacks` 不是"正在被攻击"**：它全程恒定 63–64 条、跨 3 天抓包不变 ⇒ 邻接表；
> 2. **`campaigns[].race` 不是 owner 的替代**：正常解放战役全是 `race = 1`，
>    而防守/联合作战是 `race = 3`（自动机）/ `4`（光明族）—— 它是"这一仗打谁"。

---

## 1. Status 的真实骨架（18 个顶层键，全部样本一致）

| 键 | 规模 | 说明 |
|---|---|---|
| `warId` / `time` / `impactMultiplier` / `storyBeatId32` / `layoutVersion` | 标量 | `time` 是防守倒计时的基准 |
| `planetStatus[]` | **273** | `index/owner/health/regenPerSecond/players/position` |
| `planetAttacks[]` | **63–64** | `{source,target}` 邻接 |
| `campaigns[]` | **37–39** | `{id,planetIndex,type,count,race}` |
| `planetEvents[]` | **0 或 1** | 只有联合作战/防守时出现（见 §0） |
| `jointOperations[]` | **0 或 1** | 与 `planetEvents` 同 id |
| `communityTargets[]`、`planetActiveEffects[]`（137）、`planetRegions[]`、`globalEvents[]`、`activeElectionPolicyEffects[]`、`spaceStations[]`、`globalResources[]`、`superEarthWarResults[]` | — | 本轮未展开 |

抓包里 `campaigns` 的 `(type, race)` 组合分布（全部 Status 样本）：

| type | race | 出现次数 | 含义 |
|---:|---:|---:|---|
| 0 | 1 | 2042 | 常规解放战役 |
| 4 | 3 | 1 | **本次自动机防守/联合作战（planet 244）** |
| 4 | 4 | 19 | 光明族联合作战（planet 144） |

⇒ 抓包窗口内**没有第二种防守形状**，`type` 只有 0 和 4。

---

## 2. 客户端请求体（同一批抓包里的 `req_*.json`）

`POST /api/Operation/Create` —— 两例，能看出"防守/联合作战"在**请求侧**长什么样：

```json
// 常规（planet 158，type 0，1 个任务）
{"operations":[{ "operationSettingsId":2807074392, "jointOperationId":-1, "type":0,
  "id":1219, "seed":1756397409, "race":3, "warId":801, "placementNodeIndex":0,
  "campaignId":51705, "planetIndex":158, "difficulty":1,
  "missions":[{"type":1,"state":1,"index":0}]}]}
```

```json
// 联合作战/防守（planet 244，type 4，jointOperationId=5729，3 个任务）
{"operations":[{ "operationSettingsId":538077316, "jointOperationId":5729, "type":4,
  "id":1220, "seed":-1308704879, "race":3, "warId":801, "placementNodeIndex":16,
  "campaignId":51751, "planetIndex":244, "difficulty":5,
  "missions":[{"type":3,"state":1,"index":0},{"type":3,"state":1,"index":1},{"type":3,"state":1,"index":2}]}]}
```

要点：**客户端自己就把 `type`、`jointOperationId`、`missions[].type`（1 vs 3）选好了** ——
所以"能不能造防守"在客户端侧就已经是数据选择，而不是需要服务器许可。

`POST /api/Operation/Mission/Start`（167 B）：

```json
{"planetIndex":244,"warId":801,"regionIndex":-1,"operationId":1220,
 "missionIndex":1,"territoryIndex":160,"participants":["<账号 id 已脱敏>"]}
```

---

## 3. 下一步（用这份样本注入）

1. 选一个**自动机**星球的 `planetIndex`（例如想刷防守的目标），复制 §0 三块：
   `campaigns` 加一条 `{type:4, race:3, count:<invasion level>}`、
   `planetEvents` 加一条 `{eventType:1, race:3, health/maxHealth, startTime/expireTime, campaignId, jointOperationIds:[id]}`、
   `jointOperations` 加一条 `{id, planetIndex, hqNodeIndex}` —— **三块 id 必须互相一致**；
2. 代理侧只改 Status 响应（passthrough 之外开 rewrite），其余端点不动；
3. 判读：星球卡是否从 LIBERATION 变 DEFENSE、倒计时是否按 `expireTime` 走、
   进任务后 `Operation/Create` 是否带出 `type:4` 与 `jointOperationId`。

> 与旧结论的关系：`docs/E8-REACHABILITY.md` 与 `EXPERIMENTS-2026-10-27.md` 里
> "type=4 无任何状态显示"、「planetEvents 单独伪造无效」两条都被本样本解释了 ——
> **不是被服务器拒绝，而是三块缺一不可**。

---

## 4. 注入器已就绪（2026-10-29 晚）

做法：不动第三方主流程，只给已有的 `HD2_GWE_EXTRA` 钩子补两处与真实样本的差异，然后用 spec 驱动。

### 4.1 补丁（幂等、留备份）

`tools/defense_inject.py apply --proxy D:/Downloads/variant_mod/tools/war_proxy.py`

| 补的东西 | 为什么 |
|---|---|
| `planetEvents[]` 增补 `potentialBuildUp: 0` | 真实样本有这一格，钩子原来没有 |
| `campaignId` 兜底 = 同星球注入的 campaign id | 写错或不写 ⇒ 事件挂不到战役上，卡片不出 |

其它逻辑一行未改（`HD2_GWE_EXTRA` 原有的 campaigns / attacks / events / jointOperations / globalEvents / owner 全部沿用）。

### 4.2 本次注入的 spec（真实形状照抄）

```json
{"campaigns":[{"planet":156,"id":51990,"type":4,"count":38,"race":3}],
 "attacks":[{"source":157,"target":156}],
 "events":[{"planet":156,"id":9101,"eventType":1,"race":3,
            "health":990000,"maxHealth":1000000,
            "startOffset":-3600,"endOffset":169200,
            "campaignId":51990,"hqNodeIndex":2}],
 "owner":{"156":1}}
```

| 项 | 取值 | 依据 |
|---|---|---|
| 目标星球 | **156 CASTOR**（我方 owner=1、原本无战役的安静星球） | 真实防守是「我方星球被敌星打进」 |
| 进攻方 | **157 DURGEN**（自动机 owner=3，与 156 相邻，距离 0.069） | `planetAttacks` 里唯一的 3→1 边就是真实防守 |
| `count` | 38 | = 截图里的 INVASION LEVEL |
| `race` | 3 | 自动机 |
| 事件 | `eventType 1`、47 h、health 99% | 真实样本：48 h、99.15% |
| id | campaign 51990 / event 9101 / jointOperation 9101 | 三者必须互相一致 |

### 4.3 离线自检（已通过）

- `defense_inject.py selftest`：用抓包样本走同构变换 → campaigns 38→39、attacks 64→65、events 1→2、
  jointOperations 1→2，7 条一致性门禁全 PASS；
- **真实代码路径**：`import` 打过补丁的 `war_proxy.py`，直接调用 `rewrite_status(真实样本, {})` →
  日志出现四行 `REWRITE-EXTRA 追加战役/攻击边/星球事件/联合作战`，返回改动数 4，
  `campaignId` 与 `jointOperations.id` 自洽、`potentialBuildUp` 存在。

### 4.4 运行态

代理以 **rewrite 模式**（`passthrough=False`）运行，环境变量：

```
HD2_GWE_EXTRA = <上面那行 spec>
HD2_GWE_DUMP  = D:\mod\out\gwe      （继续抓包）
HD2_GWE_PATHS = /api/
```

判读：进游戏 → 星图 → **CASTOR(156)** 应出现 DEFENSE 卡（AUTOMATON / INVASION LEVEL 38 / 倒计时 47 h）；
`logs/proxy.log` 里应出现对应的四行 `REWRITE-EXTRA`。

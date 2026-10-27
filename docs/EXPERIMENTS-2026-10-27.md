# 实验总记录：改写战况接口能做什么（2026-10-27，warId 801）

> 全部在本机实机完成；每条都注明「判据 → 现象 → 结论 → 等级」。
> 等级：✓✓ 实机验证 / ✓ 离线+数据验证 / ⚠ 未证 / ✗ 否证。

## 0. 总表

| # | 实验 | 变量 | 结果 | 等级 |
|---|---|---|---|---|
| E1 | 抓包链路 | 代理 + 白名单落盘 | GWE / Status / Operation / Mission 全部落盘 | ✓✓ |
| E2 | 首例可见证据 | 182 注入 1373 | 作战卡 `AVERT VOID` + 局内 Exostorm 天气 + `TAKE DOWN OVERSHIP` | ✓✓ |
| E3 | 作战卡文本来源 | 本地 `.strings` 反查 | 卡片四段文字全是本地 locid | ✓ |
| E4 | 同星 A/B/A | 93：无 → 1373 | `operationSettingsId` 2796992372 → **3194790369** | ✓✓ |
| E5 | 作战卡由谁生成 | verbose 全量路径日志 | 打开部署界面**零请求**；Create 是客户端提案，服务器只发号 | ✓✓ |
| E6 | 跨阵营 | 1386（terminid）注入光照星球 | 星图卡 + `COMBATANT FORCES` 出现，作战卡不变 | ✓✓ |
| E7 | presence 种类字段 | `+0x14` 对照实机 | 0 地图标记 / 1 事件作战 / 3 战术 / 4 敌情，与 E2/E6 完全吻合 | ✓✓ |
| E8 | 可达性 | 139：campaign / owner | 可选、可进、可开任务（服务器侧见 §E8 更正） | ✓✓ |
| E9 | 敌人阵营 | 139：owner 1 ↔ 4 | 虫子 ↔ 光照族，跟着 owner 走 | ✓✓ |
| E10 | 序号↔名字 | warinfo `settingsHash` | 273/273 全部对上 | ✓ |

---

## E2：一个 effect id = 一整个事件包

**设计**：182（HEZE BAY，光照族、0 玩家、零效果）注入 `1373 = illuminate_ritual_storm_lvl1`。

**证据**：

```
20:45:51 REWRITE +1 entries (planet 182 -> [1373])
20:46:31 player planet -> 182 (lobby)
```

**现象**：部署界面出现 `OPERATION / AVERT VOID`（`Charge into the Exostorm and save this planet from falling to the Void.`），
进局后天空/能见度/天气呈 Exostorm 特征，任务是 `TAKE DOWN OVERSHIP`。

**链路**（每段都有数据支撑）：

```
Status.planetActiveEffects += 1373
  → 客户端本地解析（零请求，见 E5）
  → GWE type71: values[0] == murmur32('illuminate_ritual_storm_lvl1')
  → presence 行 +0x14=1（事件）→ operationSettingsId
  → POST /api/Operation/Create（客户端提案）→ 服务器发号
  → 局内天气 = weather_settings 里 8 行 illuminate_ritual_storm_* 覆盖
```

## E4：同星 A/B/A —— 变量只有注入

同一颗星球 93（NEW STOCKHOLM），只改 Status：

| 时间 | 注入 | `operationSettingsId` | 卡片 |
|---|---|---|---|
| 21:25:42 | 无 | 2796992372 | 普通作战 |
| 21:33:17 | `REWRITE planet 93 -> [1373]` | **3194790369** | **AVERT VOID** |

`campaignId` 两次都是 51686，排除“换了颗星球”的干扰。

> 后续在 139（无效果）上又拿到 2796992372 —— 与 93 无效果时同值，
> 说明 `operationSettingsId` 是**效果集的函数**，不是星球身份的函数。

## E5：作战卡是客户端本地算的

打开部署界面期间（21:24:34→21:24:40）全部请求：

```
POST /api/Operation/Abandon        27B  {"operationIds":[1203]}
POST /api/Operation/Create        301B  operationSettingsId=3194790369 ...
POST /api/Account/ReportPosition   80B
PUT  /api/lobby
```

**没有任何“请给我这颗星球的可选作战”的请求。** `/api/Operation` 只在登录时拉一次，
返回的是**玩家已有的 operation**。

也就是说：客户端拿 Status 自己算，服务器只负责发号；客户端还会**复用缓存**
（先 `Abandon {1203}`，再用同一个 settings id 重建 1206）。

## E6/E7：跨阵营与 presence 种类

**E6**：把终结族 presence `bugs_gloom`（effect 1386）注入光照星球 93：

```
21:39:18 REWRITE +1 entries (planet 93 -> [1386])
```

星图卡出现 `SPORE BURST STRAIN`（带完整描述），部署界面多出
`COMBATANT FORCES PRESENT: SPORE BURST STRAIN`，**但作战卡不变**。

**E7**：把 presence 表的 `+0x14` 摊开，正好解释了这个差异：

| `+0x14` | 含义 | 条数 | 客户端表现 |
|---|---|---|---|
| 0 | 地图标记 | 19 | 星图图标 |
| **1** | **事件作战** | **7** | **作战卡**（E2 的 1373 属这类） |
| 3 | 战术行动 | 4 | 未测 |
| **4** | **敌情 / 设施** | **107** | 星图卡 + `COMBATANT FORCES`（E6 的 1386 属这类） |

⇒ **引擎不校验阵营**（终结族 presence 挂在光照星球上照常渲染）；
`variant_mod` 里那道 `resolve_plan()` 阵营过滤是 mod 作者自己的保险。

## E8：可达性 —— 能进原本打不了的星球

**设计**：139（ALAMAK VII，光照族、0 玩家、无战役、星图上点不进去）。

三轮（原因是第一轮撞上了我们自己的 bug，见「踩坑」）：

1. 只伪造 campaign → 无效（且该轮结论作废）；
2. 只改 owner → 卡片 `ILLUMINATE` 标题消失；
3. owner + campaign → 卡片变成 `LIBERATION / ALAMAK VII / 99.99783% LIBERATED`，
   **可选、可进、可开任务**。

**服务器侧全部 200**（⚠ 见本节末尾更正，不能据此断言"服务器缺少校验"）：

```
22:18:49 POST /api/Operation/Create
  campaignId: 51999   ← 我们自己编的假战役 id
  planetIndex: 139
  → {"operations":[{"id":1209,...}]}

22:19:19 POST /api/Operation/Mission/Start
  {"planetIndex":139,"operationId":1209,"territoryIndex":490,...}
  → {"missionId":"c85becc2-..."}
```

**第四轮（E9）**：只留 campaign、owner 不动（仍为 4）→ 照样能进。
⇒ **可点性只由 `campaigns` 决定，owner 不是必要条件**。

> **⚠ 更正（用户指出，2026-10-27 夜）**：原文把「服务器接受在无战役星球上创建作战」写成
> "服务器不校验战役存在性"，属过度解读，撤回。游戏本来就允许**未完成作战在战役结束后继续存在**，
> 所以「无活动战役的星球上存在一个 operation」对服务器是**合法状态**，不是异常输入。
> 我们只是把玩家放进了这条既有规则里：
> 用客户端状态欺骗进入「继续未完成作战」状态，而不是绕过了一道校验。
> 「`campaignId=51999` 被接受」仍只说明它不构成拒绝条件；该字段是否参与奖励/归属统计未知。

## E9：owner 决定敌人阵营

| 星球 | owner | Create 体里的 `race` | 实际敌人（用户实测） |
|---|---|---|---|
| 93 / 182 | 4 illuminate（未改） | 4 | — |
| 139 | **1 human**（改） | **2** | **Terminids** |
| 139 | 4 illuminate（改回） | **4** | **Illuminate** |

⇒ `planetStatus.owner` 同时决定：星球卡阵营标题、任务里刷哪一族敌人。
owner 改成“自己人”时客户端取不到敌人，回退成默认值 2（终结族）。

## E10：游戏索引 ↔ 星球名字

服务器 `warinfo` 有 273 条 `planetInfos`，每条带 `settingsHash`；
`planet_data` 文件尾部 **3504 B = 438 行 × 8 B**，每条第 4 字节起正是该行的 `settingsHash`。

```
warinfo.settingsHash → 尾部第 N 条 → planet_data 第 N 行 → +0x08 locid → 名字
```

273/273 全部对上、全部拿到名字。四个独立锚点：`93=NEW STOCKHOLM`、`182=HEZE BAY`、
`268=LUXURIANT`、`139=ALAMAK VII`。

> 副作用：纠正了旧结论「`planet_data` 行号就是游戏索引」——行号是另一套编号，偏移不是常数。

---

## 踩坑（每条都花了一次实机）

### 1. helper 定义在 `if __name__ == "__main__":` 之后 → `NameError`

代理起来后每次 Status 请求都炸，客户端报 `CURLE_RECV_ERROR`。
→ 补自检：断言 helper 的偏移 < 守卫的偏移，并加一条“反序必须被切出来”的阴性对照。

### 2. 改动算出来了，响应体没换（最坑）

`rewrite_status()` 返回 `(new_body, count)`，调用方 `if rewrite_added:` 才替换 body。
我们的 `extra`（campaign / owner）没计入 count ⇒ **doc 改好了、返回的还是原始 body**，
日志还打一句 `Status 200 但还没有可注入的星球`。

> **判据纠正**：`REWRITE-EXTRA ...` 只说明算出来了，`REWRITE +N entries` 才说明真的写回去了。

### 3. 命名陷阱：`bugs_gloom` ≠ `gloom`

`bugs_gloom`（`+0x14=4`，`SPORE BURST STRAIN`，有 effect 1386）与
`gloom`（`+0x14=1`，`GLOOM RESEARCH EXPEDITION`，无 effect）是两行数据；
`gloom` 还与 `gloom_hiveworld` 共用同一个显示名。按名字猜语义会连错两次。

### 4. 行星索引不是行号

见 E10。任何“按编号取名字”的表在修正前都是错的。

---

## 能力边界总结

**已验证可做**：

* 任意 GWE 目录内的 effect → 注入任意星球（跨阵营亦可），只加不删；
* 一次批量注入多颗星球；
* 让任意星球变成可打的前线（伪造 campaign），并**在服务器侧真实创建作战、开始任务**；
* 选定任务的敌人阵营（改 owner）；
* 改变局内天气（effect → presence → weather 覆盖）。

**做不到 / 未证**：

* 目录外的 effect id（客户端解析不出；不过服务器自己也在发解析不出的效果，客户端不崩）；
* 直接指定 `operationSettingsId`（只能通过 effect 集间接影响）；
* 服务器是否校验 settings id 与星球的匹配（跨星球复用已被接受，非法值未测）；
* 终结族事件（`hive_world` / `gloom`）—— 当前 GWE 无对应 effect，注入不了。

---

## E12：伪造「被敌人进攻」（限时防守事件）

**目标**：刷出只在防守战役出现的任务池。

### 12.1 `campaigns[].type` 是战役形态枚举（✓✓ 四个值全部实测）

同一条伪造战役，只改 `type`，卡片标题依次变成：

| `type` | 卡片标题 | 语义（来自卡片文案） |
|---:|---|---|
| 0 | `LIBERATION` | 常规解放 |
| 1 | `RECON CAMPAIGN` | “Super Earth will not liberate Recon campaign planets, but they will remain available as long as the sector is active.” |
| 2 | `HIGH-PRIORITY CAMPAIGN` | “contain unique missions related to the current Major Order” |
| 3 | `BATTLE FOR SUPER EARTH` | 光照族入侵 Mega City 事件形态 |
| ≥4 | 无状态（只剩星球名与进度条） | 枚举终点 |

> 附带结论：客户端**完全按枚举渲染**，不看星球是否“配得上”这个形态——
> `BATTLE FOR SUPER EARTH` 被挂在一颗丛林星球（ALAIRT III）上照样正常显示。

### 12.2 防守不在 `campaigns.type` 里

- `type=4` 已无状态 ⇒ 防御不是第四个之后的取值；
- `owner=1` + `campaign{race=2}` ⇒ 仍是 `LIBERATION`，只有阵营图标变成 `TERMINID`
  ⇒ **星球卡阵营取自 `campaigns[].race`，不是 `planetStatus.owner`**；
- `owner=1` + `campaign{race=4}` + 反向攻击边 `139 → 138` ⇒ 仍是 `LIBERATION`。
  （线上 63 条攻击边全是「人类星球 → 敌星」，反向边并没有触发防守。）

### 12.3 防守在 `planetEvents[]`（⚠ 未成功，客户端拒绝）

社区 API 模型（Helldivers2API-NET 的 `PlanetEvent`）标注：

```
eventType      1 = defended, 2 = attack
startTime / expireTime    与 WarStatus.time 同一时钟
health / maxHealth        覆盖 PlanetStatus
campaignId                关联战役
```

按此伪造一条 `eventType=1` 的事件（开启 30 分钟、1.5 小时后结束）后：

* 代理侧一切正常：`REWRITE +3 entries`，`RESP 200`，客户端后续还成功发了 friends / lobby 请求；
* 客户端随后弹出 **`ERROR / Something unexpected went wrong while trying to communicate with our server`**，
  并反复重拉 Status。

⇒ **`planetEvents` 是客户端解析很严格的字段**：不像无法解析的 effect 那样被静默忽略，条目形状不对就直接报通讯错误。

**单变量对照已闭环**：

| 配置 | 结果 |
|---|---|
| `owner + campaign`（23:33，不含 planetEvents） | 卡片正常、可进入 |
| `owner + campaign` **+ `planetEvents`**（23:52） | 弹 "Something unexpected went wrong while trying to communicate with our server"，此后客户端零请求 |
| 纯转发（撤销全部注入） | 正常进入 |

⇒ 嫌疑锁定在 `planetEvents` 条目本身的形状（键名/单位/必填字段），与网络、证书、端口无关。
客户端在**本地反序列化**阶段就判定了这份 Status 不可用。

**下一步需要一份真实样本**：等线上真的出现防守战役时（`planetEvents` 非空）抓一次 Status，
按真实键名/单位复刻，而不是靠猜。

### 12.4 现场处置

实验后已切回 **Passthrough（纯转发）**，注入全部撤销，游戏恢复正常。

---

## 13. 防守事件：拿到真实样本后仍然失败（2026-10-28 00:20）

### 13.1 真实样本来源

GitHub 代码搜索命中一份真实历史的 `WarStatus` 抓包：

* 仓库：`EdouardCourty/helldivers2-api`，路径 `tests/fixtures/WarStatusResponse.json`
* 已脱敏存到本仓库：`docs/fixtures/warstatus-sample-planet-events.json`（1.6 KB，仅战况字段）

其中的 `planetEvents`（**真实防守事件，两条**）：

```json
{"id":4327,"planetIndex":197,"eventType":1,"race":3,"health":249722,"maxHealth":400000,
 "startTime":3736520,"expireTime":3822920,"campaignId":50031,"jointOperationIds":[4327]}
{"id":4330,"planetIndex":212,"eventType":1,"race":2,"health":470354,"maxHealth":800000,
 "startTime":3768960,"expireTime":3855360,"campaignId":50034,"jointOperationIds":[4330]}
```

配套的 `jointOperations`（**之前完全不知道要写**）：

```json
{"id":4327,"planetIndex":197,"hqNodeIndex":1}
{"id":4330,"planetIndex":212,"hqNodeIndex":2}
```

由此确认的事实：

| 项 | 值 |
|---|---|
| `eventType` | `1` = 防守（与社区模型一致） |
| 时长 | **恰好 86400 秒 = 24 小时**（两条一致） |
| `startTime`/`expireTime` | **绝对 war time**，与 `Status.time` 同一时钟 |
| `jointOperationIds` | **非空**，内容就是事件自己的 id |
| 键名 | `race` / `planetIndex` / `campaignId` 都猜对了 |

### 13.2 补齐三件套后依然失败

按真实形状注入（`campaign` + `planetEvents{jointOperationIds:[9001]}` + `jointOperations{id:9001}` + `owner=1`）：

```
00:16:58  REWRITE +4 entries   →  RESP 200
00:17:03  客户端继续发 friends / lobby 请求（说明链路正常）
00:18:49  客户端重新拉 Status（重试）
00:18:52  再次注入 → 随后弹 ERROR "trying to communicate with our server"
```

⇒ **仍缺某个约束**。与真实样本的已知差异只剩：

| 候选 | 我们的值 | 真实值 | 优先级 |
|---|---|---|---|
| `health` 与 `maxHealth` 关系 | 两者相等（1000000/1000000） | **health < maxHealth**（249722/400000） | ★★★ 最可能（进度计算可能除零/越界） |
| `campaigns[].race` 是否需要等于事件 race | campaign race=2、event race=2 ✓ | 样本里 campaign **没有 race 字段**（裁剪或旧版） | ★★ |
| `planetEvents` 是否要求对应星球在 `planetStatus` 里有非默认值 | owner=1、health/maxHealth 未改 | 未知（样本被裁剪） | ★ |
| `jointOperations[].hqNodeIndex` 合法范围 | 1 | 1 / 2 | ★ |

**下次开工第一件事**：把 `health` 设成 `maxHealth` 的一半（例如 1100000/2200000，跟真实比例接近），其余不变——一个字段、一次重启就能判。

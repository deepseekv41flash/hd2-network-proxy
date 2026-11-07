# E8：改写 Status 能否进入「原本不能访问」的星球

> 2026-10-27 夜，warId 801，build 26088801。目标星球 **139 = ALAMAK VII**（光照族占领、0 玩家、无战役、星图上点不进去）。

## 0. 结论

**客户端侧：能。** 客户端把「哪颗星球可以打」完全交给了 Status —— 伪造一条 `campaigns` 条目就能让一颗原本点不进去的星球变成可部署的前线（✓✓ 实机）。

**服务器侧：接受，但不宜解读为「缺少校验」。** 见 §0.1 的更正。

| 层 | 谁在管 | 结果 |
|---|---|---|
| 客户端可点性 / 可部署性 | Status 的 `campaigns`（`owner` 不是必要条件） | ✓✓ 被改写绕过 |
| 服务器 | `/api/Operation/Create`、`/api/Operation/Mission/Start` | 全部 200，照发 operation id 与 missionId |

### 0.1 更正（2026-10-27 夜间，用户指出）

我原先把「服务器接受在无战役星球上创建作战」写成 **"服务器不校验战役存在性"** —— 这是**过度解读**，撤回。

游戏本来就允许**未完成的作战在战役结束后继续存在、继续打**。也就是说，
「在没有活动战役的星球上存在一个 operation」对服务器而言是一条**合法状态**，不是异常输入。
我们的 `Create` 正好落在这条既有规则里，因此：

| 说法 | 状态 |
|---|---|
| 客户端可达性由 Status 决定 | ✓✓ 成立（E8/E9 实机） |
| 服务器照发了 operation id / missionId | ✓✓ 事实 |
| **"服务器缺少战役校验"** | **✗ 撤回**：与「作战可以脱离战役继续」的设计一致，不能作为缺陷证据 |
| 伪造的 `campaignId: 51999` 被接受 | ⚠ **待判定**：只能说明它不构成拒绝条件；该字段是否被用于奖励/归属统计，未知 |

**所以这条链的准确定位是**：
用客户端侧的状态欺骗，把玩家放进一个「服务器本就允许的『继续未完成作战』状态」——
而不是绕过了一道服务器校验。

## 1. 三轮实验

### 1.1 第一轮：只伪造 campaign（21:58–22:00）→ 无效

```json
{"campaigns": [{"planet": 139, "id": 51999, "type": 0, "count": 1, "race": 1}]}
```

日志显示 `REWRITE-EXTRA 追加战役` 打了两次，星图无变化。

> ⚠ **这一轮的结论无效**：当时的失败是**我们自己的接线 bug**（见 §3），伪造的战役根本没进响应体。

### 1.2 第二轮：只改 owner（22:07、22:12）→ 成功

```json
{"owner": {"139": 1}}
```

22:07 那次同样被 bug 吞掉；修好后 22:12:29 出现 `REWRITE +1 entries (extra: campaigns/owner)`，
用户截图确认星球卡上的 `ILLUMINATE` 标题消失。

### 1.3 第三轮：owner + campaign（22:16 起）→ 完全打通

```json
{"campaigns": [{"planet": 139, "id": 51999, "type": 0, "count": 1, "race": 1}],
 "owner": {"139": 1}}
```

客户端表现（用户截图）：

```
LIBERATION / ALAMAK VII
This planet is considered enemy territory. The Hell divers must reclaim it from its oppressive occupants.
99.99783% LIBERATED          RESISTANCE LOW (0.00%)
[SELECT CAMPAIGN]            ← 可点、可进
```

## 2. 服务器侧记录（全部 200）

```
22:18:49  POST /api/Operation/Create
  {"operations":[{"operationSettingsId":2350081063,"id":1209,"seed":1762146350,
                  "race":2,"campaignId":51999,      ← 我们自己编的假战役 id
                  "planetIndex":139,"placementNodeIndex":30,
                  "missions":[{"type":1,"state":1,"index":0}]}]}
  → {"operations":[{"id":1209,"rewards":[],"backupRewards":[]}]}

22:19:19  POST /api/Operation/Mission/Start
  {"planetIndex":139,"warId":801,"regionIndex":-1,"operationId":1209,
   "missionIndex":0,"territoryIndex":490,"participants":["<account-id>"]}
  → {"missionId":"c85becc2-d424-4326-ba25-0f930c0b3f0f"}

22:19:40  POST /api/Operation/Mission/SetMaxRewards → 200
```

服务器既没拒绝不存在的 `campaignId`，也没拒绝这颗星球上的 `Mission/Start`，还正常发了一个 `missionId`。

## 3. 踩到的坑：改动算出来了，body 没换

`rewrite_status()` 返回 `(new_body, count)`，调用方是：

```python
new_body, rewrite_added = rewrite_status(plain, plan)
if rewrite_added:              # ← 0 就发原始 body
    out_body = new_body
```

我们的 `extra`（campaigns / owner）改动一开始没计入 `count`，于是**函数改好了 doc、返回的却还是原始 body**，
日志还会打一句 `Status 200 但还没有可注入的星球` —— 极具误导性。

修法：`return json.dumps(doc).encode(), added + extra`，并在只有 extra 时把 summary 写成 `extra: campaigns/owner`。

> 教训：**判"注入有没有生效"要看分支日志，不要看我们自己的计算日志。**
> `REWRITE-EXTRA ...` 只说明算出来了，`REWRITE +N entries` 才说明真的写回去了。

## 4. 遗留观察

* 作战卡上的解放度是 **99.99783%**（不是 100%）：`owner=1` + 满血 → 客户端按 health/maxHealth 算出来接近满，但不是整。
* `Create` 请求体里 `race` = **2（terminid）**，而这颗星球是 `primordial` 生态、真实归属是光照族。
  → 作战的「敌人阵营」可能来自**本地星球数据/区域设置**，而不是服务器的 owner。待验证：进局看敌人是不是虫子。
* `operationSettingsId` = 2350081063（该星球无任何 effect 时的取值），与 182/93 注入风暴后的 3194790369 不同，
  再次支持「settings id 是客户端按星球状态算出来的」。

## 5. 第四轮（E9）：只留 campaign，owner 改回 4

```json
{"campaigns": [{"planet": 139, "id": 51999, "type": 0, "count": 1, "race": 1}]}
```

`22:27:45 REWRITE +1 entries (extra: campaigns/owner)` → `22:28:41 player planet -> 139 (mission)`

* **星球照样可选、可进、可开任务** ⇒ **`owner` 不是可点性的必要条件，campaign 单独就够。**
* `Create` 请求体：`"race": 4`，用户确认局内敌人 = **Illuminate**。
* 对照第三轮（`owner=1` 时 `race: 2`、敌人 Terminids）：

| 星球 | owner | Create 里的 race | 实际敌人 |
|---|---|---|---|
| 93 / 182（未改） | 4 illuminate | 4 | — |
| 139（改 1） | 1 human | **2** | **Terminids** |
| 139（改回 4） | 4 illuminate | **4** | **Illuminate** |

⇒ **`planetStatus.owner` 同时决定：星球卡阵营标题、以及任务里刷哪一族敌人。**
把 owner 改成 1（自己人）时客户端取不到敌人，回退成默认值 2（终结族）。

### 5.1 顺带纠正一条：`operationSettingsId` 是「效果集」的函数

| 星球 | 效果集 | operationSettingsId |
|---|---|---|
| 93（注入前）/ **139（无效果）** | `{}` | **2796992372** |
| 182 / 93（注入 1373 后） | `{1373}` | **3194790369** |

同一个 `{}` 在不同星球上得到同一个值，`{1373}` 在不同星球上也得到同一个值
⇒ 它不是按星球算的，而是**按该星球当前生效的 effect 集合**算的。

## 6. 能力小结（这一条链上已经全部实机验证）

| 改写字段 | 客户端表现 | 等级 |
|---|---|---|
| `planetActiveEffects` | 星图效果芯片 / 作战卡 / `COMBATANT FORCES` / 局内天气 | ✓✓ |
| `campaigns` | 任意星球变「前线」：可选、可进、可开任务 | ✓✓ |
| `planetStatus.owner` | 星球卡阵营标题 + **任务敌人阵营** | ✓✓ |
| 伪造 `campaignId` 发给服务器 | 服务器照发 operation id 与 missionId（⚠ 不构成"缺少校验"证据，见 §0.1） | ✓✓ |

## 7. 复原

```powershell
D:\Downloads\variant_mod\stop.ps1          # 停代理，恢复纯转发
# 配置备份：D:\mod\work\variant-net\rollback\config.json.before-campaign
```

## 8. 延伸到「休眠星」：不在 `planetStatus` 里的 165 颗（2026-11-07 追加，⚠ 未验证）

E8 的实验对象 139 属于「**在 Status 里、但没有战役**」这一类。本季还多一层：
本地 `planet_data` 有 438 颗，而最新 `Status` 只返回 **273** 条 `planetStatus`（`index` 0–273，
缺 263）⇒ **165 颗根本没有节点**（`index` 263、274–437）。对它们，可达性要过两道：

| 层 | 数据在哪 | 伪造内容 |
|---|---|---|
| 星图节点存在性 + 坐标 | `planetStatus[i]`：`{index, owner, health, regenPerSecond, players, position{x,y}}` | 先造一条 `planetStatus`（`position` 可从邻近星抄）|
| 可部署性 | `campaigns[]`：`{id, planetIndex, type, count, race}`（本季 43 条，全在 Status 内）| 再追加一条 `campaigns`（E8 已验证这一层）|

补充口径（同一次 Status 抓包实测）：

- 本季 `planetStatus` 273 / `campaigns` 覆盖 43 颗 / `planetAttacks` 45 条（`{source, target}`）/ `planetEvents` 1 条；
- 只伪造 `campaigns` 而不造 `planetStatus` ⇒ 客户端连节点都没有（星图按 Status 渲染，坐标也来自 Status）；
- 只造 `planetStatus` 不造 `campaigns` ⇒ 节点会出现但大概率点不进去（E8 的对照组正是"无战役"）；
- **服务器侧未测**：`Operation/Create` 用的 `planetIndex` 若落在本季未启用的号段（≥274），服务器是否接受未知。
  E8 的 200 是"战役结束后未完成作战可继续"的合法路径（§0.1），不能直接外推到号段外的星球；
- **presence 缺失风险**：敌人组成（含变种）由服务端下发的 presence 决定，本地表没有"某星有哪些 presence"。
  进入一颗本季未启用的星，可能出现**没有敌军 presence → 空图 / 只有地形**；
- 客户端只在登录时拉 `Status`（改完必须完全退出游戏重登）。

**最小实验建议**：拿本地有定义、本季却没节点的 **263** 或 **300**（`index` 274–437 之一）做一发：
先只加 `planetStatus` 看节点是否出现 → 再加 `campaigns` 看能否部署 → 最后看 `Operation/Create` 与进局敌军。

## 9. 2026-11-07 落地：两层伪造已实现并起代理（目标 planet 300）

- **代理改动**：`tools/war_proxy.py` 的 `_gwe_apply_extra` 新增 `planet_nodes`（标记 `DSH-PLANET-NODE-V1`）——
  按 `{index, owner, health, regenPerSecond, players, position{x,y}}` 往 `planetStatus` 追加节点（已存在则跳过）。
  提交 `876d3e4`。
- **启动器**：`D:\Downloads\variant_mod\run-planetnode.ps1`（设 `HD2_GWE_EXTRA` 后调 `run.ps1`；
  规格同时落 `runtime\planet_node.json`）。
- **本次注入**：planet **300**（本地 `planet_data` 有、本季 Status 无，PlanetType 12 = magma），
  `owner=1`、`position=(0.30, -0.55)`、`campaigns[{id:51999, planetIndex:300, type:0, count:1, race:1}]`。
- **离线单测**：`_gwe_apply_extra` 返回 `changed=2`，新节点/新战役按预期追加，已有节点未被改动。
- **链路实测**（经代理 `curl --cacert certs\anchor.pem --resolve ...:100.67.169.17`）：
  `HTTP 200`（需带 `Accept-Language`，否则上游 400 `Accept-Language HTTP header missing`）；
  `planetStatus` **273 → 274**、`campaigns` **43 → 44**，目标条目逐字段正确。
- **待验（需重登游戏）**：① 星图是否出现新节点 ② 能否点选/部署 ③ `Operation/Create` 是否 200
  ④ 进局有没有敌军 presence（休眠星可能没有刷怪数据）。
- **回滚**：`stop.ps1`；`HD2_GWE_EXTRA` 只存在于启动它的会话，`config.json` 未改（备份
  `config.json.bak-planetnode-20261107-115317`）。

## 10. 生态/地形的真正开关：warinfo `settingsHash`（2026-11-07）

**否证**：改本地 `planet_data`（`PlanetType` + `Inherits` setup 串 + `RegionLowland.Name`）**视觉上没有任何变化**（TRANDOR 实测两轮）。
原因：客户端还有 `GET /api/WarSeason/801/warinfo`，`planetInfos[].settingsHash` 才是每颗星的关卡生成"设置"；
本地 `planet_data` 的 setup 串只是描述性字段。

**桥（已自证）**：`planet_data` 尾部 `438 × 8 B` 每项 **高 4 字节 = 该行 settingsHash**。
`warinfo.index 0 → 897386910 = 行 0`、`index 100 → 3515299681 = 行 103`（TRANDOR）——两条都对上，
**行号 ≠ 游戏索引**在这里第二次被证实。

**实现**：代理新增 `WARINFO_MARK` + `_warinfo_apply_extra`，由 `HD2_GWE_EXTRA.settings_hash = {"<index>": <hash>}`
改写 warinfo 响应。实测（经代理拉 warinfo）：`index 100: 3515299681 → 2807946366`（= 表行 274，真实
`oasis` 星的 settingsHash），邻居 99/101 未动，日志 `REWRITE-WARINFO ...`。

⇒ 换生态的正确配方从「改本地表」变成「**改 warinfo 的 settingsHash**」。待验：进 TRANDOR 是否变成绿洲；
若仍不变，下一层是 warinfo 的 `planetRegions`（211 条）与 `planetBiomeId32`。

## 11. ✓✓ 实机：settingsHash 就是「行星内容身份」（2026-11-07 12:3x）

把 TRANDOR（游戏索引 100）的 `settingsHash` 改成表行 274 的值 `2807946366` 后，用户实机回报：

| 观察 | 说明 |
|---|---|
| 地形变成**绿洲** | `settingsHash` 决定关卡生成内容 ✓（本地 `planet_data` 改三件套两轮都没反应，已否证）|
| 星球**名字变成 `FRONTERIA`** | 客户端把 settingsHash 解析到**本地 `planet_data` 行 274**，名字 locid、生态、天气、修饰符**整套**跟着换 ⇒ settingsHash = **行星内容身份**，不只是地形 |
| 出现 **INTENSE HEAT** 效果 | 同一套内容里的环境/天气条件也一并带过来了 |

⇒ 换生态的正确配方（纯网络层、一行配置）：

```
HD2_GWE_EXTRA = {"settings_hash": {"<游戏索引>": <目标行星行的 settingsHash>}}
# settingsHash = planet_data 尾部 438×8 每项高 4 字节；行号 ≠ 游戏索引，桥就是它
```

**副作用与对策**：名字会变成被借用内容的行星名（本次 FRONTERIA）。若想保名，改**本地**被借用行
（274）的 `+0x008` name locid 为目标星的名字 locid（本地表编辑），或接受"换了一颗星"。

**待验**：① 进任务看局内地貌/天气是否同步；② 换 `deciduous`/`coniferous` 行验证通用性；
③ 批量把多颗战役星映射到不同生态（一季换装）。

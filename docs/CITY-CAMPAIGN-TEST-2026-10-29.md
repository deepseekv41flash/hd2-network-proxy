# 城市战役可玩化：按社区文档实测（2026-10-29 起）

> 社区文档原文：`D:/Downloads/城市战役可玩化技术说明.md`（warId 801 / layout 717）。
> 核心主张：**目标星球在 `WarInfo.planetRegions` 里有原生分区定义，但 `Status.planetRegions` 里没有条目**
> ⇒ 星球能点开却没有可选作战；按原生定义补齐**缺失**的分区状态后，客户端才生成作战。

---

## 1. 先用我们自己的抓包核对文档的事实主张（全部成立）

| 主张 | 我们的抓包读数 | 判定 |
|---|---|---|
| `WarInfo.planetRegions` 是静态定义（planetIndex/regionIndex/settingsHash/maxHealth/regionSize/flags/damageMultiplier） | 211 条 / **84 颗星球**；星球 0 = 7 条、260 = 8 条 | ✓ |
| `Status.planetRegions` 是状态（owner/health/regerPerSecond/availabilityFactor/isAvailable/players） | 35 条 / 15 颗星球；**0 与 260 均无条目** | ✓ |
| 两个同名但结构不同，不能整行复制 | 字段集合确实不同 | ✓ |
| 字段拼写是 `regerPerSecond`（拼写错误照抄） | 真实响应里就是 `regerPerSecond` | ✓ |
| `warId` / `layoutVersion` 需一致 | 两份样本都是 801 / 717 | ✓ |

## 2. 我们的实现（最小、只补缺失）

给第三方代理的 `HD2_GWE_EXTRA` 钩子加一个 `regions` 分支（`tools/city_campaign.py patch`，幂等、留 `.bak`、语法门禁）：

```python
for rg in cfg["regions"]:                       # 来自 WarInfo 的 (planet, regionIndex, maxHealth)
    if (planet, regionIndex) in 已有: continue  # 只补缺失，已有的完整保留
    append({planetIndex, regionIndex, owner, health: maxHealth // 2,
            players: 0, regerPerSecond: 0, isAvailable: true, availabilityFactor: 1})
```

与文档 §3.2/§3.3 的初始化规则逐条一致。

### 2.1 本次 spec（生化斯坦 260，城市模板已由文档 §5.4 佐证）

```json
{"campaigns":[{"planet":260,"id":51991,"type":0,"count":20,"race":3}],
 "regions":[{"planet":260,"regionIndex":0,"owner":3,"maxHealth":2000000},
            … 共 8 条，编号 0–7，数值全部取自本次 WarInfo …]}
```

- 战役类型：`0`（常规解放）——文档对生化斯坦用的就是 `type 0 / race 3`；
- 分区 `owner` = 3（自动机，与战役 race 一致）；`health = maxHealth // 2`；
- 分区编号与数量**现算**（不写死 8），并校验 `layoutVersion == 717`。

## 3. 离线验证（两道都过）

| 检查 | 结果 |
|---|---|
| `city_campaign.py selftest`（真实 Status 样本） | regions 35 → **43**（第一次补 8、第二次 0 → 幂等）；7 条门禁 PASS：数量/maxHealth//2/isAvailable/字段拼写/其它星球未动/编号不重复 |
| 真实代码路径（`import` 打过补丁的 `war_proxy.py` → `rewrite_status(真实样本)`） | 改动 9（1 战役 + 8 分区），日志 9 行 `REWRITE-EXTRA`；260 分区 8 条、其它星球仍 35 条未变 |

## 4. 运行态与判读

代理以 **rewrite 模式**运行，`HD2_GWE_EXTRA = out/city_spec.json`（**本次只开城市注入，伪造防守暂时关掉**，
单变量；要恢复防守就把 156 那套 spec 换回去）。

| 现象 | 判读 |
|---|---|
| **CYBERSTAN(260) 出现可选作战、能进任务** | ✅ 社区文档主张成立（分区状态是"作战为空"的缺口） |
| 星球卡片正常但仍**没有可选作战** | 分区不是唯一条件：下一步试 `campaigns[].type = 3`（文档里超级地球用的组合）或补 `availabilityFactor` 之外的字段 |
| 星图/游戏报**通讯错误** | 分区行被客户端拒绝 ⇒ 优先查 `settingsHash` 是否需要（文档 §5.3 提到它是"行索引哈希高 32 位"，我们这版没写进状态行）与 `regionSize` |
| CYBERSTAN 点不开/没战役 | 战役条目没生效（看 `logs/proxy.log` 是否有 `追加战役`） |

## 5. 与"伪造防守"的关系

两条线用的是同一个钩子、互不依赖：

- 防守 = `campaigns{type:4}` + `planetEvents` + `jointOperations` + 攻击边（[DEFENSE-FORGE-RECIPE](DEFENSE-FORGE-RECIPE.md)，✓✓ 已实机）
- 城市 = `campaigns{type:0/3}` + **`planetRegions` 补齐**（本文件，待实机）

## 6. 回滚

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\stop.ps1
# 撤城市补丁（regions 分支）
Copy-Item D:\Downloads\variant_mod\tools\war_proxy.py.cityregions.bak D:\Downloads\variant_mod\tools\war_proxy.py
# 撤防守补丁（potentialBuildUp / campaignId 兜底）
python tools/defense_inject.py revert --proxy D:/Downloads/variant_mod/tools/war_proxy.py
```

---

## 7. 实机结果

### 7.1 CYBERSTAN（260）—— ✓✓ 成立

- 注入：`campaigns{planet:260, type:0, race:3}` + **8 条分区**（0–7，`owner=3`，`health=maxHealth//2`）；
- 游戏内：星图出现 **BATTLE FOR CYBERSTAN** 卡，正文列出 **CYBERSTAN MEGAFACTORIES** 八个分区
  （TRANSCENDI / URSOOT NIN / STAR KIELD / CAMRAT FOR / LURZA / OMNIPARITL / SOLIDARITE / AUTONOMY），
  每个分区带进度条；**能点开、能进任务**。

⇒ 社区文档的核心主张成立：**"星球能开但没有可选作战" 的缺口 = `Status.planetRegions` 缺条目**；
按原生定义补齐后客户端就生成作战。城市/巨型工厂地图也随之出现（分区名由客户端的地区名表渲染）。

### 7.2 SUPER EARTH（0）—— 已装，待实机

按文档 §2.2 给超级地球的组合（`type = 3`、`race = 4` 光明族）另做一份 spec：

| 项 | 值 |
|---|---|
| 战役 | `{id:51992, planetIndex:0, type:3, count:20, race:4}` |
| 分区 | **7 条**（regionIndex 0–6，`owner=4`，`health=maxHealth//2 = 300,000`，`maxHealth` 600,000 取自 WarInfo） |
| 星球归属 | **保留服务器值**（文档要求；我们不动 `planetStatus[0].owner`） |
| 离线验证 | selftest：regions 35→42（第二次 0 ⇒ 幂等）；真实代码路径改动 8（1 战役 + 7 分区），其它星球 35 条未动 |

判读：星图应出现 **BATTLE FOR SUPER EARTH**（`type=3` 按枚举渲染，客户端不校验星球类型 —— 与 2026-10-27 的结论一致），
并且**有可选作战、能进**。若这次"有卡无作战"，就说明超级地球还差别的条件（下一步试 `type` 保持 3 但把 `count` 提高 / 补 `settingsHash`）。

### 7.3 SUPER EARTH（0）—— ✓✓ 成立（光照族版）

`campaigns{planet:0, type:3, count:20, race:4}` + 7 条分区（`owner=4`）：
游戏内出现 **BATTLE FOR SUPER EARTH**，**有可选作战、能进**。

⇒ `type = 3` 在超级地球上是"超级地球保卫战/Mega City"的正确枚举（与 2026-10-27 那条"客户端只按枚举渲染、不校验星球类型"的结论一致）。

### 7.4 换敌人：Super Earth + 终结者（race 2）—— 已装，待实机

问题：**超级地球的城市战役是否接受 Illuminate 之外的敌人？**

| 项 | 值 |
|---|---|
| 战役 | `{id:51993, planetIndex:0, type:3, count:20, **race:2（终结者）**}` |
| 分区 | 7 条（regionIndex 0–6，**`owner=2`**，`health=300,000`） |
| 其它 | 与 7.3 完全相同（星球归属不动、layout/战争同一份） |
| 离线验证 | selftest 7 条门禁 PASS；spec 文件 `out/city_spec_se_terminid.json` |

判读：卡片是否仍为 BATTLE FOR SUPER EARTH、**任务里刷的是不是虫子**、能否进/结算。

| 现象 | 判读 |
|---|---|
| 卡在、能进、局内是**终结者** | 城市战役**不绑定光明族**，敌人由 `race` 决定（最强的结论） |
| 卡在、能进、局内仍是**光明族** | 客户端对 `type=3` 硬绑光明族 ⇒ `race` 只是展示 |
| 有卡**无作战** | 终结者在 super earth 上缺任务池（地区模板不含虫子） |
| 通讯错误/崩 | 该组合非法，回滚到 7.3 的光明族版 |

### 7.5 SUPER EARTH + 终结者（race 2）—— ✓✓ 成立

同一套注入只把 `race` / 分区 `owner` 换成 **2（终结者）**：卡片头部阵营显示 **TERMINID**、
**能进任务、局内刷的就是虫子**。

两个细节值得记：

1. **敌人由 `race` 决定，城市战役不绑定光明族** —— 这是本轮最硬的结论；
2. 卡片**正文**仍写着 *"Illuminate Fleet Strength must be depleted…"*：`type = 3` 的描述文案是**固定文本**，
   不随 `race` 变。⇒ 判读"敌人是谁"不能看描述，要看头部阵营与局内。

---

## 8. 结项（2026-10-29）

### 8.1 结论总表

| # | 结论 | 状态 | 证据 |
|---:|---|---|---|
| 1 | 特殊星球「能点开但没有可选作战」的缺口 = `Status.planetRegions` 缺分区条目；按原生定义补齐即生成作战 | **✓✓ 实机** | CYBERSTAN(260)：八分区卡 + 能进 |
| 2 | 补齐只需 5 个状态字段（`planetIndex/regionIndex/owner/health/…`），`health = maxHealth//2` 可用 | **✓✓ 实机** | 260 / 0 两次 |
| 3 | 分区条目可以只用**一条** campaign 通吃（type 0 与 type 3 都成） | **✓✓ 实机** | 260(type0,race3) / 0(type3,race4) |
| 4 | **`race` 决定敌人阵营**，城市战役不绑定光明族 | **✓✓ 实机** | 0 号星球换 race=2 → 局内终结者 |
| 5 | 卡片正文文案是 `type` 的固定文本，不随 `race` 变 | **✓✓ 实机** | 终结者版正文仍写 "Illuminate Fleet Strength" |
| 6 | 只需改 `Status` 响应，不动 WarInfo、不调任何作战/奖励接口 | **✓ 实机** | 全程 passthrough/rewrite 只碰 Status |

### 8.2 标准配方（城市战役）

```json
{"campaigns":[{"planet":<目标>,"id":<唯一>,"type":<0 常规|3 超级地球>,"count":<20 左右>,"race":<2/3/4>}],
 "regions":[{"planet":<目标>,"regionIndex":<原生编号>,"owner":<同 race>,"maxHealth":<取自 WarInfo>"} …]}
```

- 分区条目：**只补缺失**（已有同编号条目一律保留），`health = maxHealth//2`、`players=0`、
  `regerPerSecond=0`（拼写照抄）、`isAvailable=true`、`availabilityFactor=1`；
- 分区编号/数量从**本次** `WarInfo` 现算，并校验 `layoutVersion`；
- 星球归属（`planetStatus[].owner`）**不改**。

### 8.3 未证 / 边界

| 项 | 现状 |
|---|---|
| 其它特殊星球（虫巢世界、其它首都）是否同一条路径 | **⚠ 未测**；文档 §9 也明确未证 |
| 分区进度是否真的会推进 / 结算 | **⚠ 未测**（本机新建状态，服务器不记账） |
| `settingsHash` / `regionSize` 是否影响任务池 | **⚠ 未测**（这次没写进状态行也能出作战） |
| 24h 事件与城市战役叠加（防守 + 分区） | **⚠ 未测**（两条线都通了，但没同时开） |

### 8.4 收尾后的盘面（当前）

| 项 | 状态 |
|---|---|
| 代理 | rewrite 模式，PID 8768，`HD2_GWE_EXTRA = out/city_spec_se_terminid.json`（**超级地球 + 终结者**） |
| 已装效果 | SUPER EARTH 上有 BATTLE FOR SUPER EARTH，敌人 = 终结者 |
| 切回光照族版 | `out/city_spec_se.json` |
| 切回生化斯坦 | `out/city_spec.json` |
| 切回伪造防守 | `out/defense_spec.json`（配 [DEFENSE-FORGE-RECIPE](DEFENSE-FORGE-RECIPE.md)） |
| 正常玩 | 代理用 `-Passthrough` 重启 |
| 彻底还原 | `stop.ps1` → （管理员）`teardown.ps1` |

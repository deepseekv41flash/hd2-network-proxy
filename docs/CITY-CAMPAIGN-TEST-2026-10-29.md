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

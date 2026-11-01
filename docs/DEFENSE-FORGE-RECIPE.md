# 伪造防守战役：标准配方（✓✓ 已实机 2026-10-29）

> 一句话：**只改 `/api/WarSeason/801/Status` 响应**，给目标星球补齐五样东西——
> `owner=1`、一条**敌方→该星球**的 `planetAttacks` 边、`campaigns[]` 一条 `type:4` 战役、
> `planetEvents[]` 一条 `eventType:1` 事件（`health < maxHealth`）、`jointOperations[]` 一条同 id 记录。
> 游戏里就出现 **DEFENSE 卡，且能点进去开一局**。
>
> 现场：2026-10-29 22:53，目标 **CHARBAL-VII（游戏索引 156）** ← 进攻方 **DURGEN（157，自动机）**，
> 界面读数 `AUTOMATON / INVASION LEVEL 20 / DEFEND 01:22:59:04 / SELECT CAMPAIGN`，点进去可开。

---

## 1. 五件套（缺一不可，实测）

| # | 位置 | 本次取值 | 作用 |
|---|---|---|---|
| 1 | `planetStatus[156].owner` | `1` | 必须是我方星球（防守 = 守自己的） |
| 2 | `planetAttacks[]` | `{source:157, target:156}` | **敌方 → 我方**的进攻边；真实防守在线上也只有 1 条这种反向边 |
| 3 | `campaigns[]` | `{id:51990, planetIndex:156, type:4, count:38, race:3}` | **`type:4` 是防守/联合作战的标记**（0 = 常规解放） |
| 4 | `planetEvents[]` | `{id:9101, planetIndex:156, eventType:1, race:3, health:990000, maxHealth:1000000, startTime, expireTime, campaignId:51990, jointOperationIds:[9101], potentialBuildUp:0}` | 倒计时 + 进度条 + 入侵等级 |
| 5 | `jointOperations[]` | `{id:9101, planetIndex:156, hqNodeIndex:2}` | **与 4 的 id 必须相同**；缺了卡片不渲染 |

自洽约束（写错任一条都不出卡）：

- `events[].campaignId` **==** 同星球 `campaigns[].id`
- `events[].jointOperationIds` **==** `[events[].id]`，且 `jointOperations[].id` 同值
- `events[].race` **==** `campaigns[].race`（本次都 3 = 自动机）
- `events[].health` **<** `events[].maxHealth`（本次 99%；`health ≥ maxHealth` 那版曾导致客户端通讯错误）

## 2. 界面字段 ↔ 数据

| 界面 | 字段 |
|---|---|
| DEFENSE | `campaigns[].type = 4` + 事件 + 联合作战齐备 |
| 阵营标题（AUTOMATON） | `race`（3 自动机 / 2 终结者 / 4 光明族） |
| **INVASION LEVEL** | **`events[].maxHealth ÷ 50,000`**（1,000,000→20；真实样本 1,900,000→38） |
| 倒计时 | `events[].expireTime − Status.time`（真实防守 48 h，社区样本 24 h，都可） |
| 进度条 | `events[].health / maxHealth` |
| 战线箭头 | `planetAttacks` 那条边 |

> 想要几级就写 `maxHealth = 等级 × 50,000`：38 级 = 1,900,000，50 级 = 2,500,000。

## 3. 怎么打进去（工具已就绪，2026-11-01 起有一键脚本）

> 2026-11-01 新增 `tools/start_defense_proxy.ps1`：一条命令完成"停旧代理 → 备份 config/selection/status →
> 写干净 config-defense.json → 带 spec 与抓包环境变量启动"。完整实测见 `MISSION-CAPTURES-2026-11-01.md`。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\start_defense_proxy.ps1 `
    -SpecFile D:\mod\work\variant-net\out\defense_spec_20261101.json
```


```bash
# ① 给第三方代理的 HD2_GWE_EXTRA 钩子补 potentialBuildUp / campaignId 兜底（幂等，留 .bak）
python tools/defense_inject.py apply --proxy D:/Downloads/variant_mod/tools/war_proxy.py

# ② 生成 spec（单行 JSON；参数按上面五件套改）
python tools/defense_inject.py spec --target 156 --source 157 --count 38 --race 3 \
    --camp-id 51990 --event-id 9101 --max-health 1000000 --out out/defense_spec.json

# ③ 离线自检（用真实抓包样本走一遍，七条一致性门禁）
python tools/defense_inject.py selftest --spec-text "$(cat out/defense_spec.json)"

# ④ 以 rewrite 模式启动代理（spec 走环境变量，抓包可同时开）
#    HD2_GWE_EXTRA=<spec>  HD2_GWE_DUMP=D:\mod\out\gwe  HD2_GWE_PATHS=/api/
```

进游戏刷一次星图即可；`logs/proxy.log` 会出现四行 `REWRITE-EXTRA`（战役 / 攻击边 / 事件 / 联合作战）。

## 4. 为什么 Oct-27/28 三次失败（差异清单）

| 那次的做法 | 本次 | 结论 |
|---|---|---|
| `campaigns[].type = 0`（当解放战役写） | **`type = 4`** | 决定性差异：type 0 只是"我方打别人" |
| 只加 `planetEvents`，没有 `jointOperations` | 三块同 id | 缺块不渲染 |
| `race` 未与事件对齐 / `health = maxHealth` | 99% | `health ≥ maxHealth` 会触发客户端通讯错误（旧记录） |
| 事件无 `potentialBuildUp` | 有（0） | 与真实样本对齐 |
| 攻击边只有"人类→敌星" | 补了 **敌星→我方** | 真实防守线上只有 1 条这种边，本次照抄 |

## 5. 回滚

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\stop.ps1     # 停代理
python tools/defense_inject.py revert --proxy D:/Downloads/variant_mod/tools/war_proxy.py # 撤补丁
# 用 start_defense_proxy.ps1 启过的话，还要还原它做的三份备份：
copy /Y D:\Downloads\variant_mod\config.json.bak-defense-<stamp>             D:\Downloads\variant_mod\config.json
copy /Y D:\Downloads\variant_mod\runtime\selection.json.bak-defense-<stamp>  D:\Downloads\variant_mod\runtime\selection.json
copy /Y D:\Downloads\variant_mod\runtime\status.json.bak-defense-<stamp>     D:\Downloads\variant_mod\runtime\status.json
# 正常联机前还要（管理员）：
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Downloads\variant_mod\teardown.ps1 # 撤 hosts + 证书
```

> 想"继续正常玩但保留工具"：代理以 `-Passthrough` 重启即可（不注入、纯转发）。
> ⚠ hosts 在重定向期间必须保持代理运行，否则游戏连不上服务器。

## 6. 边界

- 这是**本机客户端侧**的 Status 改写：服务器不知道、也不会给这条伪造战役记账；
  进任务能开是因为"作战创建"走的是客户端自己选的战役参数（见 §2 的 `Operation/Create` 请求体）。
- 伪造战役的防守进度不会真的推进（没有服务器 tick），倒计时走本地时钟。
- 只建议单人/受控环境试，别扩散到多人对局。

## 7. 2026-11-01 复跑：能完整打完并结算，但有两个坑（✓✓ 实机）

配方原样复用（目标 156 CHARBAL-VII、进攻方 157、等级 38、事件 id 9101），这次**把一局打完了**：

| 环节 | 结果 |
|---|---|
| Status 注入 | 日志 `REWRITE +4 entries`（战役/攻击边/事件/联合作战）✓ |
| `Operation/Create` | 服务器接受，op **1237**；请求体 `type=4 / jointOperationId=9101 / operationSettingsId=538077316 / 3×任务 type=3` ✓ |
| `Mission/Start` | 返回 missionId ✓ |
| `Mission/end` | 成功撤离，XP 258 / 影响力 86 / 货币 1,002 ✓（真实发放）|

两个必须知道的坑：

1. **任务内容不是真防守任务**：本局目标是 `ERADICATE AUTOMATON FORCES`（普通清剿）；
   真防守（244/207）是 `EVACUATE HIGH-VALUE ASSETS` / `EVACUATE PRIORITY CITIZENS` 一类撤离任务。
   ⇒ 伪造 campaign/event 不足以让客户端选到"防守任务池"。
2. **结算里的战役字段是残值**：`campaignWon=true`、`othersImpactPlanetEvent=1,880,999`
   （= 注入事件血量 −1），但战后 Status 里 156 号星球毫无变化 ⇒ 服务器把"不存在的事件"按 0 血处理。
   ⇒ 做防守语义研究必须用**真实事件**样本（见 `MISSION-CAPTURES-2026-11-01.md` 第三局）。

配套结论：`operationSettingsId=538077316` 在真实防守（244/207）与伪造防守（156）三个星球、难度 5/8 下完全一致，
它是"防守类作战"的固定设置 id。


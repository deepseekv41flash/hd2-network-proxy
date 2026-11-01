# CAUSTIC STRAIN 首次激活实验（2026-11-01 ✓✓ 实机）

> 目标：验证**「已发布但从未在线上出现过」的变种词条**能否由客户端本地激活，并顺便证实
> effect 1430（tag）与 1431（mechanic）的配对。单变量：只往一颗星球注入这一对。
> 工具：[variant_mod MITM 代理](https://github.com/deepseekv41flash/hd2-network-proxy)（响应改写，不改游戏文件）。

---

## 1. 数据身份（✓ 离线）

| 项 | 值 |
|---|---|
| 词条（tag） | **effect 1430**，`effectType=40`，`values[0]=585432236` |
| 玩法（mechanic） | **effect 1431**，`effectType=71`，`values[0]=0x80D76742 = murmur32("bugs_acid")` |
| presence 行 | `bugs_acid`（137 行 presence 之一）：`+0x14=4`（敌情）、`+0x18=1`（strain）、`+0x1C=2`（terminid） |
| 显示名 locid | **461034013 = `CAUSTIC STRAIN`**（中文客户端渲染为「腐蚀变种」） |
| 描述 locid | 3001998873 = `A strain of Terminids with highly alkaline bile sacs have infested this planet. Prepare to face enemies that discharge c…`（中文：一种拥有高碱性胆汁囊的终结族已侵染此星球。请做好应对准备，敌人会喷吐腐蚀性体液、并在死亡时爆裂。）|
| 线上历史 | 68 份 `801_Status` 抓包中 **0 次在线**；1430/1431 是最近一次 GWE 目录（310→312 条）**新增的两条** ⇒ 典型「已发布、从未出现」内容 |

配对依据：1430/1431 是同一批新增的**相邻 id**（原生目录里 tag/mechanic 成对发布），且 1431 的
`values[0]` 精确等于 `murmur32("bugs_acid")`；此前 13 个 tag ↔ 13 个 mechanic 的邻接启发式表里没有它
（1430 使 tag 总数 13→14）——本轮实机结果**反证该配对正确**。

## 2. 注入配置

```jsonc
// variant_catalog.json
"variants": { "caustic_strain": [1430, 1431] },
"meta":     { "caustic_strain": { "faction": "terminid", "presence": "bugs_acid", "tag": 1430, "mechanic": 1431 } }

// runtime/selection.json
{ "enabled": true, "variants": ["caustic_strain"] }

// config.json
"targets": [ { "planet": 100, "variant": "caustic_strain" } ]   // 100 = TRANDOR，terminid 解放战、原版无任何 effect
```

启动：`run_capture.ps1 -Rewrite`（代理 `passthrough=False`，只改写 `801/Status`，其余原样转发）。

## 3. 服务端证据

```
D:\Downloads\variant_mod\logs\audit.log:
2026-11-01T20:06:13  REWRITE +2 entries (planet 100 -> [1430, 1431])  变种=caustic_strain
```

原始 Status 已抓在 `D:\mod\out\gwe\b761cdc3_api_WarSeason_801_Status.json`（49,090 B，改写前）。
离线回放同一份 body：`139 → 141` 条，恰好新增 `(100,1430)` 与 `(100,1431)`。

## 4. 实机结果（✓✓）

- 星图/作战界面出现 **「腐蚀变种 / CAUSTIC STRAIN」** 词条与描述（与 presence 描述 locid 逐字一致）；
- 进图后**终结族刷新为腐蚀变体**：喷吐腐蚀性体液、死亡时爆裂（与描述一致）；
- 无崩溃/通讯错误。

## 5. 结论

1. **「已发布但从未出现过」的变种词条可以本地激活**：只要本地存在 presence 行 + GWE 目录里有 tag/mechanic，
   即使服务器 0 在线，也能按「tag + mechanic」成对注入完整生效（卡面 + 局内）。
2. **tag 1430 = CAUSTIC STRAIN 的配对 tag**，`bugs_acid` 的 presence 机制从此闭合。
3. 该方法与 type94 实验（`INCENDIARY GATLING BARRAGE`）合起来说明：**GWE 目录 = 服务器准备的内容清单**，
   客户端本地已经具备所有实现；服务器没排期 ≠ 客户端没内容。

## 6. 候选：其它从未在线的可玩法词条（39 条 type71 里挑）

| effect | presence / 名称 | 类型 | 备注 |
|---:|---|---|---|
| 1355 | `bots_increased_warstriders` / HEAVY ARMOR SURGE | 机器人激增 | tag 可能是 1360（该 tag 在线，配 1359/1361/1362） |
| 1357 | `bots_increased_hulks` / HULK SURGE | 机器人激增 | 同上 |
| 1359 | `bots_increased_devastators` / DEVASTATOR SURGE | 机器人激增 | 旧报告邻接表里 1360→1359 |
| 1362 | `bot_battle_intense` | 敌情 | 同上 |
| 1269 | `illuminate_fleet` / The Great Host | 事件作战(kind=1) | 可发作战卡 |
| 1373/1374/1375 | `illuminate_ritual_storm_lvl1/2/3` | 事件作战(kind=1) | 1373 曾 ✓✓ 注入（AVERT VOID） |
| 1407 | `illuminate_rift_sideboard_gate` / VOID GATEWAY | 敌情/设施 | |
| 1211/1212/1213 | 战术行动（行星轰炸 / 鹰暴 / 轨道封锁） | 战术行动(kind=3) | |

完整名单可由 `out/gwe/effects-full.csv` 过滤 `effect_type=71` 且 `live_count=0, ever_snapshot_count=0` 重算。

## 7. 回滚

```powershell
# 还原配置（本次改动前备份：config.json.bak-type94-20261101 / variant_catalog.json.bak-type94-20261101 /
#                           runtime/status.json.bak-before-caustic / runtime/selection.json.bak-type94-20261101）
D:\Downloads\variant_mod\stop.ps1
# 彻底回滚（删信任证书 + hosts，需管理员）
D:\Downloads\variant_mod\teardown.ps1
```

# 可注入效果菜单（warId 801）

> 生成自 `fb1b64f6_api_WarSeason_GalacticWarEffects.json`（310 条）、`3c3e7228_api_WarSeason_801_Status.json`（在线 66 个不同 effect）
> presence 分类依据 `generated_galactic_presence_settings.dl_bin` 的 `+0x14/+0x18/+0x1C`，见 PLANET-TABLES。

## 0. 一句话

**GWE 是「服务器这场战争准备好的效果清单」，不是「客户端全部内容」。** 目录里的 id 可以直接塞进 `Status.planetActiveEffects` 生效；目录外的 id 客户端解析不出来。

## 1. 总览

| 项 | 数 |
|---|---:|
| GWE 目录条目 | 310 |
| 其中 type71（presence 引用，本表主体） | 75 |
| type71 且本地能解析 | 70 |
| type71 但本地无对应 presence | 5 |
| 当前在线（挂在星球上） | 66 |

### 按种类（type71）

| `+0x14` | 含义 | 条数 | 在线 |
|---|---|---:|---:|
| 0 | 地图标记 | 12 | 1 |
| 1 | 事件作战 | 3 | 0 |
| 3 | 战术行动 | 3 | 0 |
| 4 | 敌情 | 52 | 32 |
| — | 本地无对应 presence | 5 | 4 |

## 1.5 怎么把表里的一行跑起来

代理只认 `variant_catalog.json` 里的**变种名**，不认裸 effect id。所以要跑表里任意一条，两步：

```jsonc
// 1) variant_catalog.json：加一条，ids 填本表的 effect，faction 填该条目的阵营
"variants": { "my_test": [1373] },
"meta":     { "my_test": { "faction": "illuminate", "mechanic": 1373 } }

// 2) config.json：指到目标星球（星球游戏索引，见 PLANET-INDEX）
"targets": [ { "planet": 182, "variant": "my_test" } ]
```

然后 `run_capture.ps1 -Rewrite` 重启代理 → **重启游戏**（Status 只在登录流程拉）→ 进目标星球。

⚠ `meta.faction` 是**我们自己的过滤器**（`resolve_plan()`），不是游戏校验。实测跨阵营效果客户端照收，所以想让 A 阵营 presence 上 B 阵营星球，把 `faction` 写成 B 即可（本表「阵营」列仍是 presence 的真实阵营）。

## 2. 能发「事件作战」的（kind=1）

注入后部署界面出现对应主题的作战卡（实测：`1373` → `AVERT VOID`）。

| effect | presence | 阵营 | 作战名 | 在线星球数 | 证据 |
|---|---|---|---|---|---|
| 1373 | illuminate_ritual_storm_lvl1 | illuminate | CLASS 1 EXOSTORM | 0 | ✓✓ 实机 |
| 1374 | illuminate_ritual_storm_lvl2 | illuminate | CLASS 2 EXOSTORM | 0 | ⚠ 未证 |
| 1375 | illuminate_ritual_storm_lvl3 | illuminate | CLASS 3 EXOSTORM | 0 | ⚠ 未证 |

## 3. 战术行动（kind=3）

| effect | presence | 阵营 | 名称 | 在线 |
|---|---|---|---|---|
| 1211 | tactical_action_planetary_bombardment | SE | PLANETARY BOMBARDMENT | 0 |
| 1212 | tactical_action_eagle_storm | SE | EAGLE STORM | 0 |
| 1213 | tactical_action_defensive_lockdown | SE | ORBITAL BLOCKADE | 0 |

## 4. 敌情（kind=4，进 `COMBATANT FORCES PRESENT`）

实测：`1386`（`bugs_gloom`）跨阵营注入光照星球后，星图卡显示 `SPORE BURST STRAIN`，作战界面 `COMBATANT FORCES PRESENT` 列出该项，但**不改变作战卡**。

| effect | presence | 阵营 | 名称 | +0x18 | 在线 | 证据 |
|---|---|---|---|---|---|---|
| 1228 | black_hole | - | MERIDIAN BLACK HOLE | 0 | 0 | ⚠ 未证 |
| 1229 | black_hole_intensified | - | MERIDIAN BLACK HOLE | 0 | 1 | ⚠ 未证 |
| 1230 | black_hole_travel_blocked | - | MERIDIAN BLACK HOLE | 0 | 0 | ⚠ 未证 |
| 1241 | destroyed_by_black_hole | - | FRACTURED PLANET | 0 | 1 | ⚠ 未证 |
| 1252 | destroyed_by_black_hole | - | FRACTURED PLANET | 0 | 2 | ⚠ 未证 |
| 1352 | destroyed_by_death_laser | - | CONVENTIONAL BLACK HOLE | 0 | 1 | ⚠ 未证 |
| 1195 | democracy_station_phase_1 | SE | DSS CONSTRUCTION SITE - PHASE 1 | 0 | 0 | ⚠ 未证 |
| 1196 | civilian_cargo | SE | DSS LOGISTICS HUB | 0 | 0 | ⚠ 未证 |
| 1197 | research_bio_research | SE | XENOENTOMOLOGY CENTER | 0 | 1 | ⚠ 未证 |
| 1198 | manufacturing_forge | SE | DEEP MANTLE FORGE COMPLEX | 0 | 1 | ⚠ 未证 |
| 1199 | democracy_station_phase_2 | SE | DSS CONSTRUCTION SITE - PHASE 2 | 0 | 0 | ⚠ 未证 |
| 1204 | liberty_day | SE | LIBERTY DAY CELEBRATION | 0 | 0 | ⚠ 未证 |
| 1205 | democracy_station_phase_3 | SE | DSS CONSTRUCTION SITE - PHASE 3 | 0 | 0 | ⚠ 未证 |
| 1206 | military_tower | SE | TERMINID RESEARCH PRESERVE | 0 | 0 | ⚠ 未证 |
| 1217 | democracy_station_final | SE | DEMOCRACY SPACE STATION | 0 | 0 | ⚠ 未证 |
| 1232 | manufacturing_generic | SE | FACTORY HUB | 0 | 1 | ⚠ 未证 |
| 1234 | research_generic | SE | CENTER OF SCIENCE | 0 | 1 | ⚠ 未证 |
| 1236 | civilian_surveillance | SE | CENTER FOR CIVILIAN SURVEILLANCE AND SAFETY | 0 | 1 | ⚠ 未证 |
| 1268 | research_energy_lab | SE | NEGATIVE ENERGY LABORATORY | 0 | 0 | ⚠ 未证 |
| 1282 | military_helldiver_training | SE | HELLDIVER TRAINING FACILITIES | 0 | 1 | ⚠ 未证 |
| 1286 | construction_hope | SE | NEW HOPE CONSTRUCTION SITE | 0 | 0 | ⚠ 未证 |
| 1287 | completed_hope | SE | NEW HOPE CITY | 0 | 1 | ⚠ 未证 |
| 1291 | completed_aspiration | SE | NEW ASPIRATION CITY | 0 | 1 | ⚠ 未证 |
| 1292 | completed_yearning | SE | NEW YEARNING CITY | 0 | 1 | ⚠ 未证 |
| 1295 | civilian_bug_park | SE | TYRANNY PARK 2 | 0 | 0 | ⚠ 未证 |
| 1324 | manufacturing_industry | SE | ULTRAMAFIC MINE | 0 | 1 | ⚠ 未证 |
| 1329 | liberty_day | SE | LIBERTY DAY CELEBRATION | 0 | 0 | ⚠ 未证 |
| 1342 | dissident_prison | SE | CENTER FOR THE CONFINEMENT OF DISSIDENCE (CECOD) | 0 | 0 | ⚠ 未证 |
| 1344 | dss_augmentation | SE | PANDORA BASE | 0 | 1 | ⚠ 未证 |
| 1395 | tcs_wall | SE | TERMINID CONTROL SYSTEM+ | 0 | 14 | ⚠ 未证 |
| 1400 | seaf | SE | Heavy SEAF Presence | 1 | 3 | ⚠ 未证 |
| 1203 | elite_bot_jumpattack | automaton | THE JET BRIGADE | 1 | 1 | ⚠ 未证 |
| 1239 | bot_facility_jetbrigade | automaton | JET BRIGADE FACTORIES | 0 | 1 | ⚠ 未证 |
| 1249 | bots_ivory_legion | automaton | THE INCINERATION CORPS | 1 | 4 | ⚠ 未证 |
| 1353 | bot_facility_data | automaton | DATA CENTER | 0 | 1 | ⚠ 未证 |
| 1355 | bots_increased_warstriders | automaton | HEAVY ARMOR SURGE | 1 | 0 | ⚠ 未证 |
| 1357 | bots_increased_hulks | automaton | HULK SURGE | 1 | 0 | ⚠ 未证 |
| 1359 | bots_increased_devastators | automaton | DEVASTATOR SURGE | 1 | 0 | ⚠ 未证 |
| 1361 | bots_cyborgs | automaton | CYBORGS | 1 | 2 | ⚠ 未证 |
| 1387 | bot_facility_comms | automaton | COMMUNICATIONS ARRAY | 0 | 1 | ⚠ 未证 |
| 1269 | illuminate_fleet | illuminate | The Great Host | 0 | 0 | ⚠ 未证 |
| 1378 | illuminate_harvester | illuminate | MINDLESS MASSES | 1 | 2 | ⚠ 未证 |
| 1379 | illuminate_engineer | illuminate | APPROPRIATORS | 1 | 1 | ⚠ 未证 |
| 1403 | illuminate_bodyhorror | illuminate | VOTE SNATCHERS | 1 | 2 | ⚠ 未证 |
| 1407 | illuminate_rift_sideboard_gate | illuminate | VOID GATEWAY | 0 | 0 | ⚠ 未证 |
| 1414 | illuminate_invading | illuminate | INVASION FLEET | 1 | 1 | ⚠ 未证 |
| 1245 | bugs_super_predator | terminid | PREDATOR STRAIN | 1 | 1 | ⚠ 未证 |
| 1308 | bugs_hive_lord | terminid | HIVE LORDS | 1 | 2 | ⚠ 未证 |
| 1309 | bugs_dragon | terminid | DRAGONROACHES | 1 | 3 | ⚠ 未证 |
| 1310 | bugs_burrower | terminid | RUPTURE STRAIN | 1 | 2 | ⚠ 未证 |
| 1386 | bugs_gloom | terminid | SPORE BURST STRAIN | 1 | 1 | ✓✓ 实机 |
| 1396 | bug_tcs_towers | terminid | — | 0 | 0 | ⚠ 未证 |

## 5. 地图标记（kind=0）

| effect | presence | 名称 | 在线 |
|---|---|---|---|
| 1240 | planet_at_risk | — | 0 |
| 1242 | travel_path_to_super_earth | — | 0 |
| 1330 | fireworks | — | 0 |
| 1362 | bot_battle_intense | — | 0 |
| 1376 | illuminate_rift | — | 0 |
| 1408 | illuminate_rift_mesh | — | 0 |
| 1409 | illuminate_rift_other_planets | — | 0 |
| 1410 | void_cluster_one | — | 0 |
| 1411 | void_cluster_two | — | 0 |
| 1412 | operation_rift_source | — | 0 |
| 1417 | illuminate_rift | — | 0 |
| 1418 | force_evacuate | — | 1 |

## 6. 本地解析不出来（注入后大概率无显示）

| effect | values | 在线 |
|---|---|---|
| 1304 | 2524180707,0 | 1 |
| 1311 | 3401633102,0 | 2 |
| 1327 | 2911168129,0 | 1 |
| 1333 | 358233407,0 | 1 |
| 1341 | 1735773337,0 | 0 |

## 7. 其余类型（非 type71，共 235 条）

| effectType | 已知语义 | 条数 | 在线 |
|---|---|---:|---:|
| 1 | 数值参数 | 6 | 0 |
| 21 | 数值参数 | 12 | 2 |
| 23 | 数值参数 | 9 | 2 |
| 24 | ⚠ 未证 | 1 | 0 |
| 25 | 数值参数 | 6 | 0 |
| 29 | ⚠ 未证 | 1 | 0 |
| 32 | 战备引用（hash→战备） | 88 | 2 |
| 36 | 空间站临时装备（EXO-45/49） | 16 | 1 |
| 40 | 标签（与 71 严格成对） | 13 | 13 |
| 43 | ⚠ 未证 | 1 | 0 |
| 44 | ⚠ 未证 | 1 | 0 |
| 45 | ⚠ 未证 | 1 | 0 |
| 46 | ⚠ 未证 | 1 | 0 |
| 47 | ⚠ 未证 | 1 | 0 |
| 48 | ⚠ 未证 | 1 | 0 |
| 49 | ⚠ 未证 | 6 | 0 |
| 50 | ⚠ 未证 | 2 | 0 |
| 51 | ⚠ 未证 | 1 | 0 |
| 54 | ⚠ 未证 | 1 | 0 |
| 55 | ⚠ 未证 | 1 | 0 |
| 56 | 数值参数 | 7 | 3 |
| 59 | ⚠ 未证 | 2 | 0 |
| 61 | ⚠ 未证 | 2 | 0 |
| 63 | ⚠ 未证 | 1 | 0 |
| 67 | ⚠ 未证 | 1 | 0 |
| 69 | 未知 | 3 | 2 |
| 70 | ⚠ 未证 | 3 | 0 |
| 72 | 未解 | 15 | 0 |
| 73 | 未解 | 5 | 2 |
| 74 | ⚠ 未证 | 1 | 0 |
| 76 | 未解 | 1 | 1 |
| 77 | ⚠ 未证 | 4 | 0 |
| 80 | ⚠ 未证 | 2 | 0 |
| 83 | ⚠ 未证 | 3 | 0 |
| 87 | ⚠ 未证 | 3 | 0 |
| 88 | ⚠ 未证 | 1 | 0 |
| 89 | ⚠ 未证 | 1 | 0 |
| 90 | ⚠ 未证 | 1 | 0 |
| 92 | 未解 | 1 | 1 |
| 93 | ⚠ 未证 | 1 | 0 |
| 94 | ⚠ 未证 | 3 | 0 |
| 95 | ⚠ 未证 | 2 | 0 |
| 96 | ⚠ 未证 | 2 | 0 |
| 97 | ⚠ 未证 | 1 | 0 |

## 8. 证据等级

| 结论 | 等级 | 依据 |
|---|---|---|
| kind=1 注入 → 作战卡变化 | ✓✓ 实机 | `1373` on 182/93：卡片 AVERT VOID、`operationSettingsId` 2796992372→3194790369 |
| kind=4 注入 → 星图卡 + COMBATANT FORCES | ✓✓ 实机 | `1386` on 93（跨阵营） |
| 跨阵营不校验 | ✓✓ 实机 | 同上，终结族 presence 挂在 illuminate 星球 |
| kind∈{0,3} 的表内其余条目可注入 | ⚠ 未证 | 同一通道、同一解析路径，但未逐条实测 |
| 本地无对应 presence 的 5 条 | ⚠ 未证 | 预期客户端解析失败、无显示 |

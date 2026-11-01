# GWE 全量效果表 + planetActiveEffects（warId 801）

> 目录：`fb1b64f6_api_WarSeason_GalacticWarEffects.json` + `71efaac9_api_WarSeason_GalacticWarEffects.json`（并集 **312** 条）
> 在线快照：`013ec696_api_WarSeason_801_Status.json`（**139** 条 planetActiveEffects，273 颗星球）；历史快照 69 份
> 名称/描述：`refs/strings-en-26088801.json`（24,834 条 locid）；presence 行与 modifier 行均为本地明文表。
> 机读版：`out/gwe/effects-full.csv`、`out/gwe/planet-active-effects.csv`（`out/` 含账号 id，本地生成不入库）；生成器 `tools/gwe_full_table.py`（可重跑）。
> presence 视角的可注入菜单见 [EFFECT-MENU-801](EFFECT-MENU-801.md)；本文档是全类型总表。

## 1. 覆盖

| 项 | 数 |
|---|---:|
| 目录效果 | 312 |
| 有官方名称（nameHash 解出） | 174 |
| 有官方描述（short/long） | 166 |
| 目标解到具名对象（presence/战备/modifier 行） | 176 |
| 只有名称/描述（值语义未解） | 38 |
| 全 raw（名称/描述/目标都没有） | 98 |
| 当前在线效果（不同 id） | 65 |
| 在线条目（planetActiveEffects） | 139 |
| 出现在历史任何快照 | 66 |

## 1.5 在线快照按类型

| type | 语义 | 在线条目 | 不同 effect |
|---:|---|---:|---:|
| 21 | 数值参数（如 AERIAL DOMINANCE：撤离时间 -N 秒） | 4 | 2 |
| 23 | 数值参数（⚠ 数值语义未解） | 5 | 2 |
| 32 | 临时配发战备（values[0] = 战备 hash）✓ | 2 | 2 |
| 36 | DSS 空间站临时装备/加成（values[0]=hash，values[1]=百分比）✓ | 1 | 1 |
| 40 | 星图词条 tag（hash，与 type71 成对出现）✓ | 27 | 13 |
| 56 | ⚠ 百分比参数（#AMOUNT，战场弹药量） | 6 | 3 |
| 69 | ⚠ 数值（未解） | 3 | 2 |
| 71 | presence 引用（values[0] = murmur32(presence 名)）✓✓ | 64 | 36 |
| 73 | ⚠ 双数值（17 条边缘，未解） | 13 | 2 |
| 76 | ⚠ 无参（未解） | 9 | 1 |
| 92 | ⚠ 无参（未解） | 5 | 1 |

## 1.6 当前在线里的关键条目

- **type32 在线 2 条**：effect 1279 on 星球 82（URSICA XI）、effect 1427 on 星球 158（CHOEPESSA IV）。其中 `1427` 是**未发布战备**的临时配发（`WEAPONS EXPERIMENTATION` / 战备 hash `0x166D0C91`，本地明文表 0 命中）⇒ 属于「服务器清单领先客户端」的实例，客户端大概率解析不出该战备。
- **type71 presence 在线 64 条**（36 个不同 presence）——这是星图卡/作战界面的主体。
- **type40 tag 在线 27 条**（13 个不同 tag）；tag 与 presence 成对出现，但 tag hash 与 presence 键不是同一命名空间。
- 其余在线类型：type 21×4、type 23×5、type 36×1、type 56×6、type 69×3、type 73×13、type 76×9、type 92×5（多数是数值/未解解释器，见 §2）。

## 2. 类型语义表

| type | 语义 | 条数 | 有名称 | 目标已解 | raw | 在线 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 数值参数（ENEMY FORCE INCREASE 等，数值语义未解） | 6 | 3 | 0 | 3 | 0 |
| 21 | 数值参数（如 AERIAL DOMINANCE：撤离时间 -N 秒） | 12 | 6 | 0 | 6 | 2 |
| 23 | 数值参数（⚠ 数值语义未解） | 9 | 1 | 0 | 8 | 2 |
| 24 | ⚠ 未证/未解 | 1 | 0 | 0 | 1 | 0 |
| 25 | 数值参数（如 INCREASED STARTING AMMO） | 6 | 2 | 0 | 4 | 0 |
| 29 | 数值开关（⚠ 未证） | 1 | 0 | 0 | 1 | 0 |
| 32 | 临时配发战备（values[0] = 战备 hash）✓ | 88 | 73 | 84 | 0 | 2 |
| 36 | DSS 空间站临时装备/加成（values[0]=hash，values[1]=百分比）✓ | 16 | 2 | 12 | 3 | 1 |
| 40 | 星图词条 tag（hash，与 type71 成对出现）✓ | 14 | 0 | 0 | 14 | 13 |
| 43 | ⚠ 数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 44 | ⚠ 数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 45 | ⚠ hash（描述=ADDITIONAL PAYOUT） | 1 | 1 | 0 | 0 | 0 |
| 46 | ⚠ 数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 47 | 全局 modifier（无参，按名生效）✓ | 1 | 1 | 1 | 0 | 0 |
| 48 | 全局 modifier（无参，按名生效）✓ | 1 | 1 | 1 | 0 | 0 |
| 49 | ⚠ 双数值（攻击强度） | 6 | 6 | 0 | 0 | 0 |
| 50 | ⚠ 双 hash（未解） | 2 | 0 | 0 | 2 | 0 |
| 51 | ⚠ 双数值（EXPERIMENTAL SUPER SOLDIERS） | 1 | 1 | 0 | 0 | 0 |
| 54 | ⚠ 无参（INTEL SCANNERS） | 1 | 1 | 1 | 0 | 0 |
| 55 | ⚠ 无参（COMPROMISED INTEL PACKAGES） | 1 | 1 | 1 | 0 | 0 |
| 56 | ⚠ 百分比参数（#AMOUNT，战场弹药量） | 7 | 3 | 0 | 4 | 3 |
| 59 | ⚠ hash（ACCOUNTING CORRECTIONS 等） | 2 | 1 | 0 | 1 | 0 |
| 61 | ⚠ 数值（医疗补给） | 2 | 1 | 0 | 1 | 0 |
| 63 | ⚠ 数值（PLENTYFUL STIMS） | 1 | 1 | 0 | 0 | 0 |
| 67 | ⚠ 数值（MARKET CRASH） | 1 | 1 | 0 | 0 | 0 |
| 69 | ⚠ 数值（未解） | 3 | 1 | 0 | 2 | 2 |
| 70 | ⚠ hash（未解） | 3 | 0 | 0 | 3 | 0 |
| 71 | presence 引用（values[0] = murmur32(presence 名)）✓✓ | 76 | 58 | 71 | 5 | 36 |
| 72 | ⚠ hash+数值（15 条，未解） | 15 | 0 | 0 | 15 | 0 |
| 73 | ⚠ 双数值（17 条边缘，未解） | 5 | 0 | 0 | 5 | 2 |
| 74 | ⚠ 数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 76 | ⚠ 无参（未解） | 1 | 0 | 0 | 1 | 1 |
| 77 | ⚠ 数值（未解） | 4 | 0 | 0 | 4 | 0 |
| 80 | ⚠ 数值（未解） | 2 | 0 | 0 | 2 | 0 |
| 83 | ⚠ hash（booster 自动生效） | 3 | 1 | 0 | 2 | 0 |
| 87 | DSS 轨道支援效果（PLANETARY BOMBARDMENT / EAGLE STORM）✓ | 3 | 3 | 0 | 0 | 0 |
| 88 | ⚠ 数值（EAGLE STORM 防守进度） | 1 | 1 | 0 | 0 | 0 |
| 89 | ⚠ 无参（ORBITAL BLOCKADE） | 1 | 1 | 1 | 0 | 0 |
| 90 | ⚠ 数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 92 | ⚠ 无参（未解） | 1 | 0 | 1 | 0 | 1 |
| 93 | ⚠ hash+数值（未解） | 1 | 0 | 0 | 1 | 0 |
| 94 | 行星实验性战备变体修饰符（values[0] = generated_modifier_settings 行键）✓✓ | 3 | 3 | 3 | 0 | 0 |
| 95 | ⚠ hash+数值（未解） | 2 | 0 | 0 | 2 | 0 |
| 96 | ⚠ hash（未解） | 2 | 0 | 0 | 2 | 0 |
| 97 | ⚠ hash（未解） | 1 | 0 | 0 | 1 | 0 |

## 3. 全量目录（312 条）

| effect | type | 名称 | 目标/解码 | 在线 |
|---:|---:|---|---|---:|
| 1 | 43 |  |  | — |
| 5 | 1 | ENEMY FORCE INCREASE |  | — |
| 8 | 44 |  |  | — |
| 12 | 45 | ADDITIONAL PAYOUT |  | — |
| 13 | 46 |  |  | — |
| 55 | 25 | INCREASED STARTING AMMO |  | — |
| 67 | 51 | EXPERIMENTAL SUPER SOLDIERS |  | — |
| 70 | 54 | INTEL SCANNERS | 无参 | — |
| 71 | 55 | COMPROMISED INTEL PACKAGES | 无参 | — |
| 76 | 47 | IMPENETRABLE DEFENSE | 无参 | — |
| 77 | 48 | CRIPPLED SUPPLY | 无参 | — |
| 80 | 49 | MINOR ATTACK INCREASE |  | — |
| 87 | 56 | MORE BATTLEFIELD AMMO |  | — |
| 95 | 21 |  |  | — |
| 102 | 49 | LARGE ATTACK INCREASE |  | — |
| 103 | 49 | ATTACK INCREASE |  | — |
| 104 | 49 | SUBSTANTIAL ATTACK INCREASE |  | — |
| 105 | 49 | MAJOR ATTACK INCREASE |  | — |
| 106 | 49 | MASSIVE ATTACK INCREASE |  | — |
| 113 | 63 | PLENTYFUL STIMS |  | — |
| 114 | 56 | LESS BATTLEFIELD AMMO |  | — |
| 121 | 67 | MARKET CRASH |  | — |
| 1126 | 29 |  |  | — |
| 1127 | 32 |  | stratagem:飞鹰500千克炸弹 | — |
| 1128 | 32 |  | stratagem:飞鹰500千克炸弹 | — |
| 1129 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道激光炮 | — |
| 1130 | 32 | WEAPONS EXPERIMENTATION | stratagem:MG-206 重机枪 | — |
| 1131 | 50 |  |  | — |
| 1132 | 50 |  |  | — |
| 1133 | 32 |  | stratagem:A/M-23 电磁迫击炮哨戒炮 | — |
| 1134 | 25 |  |  | — |
| 1135 | 36 |  | DSS 临时装备:RS-422 轨道炮 | — |
| 1136 | 1 |  |  | — |
| 1137 | 32 | WEAPONS EXPERIMENTATION | stratagem:RS-422 轨道炮 | — |
| 1138 | 59 |  |  | — |
| 1139 | 32 |  | stratagem:飞鹰凝固汽油弹空袭 | — |
| 1140 | 25 |  |  | — |
| 1141 | 1 |  |  | — |
| 1142 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰500千克炸弹 | — |
| 1143 | 32 | WEAPONS EXPERIMENTATION | stratagem:MG-43 机枪 | — |
| 1144 | 25 | AMMO SHORTAGE |  | — |
| 1145 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道激光炮 | — |
| 1147 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道电磁冲击波攻击 | — |
| 1148 | 32 |  | stratagem:EXO-45 爱国者外骨骼装甲 | — |
| 1149 | 32 | EQUIPMENT TESTING | stratagem:LIFT-850 喷气背包 | — |
| 1150 | 32 | EQUIPMENT TESTING | stratagem:B-1 补给背包 | — |
| 1152 | 32 | WEAPONS EXPERIMENTATION | stratagem:APW-1 反器材步枪 | — |
| 1153 | 32 | WEAPONS EXPERIMENTATION | stratagem:RS-422 轨道炮 | — |
| 1154 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道炮攻击 | — |
| 1155 | 32 | WEAPONS EXPERIMENTATION | stratagem:AC-8 机炮 | — |
| 1156 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰110毫米火箭巢 | — |
| 1159 | 59 | ACCOUNTING CORRECTIONS |  | — |
| 1160 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道电磁冲击波攻击 | — |
| 1161 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰凝固汽油弹空袭 | — |
| 1162 | 32 | WEAPONS EXPERIMENTATION | stratagem:EXO-45 爱国者外骨骼装甲 | — |
| 1163 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰110毫米火箭巢 | — |
| 1165 | 32 | WEAPONS EXPERIMENTATION | stratagem:LIFT-850 喷气背包 | — |
| 1166 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰500千克炸弹 | — |
| 1167 | 32 | WEAPONS EXPERIMENTATION | stratagem:FLAM-40 火焰喷射器 | — |
| 1168 | 32 | WEAPONS EXPERIMENTATION | stratagem:LAS-99 类星体加农炮 | — |
| 1169 | 32 | WEAPONS EXPERIMENTATION | stratagem:EAT-17 消耗性反坦克武器 | — |
| 1170 | 32 | WEAPONS EXPERIMENTATION | stratagem:RL-77 空爆火箭筒 | — |
| 1171 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-17 反坦克地雷 | — |
| 1172 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道毒气攻击 | — |
| 1173 | 32 | WEAPONS EXPERIMENTATION | stratagem:EXO-49 解放者外骨骼装甲 | — |
| 1174 | 32 | WEAPONS EXPERIMENTATION | stratagem:A/M-23 电磁迫击炮哨戒炮 | — |
| 1175 | 32 | WEAPONS EXPERIMENTATION | 战备 hash 0x3A460EA5；本地明文表无此键（未发布/无本地行） | — |
| 1176 | 70 |  |  | — |
| 1177 | 70 |  |  | — |
| 1178 | 32 | WEAPONS EXPERIMENTATION | stratagem:FX-12 防护罩生成中继器 | — |
| 1179 | 32 | WEAPONS EXPERIMENTATION | stratagem:AC-8 机炮 | — |
| 1181 | 32 | WEAPONS EXPERIMENTATION | stratagem:MLS-4X 突击兵 | — |
| 1182 | 21 | AERIAL DOMINANCE |  | — |
| 1186 | 73 |  |  | — |
| 1187 | 73 |  |  | — |
| 1188 | 73 |  |  | 8 |
| 1189 | 73 |  |  | — |
| 1190 | 76 |  |  | 9 |
| 1191 | 72 |  |  | — |
| 1192 | 72 |  |  | — |
| 1193 | 73 |  |  | 5 |
| 1194 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道凝固汽油弹火力网 | — |
| 1195 | 71 | DSS CONSTRUCTION SITE - PHASE 1 | presence:democracy_station_phase_1 | — |
| 1196 | 71 | DSS LOGISTICS HUB | presence:civilian_cargo | — |
| 1197 | 71 | XENOENTOMOLOGY CENTER | presence:research_bio_research | 1 |
| 1198 | 71 | DEEP MANTLE FORGE COMPLEX | presence:manufacturing_forge | 1 |
| 1199 | 71 | DSS CONSTRUCTION SITE - PHASE 2 | presence:democracy_station_phase_2 | — |
| 1200 | 32 | WEAPONS EXPERIMENTATION | stratagem:A/ARC-3 特斯拉塔 | — |
| 1201 | 70 |  |  | — |
| 1202 | 40 |  |  | 2 |
| 1203 | 71 | THE JET BRIGADE | presence:elite_bot_jumpattack | — |
| 1204 | 71 | LIBERTY DAY CELEBRATION | presence:liberty_day | — |
| 1205 | 71 | DSS CONSTRUCTION SITE - PHASE 3 | presence:democracy_station_phase_3 | — |
| 1206 | 71 | TERMINID RESEARCH PRESERVE | presence:military_tower | — |
| 1207 | 32 | WEAPONS EXPERIMENTATION | stratagem:E/MG-101 重机枪炮台 | — |
| 1208 | 87 | PLANETARY BOMBARDMENT |  | — |
| 1209 | 87 | EAGLE STORM |  | — |
| 1210 | 83 | ORBITAL BLOCKADE |  | — |
| 1211 | 71 | PLANETARY BOMBARDMENT | presence:tactical_action_planetary_bombardment | — |
| 1212 | 71 | EAGLE STORM | presence:tactical_action_eagle_storm | — |
| 1213 | 71 | ORBITAL BLOCKADE | presence:tactical_action_defensive_lockdown | — |
| 1214 | 1 | PLANETARY BOMBARDMENT |  | — |
| 1215 | 89 | ORBITAL BLOCKADE | 无参 | — |
| 1216 | 88 | EAGLE STORM |  | — |
| 1217 | 71 | DEMOCRACY SPACE STATION | presence:democracy_station_final | — |
| 1218 | 74 |  |  | — |
| 1219 | 77 |  |  | — |
| 1220 | 77 |  |  | — |
| 1222 | 77 |  |  | — |
| 1223 | 83 |  |  | — |
| 1224 | 83 |  |  | — |
| 1225 | 1 |  |  | — |
| 1226 | 32 | WEAPONS EXPERIMENTATION | stratagem:FAF-14 飞矛 | — |
| 1227 | 32 | WEAPONS EXPERIMENTATION | stratagem:MG-43 机枪 | — |
| 1228 | 71 | MERIDIAN BLACK HOLE | presence:black_hole | — |
| 1229 | 71 | MERIDIAN BLACK HOLE | presence:black_hole_intensified | 1 |
| 1230 | 71 | MERIDIAN BLACK HOLE | presence:black_hole_travel_blocked | — |
| 1231 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-8 毒气地雷 | — |
| 1232 | 71 | FACTORY HUB | presence:manufacturing_generic | 1 |
| 1233 | 32 | WEAPONS EXPERIMENTATION | stratagem:StA-X3 W.A.S.P. 发射器 | — |
| 1234 | 71 | CENTER OF SCIENCE | presence:research_generic | 1 |
| 1235 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-17 反坦克地雷 | — |
| 1236 | 71 | CENTER FOR CIVILIAN SURVEILLANCE AND SAFETY | presence:civilian_surveillance | 1 |
| 1237 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道380毫米高爆火力网 | — |
| 1238 | 1 | OPERATIONAL SUPPORT |  | — |
| 1239 | 71 | JET BRIGADE FACTORIES | presence:bot_facility_jetbrigade | 1 |
| 1240 | 71 |  | presence:planet_at_risk | — |
| 1241 | 71 | FRACTURED PLANET | presence:destroyed_by_black_hole | 1 |
| 1242 | 71 |  | presence:travel_path_to_super_earth | — |
| 1243 | 40 |  |  | 1 |
| 1244 | 40 |  |  | 1 |
| 1245 | 71 | PREDATOR STRAIN | presence:bugs_super_predator | 1 |
| 1246 | 92 |  | 无参 | 5 |
| 1247 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-8 毒气地雷 | — |
| 1248 | 40 |  |  | 4 |
| 1249 | 71 | THE INCINERATION CORPS | presence:bots_ivory_legion | 4 |
| 1250 | 23 |  |  | — |
| 1251 | 23 |  |  | — |
| 1252 | 71 | FRACTURED PLANET | presence:destroyed_by_black_hole | 2 |
| 1253 | 24 |  |  | — |
| 1254 | 32 | WEAPONS EXPERIMENTATION | stratagem:MG-206 重机枪 | — |
| 1255 | 77 |  |  | — |
| 1256 | 32 | WEAPONS EXPERIMENTATION | stratagem:E/GL-21 掷弹兵阵地 | — |
| 1257 | 56 |  |  | — |
| 1258 | 69 |  |  | — |
| 1261 | 36 | EXOSUIT RESERVES | DSS 临时装备:EXO-45 爱国者外骨骼装甲 | — |
| 1262 | 36 |  | DSS 临时装备:EXO-49 解放者外骨骼装甲 | — |
| 1263 | 32 | WEAPONS EXPERIMENTATION | stratagem:M-105 盟友 | — |
| 1264 | 80 |  |  | — |
| 1265 | 36 |  | DSS 临时装备:M-102 快速侦察载具 | — |
| 1267 | 32 |  | stratagem:轨道毒气攻击 | — |
| 1268 | 71 | NEGATIVE ENERGY LABORATORY | presence:research_energy_lab | — |
| 1269 | 71 | The Great Host | presence:illuminate_fleet | — |
| 1270 | 93 |  |  | — |
| 1271 | 90 |  |  | — |
| 1272 | 69 |  |  | 1 |
| 1273 | 23 |  |  | — |
| 1274 | 32 |  | stratagem:M-105 盟友 | — |
| 1275 | 36 |  |  | — |
| 1276 | 32 | WEAPONS EXPERIMENTATION | stratagem:FX-12 防护罩生成中继器 | — |
| 1277 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道凝固汽油弹火力网 | — |
| 1278 | 25 |  |  | — |
| 1279 | 32 | WEAPONS EXPERIMENTATION | stratagem:M-102 快速侦察载具 | 1 |
| 1280 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道烟雾攻击 | — |
| 1281 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰烟雾攻击 | — |
| 1282 | 71 | HELLDIVER TRAINING FACILITIES | presence:military_helldiver_training | 1 |
| 1283 | 72 |  |  | — |
| 1284 | 32 |  | stratagem:GR-8 无后座力步枪 | — |
| 1285 | 72 |  |  | — |
| 1286 | 71 | NEW HOPE CONSTRUCTION SITE | presence:construction_hope | — |
| 1287 | 71 | NEW HOPE CITY | presence:completed_hope | 1 |
| 1288 | 72 |  |  | — |
| 1289 | 36 |  | DSS 临时装备:轨道炮攻击 | — |
| 1291 | 71 | NEW ASPIRATION CITY | presence:completed_aspiration | 1 |
| 1292 | 71 | NEW YEARNING CITY | presence:completed_yearning | 1 |
| 1293 | 72 |  |  | — |
| 1294 | 72 |  |  | — |
| 1295 | 71 | TYRANNY PARK 2 | presence:civilian_bug_park | — |
| 1296 | 72 |  |  | — |
| 1297 | 72 |  |  | — |
| 1298 | 36 |  | DSS 临时装备:M-102 快速侦察载具 | — |
| 1299 | 21 |  |  | — |
| 1300 | 25 |  |  | — |
| 1301 | 32 |  | stratagem:A/G-16 加特林哨戒炮 | — |
| 1302 | 32 |  | stratagem:AX/LAS-5 护卫犬漫游者 | — |
| 1303 | 40 |  |  | 2 |
| 1304 | 71 |  |  | 1 |
| 1305 | 21 |  |  | — |
| 1306 | 40 |  |  | 3 |
| 1307 | 40 |  |  | 2 |
| 1308 | 71 | HIVE LORDS | presence:bugs_hive_lord | 2 |
| 1309 | 71 | DRAGONROACHES | presence:bugs_dragon | 3 |
| 1310 | 71 | RUPTURE STRAIN | presence:bugs_burrower | 2 |
| 1311 | 71 |  |  | 2 |
| 1312 | 21 | LIGHT GLOOM COVER |  | — |
| 1313 | 21 | MODERATE GLOOM BLANKET |  | — |
| 1314 | 23 |  |  | — |
| 1315 | 21 | HEAVY GLOOM SHROUD |  | 3 |
| 1316 | 23 |  |  | 3 |
| 1317 | 56 |  |  | 3 |
| 1318 | 69 | GLOOM SOURCE |  | 2 |
| 1319 | 56 |  |  | 2 |
| 1320 | 23 |  |  | 2 |
| 1321 | 21 |  |  | — |
| 1322 | 21 |  |  | — |
| 1323 | 23 |  |  | — |
| 1324 | 71 | ULTRAMAFIC MINE | presence:manufacturing_industry | 1 |
| 1325 | 23 |  |  | — |
| 1326 | 21 |  |  | — |
| 1327 | 71 |  |  | 1 |
| 1328 | 32 |  | stratagem:RL-77 空爆火箭筒 | — |
| 1329 | 71 | LIBERTY DAY CELEBRATION | presence:liberty_day | — |
| 1330 | 71 |  | presence:fireworks | — |
| 1331 | 32 | WEAPONS EXPERIMENTATION | stratagem:CQC-1（One True Flag） | — |
| 1332 | 32 |  | stratagem:LIFT-182 跃迁背包 | — |
| 1333 | 71 |  |  | 1 |
| 1334 | 32 |  | stratagem:LAS-98 激光大炮 | — |
| 1335 | 32 |  | stratagem:轨道游走火力网 | — |
| 1336 | 56 |  |  | — |
| 1337 | 36 |  | DSS 临时装备:轨道烟雾攻击 | — |
| 1338 | 36 |  | DSS 临时装备:M-102 快速侦察载具 | — |
| 1339 | 36 |  | DSS 临时装备:EXO-45 爱国者外骨骼装甲 | — |
| 1340 | 36 |  | DSS 临时装备:EXO-49 解放者外骨骼装甲 | — |
| 1341 | 71 |  |  | — |
| 1342 | 71 | CENTER FOR THE CONFINEMENT OF DISSIDENCE (CECOD) | presence:dissident_prison | — |
| 1343 | 32 |  | stratagem:飞鹰凝固汽油弹空袭 | — |
| 1344 | 71 | PANDORA BASE | presence:dss_augmentation | 1 |
| 1345 | 94 | ORBITAL 120MM HE/EMS BARRAGE | modifier 行 #6 | — |
| 1346 | 94 | INCENDIARY GATLING BARRAGE | modifier 行 #2 | — |
| 1347 | 32 | WEAPONS EXPERIMENTATION | stratagem:LIFT-860 悬浮背包 | — |
| 1348 | 32 | WEAPONS EXPERIMENTATION | stratagem:GL-52（De-Escalator） | — |
| 1349 | 32 | WEAPONS EXPERIMENTATION | stratagem:AX/ARC-3（K-9） | — |
| 1350 | 94 | SMOKE-ENHANCED WALKING BARRAGE  | modifier 行 #14 | — |
| 1351 | 32 | WEAPONS EXPERIMENTATION | stratagem:PORTABLE HELLBOMB | — |
| 1352 | 71 | CONVENTIONAL BLACK HOLE | presence:destroyed_by_death_laser | 1 |
| 1353 | 71 | DATA CENTER | presence:bot_facility_data | 1 |
| 1354 | 72 |  |  | — |
| 1355 | 71 | HEAVY ARMOR SURGE | presence:bots_increased_warstriders | — |
| 1356 | 72 |  |  | — |
| 1357 | 71 | HULK SURGE | presence:bots_increased_hulks | — |
| 1358 | 72 |  |  | — |
| 1359 | 71 | DEVASTATOR SURGE | presence:bots_increased_devastators | — |
| 1360 | 40 |  |  | 3 |
| 1361 | 71 | CYBORGS | presence:bots_cyborgs | 3 |
| 1362 | 71 |  | presence:bot_battle_intense | — |
| 1363 | 21 | PILOT SHORTAGE |  | 1 |
| 1364 | 21 | AERIAL DOMINANCE |  | — |
| 1365 | 36 | ORBITAL FLUCTUATIONS |  | 1 |
| 1366 | 56 | LESS BATTLEFIELD AMMO |  | 1 |
| 1367 | 61 | MEDICAL SUPPLY STRAIN |  | — |
| 1368 | 80 |  |  | — |
| 1369 | 61 |  |  | — |
| 1370 | 23 | SLOWER EAGLE REARM |  | — |
| 1371 | 72 |  |  | — |
| 1373 | 71 | CLASS 1 EXOSTORM | presence:illuminate_ritual_storm_lvl1 | — |
| 1374 | 71 | CLASS 2 EXOSTORM | presence:illuminate_ritual_storm_lvl2 | — |
| 1375 | 71 | CLASS 3 EXOSTORM | presence:illuminate_ritual_storm_lvl3 | — |
| 1376 | 71 |  | presence:illuminate_rift | — |
| 1377 | 40 |  |  | 2 |
| 1378 | 71 | MINDLESS MASSES | presence:illuminate_harvester | 2 |
| 1379 | 71 | APPROPRIATORS | presence:illuminate_engineer | 1 |
| 1380 | 40 |  |  | 1 |
| 1381 | 95 |  |  | — |
| 1382 | 95 |  |  | — |
| 1383 | 32 | WEAPONS EXPERIMENTATION | stratagem:轨道加特林（普通型） | — |
| 1384 | 36 |  |  | — |
| 1385 | 36 |  |  | — |
| 1386 | 71 | SPORE BURST STRAIN | presence:bugs_gloom | 1 |
| 1387 | 71 | COMMUNICATIONS ARRAY | presence:bot_facility_comms | 1 |
| 1388 | 32 | WEAPONS EXPERIMENTATION | stratagem:CQC-1（One True Flag） | — |
| 1389 | 32 | WEAPONS EXPERIMENTATION | stratagem:DARK FLUID VESSEL | — |
| 1390 | 32 | WEAPONS EXPERIMENTATION | stratagem:CQC-20（Breaching Hammer） | — |
| 1392 | 32 | WEAPONS EXPERIMENTATION | stratagem:M-103（Supply FRV） | — |
| 1393 | 32 | WEAPONS EXPERIMENTATION | stratagem:M-104（Incinerator FRV） | — |
| 1394 | 36 |  | DSS 临时装备:轨道毒气攻击 | — |
| 1395 | 71 | TERMINID CONTROL SYSTEM+ | presence:tcs_wall | 14 |
| 1396 | 71 |  | presence:bug_tcs_towers | — |
| 1397 | 32 | WEAPONS EXPERIMENTATION | stratagem:AX/TX-13（Dog Breath） | — |
| 1398 | 32 | WEAPONS EXPERIMENTATION | stratagem:A/GM-17 毒气迫击炮哨戒炮 | — |
| 1399 | 32 | WEAPONS EXPERIMENTATION | stratagem:TX-41 灭菌者 | — |
| 1400 | 71 | Heavy SEAF Presence | presence:seaf | 3 |
| 1401 | 40 |  |  | 3 |
| 1402 | 40 |  |  | 2 |
| 1403 | 71 | VOTE SNATCHERS | presence:illuminate_bodyhorror | 2 |
| 1404 | 96 |  |  | — |
| 1405 | 96 |  |  | — |
| 1406 | 97 |  |  | — |
| 1407 | 71 | VOID GATEWAY | presence:illuminate_rift_sideboard_gate | — |
| 1408 | 71 |  | presence:illuminate_rift_mesh | — |
| 1409 | 71 |  | presence:illuminate_rift_other_planets | — |
| 1410 | 71 |  | presence:void_cluster_one | — |
| 1411 | 71 |  | presence:void_cluster_two | — |
| 1412 | 71 |  | presence:operation_rift_source | — |
| 1413 | 40 |  |  | 1 |
| 1414 | 71 | INVASION FLEET | presence:illuminate_invading | 1 |
| 1415 | 72 |  |  | — |
| 1416 | 32 | WEAPONS EXPERIMENTATION | stratagem:SH-32 防护罩生成背包 | — |
| 1417 | 71 |  | presence:illuminate_rift | — |
| 1418 | 71 |  | presence:force_evacuate | 1 |
| 1419 | 32 | WEAPONS EXPERIMENTATION | stratagem:飞鹰毒气攻击 | — |
| 1420 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-6 反步兵雷区 | — |
| 1421 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-I4 燃烧地雷 | — |
| 1422 | 32 | WEAPONS EXPERIMENTATION | stratagem:MD-8 毒气地雷 | — |
| 1423 | 32 | WEAPONS EXPERIMENTATION | stratagem:TD-110（Maelstrom） | — |
| 1424 | 36 |  | DSS 临时装备:TD-110（Maelstrom） | — |
| 1425 | 87 | EAGLE STORM |  | — |
| 1426 | 32 | WEAPONS EXPERIMENTATION | 战备 hash 0x8DFA4622；本地明文表无此键（未发布/无本地行） | — |
| 1427 | 32 | WEAPONS EXPERIMENTATION | 战备 hash 0x166D0C91；本地明文表无此键（未发布/无本地行） | 1 |
| 1428 | 32 | WEAPONS EXPERIMENTATION | 战备 hash 0x0C064A00；本地明文表无此键（未发布/无本地行） | — |
| 1429 | 72 |  |  | — |
| 1430 | 40 |  |  | — |
| 1431 | 71 | CAUSTIC STRAIN | presence:bugs_acid | — |

## 4. 当前在线：planetActiveEffects 快照

`013ec696_api_WarSeason_801_Status.json`：139 条，逐星球展开（同星球多效果合并一行）。

| 星球 | owner | 效果（id=名称） |
|---:|---|---|
| 7 ZEA RUGOSIA | illuminate | 1402=tag hash 0xFD8B9706（星图词条）、1403=VOTE SNATCHERS、1413=tag hash 0x33FA1AB8（星图词条）、1414=INVASION FLEET |
| 16 FORT UNION | SE | 1287=NEW HOPE CITY |
| 22 ZEGEMA PARADISE | SE | 1282=HELLDIVER TRAINING FACILITIES |
| 32 FORT SANCTUARY | SE | 1292=NEW YEARNING CITY |
| 34 HELLMIRE | SE | 1304=presence 键 0x9673F0E3 本地无对应行 |
| 42 EMERIA | SE | 1291=NEW ASPIRATION CITY |
| 45 MASTIA | SE | 1236=CENTER FOR CIVILIAN SURVEILLANCE AND、1272 |
| 51 IVIS | SE | 1252=FRACTURED PLANET |
| 64 MERIDIA | SE | 1229=MERIDIAN BLACK HOLE |
| 75 ESKER | SE | 1188、1193、1244=tag hash 0xA3A3DB9F（星图词条）、1306=tag hash 0x9FD5943A（星图词条）、1309=DRAGONROACHES、1315=HEAVY GLOOM SHROUD、1316、1317、1386=SPORE BURST STRAIN |
| 76 TERREK | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 78 CRIMSICA | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 82 URSICA XI | SE | 1279=WEAPONS EXPERIMENTATION |
| 85 MORADESH | SE | 1252=FRACTURED PLANET |
| 92 GRAFMERE | illuminate | 1327=presence 键 0xAD84E681 本地无对应行 |
| 97 CALYPSO | SE | 1190、1418=presence:force_evacuate |
| 114 AURORA BAY | automaton | 1239=JET BRIGADE FACTORIES、1363=PILOT SHORTAGE |
| 115 PENTA | SE | 1246=无参、1352=CONVENTIONAL BLACK HOLE |
| 122 ERSON SANDS | terminid | 1193、1246=无参、1315=HEAVY GLOOM SHROUD、1316、1317 |
| 123 SOCORRO III | terminid | 1188、1193、1315=HEAVY GLOOM SHROUD、1316、1317 |
| 124 BORE ROCK | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 125 FENRIR III | SE | 1234=CENTER OF SCIENCE |
| 126 TURING | SE | 1197=XENOENTOMOLOGY CENTER、1366=LESS BATTLEFIELD AMMO、1395=TERMINID CONTROL SYSTEM+ |
| 127 ANGEL'S VENTURE | SE | 1241=FRACTURED PLANET |
| 128 DARIUS II | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 130 ACHERNAR SECUNDUS | SE | 1232=FACTORY HUB、1395=TERMINID CONTROL SYSTEM+ |
| 131 ACHIRD III | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 136 AFOYAY BAY | SE | 1344=PANDORA BASE |
| 137 AIN-5 | SE | 1379=APPROPRIATORS、1380=tag hash 0xE2136DAA（星图词条） |
| 144 BELLATRIX | illuminate | 1400=Heavy SEAF Presence、1401=tag hash 0xBA586F51（星图词条） |
| 158 CHOEPESSA IV | automaton | 1202=tag hash 0xAE2ED4E9（星图词条）、1202=tag hash 0xAE2ED4E9（星图词条）、1360=tag hash 0x08766602（星图词条）、1361=CYBORGS、1400=Heavy SEAF Presence、1401=tag hash 0xBA586F51（星图词条）、1427=WEAPONS EXPERIMENTATION |
| 160 CHORT BAY | SE | 1365=ORBITAL FLUCTUATIONS |
| 161 CLAORELL | SE | 1198=DEEP MANTLE FORGE COMPLEX |
| 162 CLASA | SE | 1353=DATA CENTER |
| 166 ENULIALE | terminid | 1190、1193 |
| 167 EPSILON PHOENCIS VI | terminid | 1188、1190 |
| 168 ERATA PRIME | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 170 FORI PRIME | SE | 1243=tag hash 0x89E4FC2A（星图词条）、1245=PREDATOR STRAIN、1395=TERMINID CONTROL SYSTEM+ |
| 175 GRAND ERRANT | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 185 KARLIA | SE | 1402=tag hash 0xFD8B9706（星图词条）、1403=VOTE SNATCHERS |
| 201 MEISSA | automaton | 1387=COMMUNICATIONS ARRAY |
| 204 MERAK | SE | 1246=无参 |
| 207 MINTORIA | SE | 1324=ULTRAMAFIC MINE |
| 209 NABATEA SECUNDUS | terminid | 1188、1190 |
| 210 NAVI VII | terminid | 1188、1190 |
| 211 NIVEL 43 | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 212 OSHAUNE | SE | 1303=tag hash 0x907204FE（星图词条）、1306=tag hash 0x9FD5943A（星图词条）、1307=tag hash 0x194C725F（星图词条）、1308=HIVE LORDS、1309=DRAGONROACHES、1310=RUPTURE STRAIN、1333=presence 键 0x155A353F 本地无对应行 |
| 215 PARTION | terminid | 1303=tag hash 0x907204FE（星图词条）、1310=RUPTURE STRAIN |
| 218 PHERKAD SECUNDUS | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 231 SIEMNOT | illuminate | 1377=tag hash 0x021B60B3（星图词条）、1378=MINDLESS MASSES |
| 244 VARYLIA 5 | SE | 1248=tag hash 0x658544D8（星图词条）、1249=THE INCINERATION CORPS |
| 245 WASAT | SE | 1248=tag hash 0x658544D8（星图词条）、1249=THE INCINERATION CORPS |
| 246 VEGA BAY | SE | 1248=tag hash 0x658544D8（星图词条）、1249=THE INCINERATION CORPS |
| 253 ZZANIAH PRIME | automaton | 1360=tag hash 0x08766602（星图词条）、1361=CYBORGS |
| 256 DIASPORA X | terminid | 1190、1193 |
| 257 GEMSTONE BLUFFS | terminid | 1188、1190 |
| 258 ZAGON PRIME | terminid | 1188、1246=无参、1311=presence 键 0xCAC0CD4E 本地无对应行、1318=GLOOM SOURCE、1319、1320 |
| 259 OMICRON | terminid | 1188、1306=tag hash 0x9FD5943A（星图词条）、1307=tag hash 0x194C725F（星图词条）、1308=HIVE LORDS、1309=DRAGONROACHES、1311=presence 键 0xCAC0CD4E 本地无对应行、1318=GLOOM SOURCE、1319、1320、1400=Heavy SEAF Presence、1401=tag hash 0xBA586F51（星图词条） |
| 260 CYBERSTAN | automaton | 1246=无参、1360=tag hash 0x08766602（星图词条）、1361=CYBORGS |
| 261 FURY | SE | 1248=tag hash 0x658544D8（星图词条）、1249=THE INCINERATION CORPS |
| 264 NEW INSIGHT | SE | 1190 |
| 265 WAYWARD | SE | 1190 |
| 269 BRILLIANCE | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 270 FRONTERIA | SE | 1395=TERMINID CONTROL SYSTEM+ |
| 272 BASQUINE VIII | SE | 1377=tag hash 0x021B60B3（星图词条）、1378=MINDLESS MASSES |

## 4.5 在线效果（按 effect 汇总）

| effect | type | 名称 | 星球数 | 星球（名称） |
|---:|---:|---|---:|---|
| 1395 | 71 | TERMINID CONTROL SYSTEM+ | 14 | 76 TERREK、78 CRIMSICA、124 BORE ROCK、126 TURING、128 DARIUS II、130 ACHERNAR SECUNDUS、131 ACHIRD III、168 ERATA PRIME、170 FORI PRIME、175 GRAND ERRANT、211 NIVEL 43、218 PHERKAD SECUNDUS …共14 |
| 1190 | 76 |  | 9 | 97 CALYPSO、166 ENULIALE、167 EPSILON PHOENCIS VI、209 NABATEA SECUNDUS、210 NAVI VII、256 DIASPORA X、257 GEMSTONE BLUFFS、264 NEW INSIGHT、265 WAYWARD |
| 1188 | 73 |  | 8 | 75 ESKER、123 SOCORRO III、167 EPSILON PHOENCIS VI、209 NABATEA SECUNDUS、210 NAVI VII、257 GEMSTONE BLUFFS、258 ZAGON PRIME、259 OMICRON |
| 1193 | 73 |  | 5 | 75 ESKER、122 ERSON SANDS、123 SOCORRO III、166 ENULIALE、256 DIASPORA X |
| 1246 | 92 | 无参 | 5 | 115 PENTA、122 ERSON SANDS、204 MERAK、258 ZAGON PRIME、260 CYBERSTAN |
| 1248 | 40 | tag hash 0x658544D8（星图词条） | 4 | 244 VARYLIA 5、245 WASAT、246 VEGA BAY、261 FURY |
| 1249 | 71 | THE INCINERATION CORPS | 4 | 244 VARYLIA 5、245 WASAT、246 VEGA BAY、261 FURY |
| 1306 | 40 | tag hash 0x9FD5943A（星图词条） | 3 | 75 ESKER、212 OSHAUNE、259 OMICRON |
| 1309 | 71 | DRAGONROACHES | 3 | 75 ESKER、212 OSHAUNE、259 OMICRON |
| 1315 | 21 | HEAVY GLOOM SHROUD | 3 | 75 ESKER、122 ERSON SANDS、123 SOCORRO III |
| 1316 | 23 |  | 3 | 75 ESKER、122 ERSON SANDS、123 SOCORRO III |
| 1317 | 56 |  | 3 | 75 ESKER、122 ERSON SANDS、123 SOCORRO III |
| 1360 | 40 | tag hash 0x08766602（星图词条） | 3 | 158 CHOEPESSA IV、253 ZZANIAH PRIME、260 CYBERSTAN |
| 1361 | 71 | CYBORGS | 3 | 158 CHOEPESSA IV、253 ZZANIAH PRIME、260 CYBERSTAN |
| 1400 | 71 | Heavy SEAF Presence | 3 | 144 BELLATRIX、158 CHOEPESSA IV、259 OMICRON |
| 1401 | 40 | tag hash 0xBA586F51（星图词条） | 3 | 144 BELLATRIX、158 CHOEPESSA IV、259 OMICRON |
| 1202 | 40 | tag hash 0xAE2ED4E9（星图词条） | 2 | 158 CHOEPESSA IV、158 CHOEPESSA IV |
| 1252 | 71 | FRACTURED PLANET | 2 | 51 IVIS、85 MORADESH |
| 1303 | 40 | tag hash 0x907204FE（星图词条） | 2 | 212 OSHAUNE、215 PARTION |
| 1307 | 40 | tag hash 0x194C725F（星图词条） | 2 | 212 OSHAUNE、259 OMICRON |
| 1308 | 71 | HIVE LORDS | 2 | 212 OSHAUNE、259 OMICRON |
| 1310 | 71 | RUPTURE STRAIN | 2 | 212 OSHAUNE、215 PARTION |
| 1311 | 71 | presence 键 0xCAC0CD4E 本地无对应行 | 2 | 258 ZAGON PRIME、259 OMICRON |
| 1318 | 69 | GLOOM SOURCE | 2 | 258 ZAGON PRIME、259 OMICRON |
| 1319 | 56 |  | 2 | 258 ZAGON PRIME、259 OMICRON |
| 1320 | 23 |  | 2 | 258 ZAGON PRIME、259 OMICRON |
| 1377 | 40 | tag hash 0x021B60B3（星图词条） | 2 | 231 SIEMNOT、272 BASQUINE VIII |
| 1378 | 71 | MINDLESS MASSES | 2 | 231 SIEMNOT、272 BASQUINE VIII |
| 1402 | 40 | tag hash 0xFD8B9706（星图词条） | 2 | 7 ZEA RUGOSIA、185 KARLIA |
| 1403 | 71 | VOTE SNATCHERS | 2 | 7 ZEA RUGOSIA、185 KARLIA |
| 1197 | 71 | XENOENTOMOLOGY CENTER | 1 | 126 TURING |
| 1198 | 71 | DEEP MANTLE FORGE COMPLEX | 1 | 161 CLAORELL |
| 1229 | 71 | MERIDIAN BLACK HOLE | 1 | 64 MERIDIA |
| 1232 | 71 | FACTORY HUB | 1 | 130 ACHERNAR SECUNDUS |
| 1234 | 71 | CENTER OF SCIENCE | 1 | 125 FENRIR III |
| 1236 | 71 | CENTER FOR CIVILIAN SURVEILLANCE AND SAFETY | 1 | 45 MASTIA |
| 1239 | 71 | JET BRIGADE FACTORIES | 1 | 114 AURORA BAY |
| 1241 | 71 | FRACTURED PLANET | 1 | 127 ANGEL'S VENTURE |
| 1243 | 40 | tag hash 0x89E4FC2A（星图词条） | 1 | 170 FORI PRIME |
| 1244 | 40 | tag hash 0xA3A3DB9F（星图词条） | 1 | 75 ESKER |
| 1245 | 71 | PREDATOR STRAIN | 1 | 170 FORI PRIME |
| 1272 | 69 |  | 1 | 45 MASTIA |
| 1279 | 32 | WEAPONS EXPERIMENTATION | 1 | 82 URSICA XI |
| 1282 | 71 | HELLDIVER TRAINING FACILITIES | 1 | 22 ZEGEMA PARADISE |
| 1287 | 71 | NEW HOPE CITY | 1 | 16 FORT UNION |
| 1291 | 71 | NEW ASPIRATION CITY | 1 | 42 EMERIA |
| 1292 | 71 | NEW YEARNING CITY | 1 | 32 FORT SANCTUARY |
| 1304 | 71 | presence 键 0x9673F0E3 本地无对应行 | 1 | 34 HELLMIRE |
| 1324 | 71 | ULTRAMAFIC MINE | 1 | 207 MINTORIA |
| 1327 | 71 | presence 键 0xAD84E681 本地无对应行 | 1 | 92 GRAFMERE |
| 1333 | 71 | presence 键 0x155A353F 本地无对应行 | 1 | 212 OSHAUNE |
| 1344 | 71 | PANDORA BASE | 1 | 136 AFOYAY BAY |
| 1352 | 71 | CONVENTIONAL BLACK HOLE | 1 | 115 PENTA |
| 1353 | 71 | DATA CENTER | 1 | 162 CLASA |
| 1363 | 21 | PILOT SHORTAGE | 1 | 114 AURORA BAY |
| 1365 | 36 | ORBITAL FLUCTUATIONS | 1 | 160 CHORT BAY |
| 1366 | 56 | LESS BATTLEFIELD AMMO | 1 | 126 TURING |
| 1379 | 71 | APPROPRIATORS | 1 | 137 AIN-5 |
| 1380 | 40 | tag hash 0xE2136DAA（星图词条） | 1 | 137 AIN-5 |
| 1386 | 71 | SPORE BURST STRAIN | 1 | 75 ESKER |
| 1387 | 71 | COMMUNICATIONS ARRAY | 1 | 201 MEISSA |
| 1413 | 40 | tag hash 0x33FA1AB8（星图词条） | 1 | 7 ZEA RUGOSIA |
| 1414 | 71 | INVASION FLEET | 1 | 7 ZEA RUGOSIA |
| 1418 | 71 | presence:force_evacuate | 1 | 97 CALYPSO |
| 1427 | 32 | WEAPONS EXPERIMENTATION | 1 | 158 CHOEPESSA IV |

## 5. 未解清单（诚实标注）

- **98 条**全 raw：既无官方名称/描述，也没有解到具名目标（type 1×3、type 21×6、type 23×8、type 24×1、type 25×4、type 29×1、type 36×3、type 40×14、type 43×1、type 44×1、type 46×1、type 50×2、type 56×4、type 59×1、type 61×1、type 69×2、type 70×3、type 71×5、type 72×15、type 73×5、type 74×1、type 76×1、type 77×4、type 80×2、type 83×2、type 90×1、type 93×1、type 95×2、type 96×2、type 97×1）。
- **31 个 effectType** 语义仍是 ⚠：43、44、45、46、49、50、51、54、55、56、59、61、63、67、69、70、72、73、74、76、77、80、83、88、89、90、92、93、95、96、97。
- type40 的 tag hash 与 type71 的 presence 键不是同一命名空间（0 交集），tag→presence 的配对关系只能从 variant 目录/实机注入确认。
- type32：84/88 条已从 [TYPE32-STRATAGEMS](TYPE32-STRATAGEMS.md) 对表拿到战备名；官方描述文本里只有 6 个 hash 能直接抽出名字（其余是 `#V_ONE` 占位）。1426/1427/1428 三条的 hash 本地明文表 0 命中 ⇒ 对应新战备未发布。
- type36 的 `values[0]` 与 type32 是**同一战备 hash 空间**（12/16 条能复用 type32 的名字，如 EXO-45/49）。

## 6. 实机与进行中的实验（2026-11-01）

- **type94 ✓✓ 实机**：经代理向 38 颗战役星球的 `planetActiveEffects` 注入 `1346` 后，客户端「行动变量」出现「燃烧加特林火力网」卡面，Orbital Gatling Barrage 实弹变燃烧弹；证据 `audit.log`: `REWRITE +38 entries (planet 100 -> [1346] …)`。
- **进行中**：`CAUSTIC STRAIN`（effect 1430 tag + 1431 mechanic，presence `bugs_acid`，name locid 461034013）注入 100 `TRANDOR`，验证「已发布但从未出现」的变种词条。

## 7. 复现

```bash
python tools/gwe_full_table.py        # 两张 CSV + 本文档
python tools/gwe_join.py report       # presence 对表（旧）
python tools/effect_menu.py           # presence 菜单（旧）
```


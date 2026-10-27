# GWE 抓包 + 对表：探明「让引擎相信服务器」的能力边界

> 两个工具：`tools/gwe_capture.py`（给第三方代理加只读落盘开关）+ `tools/gwe_join.py`（拿 dump 对本地对象空间）。
> 状态：两个工具都过了离线自检（`selftest`，含**能失败的对照**）；**实机抓包尚未做**，因为要装一次代理并进一次游戏。

---

## 0. 为什么要抓这一份

「服务器给值、引擎自己解释」这条通道能做什么，只取决于一张表：
`GET /api/WarSeason/GalacticWarEffects`（约 300 条 effect）。每条 effect 的两个属性决定一切：

| 属性 | 决定 | 已知取值 |
|---|---|---|
| `effectType` | 引擎用哪个**解释器** | 32 = 临时配发战备 · 40 = 星图词条 · 71 = presence（局内玩法）· **其余未知** |
| `values[]` | 指向哪个**本地对象** | 71 的 `values[0]` = presence 身份键；32 的值为战备 hash |

**端点表在游戏文件里拿不到**：本会话扫过整装目录，`/api/` 只命中两段 EAC 相关碎片
（`/api/v1/publicAntiCheat…`），HD2 自己的 API 路径一条都没有 ⇒ 只能从流量里取。

---

## 1. 两步

### 1.1 打补丁（改的是第三方文件，就地 + 可还原）

```bash
# 先把开关设好（PowerShell）
$env:HD2_GWE_DUMP  = "D:\mod\out\gwe"
$env:HD2_GWE_PATHS = "/api/WarSeason/GalacticWarEffects"   # 可逗号分隔多个
$env:HD2_GWE_MAX   = "8388608"                              # 可选，缺省 8 MiB

python tools/gwe_capture.py status  --proxy D:/Downloads/variant_mod/tools/war_proxy.py
python tools/gwe_capture.py patch   --proxy D:/Downloads/variant_mod/tools/war_proxy.py
# …按原方式启动代理（run.ps1 或面板）→ 进一次游戏 → 回飞船看 out/gwe/index.txt
python tools/gwe_capture.py unpatch --proxy D:/Downloads/variant_mod/tools/war_proxy.py
```

补丁只加两段：一个模块级函数 + **chunked 解码之后、改写之前**的一行调用。

**硬规则（写死在代码里，不可配置）**：

* 只写**响应体**：header / cookie / query / 请求体一律不写 —— token 在请求头里，所以碰不到；
* 只落 `HD2_GWE_PATHS` 命中的路径，其它请求一个字节不动；
* 大小上限 + `index.txt` 只记 `时间 / 路径 / 字节数 / sha256 / 是否合法 JSON`；
* 任何异常都被吞掉并记一行日志：抓包失败**不允许**影响代理主流程。

补丁前会建 `war_proxy.py.bak`；`unpatch` 优先从备份还原。第三方代码不进本仓库。

### 1.2 对表

```bash
python tools/gwe_join.py report --gwe out/gwe --out out/planet/gwe-report.json
# → out/planet/gwe-report.json + gwe-report.md
```

输出：**实际字段名**（第一次跑就知道真实 schema）、`effectType` 分布、每种类型的 arity、
`tag/mechanic` 邻接配对、**presence 覆盖率 `n/137`**、以及"没对上的 values"清单。

---

## 2. 报告怎么读：四个判据

拿到报告后，对每个新字段问四个问题，就能把它归进四类（这是本线的**边界判定法**）：

| 判据 | 观测 | 结论 |
|---|---|---|
| 落地 | 星图 / 局内 / UI 是否出现 | 不落地 ⇒ 客户端根本不读这个字段 |
| **刷新** | 下一次拉 `Status` 后是否被还原 | 还原 ⇒ **纯显示层**；不还原 ⇒ 被引擎吸收成权威状态 |
| 传播 | 客机是否也看到 | 是 ⇒ 进了 board 同步（主机权威，**全队受影响**）|
| 资源 | 紫问号 / 崩溃 / 无模型 | 是 ⇒ **id 越界**，超出本地对象空间 |

三条已知硬边界（各有证据）：

1. **本地对象空间**：id 必须是客户端已定义的（137 presence / 58 战备…）——案例 10-14 崩溃对照 + Mount 线 R2 整包驻留同源；
2. **权威归属**：账号 / 货币 / 解锁 / 战功属服务端权威，改响应只改本地视图（⚠ 机制推断，未实测，也不该拿主账号测）；
3. **请求方向**：本通道只改响应；伪造提交是另一个风险层级，案例明确没做。

---

## 3. Wireshark 在这条线里能干什么

结论先说：**能做旁证和找漏，不能替代补丁**（除非 TLS 密钥能拿到）。

| 用途 | 可行性 | 具体做法 |
|---|---|---|
| **直接解密 HTTP（首选尝试）** | 取决于 TLS 后端 | 游戏目录有 `bin/libcurl.dll`。若它用 OpenSSL 且尊重 `SSLKEYLOGFILE`：设 `SSLKEYLOGFILE=D:\mod\out\tls.keys` → 启动游戏 → Wireshark `Preferences→Protocols→TLS→(Pre)-Master-Secret log filename` 指向该文件。能解就是**明文 HTTP，连补丁都不用打** |
| **主机→客机会话流量画像** | ✓ 不需要解密 | 只看协议/端口/包长/时序。若改写后主机上行出现 ~2.5 KB 粒度增量（board 记录 `0x9C0`=2496 B），就是"引擎自己同步 board"的旁证 —— 正好回答"它是不是给客机发假包" |
| **端点面外延** | ✓ 不需要解密 | 抓 DNS / TLS SNI，列出客户端还连了哪些域（遥测、EAC、CDN）。这决定**还有没有第二条"服务器→客户端"通道可写** |
| 看具体 path / body / 304 条件请求 | ✗ 无密钥 | TLS 1.2/1.3 记录是密文；Steam/EOS 数据报同理 |

抓包注意：hosts 指向**局域网 IP** 时抓对应网卡（不是 loopback）；Npcap 要装 loopback 支持才看得到 127.0.0.1 的 CRL 服务。

**推荐顺序**：先花 5 分钟试 `SSLKEYLOGFILE`（成功则最省事）→ 不行就走 §1 的补丁 → Wireshark 只用来做"会话流量画像"和"端点外延"这两件旁证。

---

## 4. 离线自检（已跑过，可复跑）

```bash
python tools/gwe_capture.py selftest    # 10 项：钩子插入 / 调用点位置 / py_compile / --help 仍可用
                                        # / gzip 落盘一致 / index 只有 5 字段(无 header) / 非白名单不落
                                        # / 自动建目录 / 超上限不落 / 未设开关完全静默
python tools/gwe_join.py selftest       # 8 项：type71→presence 精确命中 / effect id→变种名
                                        # / type32→战备 / 未知类型入候选 / 未对上值记账
                                        # / tag↔mechanic 邻接配对 / **对照：键改坏后不再命中**
```

两条对照的意义：抓包侧证明"开关关掉时对原代理零影响"，对表侧证明"匹配器是能失败的"
（把 presence 键异或掉全部位后必须不再命中）—— 否则匹配逻辑只是"总能命中"的假象。

---

## 5. 已知空白

* 真实 `GalacticWarEffects` 的 schema 未见过，工具按 id/effectType/values 三组键名自适应，并把实际键名打进报告；
* `effectType` 全集只知 3 个；其余由报告给出（这也是本线最想要的结果）；
* 邻接配对（40 与 71 按 id ±1/±2）是**启发式**，权威配对要用 `Status` 里 tag/玩法 1:1 共现次数推（案例的做法）；
* 那份 effect 菜单的另一个可能来源是社区项目 `Planet-Campaign` 的 `effect_options.lua`（案例的战备目录就是用它生成的，`kind=32` + `native_hash`）；本机没有该文件，若日后拿到，可作交叉验证面。

---

## 6. 实测结果（2026-10-27，build 26088801）

一次 Passthrough 侦察（登录 + 切一次星球）拿到的两份原始响应：

| 端点 | 体积 | sha256 前 8 位 |
|---|---:|---|
| `GET /api/WarSeason/GalacticWarEffects` | 71,833 B | `fb1b64f6` |
| `GET /api/WarSeason/801/Status`（线上 gzip 8,398 B）| 50,837 B | `43cd35c7` |

### 6.1 effect 菜单的真实形状

`310` 条 effect，字段：`id` / `gameplayEffectId32` / `effectType` / `flags` / `nameHash` /
`descriptionFluffHash` / `descriptionGamePlayLongHash` / `descriptionGamePlayShortHash` /
`valueTypes` / `values`。**所有 effect 的 `values` 都是 2 元**：`[对象或数值, 数值]`。

`effectType` 共 **45 种**，前六名占 210/310：

| type | 条数 | `values[0]` 是什么 | 对上的本地对象 |
|---:|---:|---|---|
| 32 | 88 | 32 位哈希 | **战备**（命中 `stratagem_catalog.json` 的 `effect_hash` 82 次）|
| 71 | 75 | 32 位哈希 | **presence**（`murmur32(presence 名)`，见 §6.2）|
| 36 | 16 | 32 位哈希 + 负数 | **临时装备**（`EXO-45`/`EXO-49` 等，出现在空间站）|
| 72 | 15 | 32 位哈希 | 未解（同一哈希重复出现，疑为修饰符）|
| 40 | 13 | 32 位哈希 | 星图**词条**（与 71 一一成对）|
| 21 / 23 / 56 / 1 / 25 … | 12/9/7/6/6 | **小整数**（0/±10/±45/30/100…）| 不是对象引用，是**数值参数**（时长/增量/百分比）|

⇒ **菜单分两族**：对象引用类（哈希 → 本地对象）与数值参数类（标量）。别把后者当 id 去查表。

### 6.2 关键：`effectType=71` 的键是 `murmur32(presence 名)`

即 Stingray 的 32 位名字哈希（`murmur64(seed=0) >> 32`，等价 `python -m srkit hash <名>` 里的 `murmur32=`）。

| presence | `murmur32` | GWE `values[0]` |
|---|---|---|
| `bugs_super_predator` | `0xE9DB526C` | 3923464812 ✓ |
| `bugs_gloom` | `0x60280611` | 1613235729 ✓ |
| `bots_cyborgs` | `0xA087D5A7` | 2693256615 ✓ |
| `seaf` | `0x492F408A` | 1227833482 ✓ |
| `illuminate_invading` | `0x37640CC3` | 929303747 ✓ |

按此口径，本地 **137 条 presence 有 67 条**在菜单里有对应 effect（其余是纯视觉/事件类）。
⚠ 注意：presence 表里 `+0x20/+0x24` 那对 `(lo,hi)` **不是**这个键，拿它去比会全对不上。

### 6.3 当前战局里正在生效什么（66 颗星球 / 137 条生效 / 33 个 presence）

| effect | presence | 星球数 | 星球 |
|---:|---|---:|---|
| 1395 | `tcs_wall` | 14 | 269,76,168,78,170,270,126,131,… |
| 1249 | `bots_ivory_legion` | 4 | 245,246,261,242 |
| 1309 | `bugs_dragon` | 3 | 212,259,75 |
| 1400 | `seaf` | 3 | 215,158,268 |
| 1310 | `bugs_burrower` | 2 | 212,215 |
| 1308 | `bugs_hive_lord` | 2 | 212,259 |
| 1361 | `bots_cyborgs` | 2 | 260,253 |
| 1378 | `illuminate_harvester` | 2 | 272,231 |
| 1403 | `illuminate_bodyhorror` | 2 | 185,7 |
| 1245 | **`bugs_super_predator`** | 1 | **170** |
| 1386 | `bugs_gloom` | 1 | 75 |
| 1203 | `elite_bot_jumpattack` | 1 | 203 |
| 1414 | `illuminate_invading` | 1 | 7 |

**结论：变种本来就是官方在跑的**（掠食变种正在 170 号星球上活着）。那个 mod 做的不是"造变种"，
而是把**别的星球已经有的 presence** 搬到你要打的星球上。

`effectType=40` 的 13 条与 `71` 严格成对（1248/1249、1306/1309、1401/1400…，星球数完全一致），
印证了案例里"tag + 玩法成对才有局内效果"的说法。

### 6.4 两个新发现

1. **5 个 `type71` effect 指向本地不存在的 presence**（`1304/0x9673F0E3`、`1311/0xCAC0CD4E`、
   `1327/0xAD84E681`、`1333/0x155A353F`、`1341/0x6775CC99`）：服务器有对象、客户端没有。
   这正是"注入了但客户端不认"的那一类，可作为 id 越界判据的实例。
2. **空间站是第二条表面**：`spaceStations[].activeEffectIds` 独立于 `planetActiveEffects`，
   上面挂着 `EXO-45/EXO-49` 等 `type36` 临时装备（8 个 id）。

> 2026-10-27 夜更正：这 5 条里 **4 条正在线上跑**（`1304`×1、`1311`×2、`1327`×1、`1333`×1）。
> 也就是说客户端**本来就在收自己解析不出的效果**且不崩，所以它们是"容错"实例，不是"越界"判据。

## 7. 实机链路验证（2026-10-27 夜，warId 801）

### 7.1 一个 effect id = 一整个事件包

A/B/A，同一颗星球 **93（NEW STOCKHOLM，illuminate）**，只改 Status 注入：

| 时间 | Status 注入 | `operationSettingsId`（Create 请求体） | 部署界面卡片 |
|---|---|---|---|
| 21:25:42 | 无 | 2796992372 | 普通作战 |
| 21:33:17 | `REWRITE +1 entries (planet 93 -> [1373])` | **3194790369** | **AVERT VOID** |
| 21:24:40 | 182 + 1373（另一颗星） | 3194790369 | AVERT VOID |

链路（每一段都有实测或数据支撑）：

```
Status.planetActiveEffects += 1373
  ↓ 客户端本地解析（打开部署界面期间零请求，见 7.2）
GWE type71: values[0] == murmur32('illuminate_ritual_storm_lvl1')
  ↓
presence 行 +0x14=1（事件）→ operationSettingsId = 3194790369
  ↓ 客户端 POST /api/Operation/Create 提案
服务器盖章 {"operations":[{"id":1206/1208,...}]}
  ↓
局内天气 = weather_settings 里 8 行 illuminate_ritual_storm_* 覆盖
```

### 7.2 作战卡是客户端本地算的（证据：零请求）

verbose 全量路径日志，21:24:34 切到 93 → 21:24:40 点选作战，之间只有：

```
POST /api/Operation/Abandon     27B   {"operationIds":[1203]}
POST /api/Operation/Create     301B   operationSettingsId=3194790369 ...
POST /api/Account/ReportPosition 80B
PUT  /api/lobby
```

**没有任何"请给我这颗星球的可选作战"的请求。** `/api/Operation` 只在登录时拉一次，
返回的是**玩家已有的 operation**（`id=1203, isActive=true, operationSettingsId=3194790369`）。

推论：`operationSettingsId` 是客户端根据 Status（含我们注入的 effect）**本地算出来的**，
服务器只负责发号。客户端会**复用缓存**——先 `Abandon {1203}` 再用同一个 settings id 重建（1206）。

### 7.3 跨阵营不校验

把终结族 presence `bugs_gloom`（effect **1386**）注入光照星球 93：
`21:39:18 REWRITE +1 entries (planet 93 -> [1386])`

- 星图卡出现 **`SPORE BURST STRAIN`** + 完整描述（`A mutation causes Terminids...`）
- 部署界面出现 **`COMBATANT FORCES PRESENT: SPORE BURST STRAIN`**
- **作战卡不变**——因为它是 `+0x14=4`（敌情）不是 `+0x14=1`（事件）

结论：`resolve_plan()` 里的阵营过滤是**我们自己加的保险**，游戏侧不校验阵营。

### 7.4 presence 行的种类字段（本地表 `generated_galactic_presence_settings`）

| 字段 | 含义 | 取值 |
|---|---|---|
| `+0x14` | **种类** | 0=地图标记 / 1=事件作战 / 3=战术行动 / 4=敌情或设施 |
| `+0x18` | 子类 | 1 = strain/surge 类敌情变体 |
| `+0x1C` | RaceType | 1=SE / 2=terminid / 3=automaton / 4=illuminate |
| `+0x20` | **显示名 locid** | 例：505181551=`CLASS 1 EXOSTORM`、1147205144=`SPORE BURST STRAIN` |
| `+0x24` | **描述 locid** | 例：4210400742=`Isolated Exostorm pockets...` |

137 条的分布：kind0=19 / **kind1=7** / kind3=4 / kind4=107。
其中"有 GWE effect 可在线上激活"的：kind0 12、kind1 **3**、kind3 **3**、kind4 52。

> ⚠ 命名陷阱：`bugs_gloom`（kind4，`SPORE BURST STRAIN`）≠ `gloom`（kind1，`GLOOM RESEARCH EXPEDITION`）。
> 按名字猜语义会连踩两脚；必须按 hash + `+0x14` 区分。

### 7.5 能力边界（截至本轮）

**已证实能做**：

| 能力 | 等级 | 证据 |
|---|---|---|
| 任意 GWE 目录内 effect 注入任意星球（跨阵营亦可） | ✓✓ | 1386 on 93 |
| kind=1 → 换作战卡 + 任务链 + 天气 | ✓✓ | 1373 on 182/93 |
| kind=4 → 星图卡 + COMBATANT FORCES | ✓✓ | 1386 on 93 |
| 一次批量注入多颗星球 | ✓✓ | 5 颗终结星一次 `added=5` |
| 只加不删（不动原有 effect） | ✓✓ | 星球 7 原 4 个 effect 保留 |

**做不到 / 未验证**：

| 项 | 状态 |
|---|---|
| 目录外的 effect id（如自己编的 9001） | ⚠ 客户端解析不出，预期无显示；但服务器自己也在发解析不出的效果，客户端不崩 |
| 直接指定 `operationSettingsId` | ✗ 只能通过 presence 间接影响 |
| 服务器是否校验 settings id 与星球匹配 | ⚠ 跨星球已见接受（93 用了 182 那套），非法值未测 |
| 终结族事件（`hive_world` / `gloom`） | ✗ 当前 GWE 无对应 effect，注入不了 |

### 7.6 本轮新增工具

| 文件 | 作用 |
|---|---|
| `tools/effect_menu.py` | GWE + presence + 最新 Status → `docs/EFFECT-MENU-801.md` + `out/effect-menu.csv`（310 条全表） |
| `war_proxy.py` 新增 `_gwe_capture_req()` | 请求体落盘，只对 `/api/Operation*`，只存 body 不存 header（默认路径 `HD2_GWE_REQ_PATHS`） |

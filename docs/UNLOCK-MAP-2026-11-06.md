# 解锁总览：武器上架 · 配件解锁（build `26251122`，2026-11-06 收口）

> **本文属网络层**（代理注入路线），因此放在 `hd2-network-proxy`。
> 数据表 / 实体 / dl_bin 侧的细节仍在 `hd2-datamined`，本文用 GitHub 链接指过去。
>
> 原先这些内容散在 6 处：datamined 的 `UNRELEASED-INVENTORY` §9/§10、`WEAPON-CUSTOMIZATION` §13/§14/§15、
> `RECON-LAS22-FILETOOL`，以及本仓库的 `INVENTORY-INJECTION`、`API-ENDPOINTS` §7/§8。
> 这里给**决定树 + 配方 + 结论台账**；细节与原始证据仍在各自文档（§7 有索引）。

---

## 0. 三十秒决定树

```
想让某件东西可用？
├─ 武器（军械库 / 配装界面里出不出来）
│   ├─ 账号已拥有？（/api/Progression/inventory 的 items[].mixId）
│   │   └─ 是 → 已经可用，不需要做任何事
│   └─ 否
│       ├─ 在 /api/Progression/items 目录里？（= 已发布）
│       │   ├─ 是 → 【配方 A】加一行 inventory     ← 1 层，✓✓ 实机
│       │   └─ 否 → 【配方 B】inventory + items    ← 2 层，✓✓ 实机
│       └─ 上架后能否改装？
│           ├─ 该武器有附件行（parentId=它，progressionCategory=2）→ 【配方 C】注入那些 mixId ✓✓
│           └─ 没有 → 改装页 CANNOT EDIT，且服务器侧伪造无效 ✗（已否证）→ 只能 dl_bin L0 或内存
└─ 配件（改装页里能不能选）
    └─ 同上最后两行；注意"配件"在服务端就是 inventory 里的一行，不是独立物品类型
```

**战备（2026-11-06 20:30 更正：有载体了）**：真实解锁走 `POST /api/SeasonPass/item/buy`，
授予 = inventory 加一行（`progressionCategory: 11`，id 来自战团详情的 `itemMixId`）。
所以战备与武器/附件/外观同一条机制，可用一行 inventory 注入解锁 —— 详见 [API-ENDPOINTS](API-ENDPOINTS-2026-11-01.md) §10。
（临时发放仍然只有 GWE `effectType=32` 那条路；`+0xC8` 额外战备是数据表侧的替代方案。）

---

## 1. 两个坐标轴（最容易混的地方）

| 轴 | 症状 | 服务端承载 | 判据 |
|---|---|---|---|
| **武器上架** | 军械库里根本看不到这把枪 | `inventory.items[].mixId`（拥有）+ `items` 目录（已发布） | mixId 在不在两个清单里 |
| **配件解锁** | 枪能看见，但改装页 **CANNOT EDIT** / 配件灰着 | **同样是 `inventory.items[].mixId`** —— 附件行的 `mixId` 是「这把枪 + 这个附件」的库存键 | `items` 里 `parentId=武器` 且 `progressionCategory=2` 的行，其 `mixId` 在不在 inventory |

关键区别：**附件的 optionId ≠ 它的 mixId**。

| 概念 | 字段 | 示例（AR-23A 的 ANGLED FOREGRIP） |
|---|---|---|
| 附件 optionId | `items[].itemId`，也是写进 `customization.slots[]` 的值 | `3207983096` = `0xBF35EFF8` |
| 武器 mixId | `items[].parentId` | `1160920394` = `0x45323D4A`（AR-23A） |
| 附件库存键 | `items[].mixId` | `718265621` |
| 武器包 | `AcquireUnlockableItem.packageId32` | `2221505542` |
| 货币 | `3608481516` | Requisition（`isConsumable`、`maxCap 50000`）|

> 2026-11-05 曾因为拿 **optionId 去比 `mixId` 字段**而误判"配件在服务端没有拥有层"，结论已于 2026-11-06 翻案。

---

## 2. 武器解锁

### 2.1 三分法（判据在服务端，比 wiki 更硬）

| 类别 | inventory | items 目录 | 成本 | 实机 |
|---|---|---|---|---|
| 已发布且已拥有 | ✓ | ✓ | — | — |
| **已发布未购买** | ✗ | **✓** | **配方 A（1 层）** | `✓✓` LAS-13 单件 / 24 件批量 |
| **未发布** | ✗ | ✗ | **配方 B（2 层）** | `✓✓` LAS-22 / P-41 / SG-8F |

判据用法：`GET /api/Progression/inventory` 的 `items[].mixId` 是**拥有**；
`GET /api/Progression/items`（3020 条）是**官方已发布/已知**清单。两者都没有 = 未发布。
wiki 只作人读校验（datamined `refs/wiki/pages/`，2026-11-05 重爬 241 页）；**未拥有 ≠ 未发布**。

### 2.2 配方 A：已发布未购买（1 层）

```jsonc
// runtime/inventory_inject.json
{"enabled": true,
 "items": [{"mixId": 2870692210, "amount": 1, "isDiscovered": false}]}   // 例：LAS-13 Trident
```

生效：钩子每请求现读配置 ⇒ 改完不用重启代理，**但客户端要重新登录**（登录时才拉 inventory）。

### 2.3 配方 B：未发布（2 层）

```jsonc
// runtime/items_inject.json —— 目录克隆
{"enabled": true,
 "template": 3866352840,                                   // 同族模板（LAS-5 Scythe 的 mixId）
 "add": [{"id": 2112173638, "template": 3866352840}]}       // 要补的 itemId（= mixId）
```
外加 inventory 里同一条 `mixId`。模板选**同族**（同为激光/同类型武器）最稳。

### 2.4 实机台账

| 对象 | 层 | 结果 |
|---|---|---|
| LAS-22 Shear `0x7DE53646` / P-41 `0xC9F609BA` / SG-8F `0x7349AF9A` | 双层 | `✓✓` 军械库完整显示（名/描述/四项数据/三个特性） |
| 24 件「已发布未购买」武器 | 1 层 | `✓✓` 批量出现；2026-11-06 按新基线刷新为 24 条（剔除账号已拥有的 3 件）|
| LAS-13 Trident `0xAB1B4972` | 1 层 | `✓✓` 只加拥有行就上架（目录记录本来就有）|

**边界**：注入**不写回账号**（抓包点为改写前，27 件注入物在服务端 inventory 里 24 件 0 命中，
命中 3 件是账号本来就拥有的）；但**改装状态会回写**（`Items/Customize/v2` 条目 59→67）。

---

## 3. 配件解锁

### 3.1 真购买长什么样（`POST /api/Progression/ProgressionPackage/AcquireUnlockableItem`）

```jsonc
// 请求（135 B，实例：AR-23A 的 ANGLED FOREGRIP）
{"expectedCost": [{"mixId": 3608481516, "amount": 5000}],
 "itemMixId": 718265621, "targetLevel": 7, "packageId32": 2221505542}

// 响应（114 B）
{"packageId32": 2221505542,
 "inventoryChanges": [{"mixId": 3608481516, "amount": -5000},
                      {"mixId": 718265621, "amount": 1}]}
```

⇒ **解锁 = 往 inventory 加一行**。`targetLevel` 只是购买时的界面门槛，客户端不校验。

### 3.2 配方 C：注入附件库存行（`✓✓` 两组实机）

```bash
# 生成器：从 items 抓包里挑出某把枪的附件行，剔除已拥有
python tools/attach_items.py --catalog <items抓包>.json \
    --weapon 0x45323D4A --inventory <inventory抓包>.json \
    --out runtime/inventory_attach_inject.json [--enable] [--list]
```

开关独立于武器注入（`inventory_attach_inject.json` vs `inventory_inject.json`，可分别开关、同时开启自动合并），
便于做单变量。规模：目录共 **1455 条附件行 / 57 把武器 / 247 种附件**。

| 实机 | 注入量 | 结果 |
|---|---|---|
| AR-23A Liberator Carbine | 28 行 | `✓✓` 28 个全可选、装上能用（未花 Requisition）|
| SMG-203 / MP-98 / R-4 Hyena / LAS-13 / R-40 Sightliner（原本全部 CANNOT EDIT）| 140 行 | `✓✓` 5 把全部可编辑、配件可选、装上能用 |

日志证据：`INV REWRITE +51 -0 items`（AR-23A）、`+164`（5 把）。

### 3.3 `CANNOT EDIT` 三分类（判据可复用）

| 类别 | 判据 | 代表 | 能否救 |
|---|---|---|---|
| **① 没拥有** | 目录**有**该武器的附件行，但一行都没拥有 | 今天那 5 把、任何新枪 | **✓ 配方 C 即解**（已两组实机）|
| **② 服务端没有解锁行** | 目录里该武器 **0 条**附件行 | **R/40-K Hot-shot**（L0 只有 1 个专属光学 `0xA10F7D9D`）；**LAS-22**（连武器都不在目录）| **✗ 已否证**，见 §3.4 |
| **③ 本来就没有配件体系** | 目录 0 行 **且** 游戏不给它配件（wiki `scope_options = None`）| **StA-52 Assault Rifle**（L0 仅 `0x2F7B4497` Flashlight）| **✗ 不必救**，如实反映 |

查法：`items` 里 `parentId == <武器 mixId>` 的 `cat=2` 行数 → 有 ⇒ 类别①；
没有 ⇒ 再查 datamined `refs/weapon-customization-l0-26251122.json` 该武器的 L0 默认项 / wiki `scope_options`。

### 3.4 否证：服务器侧伪造对类别② 无效（2026-11-06，两轮）

以 R/40-K Hot-Shot `0xF16B0BCF` 为试点，两层都伪造（目录行 + 库存行）：

| 轮次 | 伪造内容 | 送达证据 | 结果 |
|---|---|---|---|
| ① | 借用同为激光族的 **LAS-5 的 38 个 optionId**，38 行 | `ITEMS REWRITE +41` / `INV REWRITE +202` | **仍 CANNOT EDIT** |
| ② | 只伪造 R/40-K **自己 L0 默认项**的 optionId `0xA10F7D9D`（1 行）| `ITEMS REWRITE +4` / `INV REWRITE +165` | **仍 CANNOT EDIT** |

**第一轮失败的原因（写进数据里了）**：每把枪能用哪些 optionId 由**本地 L0 数据**决定，
服务器目录只回答"这些当中你拥有哪些"。借用别的枪的 optionId 对 R/40-K 全部不适用，客户端不认。

**逐行对表**（datamined `weapon-customization-l0`）：

| 武器 | L0 行 | 默认项数 | 默认项 | 可编辑 |
|---|---:|---:|---|---|
| MP-98 Knight | 38 | 5 | 下挂/光学/涂装/枪口/弹匣 | ✓ |
| SMG-203 Gallant | 43 | 5 | 同上 | ✓ |
| R-40 Sightliner | 115 | 4 | 光学/涂装/弹匣/枪口 | ✓ |
| LAS-13 Trident | 124 | 4 | 枪口/光学/涂装/下挂 | ✓ |
| **R/40-K Hot-shot** | 130 | **1** | 仅 `0xA10F7D9D` SNIPER SCOPE 10x SHARK（该枪专属）| ✗ |
| **StA-52** | 100 | **1** | 仅 `0x2F7B4497` Flashlight | ✗ |
| LAS-22 Shear | 121 | 5 | 枪口/光学/下挂/弹匣/涂装 | ✗（未发布）|

**结论**：类别② 的 CANNOT EDIT **不是"缺附件行"**，而是改装页另有一层判定（与 manager 槽位 / 本地
customization 注册一致），服务器侧伪造补不到。要它可编辑只剩两条：改 dl_bin（L0 默认项，不改页面状态）
或 Lua / 内存（当年 Lua 版就是补 registry 记录 + manager 槽位）。

### 3.5 为什么 5 把能成、R/40-K 不能

| | 5 把（成功） | R/40-K（失败） |
|---|---|---|
| 目录附件行 | **真实存在**（21–41 行/把）| **0 行**（伪造的）|
| 行内 optionId | 与各自本地 option 集**天然匹配** | 借用别的枪的 → ①轮不匹配；②轮用自己专属项仍不行 |
| 客户端视角 | "这些我本来就能用，只是没拥有" → 注入即解锁 | "这枪没有可选配件" → 无论怎么注入都不开门 |

---

## 4. 跨两条轴的共同事实

| 事实 | 证据 |
|---|---|
| 代理注入**不写回账号** | 抓包点在改写前（`war_proxy.py:661` vs 改写 742/759）；27 件注入物 24 件在服务端 inventory 里 0 命中 |
| 真购买**会**写回 | inventory 963 → **964**（CB-9 反射镜 `2828694410`）→ **965**（AR-23A 下挂 `718265621`）|
| 改装状态**会**回写 | `Items/Customize/v2` 59 → 67 条，其中 18 条属于服务端不拥有的武器 |
| 军械库装备路径**按需流式加载**资产 | LAS-22 + Reflex MKII + Angled Foregrip 全部自动拉取，无需资源驻留补丁（只对投送舱/L0-only 路径需要）|
| 注入武器的「可改装」取决于附件行 | LAS-22 0 行 ⇒ CANNOT EDIT；5 把有真行 ⇒ 注入即可编 |

---

## 5. 文件与命令

| 文件 | 作用 |
|---|---|
| `runtime/inventory_inject.json` | 配方 A/B 的「拥有」层（武器） |
| `runtime/items_inject.json` | 配方 B 的目录克隆；也支持**整行覆盖字段**（`itemId/mixId/parentId/progressionCategory/…`），去重按 `mixId` |
| `runtime/inventory_attach_inject.json` | 配方 C 的附件库存行（独立开关） |
| `tools/attach_items.py` | 按武器生成附件行清单（本仓库与 datamined 各一份） |
| `tools/war_proxy.py` | `_gwe_inventory_rewrite` / `_gwe_items_rewrite` / `_gwe_capture_*` |

```bash
# 回滚（都不用重启代理，下一请求即失效）
#   武器：inventory_inject.json  enabled:false
#   目录：items_inject.json      enabled:false
#   配件：inventory_attach_inject.json enabled:false
# 客户端要重新登录才会重拉这三份响应。
```

---

## 6. 能力状态（读数时刻 2026-11-06 18:10）

| 能力 | 状态 | 备注 |
|---|---|---|
| 已发布未购买武器上架 | **✓✓** | 1 层注入；24 件批量已实机 |
| 未发布武器上架 | **✓✓** | 2 层注入；LAS-22 / P-41 / SG-8F |
| 解锁任意武器的**已有**配件 | **✓✓** | 配方 C；AR-23A 28 个、5 把 140 行 |
| 让「无附件行」武器可改装（类别②） | **✗ 否证** | R/40-K 两轮伪造均 CANNOT EDIT |
| 永久解锁战备（代理，含**未发布**战备） | **✓✓ 实机（2026-11-06 20:44）** | 注入 30 条 `cat 11`：多出约 30 个全部可用，含 ORBITAL CONFETTI / ORBITAL WALKING BARRAGE SMOKE |
| 注入写回账号 | **✗ 不会** | 24/24 未命中服务端 inventory |

---

## 7. 证据索引（本文背后的原文）

| 主题 | 原文 |
|---|---|
| 三分法判据、未拥有≠未发布 | [UNRELEASED-INVENTORY §9/§9.1](https://github.com/deepseekv41flash/hd2-datamined/blob/master/docs/tables/UNRELEASED-INVENTORY-26088801.md) |
| 注入不回写账号（抓包点/命中率） | 同上 §10 |
| 军械库成员资格 = inventory `mixId` | [WEAPON-CUSTOMIZATION §13](https://github.com/deepseekv41flash/hd2-datamined/blob/master/docs/tables/WEAPON-CUSTOMIZATION-26251122.md)（含删 R-63 Diligence 的因果实证）|
| L0 默认项 / L1 选项表 / `+0x12FC` 解锁组 | 同上 §14、§15.5 |
| CANNOT EDIT 三分类与两轮否证 | 同上 §15.1.1、§15.6.1、§15.6.2 |
| 附件 = inventory 一行、`AcquireUnlockableItem` 报文、id 模型 | 本仓库 [API-ENDPOINTS](API-ENDPOINTS-2026-11-01.md) §8.1–8.3 |
| 注入开关与钩子实现、Diligence 对照回执 | 本仓库 [INVENTORY-INJECTION](INVENTORY-INJECTION-2026-11-05.md) |
| 文件版（dl_bin）身份互换 / 借组 | [RECON-LAS22-FILETOOL](https://github.com/deepseekv41flash/hd2-datamined/blob/master/docs/cases/RECON-LAS22-FILETOOL-26251122.md) |
| 战备为什么不在代理线 | 本仓库 API-ENDPOINTS §7 |
| 抓包/证书/白名单运维坑 | 本仓库 [OPS-PITFALLS](OPS-PITFALLS.md) |

---

## 9. 战备解锁：**✓✓ 实机（2026-11-06 20:44）**

### 9.1 机制

战备拥有权 = **inventory 里一行 `progressionCategory: 11` 的物品**（正式名：战备许可 / permit）。
真实解锁走 `POST /api/SeasonPass/item/buy`，响应 `items[]` 给它 **+1**；该物品的 `mixId` 来自
`GET /api/SeasonPass/<warbondId32>` 的 `seasonPassPages[].seasonPassItems[].itemMixId`。
报文与 id 模型见 [API-ENDPOINTS §10](API-ENDPOINTS-2026-11-01.md)。

⇒ 与武器（`cat 1`）/ 附件（`cat 2`）/ 商店外观（`cat 3`）**完全同一条机制**，一行 inventory 即可解锁。

### 9.2 实机结果（注入 30 条未拥有的 `cat 11` 物品）

用户回报：**多出约 30 个战备、都能用**，并且**多出 2 个未发布战备**。

| 未发布战备 | 数据（用户截图读数）|
|---|---|
| **ORBITAL CONFETTI** | OFFENSIVE STRATAGEM PERMIT · CALL-IN **4.45 s** · USES **UNLIMITED** · COOLDOWN **68 s** · 特性 `ORBITAL` · 描述 "A display of brightly colored confetti. Good for Democratic morale, but provides no strategic value."（name locid `1912361092`，描述 `826650508`）|
| **ORBITAL WALKING BARRAGE SMOKE** | CALL-IN **5.45 s** · USES **UNLIMITED** · COOLDOWN **103 s** · 特性 `EXPLOSIVE` / `ORBITAL` · 描述 "A linear artillery barrage which moves at intervals while firing smoke bombs to obscure enemy visibility."（name locid `852413008`，描述 `1772996316`）|

### 9.3 这解开了两个老结论

| 旧结论（2026-11-05）| 现在 |
|---|---|
| "59 个端点无战备解锁载体，永久解锁只能走 `+0xC8` 数据表" | **✗ 作废**：载体是 `SeasonPass/item/buy` + `cat 11` inventory 行 |
| "未发布战备（如 Orbital Walking Barrage Smoke、Orbital Confetti）在代理线拿不到" | **✗ 作废**：它们的**解锁物品本就在服务端目录里**（只是从未在任何战团/商店出售），注入 `cat 11` 行即可在军械库出现、可装备、可用 |

⇒ **"未发布"在战备上的含义是"从未上架出售"，不是"服务端不认识"** —— 所以能注入；
这与外观的边界（`cat 3` 伪造目录行不被接受）不冲突：这里**目录行是真实存在的**，我们只补 inventory。

### 9.4 仍待解

- **`cat 11` 物品 id ↔ 战备名字的对应表还没解**：30 条一次性注入所以不知道哪一条对应哪个战备。
  若要做定向解锁（只解锁某几个），需要按小批量注入反推，或在本地表里找到链接字段。
- `cat 11` 共 **108** 条，本次登录时已拥有 77、未拥有 31（其中 1 条刚真买）⇒ 我们已注入其余 30 条，
  等于**该账号的战备解锁已全覆盖**（含未发布）。

---

## 8. 外观（护甲 / 头盔 / 披风 / 横幅）：**可以，走同一条 inventory 机制**

2026-11-06 19:04–19:05 的三次**真实超级商店购买**（全量抓包）把这个分支也钉死了：

| 购买 | 端点 | 授予方式 |
|---|---|---|
| 护甲 `2556497905` / 头盔 `1233248044` / 披风 `1513263450` | `POST /api/StoreFront/buy`（`salesId` + `expectedCost`）| 响应 `items[]` 里给该 `mixId` **+1** ⇒ **inventory 加一行** |

- 购买前那份 inventory（965 条服务端真值）里三件**都不在**，购买后由响应授予 ⇒ 拥有权就是 inventory 行；
- 三件在目录里都是 `progressionCategory: 3`（横幅/其它外观为 9）；`cat 3` 共 **427 条**，本账号已拥有 **236**、未拥有 **191**；
- ⇒ **未拥有的外观可以直接注入**，不需要伪造购买（伪造购买反而要过服务端扣费校验）。

**两个 id 空间别混**：`avatarCustomization.armor_set / helmet_set` 是**外观变体 key**
（对应 `generated_customization_armor_sets.dl_bin`），不是物品 id，也不会出现在 `items[]` 里。
抓包与报文细节见 [API-ENDPOINTS](API-ENDPOINTS-2026-11-01.md) §9。

**仍未验证的角落**：

| 问题 | 现状 |
|---|---|
| 注入外观后能否在军械库显示/装备 | **✓✓ 实机（2026-11-06 19:20）**：注入 3 件轮换页未拥有外观后，用户回报「**军械库出现三件、可装备、模型正常**」，且**商店页对这三件直接显示"已拥有"** |
| 未发布护甲能否注入 | 该护甲若不在 `/api/Progression/items` 目录里 ⇒ 与未发布武器同形，需要**双层注入**（inventory + 目录克隆）；而 `itemId`/`parentId` 语义只能从目录行反推，未发布件没有真实行可参考 ⇒ 需要构造，风险更高 |

### 8.1 外观注入的实机证据（2026-11-06）

| 项 | 值 |
|---|---|
| 注入 | `runtime/inventory_cosmetic_inject.json`，3 条：`1808786641` / `209171707` / `351568294`（`cat 3`）|
| 解出的名字 | **ARCTIC DECREE**（披风）/ **SS-500 PALE PROSECUTOR**（护甲 + 头盔，同套装 `3710087385`）|
| 客户端实见 | 服务端真值 `968` + 167（24 武器 + 140 附件 + 3 外观）= **1135** 条 |
| 日志 | `ITEMS REWRITE +3 entries`（19:19:56）· `INV REWRITE +167 -0 items`（19:20:01）|
| 实机 | **军械库出现三件、可装备、模型正常** —— 无资源驻留补丁 |
| **额外发现** | **商店页把这三件显示为"已拥有"** ⇒ 商店 UI 的拥有判定**也读同一份 `/api/Progression/inventory`** 响应，不是查购买记录 |

⇒ 外观与武器/附件共用同一个"拥有层"，一次注入同时作用于**军械库 + 超级商店**两个界面。
⇒ 同时也再次印证注入不写回：同一会话的服务端真值是 `965 → 968`（正好是三次真实购买的 +3），注入的三件一件都没进去。

### 8.2 找"未发布外观"：判据与候选（2026-11-06）

**id 语义（先钉死，否则注入必然错）**：解 `generated_customization_armor_sets.dl_bin`（422 组）后逐行对表——

| 事实 | 读数 |
|---|---|
| 外观表行 id = 服务器目录的 **`itemId`**（内容定义）| 385/422 行能在 `items` 里按 `itemId` 命中 |
| **拥有判定用的是目录 `mixId`**（每件实例键）| 命中目录的 385 行里，**253 行 `itemId != mixId`**；"已拥有"的判定 `mixId` 命中 **239** 行、`itemId` 只命中 65 行 |
| `itemId == mixId` 的 132 行 | 多为披风/简单件（如 ARCTIC DECREE）|

⇒ **给外观注入不能只塞外观表的 id**：要么用目录行里真实的 `mixId`（已发布件），要么**连目录行一起伪造**
（`{itemId: 外观表id, mixId: 自造, progressionCategory: 3}` + inventory 行）。

**"未发布"判据的坑**：拿 `Progression/items` 当已发布清单对 422 行 → 37 行不在目录，
但其中 **22 行有名字且是明确的战团护甲/披风**（B-16 Battle-Scarred Veteran、CM-09 Bonesnapper、
SC-30 Trailblazer Scout、FS-05 Marksman、KDM-73 Dragoon、Beacon of Mercy、Drape of Glory…）
⇒ **`Progression/items` 只覆盖可单独购买的物品，不含战团外观**，不能用它判"未发布"。

**当前最强候选**（三条同时成立：外观表里**没有名字** + 不在目录 + 未拥有）共 **15 行**：

| id | 行大小 | 推测类型 |
|---|---|---|
| `0x135C4274` `0x6B619174` `0x732693A1` `0x9F212504` | 2712 | 护甲（大行）|
| `0x8C6B78E3` `0x0FB65A0E` `0xF6AE9439` `0xFE3437E9` `0xA57E78BA` `0x9B5BC520` `0x0BEB97BC` `0xDA9EBB65` `0x1FE1655F` `0x5EB11243` `0x0B84E99D` | 200 | 头盔/披风（小行）|

> ⚠ 保留项：本地字符串表是 **build 26088801**，而游戏是 `26251122`。所以"没名字"可能是**名字较新**而非"未发布"。
> 这一层不用去提取当前 build 的字符串也能判——**注入一次看军械库**：显示名字 ⇒ 是"名字较新"（已发布），
> 显示空名/占位 ⇒ 真未发布。

产物：`out/armor-names/armor_rows_parsed.json`（422 行解析）、`unreleased_candidates.json`（15 行候选）、
`store-cosmetics-20261106.json`（已解名字）。

### 8.3 未发布外观的"双层伪造"→ **否证**（2026-11-06 19:41 实机）

目标 `0x135C4274`，`armor_kit_weight.py` 解出的特征：

| 项 | 值 |
|---|---|
| 名字 | **无本地化名字**（locid `832682045` / `750446850` 不在 strings-26088801）|
| 重量档 / 三围 | **medium**，档位 `111111111`；**rating 100 · speed 500 · stamina 100** |
| 被动 | **0 = STANDARD ISSUE（无被动）** |
| itemId / 套装 id | `0x135C4274` / `0xACAEFB2E`（2897148718）|

伪造了两层：

| 层 | 内容 |
|---|---|
| 目录 `items` | `{itemId: 0x135C4274, parentId: 0xACAEFB2E, mixId: 0xF1420000, progressionCategory: 3, buyPrice: [], sellPrice: []}`（模板 = DP-8 护甲行 `2846302183`）|
| 库存 `inventory` | `{mixId: 0xF1420000, amount: 1}`（**同时保留**已验证的 3 件作对照）|

送达确认：`ITEMS REWRITE +4 entries` / `INV REWRITE +168 -0 items`（19:41:28 / 19:41:35）。

**结果：对照组 3 件照常出现，新件不出现。** 两种解释待区分：

| 假设 | 含义 | 如何区分 |
|---|---|---|
| **A. 无名 → 不显示** | 这件是真未发布（没有本地化名字），客户端把无名外观过滤掉 | 换成**有名字但目录里没有**的护甲（如 SC-30 Trailblazer Scout `0x756159E4`）做同样的双层伪造：出现 ⇒ A 成立 |
| **B. 伪造目录行不被接受** | 客户端只认服务端真实下发的目录行（与 R/40-K 附件伪造的失败一致）| 同上：不出现 ⇒ B 成立 |

⇒ 结论边界（当前）：**已发布但账号未拥有的外观 = 一层注入（✓✓ 已实机）；未发布外观 = 双层伪造，未通过（✗ 2026-11-06）**。

### 8.4 用户纠正后的口径修正（2026-11-06 19:49）：外观有**两条**拥有通道

用户指出 **SC-30 Trailblazer Scout 账号已拥有**（Helldivers Mobilize! 初始战团）。用数据核对，我上一节的候选判据被推翻：

| 检查 | 读数 |
|---|---|
| inventory 968 条里有多少 id **不在** `Progression/items` 目录 | **0 条** ⇒ inventory 只承载"目录里有的物品" |
| SC-30 的外观表行 id `0x756159E4` / 套装 id `0x61C5EBD6` 在目录里 | **都查不到**；也不在 inventory |
| 外观表 422 行 id ∩ inventory | 只有 **65** 行（且全部是 `itemId == mixId` 的那批）|

⇒ **外观拥有权的两条通道**：

| 通道 | 载体 | 证据 |
|---|---|---|
| **超级商店购买** | **inventory 行**（目录里带 `buyPrice` 的 `cat 3` 物品）| DP-8 三件真购买 `965 → 968`；注入 3 件 ✓✓ |
| **战团页**（含初始 Helldivers Mobilize!）| **`purchasedSeasonPassItems` 的页号**，不进 inventory | SC-30 已拥有但 inventory/目录都没有它 |

⇒ **"不在 `Progression/items`" 不能当"未发布"判据**（§8.2 那 15 行候选因此**降级**为"只有'没有本地化名字'这一条线索"，
不再是"未发布"的结论）。战团外观是否已购，要看 `purchasedSeasonPassItems` 的页覆盖，而页号→物品的映射不在已抓响应里。

⇒ §8.3 的失败解释也随之收窄：`0x135C4274` 既不是商店可购物品、也不是任何战团内容，
**"目录里没有"对它可能只意味着"不可单独购买"**。要区分"无名被过滤"还是"伪造目录行不被接受"，
需要一个**有名字但目录里没有**的目标 —— 见 §8.5。

### 8.5 A/B 区分实验：B-16 Battle-Scarred Veteran（有名字、目录里没有）

| 项 | 值 |
|---|---|
| 目标 | `0xB08E0939`（B-16 Battle-Scarred Veteran，套装 `0xDF3351D7`）|
| 特征（`armor_kit_weight --show`）| **medium**，档位 `111111111`，**rating 100 · speed 500 · stamina 100**，被动 **0 = STANDARD ISSUE**，23 部件 |
| 伪造 | 目录行 `{itemId: 0xB08E0939, parentId: 0xDF3351D7, mixId: 0xF1430000, cat 3}` + inventory `{mixId: 0xF1430000}` |
| 对照 | 保留已验证的 3 件商店外观 |
| 判读 | **出现** ⇒ 伪造目录行可用，"无名"是唯一障碍（A）<br>**不出现** ⇒ 客户端只认服务端真实目录行（B），未发布外观这条线到此为止 |

> 顺带注意：`0x135C4274`、B-16、CM-09 Bonesnapper 三件的特征完全一致
> （medium `111111111` / 100-500-100 / STANDARD ISSUE / 23 部件）—— 它们很可能是同一批"无被动中甲"，
> 区别只在有没有名字。

#### 8.5.1 结果（2026-11-06 19:53 实机）：**B-16 也不出现 ⇒ 假设 B 成立**

| 项 | 读数 |
|---|---|
| 注入送达 | `ITEMS REWRITE +4 entries` · `INV REWRITE +168 -0 items`（19:53:26 / 19:53:35）|
| 对照 3 件 | 仍在 |
| **B-16（有名字、伪造目录行）** | **不出现** |

⇒ **客户端只认服务端真实下发的目录行；伪造的 `Progression/items` 记录对 `cat 3` 外观不被接受。**
⇒ **外观注入的硬边界 = 服务端必须已经有这件物品**（= 它必须已发布且可单独购买）。
⇒ "未发布外观"这条代理路线**到此为止**（要做得走 dl_bin / 本地数据，与代理无关）。
⇒ `§8.2` 那 15 行候选**不再是未发布结论**，只保留"没有本地化名字"这一条线索。

**一个待解释的不对称（重要）**：配方 B 给**武器**（`cat 1`）伪造目录行是**成功过**的
（LAS-22 / P-41 / SG-8F 靠 `{id, template}` 克隆上架），但同样的手法对 `cat 3` 外观（本次）和
`cat 2` 附件（R/40-K 那次）**都无效**。差别可能在客户端对这三类各自用了不同的"目录 → 显示"路径：
武器走 LoadoutEntry/注册表，外观/附件另有本地绑定表。这条留作后续。

**仍可作最后一搏的变量**：本次伪造行的 `buyPrice` 是空数组；真实商店行都带
`buyPrice:[{mixId:3481751602, amount:N}]`。若怀疑客户端按"可购买"过滤，可补上 `buyPrice` 再试一次（未做）。

---

## 10. 类别探测台账（每轮只放一个 `progressionCategory` 的全部未拥有项）

工具：`tools/category_inject.py`（`--list` 看各类别 总数/已拥有/未拥有；`--cat N` 写
`runtime/inventory_probe_inject.json`）。该文件是**第五个独立开关**，与武器/附件/外观/战备互不影响。

### 10.1 总量表（读数 2026-11-06 21:10，服务端 inventory 969 条）

| cat | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 13 | 14 | 15 | 17 | 18 | 19 | 20 | 21 | 23 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 未拥有 | 29 | 1175 | 188 | 166 | 13 | 23 | 8 | 8 | 53 | **108** | 30 | 5 | 1 | 7 | 2 | 8 | 19 | 6 | 32 | 51 |

已知语义：`cat 1` 武器 · `cat 2` 附件 · `cat 3` 外观（护甲/头盔/披风）· **`cat 5` Booster** · **`cat 8` VICTORY POSE（胜利姿势）** ·
`cat 9` 横幅 · `cat 11` 战备许可 · `cat 13` 语音包 · `cat 17` 内衬 · `cat 18` 货币 · `cat 23` 称号；
`cat 0` **Warbond（战团）** · `cat 10` 已实测**不产生可见 UI 变化**（108 条全量注入无反应）。
> 更正：此前据 `avatarCustomization.victory_pose_index` 把姿势记在 `cat 7`，R3 证明**可解锁的胜利姿势在 `cat 8`**；
> **`cat 7`（32 条 / 24 已拥有 / 8 未拥有）的假设 = EMOTE（另一个动作项目）** —— 用户 2026-11-06 提出；
> 与 `cat 8` 数量级相近，符合「姿势 + Emote 各一类」的结构；待 R5 用全量注入验证。

### 10.2 轮次结果

| 轮次 | 类别 | 注入量 | 结果 |
|---|---|---:|---|
| 预探 | 每类各 1 件（10 类共 10 件）| 10 | 用户观察：**载具涂装 / Booster / 个人资料外观** 三处有变化（但 10 类混在一起，无法归因）|
| **R1** | **`cat 10`** | **108**（该类全部未拥有）| **无可见变化** ⇒ `cat 10` 不由客户端 UI 渲染（或只在特定上下文生效）|
| **R2** | **`cat 5`** | **13** | **= Booster（配装增益）✓✓** 用户确认「这轮是 Booster」|
| **R3** | **`cat 8`** | **8** | **= VICTORY POSE（胜利姿势）✓✓** 用户确认 |
| **R4** | **`cat 21`** | **32** | **无变化** ✗（32 条全部未拥有仍无反应 ⇒ 不由 UI 渲染）|
| **R5** | **`cat 7`** | **8** | **= EMOTE ✓✓**（出现新动作/表情）；但用户补充：**姿势与 Emote 有共用项，两类不能彻底切分** |
| **R6** | **`cat 4`** | **166** | **= 载具涂装选项 ✓✓**（用户确认；这也解释了预探轮“战备改装相关像载具涂装”的观察）|
| **R7** | **`cat 0`** | **119** | **= WARBOND（战团）✓✓✓** 用户回报：**“会解锁所有的 Warbonds”** —— 注入未拥有的 119 条后，全部战团在客户端变为可用 |
| **R8** | **`cat 6`** | **23** | 待测（全消费型、全部未拥有）|

`cat 10` 结构特征：111 条里 **108 条带 `parentId`，parent 全部是 `cat 11`（战备许可）**，
74 条 `isConsumable`，部分带 8 个 tags ⇒ 原假设是"战备的子项（变体/弹药/升级）"，**R1 否证了它在 UI 上的可见性**。

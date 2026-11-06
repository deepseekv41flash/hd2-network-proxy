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

**战备不在这条线里**：59 个已抓端点无战备解锁载体，唯一通道是 GWE `effectType=32` 的星球/全局临时配发；
永久解锁只能走数据表 `generated_stratagem_settings +0xC8`。见 [API-ENDPOINTS](API-ENDPOINTS-2026-11-01.md) §7。

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
| 永久解锁战备（代理） | **✗ 无载体** | 只能 `+0xC8` 数据表路线 |
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
| **未发布护甲**能否注入 | 该护甲若不在 `/api/Progression/items` 目录里 ⇒ 与未发布武器同形，需要**双层注入**（inventory + 目录克隆）；而 `itemId`/`parentId` 语义只能从目录行反推，未发布件没有真实行可参考 ⇒ 需要构造，风险更高 |
| 注入外观后**能否在军械库显示/装备** | 机制上判"拥有"看 inventory，但外观还要在本地 `customization_armor_sets` 里找得到对应行并解析出模型 ⇒ **待实机**（已备好 3 件轮换页未拥有外观的单变量实验，`runtime/inventory_cosmetic_inject.json`）|

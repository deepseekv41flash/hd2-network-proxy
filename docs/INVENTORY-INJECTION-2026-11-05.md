# 用代理把「未拥有物品」塞进账号（inventory 注入）— 2026-11-05

> 起因：`repo-datamined` 那边查明 **军械库的成员资格 = 服务端 `/api/Progression/inventory` 里拥有的 `mixId`**
> （见 `docs/tables/WEAPON-CUSTOMIZATION-26251122.md` §13）。于是自然想到：**用 GWE 代理改写这个响应**，
> 就能让游戏以为某件物品已拥有/已解锁 —— 不需要加载器、不需要 dl_bin。

## 1. 端点与响应形状

`GET /api/Progression/inventory`（登录后拉取；本次 66,855 B）：

```jsonc
{
  "items": [ {"mixId": 1945105139, "amount": 1, "isDiscovered": false}, ... ],   // 951 条 = 拥有的物品
  "customization": [ {"mixId32": 4161086429, "index": 0, "activeIndex": 0,
                      "slots": [1896165189, 2003229240, 3171207820, 0,0,0,0,0],
                      "modes": [0,0,0,0]}, ... ],                                  // 玩家改装状态（L2）
  "loadouts": [], "limitSettings": {...}, "avatarCustomization": {...}
}
```

要点：

- `items[].mixId` 与 `LoadoutEntryComponentData +0x0` 同一个 id 空间（交叉命中 83 个武器/投掷物）；
- **支援武器/背包不在 items 里**（其 `+0x0` 是家族/包声明 id），所以军械库看不到它们；
- `customization` 里连**未拥有的 LAS-22**（`mixId32 = 2112173638`）都有条目，`slots` 恰好是它的默认配件
  —— 说明服务端物品库本来就有它，缺的只是"拥有"这一条；
- 另有 `GET/PUT /api/Progression/Items/Customize/v2`（改装保存走这条，见 API-ENDPOINTS-2026-11-01.md §2）。

## 2. 我们加的改写钩子（`tools/war_proxy.py`，本机 `D:\Downloads\variant_mod`）

- 常量：`INV_PATH = "/api/Progression/inventory"`、`INV_STATE = runtime/inventory_inject.json`
- 钩子：`_gwe_inventory_rewrite(plain)` —— 只动 `items` / `customization` 两个数组；返回 `(new_body, added, removed)`
- 接线：handler 里在 Status 改写分支后面加 `elif (not passthrough) and INV_PATH in path and rbody:`，
  改写后走同一套 `_fix_headers`（修 Content-Length / 去 chunk / 去 gzip 标记）
- 开关：`runtime/inventory_inject.json`，**每次请求现读**，改完立即生效、无需重启

```jsonc
{"enabled": true,
 "items":  [{"mixId": 2112173638, "amount": 1, "isDiscovered": false}],   // 注入"拥有"
 "remove": [2307301438],                                                  // 反向：让它看起来没有（做对照）
 "customization": [{"mixId32": 4161086429, "index": 0, "activeIndex": 0,
                    "slots": [1896165189, 3905063732, 2163992125, 0,0,0,0,0], "modes": [0,0,0,0]}]}
```

（`enabled=false` 即恢复原样；代理需以**非 passthrough**模式启动才会改写。）

## 3. 本轮实机实验（2026-11-05 22:15 起）

| 注入 | 值 | 目的 |
|---|---|---|
| 添加 LAS-22 Shear | `mixId = 2112173638`（`0x7DE53646`）| 未发布武器能否**只靠服务端"拥有"**出现在军械库 |
| 移除 R-63 Diligence | `mixId = 2307301438`（`0x8986A03E`，已拥有）| **对照**：如果它从军械库消失 ⇒ 军械库确实读这份清单 |

配置落地：`config.json.targets = []`（不动机场/战况）、`runtime/selection.json.enabled = false`，
代理以 rewrite 模式运行（PID 见 `logs/proxy.pid`，443 监听）。日志里会出现 `INV REWRITE +1 -1 items`。

判读表：

| 现象 | 结论 |
|---|---|
| Diligence 从 PRIMARY 消失 | 军械库读 inventory ⇒ **拥有层可被代理改写**（重大能力）|
| LAS-22 出现且可装备 | 客户端不需要"内置 item 目录"也认这个 id ⇒ 未发布武器可**零代价、免加载器**上架 |
| Diligence 消失但 LAS-22 不出现 | 拥有层成立，但客户端还要求内置物品目录（game.dll 的 2928 条记录）里有该 id ⇒ 只能解锁"目录里已有但没买"的内容 |
| 两者都没变 | 军械库不读这份响应（或有更强缓存/校验）⇒ 换 `Items/Customize/v2` 或其它端点再试 |
| 启动即崩 | 未知 id 让客户端炸了 ⇒ 先只留 remove 做对照，再加 LAS-22 单独试 |

### 3.1 那轮的实际结果（审计日志 + 后续实机）

`logs/audit.log` 把当夜的两轮改写完整记下来了：

```
2026-11-05T22:17:19 INV REWRITE +1 -1 items      ← 第一轮：+LAS-22(2112173638) −R-63 Diligence(2307301438)
2026-11-05T22:26:15 ITEMS REWRITE +1 entries     ← 第二轮起：加「目录克隆」钩子
2026-11-05T22:26:28 INV REWRITE +1 -0 items      ← 不再移除，只加
2026-11-05T22:34:55 ITEMS REWRITE +1 entries     ← 之后每轮重启都是这一对
2026-11-05T22:35:02 INV REWRITE +1 -0 items
2026-11-05T22:41:22 ITEMS REWRITE +1 entries
2026-11-05T22:50:37 ITEMS REWRITE +1 entries     ← 最终一批（UNRELEASED §9 的 24+3 件）
```

判读结果：

| 观察 | 结论 |
|---|---|
| 第一轮（只有拥有层，+LAS-22 −Diligence）**LAS-22 没出现** | ⇒ 客户端还要求**内置物品目录**里有这个 `mixId`，"拥有"一条不够 |
| 于是 22:26 起加 `items` 目录克隆（`_gwe_items_rewrite`，`{id, template}` 从同族模板复制一条目录记录） | ⇒ **未发布物品 = 双层注入**（inventory + items）|
| 反过来，**目录里本来就有**的物品（如 LAS-13）只加拥有层就上架了（repo-datamined `UNRELEASED-INVENTORY` §9.1 实机结论） | ⇒ **已发布未购买 = 单层注入** |

即三分法的成本表就在这一夜里定型：**已拥有 = 免费 · 已发布未购买 = 1 层 · 未发布 = 2 层**。

⚠ 缺口：第一轮的**对照回执**（Diligence 当时是否真的从 PRIMARY 消失）没有单独记档 —— 那一轮之后
配置立刻改成了 `-0`（只加不删），所以"军械库读 inventory"这条是靠后续 LAS-13 单层成功**反推**成立的，
不是当夜直接观测。若要留直接证据，需再做一次纯 `remove` 对照（成本 1 分钟，重启游戏看 PRIMARY）。

## 4. 边界

- 只改**客户端看到的响应**；服务端仍认为你没买。任何"把配装/战绩回传"的请求都会以服务端数据为准，
  所以这是**纯本地效果**（和 dl_bin/加载器同一风险级别）。
- 不涉及 EAC 进程；风险面 = 与既有 GWE 变种注入相同（自签证书 + hosts），不新增攻击面。
- 证书每次续期 ≤2 天（`gen_session_certs.py` 自检），过期后 443 停听，属已知坑。

## 5. 2026-11-06 实测核验：所有权不回写，只有改装状态回写

`tools/war_proxy.py` 的抓包点在**改写之前**（`_gwe_capture_dump` 在 661 行，两个 rewrite 在 742/759 行），
所以 `*_api_Progression_inventory.json` 是**服务端真值**，可以直接拿来验"注入有没有被服务端接受"。

拿注入清单的 `mixId` 去比服务端 inventory：

| dump | 时间 | mixId 数 | 命中注入物 |
|---|---|---|---|
| `123a8ee9` / `26a026a2` | 10-29 | 951 | 0 |
| `51a32514` | 11-06 | 963 | 3（`0B4761B8` / `77E1231D` / `818A2931`）|

命中的 3 件**账号本来就已拥有**（用户确认），属正常进度 ⇒ **LAS-22 / P-41 / SG-8F 及其余 21 件在服务端 inventory 里一条都没有，
所有权注入不写回账号。**

例外：`Items/Customize/v2` 的改装槽（`{mixId32, modes[4], activeIndex, customizations[{index,slots[8]}]}`）**会被客户端 PUT 上去**，
同一会话内条数 59→64→65→66→67，新增的正是我们注入后改装过的 LAS-13 / MP-98 / R-4 / SMG-203。
67 条里 18 条属于服务端不拥有的武器。**痕迹性质：只记改装槽，不含所有权**，别的客户端仍拿不到该武器。

结论与 §4 一致并已实证：**纯本地效果**，可以做注入实验不用担心污染账号。

配置已版本化到 `configs/inventory_inject.json`（24 条 = 21 条已发布未购买 + LAS-22/P-41/SG-8F）与
`configs/items_inject.json`；线上生效副本仍在 `D:\Downloads\variant_mod\runtime\`。

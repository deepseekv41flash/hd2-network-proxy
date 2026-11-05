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

## 4. 边界

- 只改**客户端看到的响应**；服务端仍认为你没买。任何"把配装/战绩回传"的请求都会以服务端数据为准，
  所以这是**纯本地效果**（和 dl_bin/加载器同一风险级别）。
- 不涉及 EAC 进程；风险面 = 与既有 GWE 变种注入相同（自签证书 + hosts），不新增攻击面。
- 证书每次续期 ≤2 天（`gen_session_certs.py` 自检），过期后 443 停听，属已知坑。

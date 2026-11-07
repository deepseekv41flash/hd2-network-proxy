# 代理运维坑（2026-11-05 夜的实战记录）

> 这三条都在 2026-11-05 夜里真实卡过时间：证书过期让 443 直接停听、抓包钩子少一个环境变量就一片空白、
> gitbash 的路径转换让过滤条件永远不命中。写下来省下一次。

## 1. 会话证书 2 天到期 —— 症状是"游戏连不上/没有任何请求"

自签 CA 的会话证书由 `gen_session_certs.py` 限制在 **≤ 2 天**（脚本自带 `self_check`）。
过期后代理 **443 端口直接停听**，游戏侧表现为登录失败或干脆没有任何 `/api/*` 请求，
日志里也看不出"证书过期"，容易误判成 hosts 被改回、代理没起。

**2026-11-04 19:47 就发生过一次**，现象与"代理没启动"完全一样。

续期流程（不需要 UAC，`certutil -user` 装 CurrentUser 根）：

```bash
# ① 先停干净（443/8080 都要确认无监听）
powershell -File stop.ps1
netstat -ano | grep -E ":443|:8080"

# ② 重签（2 天上限）
python tools/gen_session_certs.py --out-dir certs --mode ca --days 2 --force

# ③ 装根（CurrentUser，免 UAC）
certutil -user -addstore Root certs/anchor.cer

# ④ 起代理
powershell -File run.ps1 -Passthrough
```

验证：新指纹（2026-11-05 那次是 `315EEF46F8242F4AEA1C13CB836DA1EF490B901A`）、
有效期到 `2026-11-07 21:38 +08`、CRL `http://127.0.0.1:8080/ca.crl` 返回 200、
游戏侧 `POST /api/Account/Login` / `GET /api/lobby` / `PUT /api/lobby` 全 200。

> 到期日是硬约束：**每次开工先看一眼证书 NotAfter**，别等游戏连不上再查。

## 2. 抓包要同时设两个环境变量

```bash
HD2_GWE_DUMP=D:/mod/out/gwe                          # 输出目录（必需）
HD2_GWE_PATHS="api/"                                 # 抓哪些响应（必需，注意写法见 §3）
HD2_GWE_REQ_PATHS="api/Operation,api/lobby,api/Progression"   # 抓哪些请求体（可选）
```

只设 `HD2_GWE_DUMP` 时，默认只抓 `/api/WarSeason/GalacticWarEffects` —— 游戏照常跑、代理照常转发，
但目录里只有 GWE 那一种，看起来像"什么都没抓到"。2026-11-05 因此白等了一轮。

**第二个同类坑（2026-11-06）**：请求体白名单默认只有 `/api/Operation`。
结果是明明在日志里看到了 `POST /api/Progression/ProgressionPackage/AcquireUnlockableItem`（配件解锁）
和 `PUT /api/Progression/Items/Customize/v2`（改装保存），**body 却一个都没落盘**，只有路径和字节数。
现已把默认改为 `/api/Operation,/api/lobby,/api/Progression/Items/Customize`，并给请求体文件名加上方法标签
（`req_PUT_<hash>_<path>.json`），便于区分"读"和"写"。

> 判断"抓全了没"的最快方法：看 `logs/proxy.log` 里出现过的路径，去 `out/gwe/index.txt` 里对一遍。
> 只有 REQ 没有对应 dump，就是白名单漏了。

## 3. gitbash 会把 `/api/` 转换成 Windows 路径

在 gitbash 里写：

```bash
HD2_GWE_PATHS=/api/                     # ✗ 被 MSYS 转换成 C:/Program Files/Git/api/
```

结果 `p.startswith/ in path` 的过滤条件永远不命中，抓包目录依旧空白。两种正确写法：

```bash
HD2_GWE_PATHS="api/"                    # ✓ 不带前导斜杠
MSYS_NO_PATHCONV=1 HD2_GWE_PATHS=/api/  # ✓ 关掉转换
```

启动后**先从日志确认生效**：会打印 `env ok: api/ D:/mod/out/gwe`，没有这行就说明环境变量没进去。

## 4. 一次完整登录的抓包覆盖面（用于判断"抓全了没"）

完全退出游戏 → 起代理 → 启动游戏 → 进大厅 → 进军械库，一轮能拿到：

| 指标 | 实测值（2026-11-05） |
|---|---|
| 响应文件 | **24 个** |
| 不同端点 | **19 个** |
| 最大的一份 | `Progression/inventory` 66,855 B / **963 条** |

覆盖到的关键端点：`Account/Login`、`lobby`（GET+PUT）、`Progression`、`Progression/items`(3020)、
`Progression/inventory`、`Progression/Items/Customize/v2`、`Progression/levelspec`、
`Progression/ItemPackages`、`Progression/ProgressionPackages`、`WarSeason/801/Status`、
`WarSeason/801/timeSinceStart`、`WarSeason/GalacticWarEffects`、`SeasonPass`、
`Episode/801/status`、`NewsFeed`、`v2/Assignment/Player`、`Operation`、`Operation/Create`、
`Operation/Mission/*`、`Stats/war/801/summary`。

> 若游戏在代理起之前就已在运行，只能抓到轮询尾巴（`Status`/`timeSinceStart` 的重复），
> `Account/Login` 与 `inventory` 都会缺 —— **必须完全退出游戏再起代理**。

## 5. 全量抓包与"解锁前后对表"

要让一次**真实操作**（如护甲解锁）留下可分析的证据，光抓响应不够，请求体也得抓：

```bash
HD2_GWE_DUMP="D:/mod/out/gwe/<session>"   # 独立目录，别和旧会话混在一起
HD2_GWE_PATHS="api/"                       # 所有 /api/* 响应
HD2_GWE_REQ_PATHS="api/"                   # 所有请求体（默认只抓 Operation/lobby/Progression）
HD2_GWE_MAX="33554432"                     # 32 MB
```

启动日志会打印实际生效值：`抓包 dump=… paths=api/ req=api/`（2026-11-06 起不再是写死的"不落盘请求体"）。

对表工具 `tools/capture_diff.py`（两个会话比 / 同一会话按时间切前后）：

```bash
# 两次会话对比（旧会话 vs 新会话）
python tools/capture_diff.py --old D:/mod/out/gwe --new D:/mod/out/gwe/armor-20261106 --only inventory,Progression

# 同一目录内按 UTC 时间切分：登录时抓的当基线，解锁后的当变化
python tools/capture_diff.py --old <dir> --new <dir> --split 20261106T111500Z

# 只看 id 增删（列表里的 mixId/mixId32/itemId 等）
python tools/capture_diff.py ... --ids
```

它会按 `index.txt` 的 UTC 时间戳把捕获分成"前/后"，直接列出：新出现的端点与请求体、
内容变化的响应、以及**列表里新增/移除的 id**（例如 `items 963 -> 965` 后跟着两条新 `mixId`）。

> 抓包目录里的请求体含登录凭据与大厅 `connectionString` —— `out/` 已在 `.gitignore`，任何抓包文件都不入库。

## 停代理 = 断网（hosts 仍然指向本机）——2026-11-07 再犯一次

做纯数据表（dl_bin）实验时把代理 `stop.ps1` 停掉了，但 `hosts` 第 16 行仍把
`api.live.prod.thehelldiversgame.com` 指向 `100.67.169.17`，443 无人监听 ⇒ 游戏登录报
**`Request 649,790,637 / Error 7 / Status -1`**（注意：**Error 7 = 传输层没连上**，
和 `Error 35 = TLS 握手失败（证书过期）`、`Error 0 / Status -2 = 服务器回了但客户端拒绝数据` 是三类不同故障）。

**规矩**：只要 hosts 劫持还在，代理就必须以某种模式常驻 —— 做文件侧实验时用
`.\run.ps1 -Passthrough`（纯转发、零改写），不要 `stop.ps1`。要真停就先跑 `teardown.ps1`（管理员）回收 hosts。
恢复手法：`.\run.ps1 -Passthrough` → 验证 `443 可达=True`、`CRL=200`、经代理拉一次 Status 得 200。

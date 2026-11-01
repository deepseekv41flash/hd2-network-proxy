#!/usr/bin/env python3
"""api_inventory.py -- 从 variant_mod 代理日志盘点「游戏访问了哪些 API」。

数据源（只读）
    D:/Downloads/variant_mod/logs/proxy.log.1   已轮转的旧日志（大）
    D:/Downloads/variant_mod/logs/proxy.log     当前日志
    行格式：`HH:MM:SS REQ <METHOD> <path> <size>B`

局限
    只覆盖 hosts 劫持的 `api.live.prod.thehelldiversgame.com` 这一个主机；
    Steam / CDN / PlayFab 等其它主机的流量不经过代理，本表看不到。

产物
    out/gwe/api-endpoints.csv                   机读版（本地，out/ 不入库）
    docs/API-ENDPOINTS-2026-11-01.md            分组清单 + 重点接口 + 请求体样本
"""
from __future__ import annotations

import collections
import csv
import pathlib
import re

LOGS = [pathlib.Path("D:/Downloads/variant_mod/logs/proxy.log.1"),
        pathlib.Path("D:/Downloads/variant_mod/logs/proxy.log")]
OUT_CSV = pathlib.Path("D:/mod/work/variant-net/out")
OUT_DOC = pathlib.Path("D:/mod/work/variant-net/docs")

REQ = re.compile(r"^(\d\d:\d\d:\d\d) REQ (GET|POST|PUT|DELETE|PATCH) (\S+?)(?: (\d+)B)?$")

# 端点前缀 -> (分组, 用途)
PURPOSE = {
    "/api/WarSeason/GalacticWarEffects": ("战局", "GWE 效果目录（服务器准备的内容清单）"),
    "/api/WarSeason": ("战局", "战局状态：Status / warinfo / timeSinceStart / WarId / NewsTicker"),
    "/api/Episode": ("战局", "赛季/剧集活动状态"),
    "/api/Stats/war": ("战局", "全局战况汇总（前线/星系统计）"),
    "/api/Stats/profile": ("战局", "个人战绩汇总"),
    "/api/v2/Assignment": ("命令", "Major Order/每日命令（War/Player）"),
    "/api/Operation": ("任务", "战役操作：Create/Abandon/Mission Start/end/SetMaxRewards/ActivityV2"),
    "/api/Mission": ("任务", "任务结算：RewardEntries / Session"),
    "/api/lobby": ("大厅", "组队/当前选中星球（PUT lobby 带 planet 信息）"),
    "/api/Account": ("账号", "Login / ReportPosition（反作弊上报）"),
    "/api/Progression": ("养成", "物品/背包/等级/成就/自定义"),
    "/api/SeasonPass": ("养成", "战争债券页面数据"),
    "/api/Monetization": ("商业化", "Steam DLC/商城兑换"),
    "/api/Configuration": ("配置", "GameClient 客户端配置"),
    "/api/Pes": ("消息", "PlayFab 类：GetConfiguration/GetMessages/GetMotd/GetIngameSurvey"),
    "/api/Mail": ("消息", "邮件收件箱"),
    "/api/NewsFeed": ("消息", "新闻/公告"),
    "/api/FriendsV2": ("社交", "好友请求/最近/拉黑"),
    "/api/Proxy": ("未知", "内部代理/中继（请求体未抓，响应 0B）"),
}


def normalize(meth: str, path: str) -> str:
    p = path
    p = re.sub(r"/lobby/[0-9a-f-]{36}(\.r-[0-9a-z]+)?", "/lobby/{id}", p)
    p = re.sub(r"/(\d{3,})/(?=status|timeSinceStart|warinfo|Status|summary)", r"/{warId}/", p)
    p = re.sub(r"fromTimeStamp=\d+", "fromTimeStamp={ts}", p)
    p = re.sub(r"(offset|limit)=\d+", r"\1={n}", p)
    return p


def main() -> int:
    agg: dict[tuple[str, str], dict] = {}
    total = 0
    for f in LOGS:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = REQ.match(line)
            if not m:
                continue
            ts, meth, path, size = m.groups()
            key = (meth, normalize(meth, path))
            a = agg.setdefault(key, {"count": 0, "sizes": [], "first": ts, "last": ts})
            a["count"] += 1
            if size:
                a["sizes"].append(int(size))
            a["last"] = ts
            total += 1
    rows = []
    for (meth, path), a in sorted(agg.items(), key=lambda kv: -kv[1]["count"]):
        base = path.split("?")[0]
        group, purpose = next((PURPOSE[k] for k in sorted(PURPOSE, key=len, reverse=True)
                               if base.startswith(k)), ("其他", ""))
        sizes = a["sizes"]
        rows.append({
            "group": group,
            "endpoint": base,
            "query": path.split("?", 1)[1] if "?" in path else "",
            "methods": meth,
            "count": a["count"],
            "avg_req_bytes": (sum(sizes) // len(sizes)) if sizes else 0,
            "purpose": purpose,
        })
    OUT_CSV.mkdir(parents=True, exist_ok=True)
    with (OUT_CSV / "api-endpoints.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    groups: dict[str, list] = collections.OrderedDict()
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    lines = ["# 游戏访问的 API 清单（除 GWE 以外的全部端点）", "",
             f"> 来源：`D:/Downloads/variant_mod/logs/proxy.log.1` + `proxy.log`（最近一段会话，共 **{total}** 条请求、"
             f"**{len(rows)}** 种端点模式）。",
             "> 抓取方式：hosts 把 `api.live.prod.thehelldiversgame.com` 指到本机 MITM 代理（自签会话证书），"
             "**只覆盖这一个 API 主机**；Steam / CDN / PlayFab 等其它主机不经过代理，本表看不到。",
             "> 机读版：`out/gwe/api-endpoints.csv`（本地生成，`out/` 不入库）；生成器 `tools/api_inventory.py`。",
             "", "## 1. 分组总览", "", "| 组 | 端点数 | 请求数 |", "|---|---:|---:|"]
    for g, rs in groups.items():
        lines.append(f"| {g} | {len(rs)} | {sum(r['count'] for r in rs)} |")
    lines += ["", "## 2. 全量清单（按请求数降序）", "",
              "| 组 | 方法 | 端点 | 次数 | 平均请求体 | 用途 |", "|---|---|---|---:|---:|---|"]
    for r in rows:
        ep = r["endpoint"] + (f"?{r['query']}" if r["query"] else "")
        lines.append(f"| {r['group']} | {r['methods']} | `{ep}` | {r['count']} | "
                     f"{r['avg_req_bytes']} B | {r['purpose']} |")

    lines += ["", "## 3. 与实验最相关的接口", "",
              "- **`GET /api/WarSeason/801/Status`**：战况板（planetStatus / planetActiveEffects / campaigns / "
              "planetAttacks / planetEvents / jointOperations）——我们唯一会**改写**的响应；",
              "- **`GET /api/WarSeason/GalacticWarEffects`**：效果目录（312 条，含 type32/40/71/94）——只读抓包；",
              "- **`PUT /api/lobby`**：组队 + 当前选中星球（代理从请求体里读 `player planet`，用于粘性注入）；",
              "- **`POST /api/Operation/Create` / `Mission/Start` / `Mission/end`**：任务创建、开始、结算；"
              "Create 的请求体里带 `operationSettingsId / type / planetIndex / difficulty / missions[]`，"
              "结算请求体带 `planetEventId / healthAtStart / objectives / operationId`——都是**服务端权威**，"
              "本地伪造风险高（之前防守伪造实验已经踩过）；",
              "- **`GET /api/Stats/war/801/summary`**：全局战况（前线 63 条攻击边等）；",
              "- **`GET /api/v2/Assignment/War/801`**：Major Order；**`/api/Progression/*`**：解锁/背包（服务端权威）。",
              "", "## 4. 已抓到的请求体样本（`D:/mod/out/gwe/req_*.json`）", "",
              "```jsonc",
              '// POST /api/Operation/Create',
              '{"operations":[{"operationSettingsId":2350081063,"jointOperationId":-1,"type":0,"id":1210,',
              '  "seed":804334477,"race":2,"warId":801,"placementNodeIndex":6,"campaignId":51999,',
              '  "planetIndex":139,"difficulty":1,"missions":[{"type":1,"state":1,"index":0}]}]}',
              '// POST /api/Operation/Mission/Start',
              '{"planetIndex":156,"warId":801,"regionIndex":-1,"operationId":1221,"missionIndex":0,',
              '  "territoryIndex":12,"participants":["11893343864225233967"]}',
              '// POST /api/Operation/Mission/ActivityV2',
              '{"uniqueId":2344827714,"activityId32":2140130854,"missionId":"961f1ae0-…"}',
              '// POST /api/Operation/Mission/end（节选）',
              '{"warSeasonId":801,"type":3,"planetEventId":5729,"planetIndex":244,"healthAtStartPlanet":1400000,',
              '  "campaignId":51751,"objectives":[{"id":3846731770,"succeeded":true}],"operationId":1220,…}',
              "```", "",
              "## 5. 未知/待查", "",
              "- **`POST /api/Proxy/{a}/{b}`**（15 次，请求体 ~325–334 B，响应 0 B）：像内部中继/转发，"
              "未抓请求体（需要把捕获白名单加上该路径才能看）；",
              "- **`POST /api/Mission/Session`**（9 次，583–2431 B）：任务会话/结算前上报，响应 202/200 0 B；",
              "- **`POST /api/Pes/GetIngameSurvey`**（955 B）：局后问卷；",
              "- 其余 `Pes/*`（GetConfiguration/GetMessages/GetMotd）是 PlayFab 风格的账号侧数据。",
              "", "## 6. 复现", "", "```bash",
              "python tools/api_inventory.py     # 重新统计日志 → CSV + 本文档",
              "```", ""]
    OUT_DOC.mkdir(parents=True, exist_ok=True)
    doc = OUT_DOC / "API-ENDPOINTS-2026-11-01.md"
    doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_CSV/'api-endpoints.csv'}  ({len(rows)} endpoints, {total} requests)")
    print(f"wrote {doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

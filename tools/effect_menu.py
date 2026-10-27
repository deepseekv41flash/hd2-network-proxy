#!/usr/bin/env python3
"""effect_menu.py -- 把 GWE 效果目录 + 本地 presence 表 + 最新战况拼成一张"能跑什么"的表。

数据来源（全部只读）
    GWE      D:/mod/out/gwe/*_api_WarSeason_GalacticWarEffects.json   服务器效果目录（310 条）
    Status   D:/mod/out/gwe/*_api_WarSeason_801_Status.json            最新战况（在线效果）
    presence D:/mod/refs/dlbin/plaintext-26088801/generated_galactic_presence_settings.dl_bin
    strings  D:/mod/refs/strings-en-26088801.json                      locid -> 英文文本

presence 行关键字段（本表据此分类，实测见 variant-net docs）
    +0x14  种类   0=地图标记  1=事件作战  3=战术行动  4=敌情
    +0x18  子类   1=strain/surge 变体
    +0x1C  阵营   1=SE  2=terminid  3=automaton  4=illuminate
    +0x20  显示名 locid
    +0x24  描述   locid

用法
    python tools/effect_menu.py            # 写 docs/EFFECT-MENU-801.md 与 out/effect-menu.csv
    python tools/effect_menu.py --print    # 只打印摘要
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import pathlib
import struct
import sys

GWE_GLOB = "D:/mod/out/gwe/*_api_WarSeason_GalacticWarEffects.json"
STATUS_GLOB = "D:/mod/out/gwe/*_api_WarSeason_801_Status.json"
STRINGS = pathlib.Path("D:/mod/refs/strings-en-26088801.json")
PRESENCE = pathlib.Path("D:/mod/refs/dlbin/plaintext-26088801/generated_galactic_presence_settings.dl_bin")
REPO_TOOLS = pathlib.Path("D:/mod/work/repo-datamined/tools")

KIND = {0: "地图标记", 1: "事件作战", 3: "战术行动", 4: "敌情"}
RACE = {0: "-", 1: "SE", 2: "terminid", 3: "automaton", 4: "illuminate"}

# effectType 语义：只在有实测/对表证据时写，其余留空并标 ⚠
TYPE_HINT = {
    1: "数值参数",
    21: "数值参数",
    23: "数值参数",
    25: "数值参数",
    32: "战备引用（hash→战备）",
    36: "空间站临时装备（EXO-45/49）",
    40: "标签（与 71 严格成对）",
    56: "数值参数",
    69: "未知",
    71: "presence 引用 ← 本表主体",
    72: "未解",
    73: "未解",
    76: "未解",
    92: "未解",
}


def newest(pattern: str) -> pathlib.Path | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return pathlib.Path(max(files, key=os.path.getmtime))


def load_presences() -> dict[int, dict]:
    """hash -> {name, kind, sub, race, name_id, desc_id}；同时返回 name -> row 供反查。"""
    sys.path.insert(0, str(REPO_TOOLS))
    import planet_tables as P  # noqa: E402
    from planet_index import presence_names, murmur32  # noqa: E402

    groups = P.parse_groups(PRESENCE.read_bytes())
    names = presence_names()
    out: dict[int, dict] = {}
    for i, g in enumerate(groups):
        p = g.payload
        u = lambda off: struct.unpack_from("<I", p, off)[0]  # noqa: E731
        out[murmur32(names[i])] = {
            "name": names[i],
            "kind": u(0x14),
            "sub": u(0x18),
            "race": u(0x1C),
            "name_id": u(0x20),
            "desc_id": u(0x24),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", help="只打印摘要")
    ap.add_argument("--out-dir", default="D:/mod/work/variant-net/docs")
    ap.add_argument("--csv-dir", default="D:/mod/work/variant-net/out")
    a = ap.parse_args()

    gwe_path, status_path = newest(GWE_GLOB), newest(STATUS_GLOB)
    if not gwe_path or not status_path:
        print("缺 GWE 或 Status 抓包", file=sys.stderr)
        return 1
    gwe = json.loads(gwe_path.read_text(encoding="utf-8"))
    eff = gwe["galacticEffects"] if isinstance(gwe, dict) else gwe
    status = json.loads(status_path.read_text(encoding="utf-8"))
    strings = json.loads(STRINGS.read_text(encoding="utf-8"))
    pres = load_presences()

    live_by_id: dict[int, list[int]] = {}
    for e in status.get("planetActiveEffects") or []:
        live_by_id.setdefault(int(e["galacticEffectId"]), []).append(int(e["index"]))

    rows = []
    for e in eff:
        eid, etype = int(e["id"]), int(e.get("effectType") or 0)
        vals = e.get("values") or []
        p = None
        if etype == 71 and vals and vals[0] in pres:
            p = pres[vals[0]]
        rows.append({
            "effect_id": eid,
            "effect_type": etype,
            "type_hint": TYPE_HINT.get(etype, ""),
            "flags": e.get("flags"),
            "presence": (p or {}).get("name", ""),
            "kind": (p or {}).get("kind", -1),
            "kind_label": KIND.get((p or {}).get("kind", -1), "本地无对应 presence" if etype == 71 else ""),
            "sub": (p or {}).get("sub", ""),
            "race": RACE.get((p or {}).get("race", 0), "-"),
            "display_name": strings.get(str((p or {}).get("name_id", 0)), ""),
            "description": strings.get(str((p or {}).get("desc_id", 0)), ""),
            "live_count": len(live_by_id.get(eid, [])),
            "live_planets": " ".join(map(str, sorted(live_by_id.get(eid, []))[:12])),
            "raw_values": ",".join(map(str, vals)),
            "gameplay_effect_id32": e.get("gameplayEffectId32"),
            "evidence": "⚠ 未证",
        })

    # 实机验证过的条目（见 §8）：只有这两条走完了"注入→客户端渲染"全链
    for r in rows:
        if r["effect_id"] in (1373, 1386):
            r["evidence"] = "✓✓ 实机"

    # ---- 文件产物 ----
    outdir = pathlib.Path(a.csv_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "effect-menu.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    t71 = [r for r in rows if r["effect_type"] == 71]
    others = [r for r in rows if r["effect_type"] != 71]
    live_any = [r for r in rows if r["live_count"]]

    def md_table(rs, cols):
        """cols = [(key, 标题)]；全部左对齐，空值显示 —。"""
        head = "| " + " | ".join(c[1] for c in cols) + " |"
        sep = "|" + "|".join("---" for _ in cols) + "|"
        body = []
        for r in rs:
            cells = []
            for key, _ in cols:
                v = r.get(key, "")
                v = "—" if v in ("", None) else str(v).replace("|", "\\|")[:90]
                cells.append(v)
            body.append("| " + " | ".join(cells) + " |")
        return "\n".join([head, sep] + body)

    lines = []
    lines.append("# 可注入效果菜单（warId 801）")
    lines.append("")
    lines.append(f"> 生成自 `{gwe_path.name}`（{len(eff)} 条）、`{status_path.name}`（在线 {len(live_by_id)} 个不同 effect）")
    lines.append(f"> presence 分类依据 `generated_galactic_presence_settings.dl_bin` 的 `+0x14/+0x18/+0x1C`，见 PLANET-TABLES。")
    lines.append("")
    lines.append("## 0. 一句话")
    lines.append("")
    lines.append("**GWE 是「服务器这场战争准备好的效果清单」，不是「客户端全部内容」。** 目录里的 id 可以直接塞进 "
                 "`Status.planetActiveEffects` 生效；目录外的 id 客户端解析不出来。")
    lines.append("")
    lines.append("## 1. 总览")
    lines.append("")
    lines.append("| 项 | 数 |")
    lines.append("|---|---:|")
    lines.append(f"| GWE 目录条目 | {len(eff)} |")
    lines.append(f"| 其中 type71（presence 引用，本表主体） | {len(t71)} |")
    lines.append(f"| type71 且本地能解析 | {sum(1 for r in t71 if r['kind'] >= 0)} |")
    lines.append(f"| type71 但本地无对应 presence | {sum(1 for r in t71 if r['kind'] < 0)} |")
    lines.append(f"| 当前在线（挂在星球上） | {len(live_any)} |")
    lines.append("")
    lines.append("### 按种类（type71）")
    lines.append("")
    lines.append("| `+0x14` | 含义 | 条数 | 在线 |")
    lines.append("|---|---|---:|---:|")
    for k in sorted(KIND):
        grp = [r for r in t71 if r["kind"] == k]
        if grp:
            lines.append(f"| {k} | {KIND[k]} | {len(grp)} | {sum(1 for r in grp if r['live_count'])} |")
    unk = [r for r in t71 if r["kind"] < 0]
    if unk:
        lines.append(f"| — | 本地无对应 presence | {len(unk)} | {sum(1 for r in unk if r['live_count'])} |")
    lines.append("")
    lines.append("## 1.5 怎么把表里的一行跑起来")
    lines.append("")
    lines.append("代理只认 `variant_catalog.json` 里的**变种名**，不认裸 effect id。所以要跑表里任意一条，两步：")
    lines.append("")
    lines.append("```jsonc")
    lines.append('// 1) variant_catalog.json：加一条，ids 填本表的 effect，faction 填该条目的阵营')
    lines.append('"variants": { "my_test": [1373] },')
    lines.append('"meta":     { "my_test": { "faction": "illuminate", "mechanic": 1373 } }')
    lines.append("")
    lines.append('// 2) config.json：指到目标星球（星球游戏索引，见 PLANET-INDEX）')
    lines.append('"targets": [ { "planet": 182, "variant": "my_test" } ]')
    lines.append("```")
    lines.append("")
    lines.append("然后 `run_capture.ps1 -Rewrite` 重启代理 → **重启游戏**（Status 只在登录流程拉）→ 进目标星球。")
    lines.append("")
    lines.append("⚠ `meta.faction` 是**我们自己的过滤器**（`resolve_plan()`），不是游戏校验。实测跨阵营效果客户端照收，"
                 "所以想让 A 阵营 presence 上 B 阵营星球，把 `faction` 写成 B 即可（本表「阵营」列仍是 presence 的真实阵营）。")
    lines.append("")
    lines.append("## 2. 能发「事件作战」的（kind=1）")
    lines.append("")
    lines.append("注入后部署界面出现对应主题的作战卡（实测：`1373` → `AVERT VOID`）。")
    lines.append("")
    lines.append(md_table([r for r in t71 if r["kind"] == 1],
                          [("effect_id", "effect"), ("presence", "presence"), ("race", "阵营"),
                           ("display_name", "作战名"), ("live_count", "在线星球数"), ("evidence", "证据")]))
    lines.append("")
    lines.append("## 3. 战术行动（kind=3）")
    lines.append("")
    lines.append(md_table([r for r in t71 if r["kind"] == 3],
                          [("effect_id", "effect"), ("presence", "presence"), ("race", "阵营"),
                           ("display_name", "名称"), ("live_count", "在线")]))
    lines.append("")
    lines.append("## 4. 敌情（kind=4，进 `COMBATANT FORCES PRESENT`）")
    lines.append("")
    lines.append("实测：`1386`（`bugs_gloom`）跨阵营注入光照星球后，星图卡显示 `SPORE BURST STRAIN`，"
                 "作战界面 `COMBATANT FORCES PRESENT` 列出该项，但**不改变作战卡**。")
    lines.append("")
    lines.append(md_table(sorted([r for r in t71 if r["kind"] == 4], key=lambda r: (r["race"], r["effect_id"])),
                          [("effect_id", "effect"), ("presence", "presence"), ("race", "阵营"),
                           ("display_name", "名称"), ("sub", "+0x18"), ("live_count", "在线"),
                           ("evidence", "证据")]))
    lines.append("")
    lines.append("## 5. 地图标记（kind=0）")
    lines.append("")
    lines.append(md_table([r for r in t71 if r["kind"] == 0],
                          [("effect_id", "effect"), ("presence", "presence"), ("display_name", "名称"),
                           ("live_count", "在线")]))
    if unk:
        lines.append("")
        lines.append("## 6. 本地解析不出来（注入后大概率无显示）")
        lines.append("")
        lines.append(md_table(unk, [("effect_id", "effect"), ("raw_values", "values"),
                                    ("live_count", "在线")]))
    lines.append("")
    lines.append("## 7. 其余类型（非 type71，共 %d 条）" % len(others))
    lines.append("")
    lines.append("| effectType | 已知语义 | 条数 | 在线 |")
    lines.append("|---|---|---:|---:|")
    bytype: dict[int, list] = {}
    for r in others:
        bytype.setdefault(r["effect_type"], []).append(r)
    for t, grp in sorted(bytype.items()):
        hint = TYPE_HINT.get(t) or "⚠ 未证"
        lines.append(f"| {t} | {hint} | {len(grp)} | {sum(1 for r in grp if r['live_count'])} |")
    lines.append("")
    lines.append("## 8. 证据等级")
    lines.append("")
    lines.append("| 结论 | 等级 | 依据 |")
    lines.append("|---|---|---|")
    lines.append("| kind=1 注入 → 作战卡变化 | ✓✓ 实机 | `1373` on 182/93：卡片 AVERT VOID、`operationSettingsId` 2796992372→3194790369 |")
    lines.append("| kind=4 注入 → 星图卡 + COMBATANT FORCES | ✓✓ 实机 | `1386` on 93（跨阵营） |")
    lines.append("| 跨阵营不校验 | ✓✓ 实机 | 同上，终结族 presence 挂在 illuminate 星球 |")
    lines.append("| kind∈{0,3} 的表内其余条目可注入 | ⚠ 未证 | 同一通道、同一解析路径，但未逐条实测 |")
    lines.append("| 本地无对应 presence 的 5 条 | ⚠ 未证 | 预期客户端解析失败、无显示 |")

    md = "\n".join(lines) + "\n"
    if a.print:
        print(md[:4000])
    else:
        pathlib.Path(a.out_dir).mkdir(parents=True, exist_ok=True)
        out = pathlib.Path(a.out_dir) / "EFFECT-MENU-801.md"
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}  ({len(md)} chars)")
    print(f"wrote {csv_path}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

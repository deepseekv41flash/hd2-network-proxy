#!/usr/bin/env python3
"""gwe_full_table.py -- GWE 全量效果表 + planetActiveEffects 在线表（全类型，不只 type71）。

为什么要它
    `effect_menu.py` 只把 type71（presence）解到"能跑什么"的粒度，其余 235 条只有类型提示；
    2026-11-01 定证 type94（modifier 激活）后，很多类型已经能靠**官方字符串表**直接读出名字与描述。
    本工具把 312 条目录 + 139 条在线效果一次落成两张机读表 + 一篇总表文档。

数据源（全部只读，不启动游戏、不联网）
    GWE 目录   D:/mod/out/gwe/*_GalacticWarEffects*.json      （并集，312 条）
    战况快照   D:/mod/out/gwe/*_801_Status*.json              （最新=在线表；全部=ever 统计）
    字符串表   D:/mod/refs/strings-en-26088801.json           （locid -> 英文，24,834 条）
    presence   D:/mod/refs/dlbin/plaintext-26088801/generated_galactic_presence_settings.dl_bin
    modifier   D:/mod/refs/dlbin/plaintext-26251122/generated_modifier_settings.dl_bin（15 行）
    星球名     D:/mod/work/repo-datamined/out/planet/index-names-801.json
    战备名     D:/mod/work/repo-datamined/refs/stratagem-display-names.json（本地 145 个）

产物
    out/gwe/effects-full.csv             312 条：类型/名称/描述/值/解码目标/在线
    out/gwe/planet-active-effects.csv    当前战况逐星球逐效果
    docs/GWE-EFFECTS-FULL-26088801.md    上面两张表的可读版 + 类型语义表 + 未解清单
"""
from __future__ import annotations

import collections
import csv
import glob
import json
import os
import pathlib
import re
import struct
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, r"D:\mod\work\repo-datamined\tools")

from effect_menu import KIND, RACE, load_presences  # noqa: E402

GWE_GLOB = "D:/mod/out/gwe/*_api_WarSeason_GalacticWarEffects*.json"
STATUS_GLOB = "D:/mod/out/gwe/*_api_WarSeason_801_Status*.json"
STRINGS = pathlib.Path("D:/mod/refs/strings-en-26088801.json")
MODIFIERS = pathlib.Path("D:/mod/refs/dlbin/plaintext-26251122/generated_modifier_settings.dl_bin")
PLANET_NAMES = pathlib.Path("D:/mod/work/repo-datamined/out/planet/index-names-801.json")
TYPE32_DOC = TOOLS.parent / "docs" / "TYPE32-STRATAGEMS.md"
OLD_REPORT = pathlib.Path("D:/mod/out/gwe/report.md")
OUT_CSV = pathlib.Path("D:/mod/work/variant-net/out")
OUT_DOC = pathlib.Path("D:/mod/work/variant-net/docs")

# effectType 语义（只在有对表/实测证据时写；其余标 ⚠ + 用官方文本兜底）
TYPE_SEM = {
    1: "数值参数（ENEMY FORCE INCREASE 等，数值语义未解）",
    21: "数值参数（如 AERIAL DOMINANCE：撤离时间 -N 秒）",
    23: "数值参数（⚠ 数值语义未解）",
    25: "数值参数（如 INCREASED STARTING AMMO）",
    29: "数值开关（⚠ 未证）",
    32: "临时配发战备（values[0] = 战备 hash）✓",
    36: "DSS 空间站临时装备/加成（values[0]=hash，values[1]=百分比）✓",
    40: "星图词条 tag（hash，与 type71 成对出现）✓",
    43: "⚠ 数值（未解）",
    44: "⚠ 数值（未解）",
    45: "⚠ hash（描述=ADDITIONAL PAYOUT）",
    46: "⚠ 数值（未解）",
    47: "全局 modifier（无参，按名生效）✓",
    48: "全局 modifier（无参，按名生效）✓",
    49: "⚠ 双数值（攻击强度）",
    50: "⚠ 双 hash（未解）",
    51: "⚠ 双数值（EXPERIMENTAL SUPER SOLDIERS）",
    54: "⚠ 无参（INTEL SCANNERS）",
    55: "⚠ 无参（COMPROMISED INTEL PACKAGES）",
    56: "⚠ 百分比参数（#AMOUNT，战场弹药量）",
    59: "⚠ hash（ACCOUNTING CORRECTIONS 等）",
    61: "⚠ 数值（医疗补给）",
    63: "⚠ 数值（PLENTYFUL STIMS）",
    67: "⚠ 数值（MARKET CRASH）",
    69: "⚠ 数值（未解）",
    70: "⚠ hash（未解）",
    71: "presence 引用（values[0] = murmur32(presence 名)）✓✓",
    72: "⚠ hash+数值（15 条，未解）",
    73: "⚠ 双数值（17 条边缘，未解）",
    74: "⚠ 数值（未解）",
    76: "⚠ 无参（未解）",
    77: "⚠ 数值（未解）",
    80: "⚠ 数值（未解）",
    83: "⚠ hash（booster 自动生效）",
    87: "DSS 轨道支援效果（PLANETARY BOMBARDMENT / EAGLE STORM）✓",
    88: "⚠ 数值（EAGLE STORM 防守进度）",
    89: "⚠ 无参（ORBITAL BLOCKADE）",
    90: "⚠ 数值（未解）",
    92: "⚠ 无参（未解）",
    93: "⚠ hash+数值（未解）",
    94: "行星实验性战备变体修饰符（values[0] = generated_modifier_settings 行键）✓✓",
    95: "⚠ hash+数值（未解）",
    96: "⚠ hash（未解）",
    97: "⚠ hash（未解）",
}

STRATAGEM_DESC = re.compile(
    r"The (?:<i=1>)?(.+?)(?:</i>)? stratagem (?:is temporarily available|is available|has)"
)


def newest(pattern: str) -> pathlib.Path | None:
    files = glob.glob(pattern)
    return pathlib.Path(max(files, key=os.path.getmtime)) if files else None


def load_catalog() -> tuple[dict[int, dict], list[str], pathlib.Path]:
    """并集所有抓包（后加载的覆盖先加载的）；返回 id->effect、来源文件名、最新文件。"""
    files = sorted(glob.glob(GWE_GLOB), key=os.path.getmtime)
    merged: dict[int, dict] = {}
    for f in files:
        p = pathlib.Path(f)
        data = json.loads(p.read_text(encoding="utf-8"))
        eff = data["galacticEffects"] if isinstance(data, dict) else data
        for e in eff:
            merged[int(e["id"])] = e
    return merged, [pathlib.Path(f).name for f in files], pathlib.Path(files[-1])


def load_statuses() -> tuple[pathlib.Path, dict, list[dict]]:
    files = sorted(glob.glob(STATUS_GLOB), key=os.path.getmtime)
    latest_path = pathlib.Path(files[-1])
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    all_snaps = []
    for f in files:
        try:
            all_snaps.append(json.loads(pathlib.Path(f).read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    return latest_path, latest, all_snaps


def load_modifier_ids() -> dict[int, int]:
    """modifier_settings 15 个容器：payload 首 u32 = modifier id；返回 id -> 行号。"""
    data = MODIFIERS.read_bytes()
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, {}
    for i in range(n):
        size = struct.unpack_from("<I", data, off + 12)[0]
        payload = off + 24
        mid = struct.unpack_from("<I", data, payload)[0]
        out[mid] = i
        off = payload + size
    return out


def load_type32_doc() -> tuple[dict[int, str], dict[int, str]]:
    """从 TYPE32-STRATAGEMS.md 抽 effect_id -> 战备名、战备 hash -> 战备名（84/88 条有名字）。"""
    if not TYPE32_DOC.exists():
        return {}, {}
    text = TYPE32_DOC.read_text(encoding="utf-8")
    pat = re.compile(r"^\|\s*(\d+)\s*\|\s*`(0x[0-9a-fA-F]+)`\s*\|\s*-?\d+\s*\|\s*([^|]*?)\s*\|", re.M)
    by_effect: dict[int, str] = {}
    by_hash: dict[int, str] = {}
    for m in pat.finditer(text):
        eid, h, name = int(m.group(1)), int(m.group(2), 16), m.group(3).strip()
        if not name or "未解析" in name:
            continue
        by_effect.setdefault(eid, name)
        by_hash.setdefault(h, name)
    return by_effect, by_hash


def load_tag_pairs() -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    """从 out/gwe/report.md 的 tag/mechanic 配对表抽 (tag->[mechanic]) 与反向表（⚠ 邻接启发式）。"""
    if not OLD_REPORT.exists():
        return {}, {}
    text = OLD_REPORT.read_text(encoding="utf-8", errors="replace")
    start = text.find("## tag / mechanic")
    end = text.find("## 当前激活", start if start >= 0 else 0)
    if start < 0:
        return {}, {}
    chunk = text[start:end if end > start else len(text)]
    fwd: dict[int, list[int]] = {}
    rev: dict[int, list[int]] = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|", chunk, re.M):
        tag, mech = int(m.group(1)), int(m.group(2))
        fwd.setdefault(tag, []).append(mech)
        rev.setdefault(mech, []).append(tag)
    return fwd, rev


def load_planet_names() -> dict[int, str]:
    d = json.loads(PLANET_NAMES.read_text(encoding="utf-8"))
    return {int(r["index"]): r["name"] for r in d["mapping"]}


def fmt_vals(vals: list) -> tuple[str, str]:
    raw = ",".join(str(v) for v in vals)
    hx = ",".join(f"{(v & 0xFFFFFFFF):08x}" for v in vals)
    return raw, hx


def main() -> int:
    catalog, sources, newest_cat = load_catalog()
    latest_path, latest, snaps = load_statuses()
    strings = json.loads(STRINGS.read_text(encoding="utf-8"))
    pres = load_presences()
    mod_ids = load_modifier_ids()
    planet_names = load_planet_names()
    t32_effect_names, t32_hash_names = load_type32_doc()
    tag_fwd, tag_rev = load_tag_pairs()

    # 在线：最新快照 + 历史 ever
    live_by_id: dict[int, list[int]] = collections.defaultdict(list)
    for e in latest.get("planetActiveEffects") or []:
        live_by_id[int(e["galacticEffectId"])].append(int(e["index"]))
    ever_by_id: dict[int, set[int]] = collections.defaultdict(set)
    snap_hits: collections.Counter = collections.Counter()
    for st in snaps:
        seen: set[int] = set()
        for e in st.get("planetActiveEffects") or []:
            eid = int(e["galacticEffectId"])
            ever_by_id[eid].add(int(e["index"]))
            if eid not in seen:
                seen.add(eid)
                snap_hits[eid] += 1
    planet_owner = {int(p["index"]): int(p.get("owner", 0)) for p in latest.get("planetStatus") or []}

    # type32：战备 hash -> 名称（从官方描述文本抽，忽略 #V_ONE 占位）
    t32_names: dict[int, str] = {}
    for e in catalog.values():
        if int(e.get("effectType") or 0) != 32:
            continue
        desc = strings.get(str(e.get("descriptionGamePlayShortHash") or 0), "")
        m = STRATAGEM_DESC.search(desc)
        if m and "V_ONE" not in m.group(1):
            t32_names.setdefault(int(e["values"][0]) & 0xFFFFFFFF, m.group(1))

    rows = []
    for eid in sorted(catalog):
        e = catalog[eid]
        etype = int(e.get("effectType") or 0)
        vals = list(e.get("values") or [])
        vals_u = [v & 0xFFFFFFFF for v in vals]
        vtypes = list(e.get("valueTypes") or [])
        name = strings.get(str(e.get("nameHash") or 0), "")
        short = strings.get(str(e.get("descriptionGamePlayShortHash") or 0), "")
        long_ = strings.get(str(e.get("descriptionGamePlayLongHash") or 0), "")
        fluff = strings.get(str(e.get("descriptionFluffHash") or 0), "")

        target, target_extra, note = "", "", ""
        if etype == 71 and vals_u and vals_u[0] in pres:
            p = pres[vals_u[0]]
            target = f"presence:{p['name']}"
            card_name = strings.get(str(p["name_id"]), "")
            card_desc = strings.get(str(p["desc_id"]), "")
            tags = tag_rev.get(eid, [])
            target_extra = (f"{KIND.get(p['kind'], '?')}/{RACE.get(p['race'], '?')}"
                            + (f"；配对 tag {tags}" if tags else "")
                            + (f"/{card_name}" if card_name else "")
                            + (f"/{card_desc[:80]}" if card_desc else ""))
            name = name or card_name
            short = short or card_desc
        elif etype == 71:
            note = f"presence 键 0x{vals_u[0]:08X} 本地无对应行" if vals_u else ""
        elif etype == 32 and vals_u:
            h = vals_u[0]
            nm = t32_effect_names.get(eid) or t32_names.get(h) or ""
            target = f"stratagem:{nm}" if nm else ""
            target_extra = nm or f"战备 hash 0x{h:08X}；本地明文表无此键（未发布/无本地行）"
        elif etype == 94 and vals_u:
            mid = vals_u[0]
            row_no = mod_ids.get(mid)
            target = f"modifier 行 #{row_no}" if row_no is not None else ""
            target_extra = (f"modifier id 0x{mid:08X}" if row_no is not None
                            else f"modifier id 0x{mid:08X}（本地无此行）")
        elif etype == 40 and vals_u:
            mechs = tag_fwd.get(eid, [])
            note = f"tag hash 0x{vals_u[0]:08X}（星图词条）" + (f"；配对 mechanic {mechs}" if mechs else "")
        elif etype == 36 and vals_u:
            h = vals_u[0]
            nm = t32_hash_names.get(h, "")
            target = f"DSS 临时装备:{nm}" if nm else ""
            note = f"DSS hash 0x{h:08X}" + (f"，{vals[1]}%" if len(vals) > 1 else "")
        elif etype in (47, 48, 54, 55, 89, 92):
            target = "无参"

        if target and (name or short or t32_names.get(vals_u[0] if vals_u else -1) or etype == 94):
            decode_level = "target"
        elif target:
            decode_level = "target"
        elif name or short or long_:
            decode_level = "name"
        else:
            decode_level = "raw"
        label = name or target or target_extra or note
        live = sorted(live_by_id.get(eid, []))
        live_txt = " ".join(f"{i}({planet_names.get(i, '?')})" for i in live[:8])
        if len(live) > 8:
            live_txt += f" …共{len(live)}"
        rows.append({
            "effect_id": eid,
            "effect_type": etype,
            "type_semantics": TYPE_SEM.get(etype, "⚠ 未证/未解"),
            "flags": e.get("flags", 0),
            "value_types": ",".join(str(v) for v in vtypes),
            "values_raw": fmt_vals(vals)[0],
            "values_hex": fmt_vals(vals)[1],
            "name": name,
            "short_desc": short,
            "long_desc": long_,
            "fluff": fluff,
            "target": target,
            "target_extra": target_extra,
            "note": note,
            "label": "",
            "decode_level": decode_level,
            "label": label,
            "live_count": len(live),
            "live_planets": live_txt,
            "ever_snapshot_count": snap_hits.get(eid, 0),
            "ever_planet_count": len(ever_by_id.get(eid, ())),
            "gameplay_effect_id32": e.get("gameplayEffectId32", 0),
        })

    OUT_CSV.mkdir(parents=True, exist_ok=True)
    with (OUT_CSV / "effects-full.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- planetActiveEffects 表 ----
    pae = sorted(({"planet_index": int(x["index"]), "effect_id": int(x["galacticEffectId"])}
                  for x in latest.get("planetActiveEffects") or []),
                 key=lambda r: (r["planet_index"], r["effect_id"]))
    byid = {r["effect_id"]: r for r in rows}
    with (OUT_CSV / "planet-active-effects.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["planet_index", "planet_name", "planet_owner",
                    "effect_id", "effect_type", "effect_name", "target", "type_semantics"])
        for r in pae:
            e = byid.get(r["effect_id"], {})
            w.writerow([r["planet_index"], planet_names.get(r["planet_index"], ""),
                        RACE.get(planet_owner.get(r["planet_index"], 0), ""),
                        r["effect_id"], e.get("effect_type", ""), e.get("name", ""),
                        e.get("target", ""), e.get("type_semantics", "")])

    # 在线快照按类型
    online_by_type: dict[int, set[int]] = collections.defaultdict(set)
    online_entries_by_type: collections.Counter = collections.Counter()
    for x in pae:
        et = byid.get(x["effect_id"], {}).get("effect_type")
        if et is None:
            continue
        online_entries_by_type[et] += 1
        online_by_type[et].add(x["effect_id"])
    t32_live = [(x["planet_index"], x["effect_id"]) for x in pae
                if byid.get(x["effect_id"], {}).get("effect_type") == 32]

    # ---- 文档 ----
    bytype = collections.defaultdict(list)
    for r in rows:
        bytype[r["effect_type"]].append(r)

    def named(r):
        return bool(r["name"] or r["short_desc"] or r["target"])

    lines = ["# GWE 全量效果表 + planetActiveEffects（warId 801）", "",
             f"> 目录：{' + '.join(f'`{s}`' for s in sources)}（并集 **{len(rows)}** 条）",
             f"> 在线快照：`{latest_path.name}`（**{len(latest.get('planetActiveEffects') or [])}** 条 planetActiveEffects，"
             f"{len(latest.get('planetStatus') or [])} 颗星球）；历史快照 {len(snaps)} 份",
             "> 名称/描述：`refs/strings-en-26088801.json`（{:,} 条 locid）；presence 行与 modifier 行均为本地明文表。".format(len(strings)),
             "> 机读版：`out/gwe/effects-full.csv`、`out/gwe/planet-active-effects.csv`"
             "（`out/` 含账号 id，本地生成不入库）；生成器 `tools/gwe_full_table.py`（可重跑）。",
             "> presence 视角的可注入菜单见 [EFFECT-MENU-801](EFFECT-MENU-801.md)；本文档是全类型总表。",
             "", "## 1. 覆盖", "", "| 项 | 数 |", "|---|---:|",
             f"| 目录效果 | {len(rows)} |",
             f"| 有官方名称（nameHash 解出） | {sum(1 for r in rows if r['name'])} |",
             f"| 有官方描述（short/long） | {sum(1 for r in rows if r['short_desc'] or r['long_desc'])} |",
             f"| 目标解到具名对象（presence/战备/modifier 行） | {sum(1 for r in rows if r['target'])} |",
             f"| 只有名称/描述（值语义未解） | {sum(1 for r in rows if not r['target'] and (r['name'] or r['short_desc'] or r['long_desc']))} |",
             f"| 全 raw（名称/描述/目标都没有） | {sum(1 for r in rows if not r['target'] and not r['name'] and not r['short_desc'] and not r['long_desc'])} |",
             f"| 当前在线效果（不同 id） | {len(live_by_id)} |",
             f"| 在线条目（planetActiveEffects） | {len(pae)} |",
             f"| 出现在历史任何快照 | {len(ever_by_id)} |",
             "", "## 1.5 在线快照按类型", "",
             "| type | 语义 | 在线条目 | 不同 effect |", "|---:|---|---:|---:|"]
    for t in sorted(online_by_type):
        lines.append(f"| {t} | {TYPE_SEM.get(t, '⚠ 未证/未解')} | {online_entries_by_type[t]} | {len(online_by_type[t])} |")
    lines += ["", "## 1.6 当前在线里的关键条目", ""]
    lines.append(f"- **type32 在线 {len(t32_live)} 条**：" + "、".join(
        f"effect {eid} on 星球 {pi}（{planet_names.get(pi, '?')}）" for pi, eid in t32_live) +
        "。其中 `1427` 是**未发布战备**的临时配发（`WEAPONS EXPERIMENTATION` / 战备 hash `0x166D0C91`，"
        "本地明文表 0 命中）⇒ 属于「服务器清单领先客户端」的实例，客户端大概率解析不出该战备。")
    lines.append(f"- **type71 presence 在线 {online_entries_by_type.get(71, 0)} 条**（"
                 f"{len(online_by_type.get(71, ()))} 个不同 presence）——这是星图卡/作战界面的主体。")
    lines.append(f"- **type40 tag 在线 {online_entries_by_type.get(40, 0)} 条**（{len(online_by_type.get(40, ()))} 个不同 tag）；"
                 "tag 与 presence 成对出现，但 tag hash 与 presence 键不是同一命名空间。")
    other_live = sorted(t for t in online_by_type if t not in (32, 40, 71))
    lines.append("- 其余在线类型：" + "、".join(
        f"type {t}×{online_entries_by_type[t]}" for t in other_live) + "（多数是数值/未解解释器，见 §2）。")
    lines += ["", "## 2. 类型语义表", "",
             "| type | 语义 | 条数 | 有名称 | 目标已解 | raw | 在线 |", "|---:|---|---:|---:|---:|---:|---:|"]
    for t in sorted(bytype):
        grp = bytype[t]
        lines.append(f"| {t} | {TYPE_SEM.get(t, '⚠ 未证/未解')} | {len(grp)} | "
                     f"{sum(1 for r in grp if r['name'])} | {sum(1 for r in grp if r['target'])} | "
                     f"{sum(1 for r in grp if r['decode_level'] == 'raw')} | "
                     f"{sum(1 for r in grp if r['live_count'])} |")
    lines += ["", "## 3. 全量目录（{n} 条）".format(n=len(rows)), "",
              "| effect | type | 名称 | 目标/解码 | 在线 |", "|---:|---:|---|---|---:|"]
    for r in rows:
        nm = (r["name"] or "")[:60].replace("|", "\\|")
        tg = (r["target"] or (r["target_extra"] or "")).replace("|", "\\|")[:90]
        live = f"{r['live_count']}" if r["live_count"] else "—"
        lines.append(f"| {r['effect_id']} | {r['effect_type']} | {nm} | {tg} | {live} |")

    lines += ["", "## 4. 当前在线：planetActiveEffects 快照", "",
              f"`{latest_path.name}`：{len(pae)} 条，逐星球展开（同星球多效果合并一行）。", "",
              "| 星球 | owner | 效果（id=名称） |", "|---:|---|---|"]
    per_planet: dict[int, list[int]] = collections.defaultdict(list)
    for r in pae:
        per_planet[r["planet_index"]].append(r["effect_id"])
    for pi in sorted(per_planet):
        effs = []
        for eid in per_planet[pi]:
            e = byid.get(eid, {})
            nm = (e.get("label") or "").split("；")[0][:36]
            effs.append(f"{eid}" + (f"={nm}" if nm else ""))
        lines.append(f"| {pi} {planet_names.get(pi, '')} | {RACE.get(planet_owner.get(pi, 0), '')} | "
                     f"{'、'.join(effs)} |")

    lines += ["", "## 4.5 在线效果（按 effect 汇总）", "",
              "| effect | type | 名称 | 星球数 | 星球（名称） |", "|---:|---:|---|---:|---|"]
    for eid, plist in sorted(live_by_id.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        r = byid.get(eid, {})
        planets = "、".join(f"{i} {planet_names.get(i, '')}" for i in sorted(plist)[:12])
        if len(plist) > 12:
            planets += f" …共{len(plist)}"
        label = (r.get('label') or '').split("；")[0][:44]
        lines.append(f"| {eid} | {r.get('effect_type', '')} | {label} | {len(plist)} | {planets} |")

    lines += ["", "## 5. 未解清单（诚实标注）", ""]
    unresolved = [r for r in rows if r["decode_level"] == "raw"]
    lines.append(f"- **{len(unresolved)} 条**全 raw：既无官方名称/描述，也没有解到具名目标（" +
                 "、".join(f"type {t}×{sum(1 for r in unresolved if r['effect_type'] == t)}"
                           for t in sorted({r["effect_type"] for r in unresolved})) + "）。")
    unknown_types = [t for t in bytype if TYPE_SEM.get(t, "").startswith("⚠")]
    lines.append(f"- **{len(unknown_types)} 个 effectType** 语义仍是 ⚠：" + "、".join(map(str, sorted(unknown_types))) + "。")
    lines.append("- type40 的 tag hash 与 type71 的 presence 键不是同一命名空间（0 交集），tag→presence 的配对关系只能从 "
                 "variant 目录/实机注入确认。")
    lines.append("- type32：84/88 条已从 [TYPE32-STRATAGEMS](TYPE32-STRATAGEMS.md) 对表拿到战备名；"
                 "官方描述文本里只有 6 个 hash 能直接抽出名字（其余是 `#V_ONE` 占位）。"
                 "1426/1427/1428 三条的 hash 本地明文表 0 命中 ⇒ 对应新战备未发布。")
    lines.append("- type36 的 `values[0]` 与 type32 是**同一战备 hash 空间**（12/16 条能复用 type32 的名字，如 EXO-45/49）。")
    lines += ["", "## 6. 实机与进行中的实验（2026-11-01）", "",
              "- **type94 ✓✓ 实机**：经代理向 38 颗战役星球的 `planetActiveEffects` 注入 `1346` 后，"
              "客户端「行动变量」出现「燃烧加特林火力网」卡面，Orbital Gatling Barrage 实弹变燃烧弹；"
              "证据 `audit.log`: `REWRITE +38 entries (planet 100 -> [1346] …)`。",
              "- **CAUSTIC STRAIN ✓✓ 实机（2026-11-01 20:07）**：tag 1430 + mechanic 1431"
              "（presence `bugs_acid`，name locid 461034013）注入 100 `TRANDOR` 后，客户端出现"
              "「腐蚀变种 / CAUSTIC STRAIN」词条与描述，局内刷新腐蚀变体（喷吐腐蚀体液、死亡爆裂）。"
              "证据 `audit.log`: `REWRITE +2 entries (planet 100 -> [1430, 1431]) 变种=caustic_strain`。"
              "⇒ 「已发布但从未出现过」的变种词条可以本地激活，tag 1430 就是 1431 的配对词条（邻接推断被证实）。",
              "", "## 7. 复现", "", "```bash",
              "python tools/gwe_full_table.py        # 两张 CSV + 本文档",
              "python tools/gwe_join.py report       # presence 对表（旧）",
              "python tools/effect_menu.py           # presence 菜单（旧）", "```", ""]
    OUT_DOC.mkdir(parents=True, exist_ok=True)
    doc = OUT_DOC / "GWE-EFFECTS-FULL-26088801.md"
    doc.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {OUT_CSV/'effects-full.csv'}  ({len(rows)} rows)")
    print(f"wrote {OUT_CSV/'planet-active-effects.csv'}  ({len(pae)} rows)")
    print(f"wrote {doc}  ({len(lines)} lines)")
    print(f"named={sum(1 for r in rows if r['name'])} decoded={sum(1 for r in rows if r['target'])} live_ids={len(live_by_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

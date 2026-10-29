#!/usr/bin/env python3
"""city_campaign.py -- 落地社区《城市战役可玩化技术说明》的第一步：给代理钩子加 planetRegions 支持。

社区文档（D:/Downloads/城市战役可玩化技术说明.md）的主张
    目标星球（如 260 生化斯坦）在 `WarInfo.planetRegions` 里有原生分区定义，
    但 `Status.planetRegions` 里一条都没有 ⇒ 星球能点开、却没有可选作战。
    按原生定义补齐**缺失**的分区状态后，客户端才生成作战。

本工具做三件事（都在本仓库，不改第三方主流程）
    patch     给 war_proxy.py 的 `_gwe_apply_extra` 插入 `regions` 分支（幂等、留 .bak、语法门禁）
    spec      从真实 WarInfo 提取目标星球的原生分区定义，生成注入 spec（单行 JSON）
    selftest  用真实 Status 样本离线跑一遍，验证：补齐规则、幂等、无关星球不变

用法
    python tools/city_campaign.py patch    --proxy D:/Downloads/variant_mod/tools/war_proxy.py
    python tools/city_campaign.py spec     --warinfo out/gwe/44732b02_api_WarSeason_801_warinfo.json \\
                                           --target 260 --race 3 --campaign-type 0 --count 20 \\
                                           --out out/city_spec.json
    python tools/city_campaign.py selftest --status out/gwe/8945e8dc_api_WarSeason_801_Status.json \\
                                           --spec-text "$(cat out/city_spec.json)"
"""
from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import shutil
import sys

BACKUP_SUFFIX = ".cityregions.bak"
MARK = "# DSH-CITY-REGIONS-V1"

REGION_BLOCK = '''    # 分区状态：按原生 WarInfo 定义补齐缺失的 (planetIndex, regionIndex)。
    # 现有同编号条目一律保留（社区文档 §3.2：只补缺失）。
    regs = doc.get("planetRegions")
    if isinstance(regs, list):
        have = {(r.get("planetIndex"), r.get("regionIndex"))
                for r in regs if isinstance(r, dict)}
        for rg in cfg.get("regions") or []:
            try:
                pidx = int(rg.get("planet"))
                ridx = int(rg.get("regionIndex"))
                maxhp = int(rg.get("maxHealth"))
                own = int(rg.get("owner"))
            except (TypeError, ValueError):
                continue
            if (pidx, ridx) in have:
                continue
            entry = {
                "planetIndex": pidx,
                "regionIndex": ridx,
                "owner": own,
                "health": maxhp // 2,
                "players": 0,
                "regerPerSecond": 0,
                "isAvailable": True,
                "availabilityFactor": 1,
            }
            regs.append(entry)
            have.add((pidx, ridx))
            changed += 1
            log("REWRITE-EXTRA 补分区状态 %s" % _json.dumps(entry))
'''

ANCHOR = "    for k, v in (cfg.get(\"owner\") or {}).items():"


def load_json(p: pathlib.Path):
    raw = p.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def cmd_patch(a) -> int:
    p = pathlib.Path(a.proxy)
    s = p.read_text(encoding="utf-8")
    if MARK in s:
        print("已经打过补丁。")
        return 0
    if ANCHOR not in s:
        raise SystemExit("✗ 找不到插入锚点（proxy 版本变了？）")
    if not p.with_name(p.name + BACKUP_SUFFIX).exists():
        shutil.copy2(p, p.with_name(p.name + BACKUP_SUFFIX))
        print(f"备份 → {p.name + BACKUP_SUFFIX}")
    s = s.replace(ANCHOR, MARK + "\n" + REGION_BLOCK + ANCHOR, 1)
    p.write_text(s, encoding="utf-8")
    compile(s, str(p), "exec")
    print(f"✓ 已插入 regions 分支（{len(s)} B，语法检查通过）")
    return 0


def cmd_spec(a) -> int:
    wi = load_json(pathlib.Path(a.warinfo))
    lay = wi.get("layoutVersion")
    rows = [r for r in wi.get("planetRegions") or [] if r.get("planetIndex") == a.target]
    if not rows:
        raise SystemExit(f"✗ WarInfo 里星球 {a.target} 没有原生分区定义")
    if a.layout and lay != a.layout:
        raise SystemExit(f"✗ layoutVersion 不匹配：{lay} != {a.layout}")
    spec = {
        "campaigns": [{"planet": a.target, "id": a.camp_id, "type": a.campaign_type,
                       "count": a.count, "race": a.race}],
        "regions": [{"planet": a.target, "regionIndex": r["regionIndex"],
                     "owner": a.race, "maxHealth": r["maxHealth"]} for r in sorted(
                        rows, key=lambda x: x["regionIndex"])],
    }
    text = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"→ {a.out}")
    print(f"星球 {a.target}：原生分区 {len(rows)} 条（regionIndex "
          f"{[r['regionIndex'] for r in rows]}），layoutVersion={lay}")
    print(text[:400] + ("…" if len(text) > 400 else ""))
    return 0


def cmd_selftest(a) -> int:
    st = load_json(pathlib.Path(a.status))
    spec = json.loads(a.spec_text)
    tgt = spec["campaigns"][0]["planet"]
    regions = st.setdefault("planetRegions", [])
    before = len(regions)
    other_planets_before = {p: [r for r in regions if r["planetIndex"] == p] for p in
                            {r["planetIndex"] for r in regions}}

    def apply_regions(doc):
        added = 0
        have = {(r.get("planetIndex"), r.get("regionIndex")) for r in doc["planetRegions"]
                if isinstance(r, dict)}
        for rg in spec.get("regions") or []:
            key = (rg["planet"], rg["regionIndex"])
            if key in have:
                continue
            doc["planetRegions"].append({
                "planetIndex": rg["planet"], "regionIndex": rg["regionIndex"],
                "owner": rg["owner"], "health": rg["maxHealth"] // 2, "players": 0,
                "regerPerSecond": 0, "isAvailable": True, "availabilityFactor": 1})
            have.add(key)
            added += 1
        return added

    n1 = apply_regions(st)
    n2 = apply_regions(st)          # 幂等检查
    after = [r for r in st["planetRegions"] if r["planetIndex"] == tgt]
    untouched = all([r for r in st["planetRegions"] if r["planetIndex"] == p] == v
                    for p, v in other_planets_before.items())
    print(f"样本 layoutVersion={st.get('layoutVersion')} warId={st.get('warId')}")
    print(f"planetRegions: {before} → {len(st['planetRegions'])}（第一次补 {n1} 条，第二次 {n2} 条）")
    print(f"目标星球 {tgt} 现有分区: {len(after)} 条")
    for r in after[:10]:
        print("   ", json.dumps(r, ensure_ascii=False))
    checks = [
        ("补齐数量 = spec 里的定义数", n1 == len(spec.get("regions") or [])),
        ("重复处理不新增（幂等）", n2 == 0),
        ("health = maxHealth // 2", all(r["health"] * 2 in (d["maxHealth"], d["maxHealth"] - 1)
                                       for r, d in zip(after, spec["regions"]))),
        ("isAvailable = true / availabilityFactor = 1",
         all(r["isAvailable"] is True and r["availabilityFactor"] == 1 for r in after)),
        ("regerPerSecond 拼写与真实响应一致",
         all("regerPerSecond" in r and "regenPerSecond" not in r for r in after)),
        ("其它星球的分区未被改动", untouched),
        ("分区编号不重复", len({(r["planetIndex"], r["regionIndex"]) for r in after}) == len(after)),
    ]
    ok = True
    for label, cond in checks:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        ok = ok and cond
    print("\n" + ("✓ 离线自检通过" if ok else "✗ 离线自检失败"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("patch")
    p.add_argument("--proxy", required=True)
    p.set_defaults(func=cmd_patch)
    s = sub.add_parser("spec")
    s.add_argument("--warinfo", required=True)
    s.add_argument("--target", type=int, required=True)
    s.add_argument("--race", type=int, required=True)
    s.add_argument("--campaign-type", type=int, default=0)
    s.add_argument("--count", type=int, default=20)
    s.add_argument("--camp-id", type=int, default=51991)
    s.add_argument("--layout", type=int, default=None)
    s.add_argument("--out")
    s.set_defaults(func=cmd_spec)
    t = sub.add_parser("selftest")
    t.add_argument("--status", required=True)
    t.add_argument("--spec-text", required=True)
    t.set_defaults(func=cmd_selftest)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())

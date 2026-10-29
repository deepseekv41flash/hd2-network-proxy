#!/usr/bin/env python3
"""defense_inject.py -- 给第三方 war_proxy.py 的 `_gwe_apply_extra` 钩子补两处，与真实 DEFENSE 样本对齐。

为什么需要
    第三方代理里已经有一个 `HD2_GWE_EXTRA` 钩子（追加 campaigns / planetAttacks / planetEvents /
    jointOperations / globalEvents / owner）。2026-10-29 抓到真实 DEFENSE 样本后，发现它比真实样本少两样：

    1. `planetEvents[]` 少了 `potentialBuildUp`（真实样本有，值 0）；
    2. `campaignId` 必须等于同星球那条 campaign 的 id，钩子要求手写；写错就渲染不出来。

本工具只做这两处**最小改动**（幂等、留 .bak），其余逻辑一行不改。

用法
    python tools/defense_inject.py status  --proxy D:/Downloads/variant_mod/tools/war_proxy.py
    python tools/defense_inject.py apply   --proxy D:/Downloads/variant_mod/tools/war_proxy.py
    python tools/defense_inject.py revert  --proxy D:/Downloads/variant_mod/tools/war_proxy.py
    # 生成注入 spec（可直接塞进 HD2_GWE_EXTRA）
    python tools/defense_inject.py spec --target 156 --source 157 --count 38 --race 3 --camp-id 51990 --event-id 9101
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

BACKUP_SUFFIX = ".defenseinject.bak"
MARK_APPLIED = "# DSH-DEFENSE-INJECT-V1"

OLD_EVENT_TAIL = '''                "campaignId": int(e.get("campaignId") or 0),
                # 真实样本里这里是 [事件自己的 id]，不是空数组；空数组会让客户端解析失败
                "jointOperationIds": [int(e.get("id") or 9001)],'''

NEW_EVENT_TAIL = '''                "campaignId": int(e.get("campaignId") or _camp_id_of.get(pidx) or 0),
                # 真实样本里这里是 [事件自己的 id]，不是空数组；空数组会让客户端解析失败
                "jointOperationIds": [int(e.get("id") or 9001)],
                # 真实样本里有这一格（值 0），缺了客户端可能不认这条事件
                "potentialBuildUp": int(e.get("potentialBuildUp") or 0),'''

OLD_EVENT_HEAD = '''    if isinstance(ev, list):
        now = int(doc.get("time") or 0)
        for e in cfg.get("events") or []:'''

NEW_EVENT_HEAD = '''    if isinstance(ev, list):
        now = int(doc.get("time") or 0)
        # 本 spec 里注入的 campaign：{planetIndex: id}，给事件当 campaignId 兜底
        _camp_id_of = {}
        for _c in cfg.get("campaigns") or []:
            try:
                _camp_id_of[int(_c.get("planet"))] = int(_c.get("id"))
            except (TypeError, ValueError):
                continue
        for e in cfg.get("events") or []:'''


def load(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def do_status(a) -> int:
    p = pathlib.Path(a.proxy)
    s = load(p)
    has_hook = "def _gwe_apply_extra(" in s
    has_pb = '"potentialBuildUp"' in s
    has_camp_fallback = "_camp_id_of" in s
    print(f"proxy     : {p}")
    print(f"size      : {len(s)} B")
    print(f"钩子存在  : {'YES' if has_hook else 'NO'}")
    print(f"potentialBuildUp : {'YES' if has_pb else 'NO'}")
    print(f"campaignId 兜底  : {'YES' if has_camp_fallback else 'NO'}")
    print(f"备份      : {p.with_name(p.name + BACKUP_SUFFIX).name if p.with_name(p.name + BACKUP_SUFFIX).exists() else '(无)'}")
    return 0 if (has_hook and has_pb and has_camp_fallback) else 1


def do_apply(a) -> int:
    p = pathlib.Path(a.proxy)
    s = load(p)
    if '"potentialBuildUp"' in s and "_camp_id_of" in s:
        print("已经打过补丁，无需重复。")
        return 0
    if OLD_EVENT_TAIL not in s or OLD_EVENT_HEAD not in s:
        raise SystemExit("✗ 找不到预期的钩子代码块（proxy 版本变了？）")
    if not p.with_name(p.name + BACKUP_SUFFIX).exists():
        shutil.copy2(p, p.with_name(p.name + BACKUP_SUFFIX))
        print(f"备份 → {p.name + BACKUP_SUFFIX}")
    s = s.replace(OLD_EVENT_HEAD, NEW_EVENT_HEAD, 1)
    s = s.replace(OLD_EVENT_TAIL, NEW_EVENT_TAIL, 1)
    s = s.replace("def _gwe_apply_extra(doc):",
                  f"{MARK_APPLIED}\ndef _gwe_apply_extra(doc):", 1)
    p.write_text(s, encoding="utf-8")
    compile(s, str(p), "exec")            # 语法门禁
    print(f"✓ 已打补丁（{len(s)} B，语法检查通过）")
    return 0


def do_revert(a) -> int:
    p = pathlib.Path(a.proxy)
    bak = p.with_name(p.name + BACKUP_SUFFIX)
    if not bak.exists():
        raise SystemExit("✗ 没有备份可还原")
    shutil.copy2(bak, p)
    print(f"✓ 已从 {bak.name} 还原")
    return 0


SPEC_TEMPLATE = {
    "campaigns": [{"planet": 0, "id": 0, "type": 4, "count": 0, "race": 3}],
    "attacks": [{"source": 0, "target": 0}],
    "events": [{"planet": 0, "id": 0, "eventType": 1, "race": 3,
                "health": 0, "maxHealth": 0,
                "startOffset": -3600, "endOffset": 169200,
                "campaignId": 0, "hqNodeIndex": 2}],
    "owner": {},
}


def do_spec(a) -> int:
    spec = json.loads(json.dumps(SPEC_TEMPLATE))
    spec["campaigns"][0].update({"planet": a.target, "id": a.camp_id, "count": a.count, "race": a.race})
    spec["attacks"][0].update({"source": a.source, "target": a.target})
    spec["events"][0].update({"planet": a.target, "id": a.event_id, "race": a.race,
                              "health": int(a.max_health * a.health_ratio),
                              "maxHealth": a.max_health,
                              "campaignId": a.camp_id, "hqNodeIndex": a.hq_node})
    spec["owner"] = {str(a.target): 1}
    text = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"→ {a.out}（{len(text)} B，单行 JSON，可直接给 HD2_GWE_EXTRA）")
    print(text)
    return 0


def do_selftest(a) -> int:
    """用真实抓包样本离线跑一遍「注入后应该长什么样」，不改任何文件。"""
    dump = pathlib.Path(a.dump)
    files = sorted(dump.glob("*Status*.json"))
    sample = None
    for f in files:
        try:
            raw = f.read_bytes()
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.decompress(raw)
            doc = json.loads(raw.decode("utf-8"))
            if doc.get("warId") == 801 and "campaigns" in doc and doc.get("planetEvents") is not None:
                sample = (f.name, doc)
                if doc.get("planetEvents"):
                    break
        except Exception:
            continue
    if not sample:
        raise SystemExit("✗ 找不到可用的 Status 样本")
    name, doc = sample
    spec = json.loads(a.spec_text)
    before = (len(doc["campaigns"]), len(doc.get("planetAttacks") or []), len(doc.get("planetEvents") or []),
              len(doc.get("jointOperations") or []))
    # --- 与钩子同构的离线实现（保持与 NEW_EVENT_* 完全一致的行为）---
    tgt = spec["campaigns"][0]["planet"]
    doc["campaigns"].append({"id": spec["campaigns"][0]["id"], "planetIndex": tgt,
                             "type": spec["campaigns"][0]["type"], "count": spec["campaigns"][0]["count"],
                             "race": spec["campaigns"][0]["race"]})
    for at in spec.get("attacks") or []:
        doc["planetAttacks"].append({"source": at["source"], "target": at["target"]})
    now = int(doc.get("time") or 0)
    for e in spec.get("events") or []:
        eid = e["id"]
        doc.setdefault("planetEvents", []).append({
            "id": eid, "planetIndex": e["planet"], "eventType": e["eventType"], "race": e["race"],
            "health": e["health"], "maxHealth": e["maxHealth"],
            "startTime": now + e["startOffset"], "expireTime": now + e["endOffset"],
            "campaignId": spec["campaigns"][0]["id"], "jointOperationIds": [eid],
            "potentialBuildUp": 0})
        doc.setdefault("jointOperations", []).append({"id": eid, "planetIndex": e["planet"],
                                                      "hqNodeIndex": e["hqNodeIndex"]})
    after = (len(doc["campaigns"]), len(doc["planetAttacks"]), len(doc["planetEvents"]),
             len(doc["jointOperations"]))
    print(f"样本 {name}")
    print(f"  campaigns      {before[0]} → {after[0]}")
    print(f"  planetAttacks  {before[1]} → {after[1]}")
    print(f"  planetEvents   {before[2]} → {after[2]}")
    print(f"  jointOperations{before[3]} → {after[3]}")
    ev = doc["planetEvents"][-1]
    print("  注入的 event:", json.dumps(ev, ensure_ascii=False))
    # 一致性门禁
    checks = [
        ("campaign 与 event 的 campaignId 一致", ev["campaignId"] == spec["campaigns"][0]["id"]),
        ("event 与 jointOperation 的 id 一致", ev["id"] == doc["jointOperations"][-1]["id"]),
        ("jointOperationIds == [event.id]", ev["jointOperationIds"] == [ev["id"]]),
        ("health < maxHealth", ev["health"] < ev["maxHealth"]),
        ("expireTime > startTime", ev["expireTime"] > ev["startTime"]),
        ("potentialBuildUp 存在且为 0", ev.get("potentialBuildUp") == 0),
        ("JSON 可序列化", isinstance(json.dumps(doc), str)),
    ]
    ok = True
    for label, cond in checks:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        ok = ok and cond
    print(f"\n{'✓ 自检通过' if ok else '✗ 自检失败'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "apply", "revert"):
        p = sub.add_parser(name)
        p.add_argument("--proxy", required=True)
        p.set_defaults(func={"status": do_status, "apply": do_apply, "revert": do_revert}[name])
    sp = sub.add_parser("spec")
    sp.add_argument("--target", type=int, required=True)
    sp.add_argument("--source", type=int, required=True)
    sp.add_argument("--count", type=int, default=38)
    sp.add_argument("--race", type=int, default=3)
    sp.add_argument("--camp-id", type=int, default=51990)
    sp.add_argument("--event-id", type=int, default=9101)
    sp.add_argument("--max-health", type=int, default=1000000)
    sp.add_argument("--health-ratio", type=float, default=0.99)
    sp.add_argument("--hq-node", type=int, default=2)
    sp.add_argument("--out")
    sp.set_defaults(func=do_spec)
    st = sub.add_parser("selftest")
    st.add_argument("--dump", default=r"D:\mod\out\gwe")
    st.add_argument("--spec-text", required=True, help="spec 的单行 JSON")
    st.set_defaults(func=do_selftest)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())

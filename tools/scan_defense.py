#!/usr/bin/env python3
"""scan_defense.py -- 扫一批 GWE 抓包，找「防守战役 / 入侵」相关的字段与端点。

只读：不改任何抓包文件。
用途：拿到真实 DEFENSE 期间的一批 dump 后，回答——
  ① 防守状态到底由哪个端点、哪个字段表达；
  ② `planetEvents` / `campaigns` / `planetStatus` 里防守样本长什么样（可作为注入模板）。

用法
  python tools/scan_defense.py --dump D:/mod/out/gwe
  python tools/scan_defense.py --dump D:/mod/out/gwe --since 20261029T140000Z
  python tools/scan_defense.py --dump D:/mod/out/gwe --grep DEFENSE --paths
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

KEY_RE = re.compile(r"defen|invasion|assault|liberat|health|maxhealth|campaign|planetevent|"
                    r"jointoperation|attacker|defender|owner|race|type$", re.I)


def walk(node, path="", hits=None, depth=0):
    hits = hits if hits is not None else []
    if depth > 8:
        return hits
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if KEY_RE.search(str(k)):
                hits.append((p, v))
            walk(v, p, hits, depth + 1)
    elif isinstance(node, list):
        for i, v in enumerate(node[:6]):
            walk(v, f"{path}[{i}]", hits, depth + 1)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=r"D:\mod\out\gwe")
    ap.add_argument("--since", help="只看 index 里时间戳 >= 该值（形如 20261029T140000Z）")
    ap.add_argument("--grep", help="只处理内容里含该子串的 dump")
    ap.add_argument("--paths", action="store_true", help="只列出「请求过哪些端点」")
    a = ap.parse_args()

    dump = pathlib.Path(a.dump)
    idx = dump / "index.txt"
    rows = []
    if idx.exists():
        for line in idx.read_text(encoding="utf-8", errors="replace").splitlines():
            f = line.split("\t")
            if len(f) < 2:
                continue
            if a.since and f[0] < a.since:
                continue
            rows.append(f)
    if a.paths:
        paths = sorted({f[1].split("?")[0] for f in rows})
        print(f"请求/响应过的端点 {len(paths)} 个：")
        for p in paths:
            n = sum(1 for f in rows if f[1].split("?")[0] == p)
            print(f"  {n:4d}×  {p}")
        return 0

    files = sorted(dump.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if a.since:
        files = [p for p in files if p.stat().st_mtime >= 0][:200]
    print(f"扫描 {len(files)} 个 dump …")
    for p in files:
        try:
            raw = p.read_bytes()
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.decompress(raw)
            if a.grep and a.grep.encode().lower() not in raw.lower():
                continue
            obj = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            continue
        hits = walk(obj)
        # 只报「有防守/入侵语义」的，或者 key 里出现 campaign/planetEvents 的
        interesting = [(k, v) for k, v in hits
                       if re.search(r"defen|invasion|assault|planetevent|campaign|jointoperation", k, re.I)]
        if not interesting:
            continue
        print(f"\n== {p.name}  ({len(raw):,} B)")
        seen = set()
        for k, v in interesting[:40]:
            short = json.dumps(v, ensure_ascii=False)[:160] if not isinstance(v, (int, float, str, bool)) else v
            if (k, str(short)[:80]) in seen:
                continue
            seen.add((k, str(short)[:80]))
            print(f"   {k} = {short}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

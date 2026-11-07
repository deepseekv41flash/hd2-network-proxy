#!/usr/bin/env python3
"""planet_eco_swap.py -- 生成「换生态」用的 HD2_GWE_EXTRA.settings_hash 配置。

原理（已实机 ✓✓，见 docs/E8-REACHABILITY.md §10/§11）
    warinfo 的 planetInfos[].settingsHash 是每颗星的**内容身份**（名字+地形+天气+修饰符）。
    planet_data 尾部 438×8 B 的每项高 4 字节 = 该行 settingsHash；
    把目标星的 hash 换成另一颗星（通常选休眠星）的 hash，就能把整套生态借过来。
    客户端只在登录时拉 warinfo ⇒ 改完要完全重开游戏。

用法
    python tools/planet_eco_swap.py --list                       # 每个生态给一个代表行 + hash
    python tools/planet_eco_swap.py --eco deciduous --targets 100 7 93
    python tools/planet_eco_swap.py --row 386 --targets 100       # 直接指定来源行
    python tools/planet_eco_swap.py --eco oasis --targets 100 --write runtime/planet_node.json

输出是一段可直接设为环境变量的 JSON（run.ps1 前 Set $env:HD2_GWE_EXTRA）。
需要 docs/tables/PLANET-INDEX-26088801.md 才能显示名字（可选）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys

ENUM = {0: "forest", 1: "desert", 2: "arctic", 3: "sandy", 4: "savanna", 5: "rocky", 6: "swamp",
        7: "snowy_forest", 8: "primordial", 9: "moor", 10: "superearth", 11: "bug_hiveworld",
        12: "magma", 13: "oasis", 14: "deciduous", 15: "coniferous", 16: "rift"}

DEFAULT_PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_planet_data.dl_bin"
DEFAULT_INDEX = r"D:\mod\work\repo-datamined\docs\tables\PLANET-INDEX-26088801.md"


def load_rows(plain: str):
    b = pathlib.Path(plain).read_bytes()
    n = struct.unpack_from("<I", b, 0)[0]
    off, rows = 4, {}
    for i in range(n):
        ver, tid, psz, wide = struct.unpack_from("<4I", b, off + 4)
        o = off + 24
        rows[i] = o
        off = o + psz
    tail = b[off:]
    info = {}
    for i, o in rows.items():
        psz = (rows.get(i + 1, len(b)) - o) if i + 1 in rows else (len(b) - 3504 - o)
        t = struct.unpack_from("<I", b, o + 0x1B8)[0]
        s = b[o + 624:o + 0x10000].split(b"\x00")[0].decode("latin1")
        setup = s.rsplit("/", 1)[-1] if s.startswith("content/") else ""
        node = o - (off and 0)
        sh = struct.unpack_from("<II", tail, i * 8)[1]
        info[i] = dict(type=t, eco=ENUM.get(t, f"?{t}"), setup=setup, settingsHash=sh)
    return info


def load_names(path: str) -> dict:
    names = {}
    p = pathlib.Path(path)
    if not p.is_file():
        return names
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(\d+|—)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            names[int(m.group(1))] = m.group(3).strip()
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="生成换生态用的 settings_hash 配置")
    ap.add_argument("--plain", default=DEFAULT_PLAIN)
    ap.add_argument("--index", default=DEFAULT_INDEX, help="PLANET-INDEX.md（取名字用，可省）")
    ap.add_argument("--list", action="store_true", help="每个生态一个代表行")
    ap.add_argument("--eco", default="", help="目标生态名（如 deciduous / oasis）")
    ap.add_argument("--row", type=int, default=0, help="直接指定来源表行")
    ap.add_argument("--targets", nargs="*", type=int, default=[], help="要改写的游戏索引")
    ap.add_argument("--write", default="", help="把 JSON 写到这个文件")
    a = ap.parse_args()

    info = load_rows(a.plain)
    names = load_names(a.index)

    def pick(eco: str):
        cands = [i for i, r in info.items() if r["eco"] == eco and r["setup"]]
        cands.sort(key=lambda i: (names.get(i, "zzz"), i))
        return cands[0] if cands else None

    if a.list:
        print(f"{'生态':14} {'代表行':>6} {'名字':22} {'setup':30} settingsHash")
        for eco in ENUM.values():
            row = pick(eco)
            if row is None:
                print(f"{eco:14} {'—':>6} {'（无行星行）':22}")
                continue
            r = info[row]
            print(f"{eco:14} {row:>6} {names.get(row, '?')[:22]:22} {r['setup'][:30]:30} {r['settingsHash']}")
        return 0

    if a.row:
        src = a.row
    elif a.eco:
        src = pick(a.eco)
        if src is None:
            print(f"✗ 没有生态为 {a.eco} 的行", file=sys.stderr)
            return 2
    else:
        print("✗ 需要 --list / --eco / --row 之一", file=sys.stderr)
        return 2

    if not a.targets:
        print("✗ 需要 --targets <游戏索引...>", file=sys.stderr)
        return 2

    r = info[src]
    spec = {"settings_hash": {str(t): r["settingsHash"] for t in a.targets}}
    out = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    print(f"# 来源 行 {src} = {names.get(src, '?')} / {r['eco']} / {r['setup']} / "
          f"settingsHash {r['settingsHash']}")
    print(out)
    if a.write:
        p = pathlib.Path(a.write)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out, encoding="utf-8")
        print(f"# -> {p}")
    print("# 用法：$env:HD2_GWE_EXTRA='<上面那行>'; .\\run.ps1   然后完全重开游戏")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

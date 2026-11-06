#!/usr/bin/env python3
"""按 progressionCategory 全量生成 inventory 注入清单（逐类探测用）。

用法:
  python tools/category_inject.py --cat 10                        # 写 runtime/inventory_probe_inject.json
  python tools/category_inject.py --cat 5,6,15                    # 多个类别一起
  python tools/category_inject.py --cat 4 --dry-run               # 只看条数不写
  python tools/category_inject.py --list                          # 列出每个类别的 总/已拥有/未拥有

数据源：--dir 指定的抓包目录里最新的 *Progression_items.json 与 *Progression_inventory.json
（默认 D:/mod/out/gwe/stratagem-20261106）。
"""
import argparse, glob, json, os, sys

DEF_DIR = "D:/mod/out/gwe/stratagem-20261106"
OUT = "runtime/inventory_probe_inject.json"


def latest(d, pat):
    fs = sorted(glob.glob(os.path.join(d, pat)), key=os.path.getmtime)
    if not fs:
        sys.exit("找不到 %s 里的 %s" % (d, pat))
    return fs[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DEF_DIR)
    ap.add_argument("--cat", default="")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    cat_doc = json.load(open(latest(a.dir, "*Progression_items.json"), encoding="utf-8"))
    rows = cat_doc if isinstance(cat_doc, list) else cat_doc["items"]
    inv = json.load(open(latest(a.dir, "*Progression_inventory.json"), encoding="utf-8"))
    owned = {int(i["mixId"]) for i in inv["items"]}

    by = {}
    for r in rows:
        c = int(r.get("progressionCategory") or 0)
        by.setdefault(c, []).append(r)

    if a.list:
        print("%-5s %-7s %-7s %-7s" % ("cat", "总数", "已拥有", "未拥有"))
        for c in sorted(by):
            n = len(by[c])
            o = sum(1 for r in by[c] if int(r["mixId"]) in owned)
            print("%-5d %-7d %-7d %-7d" % (c, n, o, n - o))
        return

    cats = [int(x) for x in a.cat.replace(" ", "").split(",") if x.strip()]
    if not cats:
        sys.exit("需要 --cat（或 --list）")
    picked, stat = [], {}
    for c in cats:
        rs = [r for r in by.get(c, []) if int(r["mixId"]) not in owned]
        stat[c] = (len(by.get(c, [])), len(rs))
        picked.extend(rs)
    picked = {int(r["mixId"]): r for r in picked}.values()   # 去重
    print("按类别全量：" + "  ".join("cat %d %d/%d 未拥有" % (c, stat[c][1], stat[c][0]) for c in cats))
    print("合计待注入: %d 条" % len(picked))
    if a.dry_run:
        return
    doc = {"_note": "类别全量探测：cat %s（每轮只放一个类别）" % ",".join(map(str, cats)),
           "enabled": True,
           "probe": {"cats": cats,
                     "per_cat": {str(c): {"total": stat[c][0], "unowned": stat[c][1]} for c in cats}},
           "items": [{"mixId": int(r["mixId"]), "amount": 1, "isDiscovered": False} for r in picked]}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(doc, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已写入 %s（enabled=True）" % a.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""两次抓包会话对比：找出新出现的端点、内容变化的响应，并把变化的 id 集合列出来。

用法:
  python tools/capture_diff.py --old D:/mod/out/gwe --new D:/mod/out/gwe/armor-20261106
  python tools/capture_diff.py ... --only inventory,Progression   # 只看匹配路径
  python tools/capture_diff.py ... --ids                          # 只打印 id 增删

读 index.txt（每个目录一份）。响应行: "<stamp>\t<path>\t<len>\t<sha>\t<kind>"
请求行: "<stamp>\tREQ <METHOD>\t<path>\t<len>\t<sha>"
"""
import argparse, collections, json, os

ID_KEYS = ("mixId", "mixId32", "itemId", "galacticEffectId", "id32", "index")


def load_index(d, before=None, after=None):
    """-> {('resp'|'req', path, method): (file, sha, size)}；可按 UTC 时间戳切分（stamp 形如 20261106T091043Z）"""
    out = {}
    ix = os.path.join(d, "index.txt")
    if not os.path.exists(ix):
        return out
    for line in open(ix, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        stamp = p[0]
        if before and stamp >= before:
            continue
        if after and stamp < after:
            continue
        if p[1].startswith("REQ"):            # 请求行: stamp / "REQ POST" / path / len / sha
            m = p[1].split()
            method = m[1] if len(m) > 1 else "REQ"
            path, size, sha = p[2], p[3], p[4]
            kind = "req"
        else:                                  # 响应行: stamp / path / len / sha / kind
            path, size, sha = p[1], p[2], p[3]
            method = ""
            kind = "resp"
        try:
            size = int(size)
        except ValueError:
            continue
        slug = __import__("re").sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[-60:]
        if kind == "req":
            key = ("req", path, method)
            fp = os.path.join(d, "req_%s_%s_%s.json" % (method.upper()[:6], sha[:8], slug))
        else:
            key = ("resp", path, "")
            fp = os.path.join(d, "%s_%s.json" % (sha[:8], slug))
        out[key] = (fp if os.path.exists(fp) else None, sha, size)
    return out


def collect_ids(obj, sink, depth=0):
    """递归收集带 id 类字段的字典。"""
    if depth > 6:
        return
    if isinstance(obj, dict):
        got = {}
        for k in ID_KEYS:
            v = obj.get(k)
            if isinstance(v, int):
                got[k] = v
        if got:
            sink.append(got)
        for v in obj.values():
            collect_ids(v, sink, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            collect_ids(v, sink, depth + 1)


def summarize(path, a, b):
    """比较两份 JSON，返回若干行结论。"""
    lines = []
    if isinstance(a, dict) and isinstance(b, dict):
        ka, kb = set(a), set(b)
        for k in sorted(kb - ka):
            lines.append("    + 新字段 %s" % k)
        for k in sorted(ka - kb):
            lines.append("    - 消失字段 %s" % k)
        for k in sorted(ka & kb):
            va, vb = a[k], b[k]
            if isinstance(va, list) and isinstance(vb, list):
                if len(va) != len(vb):
                    lines.append("    ~ %s 列表 %d -> %d" % (k, len(va), len(vb)))
                sa, sb = [], []
                collect_ids(va, sa)
                collect_ids(vb, sb)
                def keyset(rows):
                    return {tuple(sorted(r.items())) for r in rows}
                add = keyset(sb) - keyset(sa)
                rem = keyset(sa) - keyset(sb)
                if add and len(add) <= 40:
                    for t in sorted(add)[:40]:
                        lines.append("    + %s 新增行 %s" % (k, dict(t)))
                elif add:
                    lines.append("    + %s 新增 %d 行（略）" % (k, len(add)))
                if rem and len(rem) <= 40:
                    for t in sorted(rem)[:40]:
                        lines.append("    - %s 移除行 %s" % (k, dict(t)))
                elif rem:
                    lines.append("    - %s 移除 %d 行（略）" % (k, len(rem)))
            elif va != vb:
                lines.append("    ~ %s: %s -> %s" % (k, json.dumps(va, ensure_ascii=False)[:90],
                                                     json.dumps(vb, ensure_ascii=False)[:90]))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--only", default="", help="逗号分隔的路径子串过滤")
    ap.add_argument("--ids", action="store_true", help="只打印 id 增删（不打印字段变化）")
    ap.add_argument("--maxdetail", type=int, default=12, help="每个端点最多打印多少行细节")
    ap.add_argument("--split", default="", help="同一目录内按 UTC 时间戳切分：格式 YYYYMMDDTHHMMSSZ（此时 --old/--new 都给同一目录）")
    a = ap.parse_args()
    if a.split:
        olds = load_index(a.old, before=a.split)
        news = load_index(a.new, after=a.split)
    else:
        olds, news = load_index(a.old), load_index(a.new)
    filt = [x.strip() for x in a.only.split(",") if x.strip()]

    def keep(p):
        return (not filt) or any(f in p for f in filt)

    newpaths = sorted({k for k in news if keep(k[1]) and k not in olds})
    print("== 新出现的端点/请求（%d）==" % len(newpaths))
    for k in newpaths:
        kind, path, method = k
        print("  %s %s %s  (%d B)" % ("REQ" if kind == "req" else "RESP",
                                      method or "", path, news[k][2]))

    changed = []
    for k in sorted(set(olds) & set(news)):
        if not keep(k[1]):
            continue
        if olds[k][1] != news[k][1]:
            changed.append(k)
    print("\n== 内容变化的响应（%d）==" % len([k for k in changed if k[0] == "resp"]))
    for k in changed:
        kind, path, method = k
        if kind != "resp":
            continue
        fa = olds[k][0]; fb = news[k][0]
        if not (fa and fb):
            print("  %s  (文件缺失, 跳过)" % path)
            continue
        try:
            ja = json.load(open(fa, encoding="utf-8"))
            jb = json.load(open(fb, encoding="utf-8"))
        except Exception as e:
            print("  %s  (非 JSON: %r)" % (path, e))
            continue
        print("  %s  %d -> %d B" % (path, olds[k][2], news[k][2]))
        lines = summarize(path, ja, jb)
        if a.ids:
            lines = [l for l in lines if "新增行" in l or "移除行" in l or "列表" in l]
        for l in lines[:a.maxdetail]:
            print(l)
        if len(lines) > a.maxdetail:
            print("    … 另有 %d 行" % (len(lines) - a.maxdetail))

    reqchg = [k for k in changed if k[0] == "req"]
    if reqchg:
        print("\n== 请求体变化的请求（%d）==" % len(reqchg))
        for k in reqchg:
            print("  %s %s" % (k[2], k[1]))


if __name__ == "__main__":
    main()

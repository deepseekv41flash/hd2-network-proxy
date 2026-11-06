"""变种 Mod 的本地 TLS 代理（安全最小化版）。

与 rebase_probe 里的研究代理的区别（逐条对应 SECURITY 评审）：

  1. 只服务**一个**域名（配置里的 host），SNI 不符直接断开 —— 不是开放代理；
  2. 只改写 **/api/WarSeason/801/Status**，其它请求/响应原样透传；
  3. **默认不落盘任何请求/响应体**（含 token）；只写审计日志（改哪颗星球、注入哪对 id）；
  4. 危险功能（--add-def / --drop-def / --def-override / --inject）只在 --dev 下可用；
  5. 启动前自检会话证书：SAN 必须恰好是 host、有效期 ≤ 2 天、目录里没有多余私钥；
  6. 上游用系统信任链**正常校验证书**（不跳过验证）。

用法：
  py war_proxy.py --config ..\\config.json --catalog ..\\variant_catalog.json --cert-dir ..\\certs
  py war_proxy.py ... --passthrough          # 纯转发（不改写）= 正常游戏
  py war_proxy.py ... --dev --drop-def 1309  # 研究用
"""

import argparse
import gzip
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]                      # variant_mod\
# 数据目录：默认就是 mod 自己的 logs/ 和 runtime/。
# 面板的“一键自检”会把 VMOD_DATA 指到临时目录 —— 离线自检用的是同一份代码，
# 但绝不能碰正在跑的那个代理的 status.json / proxy.pid / 日志。
_DATA_HOME = os.environ.get("VMOD_DATA")
BASEDIR = Path(_DATA_HOME) if _DATA_HOME else ROOT
LOGDIR = BASEDIR / "logs"
PROXY_LOG = LOGDIR / "proxy.log"
AUDIT_LOG = LOGDIR / "audit.log"
RUNTIME = BASEDIR / "runtime"
SELECTION = RUNTIME / "selection.json"       # 面板写，代理读（热重载）
STRATAGEM_SELECTION = RUNTIME / "stratagems.json"
STATUS_FILE = RUNTIME / "status.json"        # 代理写，面板读（显示状态）
PROXY_PID = LOGDIR / "proxy.pid"             # 代理自己的 pid（面板据此识别"自己人"）
STRATAGEM_CATALOG = ROOT / "stratagem_catalog.json"
MAX_STRATAGEMS = 3

FACTION_TERMINID = "terminid"
FACTION_AUTOMATON = "automaton"
FACTION_ILLUMINATE = "illuminate"
FACTION_UNIVERSAL = "universal"
OWNER_FACTIONS = {
    2: FACTION_TERMINID,
    3: FACTION_AUTOMATON,
    4: FACTION_ILLUMINATE,
}


def variant_faction(meta):
    """返回词条阵营；旧目录缺少 faction 时按 presence 前缀兼容。"""
    meta = meta or {}
    faction = str(meta.get("faction") or "").lower()
    if faction in (FACTION_TERMINID, FACTION_AUTOMATON, FACTION_ILLUMINATE, FACTION_UNIVERSAL):
        return faction
    presence = str(meta.get("presence") or "").lower()
    if presence.startswith("bugs_"):
        return FACTION_TERMINID
    if presence.startswith("bots_") or presence.startswith("elite_bot_"):
        return FACTION_AUTOMATON
    if presence.startswith("illuminate_"):
        return FACTION_ILLUMINATE
    return FACTION_UNIVERSAL


def owner_faction(value):
    try:
        return OWNER_FACTIONS.get(int(value))
    except (TypeError, ValueError):
        return None

STATUS_MARK = "/api/WarSeason/801/Status"
ALLOWED_PATH = STATUS_MARK
INV_PATH = "/api/Progression/inventory"      # 拥有的物品清单（items.mixId）+ 玩家改装状态（customization）
INV_STATE = RUNTIME / "inventory_inject.json"
ITEMS_PATH = "/api/Progression/items"        # 服务端物品目录（3020 条：itemId/mixId/category/tags/prices）
ITEMS_STATE = RUNTIME / "items_inject.json"

_lock = threading.Lock()

# 1.04 起默认只留“必要日志”：启动/计划/改写/错误。
# 每条请求的 REQ/RESP 只有 --verbose（或 config.verbose=true）时才写。
VERBOSE = False
_THROTTLE = {}          # key -> (last_logged_ts, count)


def log(msg, audit=False):
    line = time.strftime("%H:%M:%S ") + msg
    with _lock:
        try:
            LOGDIR.mkdir(parents=True, exist_ok=True)
            with PROXY_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            if audit:
                with AUDIT_LOG.open("a", encoding="utf-8") as f:
                    f.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg + "\n")
        except Exception:
            pass
        print(line, flush=True)


def log_throttled(key, msg, every=60.0):
    """同类日志限流：第一次立刻写，之后每 every 秒最多一条，并带上累计次数。

    为什么需要：证书没装好时游戏每 9 秒重试一次，局域网里的扫描器也会来敲门 ——
    不限流的话 proxy.log 会被同一行刷满（以前一次会话几 KB，现在压在几十行）。
    """
    now = time.time()
    last, n = _THROTTLE.get(key, (0.0, 0))
    n += 1
    if last == 0.0 or now - last >= every:
        _THROTTLE[key] = (now, n)
        log(msg + ("" if n == 1 else "  （同类累计 %d 次）" % n))
    else:
        _THROTTLE[key] = (last, n)


def rotate_logs(max_bytes=512 * 1024):
    """启动时把过大的 proxy.log 挪成 proxy.log.1（只留一份），日志永远不涨到 MB 级。"""
    try:
        if PROXY_LOG.exists() and PROXY_LOG.stat().st_size > max_bytes:
            old = PROXY_LOG.with_suffix(".log.1")
            if old.exists():
                old.unlink()
            PROXY_LOG.rename(old)
    except Exception:
        pass


def read_head(conn):
    buf = b""
    while b"\r\n\r\n" not in buf:
        try:
            chunk = conn.recv(4096)
        except Exception:
            return b"", b""
        if not chunk:
            return b"", buf
        buf += chunk
        if len(buf) > 1 << 20:
            return b"", b""
    head, _, rest = buf.partition(b"\r\n\r\n")
    return head, rest


def parse_headers(head):
    lines = head.split(b"\r\n")
    first = lines[0].decode("latin-1") if lines else ""
    hdrs = {}
    for line in lines[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            hdrs[k.strip().decode("latin-1").lower()] = v.strip().decode("latin-1")
    return first, hdrs


def dechunk(data):
    out = b""
    while True:
        idx = data.find(b"\r\n")
        if idx < 0:
            return out or data
        try:
            size = int(data[:idx].split(b";")[0], 16)
        except ValueError:
            return out or data
        if size == 0:
            return out
        out += data[idx + 2:idx + 2 + size]
        data = data[idx + 2 + size + 2:]


def maybe_gunzip(body, hdrs):
    if (hdrs.get("content-encoding", "") or "").lower().find("gzip") >= 0:
        try:
            return gzip.decompress(body), True
        except Exception:
            return body, False
    if body[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(body), True
        except Exception:
            return body, False
    return body, False


class Mod:
    """配置 + 目录 + 面板选择：把「变种名」翻译成「星球 → [tag, 玩法]」。

    优先级：面板选择（runtime/selection.json）> config.json 的 targets。
    面板模式下面板只写变种名，目标星球自动跟随玩家正在选的星球（从 /api/lobby 请求里读）。
    """

    def __init__(self, cfg, catalog, meta=None):
        self.host = cfg["host"]
        self.listen_ip = cfg.get("listenIp") or "127.0.0.1"
        self.port = int(cfg.get("port", 443))
        self.upstream_ip = cfg.get("upstreamIp") or None
        self.upstream_test = cfg.get("upstreamTest") or None   # "127.0.0.1:9099"，测试用明文上游
        self.passthrough = bool(cfg.get("passthrough", False))
        self.allow_dev = bool(cfg.get("allowDevFlags", False))
        self.catalog = catalog
        self.aliases = cfg.get("_aliases") or {}
        self.variant_meta = dict(meta or cfg.get("_meta") or {})
        for alias, target in self.aliases.items():
            if target in self.variant_meta:
                self.variant_meta[alias] = self.variant_meta[target]
        try:
            sdoc = json.loads(STRATAGEM_CATALOG.read_text(encoding="utf-8"))
            self.stratagem_catalog = {
                int(x["id"]): x for x in sdoc.get("items") or []
                if isinstance(x, dict) and "id" in x
            }
        except Exception as e:
            log("stratagem_catalog.json 读取失败: %r" % e)
            self.stratagem_catalog = {}
        self.plan = {}
        self.target_names = {}
        self.skipped = []
        for t in cfg.get("targets") or []:
            planet = t.get("planet")
            name = t.get("variant")
            ids = catalog.get(name)
            if not isinstance(planet, int) or not (0 <= planet <= 400):
                self.skipped.append(("planet", planet, name))
                continue
            if not ids:
                self.skipped.append(("variant", planet, name))
                continue
            self.plan[planet] = list(ids)
            self.target_names[planet] = name
        # 面板状态
        self.planet = None            # 玩家当前选中的星球（/api/lobby 里读到的）
        self.sticky = []              # 本次会话注入过的星球（粘性：不撤销，最多 3 颗）
        # 1.18：把**上次会话**注入过的星球继承过来。
        # 为什么：实测发现客户端只在游戏启动/登录时拉一次 Status，而那一发往往早于
        # "玩家在哪颗星球"的报告 —— 于是第一局经常什么都不改，要重启一次游戏才生效。
        # 有了这份继承，代理重启后的第一发 Status 就能直接改。
        try:
            prev = json.loads(STATUS_FILE.read_text(encoding="utf-8-sig"))
            for p in (prev.get("planets") or [])[:3]:
                if isinstance(p, int) and p not in self.sticky:
                    self.sticky.append(p)
            if self.sticky:
                log("继承上次会话的星球: %s（第一发 Status 就能改写）" % self.sticky)
        except Exception:
            pass
        self.selection = {}           # 最近一次读到的 selection.json
        self.sel_mtime = None
        self.stratagem_selection = {}
        self.stratagem_mtime = None
        self.lock = threading.Lock()

    # ---- 面板选择（热重载） -------------------------------------------------
    def reload_selection(self):
        self.reload_stratagems()
        try:
            mtime = SELECTION.stat().st_mtime
        except OSError:
            return
        if mtime == self.sel_mtime:
            return
        try:
            doc = json.loads(SELECTION.read_text(encoding="utf-8-sig"))
        except Exception as e:
            log("selection.json 读取失败: %r" % e)
            return
        with self.lock:
            self.sel_mtime = mtime
            self.selection = doc if isinstance(doc, dict) else {}
        log("selection reloaded: %s" % json.dumps(self.selection, ensure_ascii=False))

    def reload_stratagems(self):
        try:
            mtime = STRATAGEM_SELECTION.stat().st_mtime
        except OSError:
            return
        if mtime == self.stratagem_mtime:
            return
        try:
            doc = json.loads(STRATAGEM_SELECTION.read_text(encoding="utf-8-sig"))
        except Exception as e:
            log("stratagems.json 读取失败: %r" % e)
            return
        if not isinstance(doc, dict):
            doc = {}
        with self.lock:
            self.stratagem_mtime = mtime
            self.stratagem_selection = doc
        log("stratagem selection reloaded: %s"
            % json.dumps(self.stratagem_selection, ensure_ascii=False))

    def note_planet(self, planet, why="lobby"):
        """记录玩家触碰过的星球。粘性：一旦注入过就不再撤销。

        为什么粘性：Status 每 5 分钟才重拉、切星球又会立刻刷新。
        如果只注入"最近一次选择的那颗"，切走再切回来就可能出现
        "真正想进的星球上没有变种"（因为上一次响应把它撤掉了）。
        所以这里累积本次会话碰过的星球，每次响应都全量写入。
        """
        with self.lock:
            if planet != self.planet:
                self.planet = planet
                log("player planet -> %s (%s)" % (planet, why))
            if planet not in self.sticky:
                self.sticky.append(planet)
                if len(self.sticky) > 3:
                    self.sticky.pop(0)
                log("sticky planets -> %s" % self.sticky)

    def target_planets(self):
        """本次要注入的星球集合：粘性集合 + config 里固定目标。"""
        with self.lock:
            planets = list(self.sticky)
        for p in self.plan:
            if p not in planets:
                planets.append(p)
        return planets

    def variant_entry(self, name):
        ids = list(self.catalog.get(name) or [])
        if not ids:
            return None
        return {
            "name": name,
            "ids": ids,
            "faction": variant_faction(self.variant_meta.get(name)),
        }

    def effective_plan(self):
        """返回 {星球: {"variants": 词条候选, "trials": 通用战备}}。

        词条候选在这里只描述“玩家选了哪些”，不直接展开成 ID。真正写哪颗星
        必须在 rewrite_status 看到该星球的 owner 后再决定，避免混入外阵营词条。
        """
        self.reload_selection()
        with self.lock:
            sel = dict(self.selection)
            ssel = dict(self.stratagem_selection)

        names = []
        if sel and sel.get("enabled"):
            raw = sel.get("variants")
            if isinstance(raw, list):
                names = [x for x in raw if isinstance(x, str) and x]
            elif isinstance(sel.get("variant"), str) and sel["variant"]:
                names = [sel["variant"]]

        entries = []
        for name in names:
            entry = self.variant_entry(name)
            if entry and entry not in entries:
                entries.append(entry)

        trial_ids = []
        if ssel.get("enabled"):
            for raw in ssel.get("ids") or []:
                try:
                    eid = int(raw)
                except Exception:
                    continue
                if eid in self.stratagem_catalog and eid not in trial_ids:
                    trial_ids.append(eid)
                if len(trial_ids) >= MAX_STRATAGEMS:
                    break

        if entries or trial_ids:
            return {
                planet: {"variants": list(entries), "trials": list(trial_ids)}
                for planet in self.target_planets()
            }

        plan = {}
        for planet, name in self.target_names.items():
            entry = self.variant_entry(name)
            if entry:
                plan[planet] = {"variants": [entry], "trials": []}
        return plan

    def active_names(self):
        with self.lock:
            sel = dict(self.selection)
        if not sel.get("enabled"):
            return []
        raw = sel.get("variants")
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, str) and x]
        if isinstance(sel.get("variant"), str):
            return [sel["variant"]]
        return []

    def active_stratagem_names(self):
        self.reload_stratagems()
        with self.lock:
            doc = dict(self.stratagem_selection)
        if not doc.get("enabled"):
            return []
        names, seen = [], set()
        for raw in doc.get("ids") or []:
            try:
                eid = int(raw)
            except Exception:
                continue
            item = self.stratagem_catalog.get(eid)
            if item and eid not in seen:
                seen.add(eid)
                names.append({"id": eid, "name": item.get("name") or str(eid)})
            if len(names) >= MAX_STRATAGEMS:
                break
        return names

    def describe(self):
        return {k: v for k, v in sorted(self.plan.items())}


def resolve_plan(doc, plan):
    """按每一行 planetStatus 的 owner 过滤候选词条。

    返回 (实际要写的 {planet: [id...]}, 被跨阵营过滤掉的条目)。
    旧式 list plan 原样透传，兼容已有离线测试与手工配置。
    """
    owners = {}
    for row in doc.get("planetStatus") or []:
        if not isinstance(row, dict):
            continue
        try:
            index = int(row.get("index"))
        except (TypeError, ValueError):
            continue
        owners[index] = owner_faction(row.get("owner", row.get("race")))

    resolved = {}
    filtered = []
    for raw_planet, spec in plan.items():
        try:
            planet = int(raw_planet)
        except (TypeError, ValueError):
            continue
        if isinstance(spec, list):              # 旧格式
            resolved[planet] = list(spec)
            continue
        if not isinstance(spec, dict):
            continue
        planet_faction = owners.get(planet)
        ids = []
        for variant in spec.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            faction = variant.get("faction") or FACTION_UNIVERSAL
            if faction != FACTION_UNIVERSAL and faction != planet_faction:
                filtered.append((planet, variant.get("name") or "?", faction, planet_faction))
                continue
            for eid in variant.get("ids") or []:
                if eid not in ids:
                    ids.append(eid)
        for eid in spec.get("trials") or []:
            if eid not in ids:
                ids.append(eid)
        resolved[planet] = ids
    return resolved, filtered


def rewrite_status(body, plan):
    """只处理 Status 响应：给目标星球追加 [tag, 玩法]。"""
    doc = json.loads(body)
    if not isinstance(doc, dict):
        return body, 0
    effects = doc.get("planetActiveEffects")
    if not isinstance(effects, list):
        return body, 0
    plan, _ = resolve_plan(doc, plan)
    extra = _gwe_apply_extra(doc)          # ← 我们的额外改写（campaigns / owner），见 hook 区
    have = {(e.get("index"), e.get("galacticEffectId")) for e in effects if isinstance(e, dict)}
    added = 0
    for planet, ids in plan.items():
        for eid in ids:
            if (planet, eid) not in have:
                effects.append({"index": planet, "galacticEffectId": eid})
                added += 1
    if not added and not extra:
        return body, 0
    # extra 也算"改动"，否则调用方会认为没东西可写、把原始 body 发回去（2026-10-27 踩过）
    return json.dumps(doc).encode(), added + extra


def doh_resolve(host):
    """解析白名单域名，**绕过 hosts**（hosts 里正是我们把它指到 127.0.0.1 的）。

    先问固定 IP 的 DoH 服务，再退系统解析；任何回环结果都丢弃，避免自环。
    """
    import urllib.request
    for url in ("https://223.5.5.5/resolve?name=%s&type=A" % host,
                "https://cloudflare-dns.com/dns-query?name=%s&type=A" % host):
        try:
            req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=6) as r:
                doc = json.loads(r.read().decode("utf-8", "replace"))
            for a in doc.get("Answer") or []:
                if a.get("type") == 1 and a.get("data"):
                    ip = str(a["data"])
                    if not ip.startswith(("127.", "0.")):
                        return ip
        except Exception as e:
            log("  doh %s failed: %r" % (url.split("/")[2], e))
    try:
        ip = socket.gethostbyname(host)
        if not ip.startswith(("127.", "0.")):
            return ip
    except Exception:
        pass
    return None


def upstream_addr(mod, host):
    if mod.upstream_test:
        h, p = mod.upstream_test.rsplit(":", 1)
        return h, int(p)
    if mod.upstream_ip:
        ip = mod.upstream_ip
    else:
        ip = doh_resolve(host)
    if not ip or ip.startswith(("127.", "0.")):
        raise RuntimeError("refuse upstream %r -> %r (loopback/unknown)" % (host, ip))
    return ip, 443


class Proxy:
    def __init__(self, mod, cert_dir, send_chain=False):
        self.mod = mod
        self.cert_dir = Path(cert_dir)
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        leaf = "server.chain.pem" if send_chain else "server.pem"
        self.ctx.load_cert_chain(str(self.cert_dir / leaf), str(self.cert_dir / "server.key"))
        self.ctx.options |= ssl.OP_NO_TICKET
        self.ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        self.ctx.set_servername_callback(self.on_sni)
        # 用于拒绝非白名单 SNI：一个没装证书的上下文，握手会自然失败（不发 alert 之外的任何东西）
        self.empty_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.stats = {"tls": 0, "req": 0, "deny": 0, "rewrite": 0}
        # 只放行本机来源（回环 + 本机各网卡 IP）。算一次就够，别每条连接都解析一遍。
        self.local_ips = {"127.0.0.1", self.mod.listen_ip}
        try:
            for addrinfo in socket.getaddrinfo(socket.gethostname(), None):
                self.local_ips.add(addrinfo[4][0])
        except Exception:
            pass

    def on_sni(self, sslsock, servername, ctx):
        # 单域名白名单：别的 SNI 一律拒绝（不是开放代理）
        if servername != self.mod.host:
            self.stats["deny"] += 1
            log_throttled("sni-deny", "SNI DENY %r (allowlist=%s)" % (servername, self.mod.host))
            return self.empty_ctx
        return None

    def handle(self, conn, addr):
        # 先按来源过滤、再谈 TLS：局域网里的其它设备和扫描器连握手机会都不给，
        # 也不会拿到我们的证书（1.04 之前是先握手、拿到证书之后才 PEER DENY）。
        if addr[0] not in self.local_ips:
            self.stats["deny"] += 1
            log_throttled("peer-deny",
                          "PEER DENY %s:%d (only local connections allowed)" % (addr[0], addr[1]))
            try:
                conn.close()
            except Exception:
                pass
            return
        try:
            conn.settimeout(30)
            tls = self.ctx.wrap_socket(conn, server_side=True)
        except Exception as e:
            self.stats["deny"] += 1
            log_throttled("tls-reject", "TLS REJECTED %s:%d %r" % (addr[0], addr[1], e))
            try:
                conn.close()
            except Exception:
                pass
            return
        self.stats["tls"] += 1
        try:
            tls.settimeout(60)
            while True:
                head, rest = read_head(tls)
                if not head:
                    break
                first, hdrs = parse_headers(head)
                body = rest
                if "chunked" in hdrs.get("transfer-encoding", "").lower():
                    body = dechunk(body)
                else:
                    need = int(hdrs.get("content-length", "0") or 0)
                    while len(body) < need:
                        c = tls.recv(65536)
                        if not c:
                            break
                        body += c
                self.stats["req"] += 1
                path = first.split(" ")[1] if len(first.split(" ")) > 1 else ""
                # 必要日志里只留“改写/错误”；逐条 REQ/RESP 只在 --verbose 时写。
                if VERBOSE:
                    log("REQ %s %s %dB" % (first.split(" ")[0], path[:80], len(body)))
                _gwe_capture_req(path, body, hdrs,
                                 first.split(" ")[0] if " " in first else "")
                try:
                    ip, port = upstream_addr(self.mod, self.mod.host)
                    raw = socket.create_connection((ip, port), timeout=20)
                    if self.mod.upstream_test:
                        up = raw                     # 测试上游是明文 HTTP，不做 TLS
                    else:
                        up = ssl.create_default_context().wrap_socket(
                            raw, server_hostname=self.mod.host)
                except Exception as e:
                    log("upstream error %r" % e)
                    break
                lines = [head.split(b"\r\n")[0]]
                _conditional = (b"if-none-match:", b"if-modified-since:", b"if-match:",
                                b"if-unmodified-since:", b"if-range:")
                _stripped = False
                for line in head.split(b"\r\n")[1:]:
                    low = line.lower()
                    if low.startswith(b"connection:"):
                        continue
                    # 1.15：Status 是我们要改写的那一个响应。如果客户端带条件请求头
                    # （If-None-Match / If-Modified-Since 等），上游会回 304 且**没有响应体** ——
                    # 我们就没东西可改，客户端继续用自己缓存的旧战况（现场表现：游戏在走代理、
                    # player planet 一行行地出，却一条 REWRITE 都没有）。
                    # 所以对这一个路径剥掉条件头，让上游总是回 200 + 完整 body。
                    if ALLOWED_PATH in path and low.startswith(_conditional):
                        _stripped = True
                        continue
                    lines.append(line)
                if _stripped:
                    log_throttled("status-conditional",
                                  "Status 条件请求头已剥离（否则上游 304 无响应体，就没法改写）",
                                  every=3600)
                lines.append(b"Connection: close")
                up.sendall(b"\r\n".join(lines) + b"\r\n\r\n" + body)
                resp = b""
                while True:
                    c = up.recv(65536)
                    if not c:
                        break
                    resp += c
                up.close()
                rhead, _, rbody = resp.partition(b"\r\n\r\n")
                rfirst, rhdrs = parse_headers(rhead)
                client_close = "close" in (hdrs.get("connection", "") or "").lower()
                dechunked = False
                if "chunked" in rhdrs.get("transfer-encoding", "").lower():
                    rbody = dechunk(rbody)
                    dechunked = True
                _gwe_capture_dump(path, rbody, rhdrs)
                if VERBOSE:
                    log("RESP %s %dB"
                        % (rfirst.split(" ")[1] if " " in rfirst else rfirst, len(rbody)))
                elif ALLOWED_PATH in path:
                    # 非 verbose 也留一行 Status 回执：这是“游戏有没有来拉战况”的唯一证据。
                    # 排查时它能把“没来拉”和“拉了但没改写”分开（两种现场都遇到过）。
                    log("STATUS %s %dB" % (rfirst.split(" ")[1] if " " in rfirst else "?", len(rbody)))
                if ALLOWED_PATH in path and " 304 " in (" " + rfirst + " "):
                    log_throttled("status-304",
                                  "WARN: Status 返回 304 且没有响应体 —— 这次无法改写（条件头已剥离，下次应恢复）",
                                  every=300)

                # 跟踪玩家触碰过的星球：lobby 的 planetId，以及 Operation/Mission 的 planetIndex
                if body and any(k in path for k in ("/api/lobby", "/api/Operation",
                                                    "/api/Account/ReportPosition")):
                    try:
                        m = re.search(rb'"planetIndex"\s*:\s*(-?\d+)', body)
                        why = "mission"
                        if not m:
                            m = re.search(rb'"planetId"\s*:\s*(-?\d+)', body)
                            why = "lobby"
                        if m:
                            pi = int(m.group(1))
                            if pi >= 0:
                                self.mod.note_planet(pi, why)
                    except Exception:
                        pass

                out_body = rbody
                rewrite_added = 0
                dropped_encoding = False
                if (not self.mod.passthrough) and ALLOWED_PATH in path and rbody:
                    plain, was_gz = maybe_gunzip(rbody, rhdrs)
                    plan = {}
                    try:
                        candidate_plan = self.mod.effective_plan()
                        status_doc = json.loads(plain)
                        plan, filtered = resolve_plan(status_doc, candidate_plan)
                        if filtered:
                            detail = ", ".join(
                                "planet %d %s(%s) != owner(%s)" %
                                (p, name, faction, owner or "unknown")
                                for p, name, faction, owner in filtered)
                            log("FACTION FILTER: " + detail)
                        new_body, rewrite_added = rewrite_status(plain, plan)
                    except Exception as e:
                        log("rewrite skipped: %r" % e)
                        new_body, rewrite_added = plain, 0
                    if rewrite_added:
                        self.stats["rewrite"] += 1
                        out_body = new_body
                        dropped_encoding = was_gz
                        summary = ", ".join("planet %d -> %s" % (p, ids)
                                            for p, ids in sorted(plan.items())) or "extra: campaigns/owner"
                        active = self.mod.active_names()
                        trials = self.mod.active_stratagem_names()
                        label = "+".join(active) if active else "(none)"
                        trial_label = "、".join(x["name"] for x in trials) or "(none)"
                        log("REWRITE +%d entries (%s) 变种=%s 战备试用=%s%s"
                            % (rewrite_added, summary, label, trial_label,
                               " [from gzip]" if was_gz else ""), audit=True)
                        self._write_status(plan, label, trials)
                    else:
                        # 200 有响应体但没加任何条目：最常见是"游戏在报告星球之前就拉了 Status"，
                        # 属于正常时序（下一发就会改）；也可能是没选变种。措辞按这两种情况写。
                        _pl = {str(k): v for k, v in plan.items()}
                        if not _pl:
                            log_throttled("status-noplan",
                                          "Status 200 但还没有可注入的星球 —— 游戏报告星球位置后会改写"
                                          "（如果一直不生效：重启一次游戏，或在星图里等 Status 刷新）",
                                          every=300)
                        else:
                            log_throttled("status-nochange",
                                          "Status 200 但没有新增条目（plan=%s）—— 这些 id 可能已经在响应里了"
                                          % json.dumps(_pl, ensure_ascii=False), every=300)

                elif (not self.mod.passthrough) and INV_PATH in path and rbody:
                    # DSH_GWE_INV_V1：拥有的物品清单注入/移除（见 _gwe_inventory_rewrite）
                    plain, was_gz = maybe_gunzip(rbody, rhdrs)
                    try:
                        new_body, inv_added, inv_removed = _gwe_inventory_rewrite(plain)
                    except Exception as e:
                        log("inventory rewrite failed: %r" % e)
                        new_body, inv_added, inv_removed = None, 0, 0
                    if new_body is not None and (inv_added or inv_removed):
                        out_body = new_body
                        rewrite_added = inv_added + inv_removed
                        dropped_encoding = was_gz
                        self.stats["rewrite"] += 1
                        log("INV REWRITE +%d -%d items%s"
                            % (inv_added, inv_removed, " [from gzip]" if was_gz else ""),
                            audit=True)

                elif (not self.mod.passthrough) and ITEMS_PATH in path and rbody:
                    # DSH_GWE_ITEMS_V1：往服务端物品目录里补一条（克隆同族记录，改 itemId/mixId）
                    plain, was_gz = maybe_gunzip(rbody, rhdrs)
                    try:
                        new_body, items_added = _gwe_items_rewrite(plain)
                    except Exception as e:
                        log("items rewrite failed: %r" % e)
                        new_body, items_added = None, 0
                    if new_body is not None and items_added:
                        out_body = new_body
                        rewrite_added = items_added
                        dropped_encoding = was_gz
                        self.stats["rewrite"] += 1
                        log("ITEMS REWRITE +%d entries%s"
                            % (items_added, " [from gzip]" if was_gz else ""), audit=True)

                # 只要动过 body（去 chunk / 解 gzip / 改写）就必须重写响应头，
                # 否则客户端仍按 chunked 或旧长度解析 → 直接失败
                # （curl 表现为 HTTP 200 + 0 字节 + exit 56）。
                if dechunked or rewrite_added:
                    rhead = self._fix_headers(rhead, len(out_body),
                                              keep_encoding=not dropped_encoding)

                tls.sendall(rhead + b"\r\n\r\n" + out_body)
                if client_close:
                    break
        except Exception as e:
            log("handler error: %r" % e)
        finally:
            try:
                tls.close()
            except Exception:
                pass

    @staticmethod
    def _write_status(plan, active, stratagems=None):
        """给面板看的运行时状态（原子写）。"""
        try:
            RUNTIME.mkdir(parents=True, exist_ok=True)
            doc = {
                "planet": next(iter(plan), None),
                "planets": sorted(plan.keys()),
                "plan": {str(k): v for k, v in plan.items()},
                "variant": active,
                "stratagems": stratagems or [],
                "rewritten_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "pid": os.getpid(),
            }
            tmp = STATUS_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            tmp.replace(STATUS_FILE)
        except Exception as e:
            log("status write failed: %r" % e)

    @staticmethod
    def _fix_headers(rhead, new_len, keep_encoding=True):
        kept = [rhead.split(b"\r\n")[0]]
        for line in rhead.split(b"\r\n")[1:]:
            low = line.lower()
            if low.startswith((b"content-length:", b"transfer-encoding:", b"connection:")):
                continue
            if not keep_encoding and low.startswith(b"content-encoding:"):
                continue
            kept.append(line)
        kept.append(b"Content-Length: %d" % new_len)
        kept.append(b"Connection: close")
        return b"\r\n".join(kept)


def _session_mode(cert_dir):
    """读 session.json 里记录的证书模式（leaf / ca），决定握手时要不要带链。"""
    try:
        info = json.loads((Path(cert_dir) / "session.json").read_text(encoding="utf-8"))
        return info.get("mode") or "leaf"
    except Exception:
        return "leaf"


def serve_crl(cert_dir, port=8080):
    """在本机 8080 提供 ca.crl。

    Windows Schannel 看到证书里的 CDP 就会去取；取不到就报
    CRYPT_E_NO_REVOCATION_CHECK 并拒绝握手，所以这个服务是必需的。
    """
    crl = Path(cert_dir) / "ca.crl"
    if not crl.exists():
        log("no ca.crl -> skip CRL server（Schannel 可能会拒绝握手）")
        return None
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] not in ("/ca.crl", "/ca.crl.der"):
                self.send_error(404)
                return
            data = crl.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pkix-crl")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    log("CRL server on http://127.0.0.1:%d/ca.crl (%d B)" % (port, crl.stat().st_size))
    return srv


def port_owner_report(port):
    """谁在监听这个端口：返回 ["python.exe (PID 1234)", ...]。

    1.16 加它是因为现场日志里只有一行 "端口被占了"，看不出是旧代理还是加速器 ——
    而这两种处理方式完全不同（杀旧进程 / 关加速器）。
    """
    owners, pids = [], set()
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True,
                           text=True, errors="ignore", timeout=8)
        for line in (r.stdout or "").splitlines():
            f = line.split()
            if len(f) >= 5 and f[3].upper() == "LISTENING" and f[1].endswith(":%d" % port):
                try:
                    pids.add(int(f[4]))
                except ValueError:
                    pass
    except Exception as e:
        return ["（查询 netstat 失败：%r）" % (e,)]
    for pid in sorted(pids):
        name = "?"
        try:
            t = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                               capture_output=True, text=True, errors="ignore", timeout=6)
            parts = (t.stdout or "").split()
            if parts:
                name = parts[0]
        except Exception:
            pass
        owners.append("%s (PID %d)" % (name, pid))
    return owners or ["（netstat 没列出监听者 —— 可能是系统保留/WinNAT/端口代理）"]


def preflight(mod, cert_dir):
    """启动前自检：证书与会话一致性。任一不满足就拒绝启动。"""
    problems = []
    session = Path(cert_dir) / "session.json"
    if not session.exists():
        problems.append("缺少 session.json（先跑 setup.ps1）")
    else:
        try:
            info = json.loads(session.read_text(encoding="utf-8"))
            if info.get("san_dns") != [mod.host]:
                problems.append("证书 SAN 不是单一目标域名: %r" % (info.get("san_dns"),))
            if float(info.get("days", 99)) > 2:
                problems.append("证书有效期过长: %s 天" % info.get("days"))
            if info.get("self_check") != "OK":
                problems.append("证书自检未通过: %s" % info.get("self_check"))
        except Exception as e:
            problems.append("session.json 读取失败: %r" % e)
    keys = [p.name for p in Path(cert_dir).glob("*.key") if p.name != "server.key"]
    if keys:
        problems.append("会话目录里有多余私钥: %s" % keys)
    if mod.skipped:
        problems.append("配置里有无法识别的目标: %r" % (mod.skipped,))

    # 1.04：证书过期、或证书不是 ca 模式，都直接拒绝启动 ——
    # 这两种都会让游戏卡在“尝试与服务器通讯时出错”，但日志里看不出原因。
    try:
        info2 = json.loads(session.read_text(encoding="utf-8")) if session.exists() else {}
    except Exception:
        info2 = {}
    na = info2.get("not_after")
    if na:
        try:
            from datetime import datetime, timezone
            exp = datetime.fromisoformat(str(na).replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= datetime.now(timezone.utc):
                problems.append("证书已过期（%s）-> 重跑 setup.ps1（或面板的安装按钮）" % na)
        except Exception:
            pass
    if info2 and info2.get("mode") != "ca":
        problems.append("证书模式是 %r：游戏只认 ca（leaf 没有 CRL，客户端会在握手前断开）"
                        " -> 重跑 setup.ps1" % (info2.get("mode"),))
    return problems


def main():
    global VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config.json"))
    ap.add_argument("--catalog", default=str(ROOT / "variant_catalog.json"))
    ap.add_argument("--cert-dir", default=str(ROOT / "certs"))
    ap.add_argument("--cert-mode", choices=["leaf", "ca"], default="leaf")
    ap.add_argument("--passthrough", action="store_true", help="纯转发，不改写")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--dev", action="store_true", help="启用研究用开关")
    ap.add_argument("--drop-def", default="")
    ap.add_argument("--add-def", default="")
    ap.add_argument("--inject", default="")
    ap.add_argument("--verbose", action="store_true",
                    help="把每条 REQ/RESP 也写进日志（默认只写必要日志）")
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8-sig"))
    VERBOSE = bool(a.verbose or cfg.get("verbose"))
    rotate_logs()
    catdoc = json.loads(Path(a.catalog).read_text(encoding="utf-8"))
    base = catdoc.get("variants") or {}
    aliases = catdoc.get("aliases") or {}
    catalog = dict(base)
    for alias, target in aliases.items():          # 旧名（如“掠食”“阴霾”）仍然可用
        if target in base:
            catalog[alias] = base[target]
    cfg["_aliases"] = aliases
    meta = catdoc.get("meta") or {}
    cfg["_meta"] = meta
    if a.passthrough:
        cfg["passthrough"] = True
    if a.port:
        cfg["port"] = a.port
    if a.dev and cfg.get("allowDevFlags"):
        log("DEV 模式：%s" % {"drop": a.drop_def, "add": a.add_def, "inject": a.inject})
        # 研究开关仅打日志与提示；产品路径不实现它们，避免误用
    elif a.dev:
        log("DEV 开关被忽略：config.allowDevFlags=false")

    mod = Mod(cfg, catalog, meta)
    problems = preflight(mod, a.cert_dir)
    if problems:
        for p in problems:
            log("PREFLIGHT FAIL: " + p)
        log("拒绝启动（安全自检未通过）")
        return 2
    if not mod.plan:
        log("提示：config.targets 为空 —— 注入内容完全由面板的 selection.json 决定")

    proxy = Proxy(mod, a.cert_dir,
                  send_chain=(a.cert_mode == "ca" or _session_mode(a.cert_dir) == "ca"))
    # 1.16：先重试 5 秒（面板每秒会探测一次端口占用，那一瞬间我们也绑不上；旧代理退出也需要一点时间），
    # 还不行就把**占用者姓名/PID**直接写进日志 —— 以前只说“被占了”，现场只能靠猜。
    _port = int(cfg.get("port", 443))
    srv = None
    last_err = None
    for attempt in range(1, 11):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 用独占绑定：带 SO_REUSEADDR 时 Windows 会允许“抢占”别人正在监听的端口，
        # 结果是我们以为起来了、实际流量还在别人手里。
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            s.bind((mod.listen_ip, _port))
            srv = s
            break
        except OSError as e:
            last_err = e
            s.close()
            if attempt == 1:
                log("bind %s:%d 失败（%r），重试最多 5 秒…" % (mod.listen_ip, _port, e))
            time.sleep(0.5)
    if srv is None:
        log("BIND FAIL %s:%d -> %r" % (mod.listen_ip, _port, last_err))
        for who in port_owner_report(_port):
            log("  占用者: " + who)
        log("  端口被别的程序占了。如果是本 mod 的旧代理（路径里是别的 VariantMod 目录），"
            "用任务管理器结束它，或去那个目录跑 teardown.ps1；"
            "其它程序（加速器/代理软件）则先关掉。也可以在面板里点“换监听地址（IP）”换一张网卡"
            "（listenIp 不要用 127.x —— 19411 之后客户端会拒绝回环连接）。")
        return 3
    srv.listen(64)
    serve_crl(a.cert_dir, int(cfg.get("crlPort", 8080)))
    log("=" * 60)
    log("variant_mod proxy  host=%s  listen=%s:%d  passthrough=%s  allowlist=%s"
        % (mod.host, mod.listen_ip, int(cfg.get("port", 443)), mod.passthrough, mod.host))
    log("plan: %s" % json.dumps(mod.describe(), ensure_ascii=False), audit=True)
    # 1.13：启动时把“到底选了哪些变种”明确写出来。以前没有选择时这里什么都不显示，
    # 代理看起来一切正常、实际上纯转发 —— 现场排查时极易误判成“mod 没生效”。
    mod.reload_selection()
    _active = mod.active_names()
    _trials = mod.active_stratagem_names()
    if _active or _trials:
        log("selection: 变种=%s 战备试用=%s"
            % ("、".join(_active) or "(none)",
               "、".join(x["name"] for x in _trials) or "(none)"), audit=True)
    else:
        log("WARN: 还没有选中任何词条或战备 —— 现在等于纯转发"
            "（面板里选变种或战备试用后，再点启动代理）",
            audit=True)
    log("绑定 %s 单一域名；只改写 %s；不落盘请求体" % (mod.listen_ip, STATUS_MARK))
    try:
        LOGDIR.mkdir(parents=True, exist_ok=True)
        PROXY_PID.write_text(str(os.getpid()), encoding="utf-8")
        import atexit

        def _cleanup():
            try:
                if PROXY_PID.read_text(encoding="utf-8").strip() == str(os.getpid()):
                    PROXY_PID.unlink()
            except Exception:
                pass

        atexit.register(_cleanup)
        log("proxy pid %d -> %s" % (os.getpid(), PROXY_PID))
    except Exception as e:
        log("pid file write failed: %r" % e)
    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=proxy.handle, args=(conn, addr), daemon=True)
        t.start()



# ---- DSH_GWE_ITEMS_V1 : 服务端物品目录补条目（/api/Progression/items） ----
def _gwe_items_rewrite(plain):
    """按 runtime/items_inject.json 往物品目录里补记录。

    配置示例：
        {"enabled": true, "template": 3866352840, "add": [2112173638]}

    `template` = 拿来克隆的 itemId（同族已存在的记录）；`add` = 要补的 itemId 列表。
    克隆只改 itemId / mixId，其余字段（progressionCategory / tags / 价格）保持一致。
    返回 (new_body, added)；无改动时 (None, 0)。
    """
    try:
        cfg = json.loads(ITEMS_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None, 0
    if not cfg.get("enabled"):
        return None, 0
    try:
        doc = json.loads(plain)
    except Exception:
        return None, 0
    if not isinstance(doc, list):
        return None, 0
    have = set()
    for r in doc:
        if isinstance(r, dict):
            try:
                have.add(int(r.get("itemId", 0)))
            except (TypeError, ValueError):
                pass
    tmpl = None
    try:
        t = int(cfg.get("template", 0) or 0)
    except (TypeError, ValueError):
        t = 0
    if t:
        for r in doc:
            if isinstance(r, dict):
                try:
                    if int(r.get("itemId", 0)) == t:
                        tmpl = r
                        break
                except (TypeError, ValueError):
                    continue
    by_id = {}
    for r in doc:
        if isinstance(r, dict):
            try:
                by_id[int(r.get("itemId", 0))] = r
            except (TypeError, ValueError):
                pass
    added = 0
    for spec in cfg.get("add") or []:
        if isinstance(spec, dict):
            try:
                mid = int(spec.get("id", 0))
                src = int(spec.get("template", 0) or 0)
            except (TypeError, ValueError):
                continue
            base = by_id.get(src) or tmpl
        else:
            try:
                mid = int(spec)
            except (TypeError, ValueError):
                continue
            base = tmpl
        if not mid or mid in have or base is None:
            continue
        rec = json.loads(json.dumps(base))
        rec["itemId"] = mid
        rec["mixId"] = mid
        doc.append(rec)
        have.add(mid)
        added += 1
    if not added:
        return None, 0
    return json.dumps(doc, separators=(",", ":")).encode("utf-8"), added


# ---- DSH_GWE_INV_V1 : 拥有的物品清单改写（/api/Progression/inventory） ----
def _gwe_inventory_rewrite(plain):
    """按 runtime/inventory_inject.json 改写 inventory 响应。

    配置示例：
        {"enabled": true,
         "items":    [{"mixId": 2112173638, "amount": 1, "isDiscovered": false}],
         "remove":   [2308714558],
         "customization": [{"mixId32": 4161086429, "index": 0, "activeIndex": 0,
                            "slots": [1896165189, 3905063732, 2163992125, 0,0,0,0,0],
                            "modes": [0,0,0,0]}]}

    返回 (new_body, added, removed)；没有改动时返回 (None, 0, 0)。
    只动 items / customization 两个数组，其余字段原样保留。
    """
    try:
        cfg = json.loads(INV_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None, 0, 0
    if not cfg.get("enabled"):
        return None, 0, 0
    try:
        doc = json.loads(plain)
    except Exception:
        return None, 0, 0
    items = doc.get("items")
    if not isinstance(items, list):
        return None, 0, 0

    have = set()
    for it in items:
        if isinstance(it, dict):
            try:
                have.add(int(it.get("mixId", 0)))
            except (TypeError, ValueError):
                pass

    removed = 0
    drop = set()
    for v in cfg.get("remove") or []:
        try:
            drop.add(int(v))
        except (TypeError, ValueError):
            pass
    if drop:
        kept = []
        for it in items:
            try:
                mid = int(it.get("mixId", 0)) if isinstance(it, dict) else 0
            except (TypeError, ValueError):
                mid = 0
            if mid in drop:
                removed += 1
                continue
            kept.append(it)
        items = kept
        doc["items"] = items

    added = 0
    for spec in cfg.get("items") or []:
        try:
            mid = int(spec.get("mixId", 0))
        except (TypeError, ValueError):
            continue
        if not mid or mid in have:
            continue
        items.append({"mixId": mid,
                      "amount": int(spec.get("amount", 1)),
                      "isDiscovered": bool(spec.get("isDiscovered", False))})
        have.add(mid)
        added += 1

    cust = doc.get("customization")
    if isinstance(cust, list):
        seen = set()
        for c in cust:
            if isinstance(c, dict):
                try:
                    seen.add((int(c.get("mixId32", 0)), int(c.get("index", 0))))
                except (TypeError, ValueError):
                    pass
        for spec in cfg.get("customization") or []:
            try:
                key = (int(spec.get("mixId32", 0)), int(spec.get("index", 0)))
            except (TypeError, ValueError):
                continue
            if not key[0] or key in seen:
                continue
            slots = [int(x) for x in (spec.get("slots") or [])][:8]
            modes = [int(x) for x in (spec.get("modes") or [])][:4]
            cust.append({"mixId32": key[0], "index": key[1],
                         "activeIndex": int(spec.get("activeIndex", 0)),
                         "slots": slots + [0] * (8 - len(slots)),
                         "modes": modes + [0] * (4 - len(modes))})
            seen.add(key)
            added += 1

    if not (added or removed):
        return None, 0, 0
    return json.dumps(doc, separators=(",", ":")).encode("utf-8"), added, removed


# ---- DSH_GWE_CAPTURE_V1 : read-only response dump (added by DSH tools/gwe_capture.py) ----
def _gwe_capture_dump(path, body, hdrs):
    """把匹配路径的响应体原样落盘，供离线分析。绝不写 header/token，异常一律吞掉。"""
    import gzip, hashlib, json as _json, os, re as _re, time as _time
    try:
        outdir = os.environ.get("HD2_GWE_DUMP", "")
        if not outdir or not body:
            return
        pats = [p.strip() for p in os.environ.get(
            "HD2_GWE_PATHS", "/api/WarSeason/GalacticWarEffects").split(",") if p.strip()]
        if not any(p in path for p in pats):
            return
        cap = int(os.environ.get("HD2_GWE_MAX", str(8 << 20)) or (8 << 20))
        raw = body
        if body[:2] == b"\x1f\x8b":
            try:
                raw = gzip.decompress(body)
            except Exception:
                raw = body
        if len(raw) > cap:
            log("gwe-dump skipped: %d B > cap %d" % (len(raw), cap))
            return
        os.makedirs(outdir, exist_ok=True)
        digest = hashlib.sha256(raw).hexdigest()
        slug = _re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[-60:] or "body"
        stamp = _time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime())
        # 按内容哈希命名 => 同一份响应被轮询多次也只落一个文件
        fp = os.path.join(outdir, "%s_%s.json" % (digest[:8], slug))
        if os.path.exists(fp):
            return
        with open(fp, "wb") as fh:
            fh.write(raw)
        try:
            _json.loads(raw.decode("utf-8", "replace"))
            kind = "json"
        except Exception:
            kind = "not-json"
        # 只记：时间 / 路径 / 字节数 / sha256 / 是否合法 JSON。不记 header。
        with open(os.path.join(outdir, "index.txt"), "a", encoding="utf-8") as ix:
            ix.write("%s\t%s\t%d\t%s\t%s\n" % (stamp, path, len(raw), digest, kind))
        log("gwe-dump %s %d B -> %s" % (path.split("?")[0], len(raw), fp))
    except Exception as e:
        try:
            log("gwe-dump failed (ignored): %r" % e)
        except Exception:
            pass
# ---- /DSH_GWE_CAPTURE_V1 ----

def _gwe_capture_req(path, body, hdrs, method=""):
    """请求体落盘：给“客户端提案”类请求用（Operation* / lobby / 改装保存）。绝不写 header/token。"""
    import gzip, hashlib, os, re as _re, time as _time
    try:
        outdir = os.environ.get("HD2_GWE_DUMP", "")
        if not outdir or not body:
            return
        pats = [p.strip() for p in os.environ.get(
            "HD2_GWE_REQ_PATHS",
            "/api/Operation,/api/lobby,/api/Progression/Items/Customize").split(",") if p.strip()]
        if not any(p in path for p in pats):
            return
        cap = int(os.environ.get("HD2_GWE_MAX", str(8 << 20)) or (8 << 20))
        raw = body
        if body[:2] == b"\x1f\x8b":
            try:
                raw = gzip.decompress(body)
            except Exception:
                raw = body
        if len(raw) > cap:
            log("gwe-req skipped: %d B > cap %d" % (len(raw), cap))
            return
        os.makedirs(outdir, exist_ok=True)
        digest = hashlib.sha256((method + "\x00").encode() + path.encode("utf-8", "replace")
                                + b"\x00" + raw).hexdigest()
        slug = _re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[-60:] or "req"
        stamp = _time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime())
        tag = (method or "REQ").upper()[:6]
        fp = os.path.join(outdir, "req_%s_%s_%s.json" % (tag, digest[:8], slug))
        if os.path.exists(fp):
            return
        with open(fp, "wb") as fh:
            fh.write(raw)
        with open(os.path.join(outdir, "index.txt"), "a", encoding="utf-8") as ix:
            ix.write("%s\tREQ %s\t%s\t%d\t%s\n" % (stamp, tag, path, len(raw), digest))
        log("gwe-req %s %s %d B -> %s" % (tag, path.split("?")[0], len(raw), fp))
    except Exception as e:
        try:
            log("gwe-req failed (ignored): %r" % e)
        except Exception:
            pass
# ---- /DSH_GWE_CAPTURE_V1_END ----

# DSH-DEFENSE-INJECT-V1
def _gwe_apply_extra(doc):
    """按环境变量 HD2_GWE_EXTRA 对 Status 做额外改写：追加战役 / 改星球归属。

    格式（JSON 字符串）：
        {"campaigns": [{"planet": 139, "id": 51999, "type": 0, "count": 1, "race": 1}],
         "owner":     {"139": 1}}

    只动目标条目，不删不改其它星球；异常一律吞掉并记一行日志。
    返回改动条数（0 = 没动，调用方据此决定要不要重发 body）。
    """
    import json as _json, os
    spec = (os.environ.get("HD2_GWE_EXTRA") or "").strip()
    if not spec:
        return 0
    try:
        cfg = _json.loads(spec)
    except Exception as e:
        log_throttled("extra-json", "gwe-extra: 解析失败 %r" % e, every=600)
        return 0
    if not isinstance(cfg, dict):
        return 0
    changed = 0
    camps = doc.get("campaigns")
    if isinstance(camps, list):
        for c in cfg.get("campaigns") or []:
            try:
                pidx = int(c.get("planet"))
            except (TypeError, ValueError):
                continue
            if any(isinstance(x, dict) and x.get("planetIndex") == pidx for x in camps):
                log_throttled("extra-camp-dup", "gwe-extra: 星球 %d 已有战役，跳过" % pidx, every=3600)
                continue
            entry = {
                "id": int(c.get("id") or 51999),
                "planetIndex": pidx,
                "type": int(c.get("type") or 0),
                "count": int(c.get("count") or 1),
                "race": int(c.get("race") if c.get("race") is not None else 1),
            }
            camps.append(entry)
            changed += 1
            log("REWRITE-EXTRA 追加战役 %s" % _json.dumps(entry))
    # 追加攻击边：{source, target}。线上 63 条全是「人类星球 -> 敌星」，
    # 防守如果要成立，很可能需要「敌星 -> 我方星球」这个反向边。
    atk = doc.get("planetAttacks")
    if isinstance(atk, list):
        for a in cfg.get("attacks") or []:
            try:
                src, dst = int(a.get("source")), int(a.get("target"))
            except (TypeError, ValueError):
                continue
            if any(isinstance(x, dict) and x.get("source") == src and x.get("target") == dst
                   for x in atk):
                log_throttled("extra-atk-dup",
                              "gwe-extra: 攻击边 %d->%d 已存在，跳过" % (src, dst), every=3600)
                continue
            atk.append({"source": src, "target": dst})
            changed += 1
            log("REWRITE-EXTRA 追加攻击边 %d -> %d" % (src, dst))
    # 追加星球事件（限时战役）：eventType 1=防守 / 2=进攻（源自社区 API 模型 PlanetEvent）。
    # startTime/expireTime 与 Status.time 同一时钟，这里用 startOffset/endOffset 相对算，
    # 免得手写绝对值写错。
    ev = doc.get("planetEvents")
    if isinstance(ev, list):
        now = int(doc.get("time") or 0)
        # 本 spec 里注入的 campaign：{planetIndex: id}，给事件当 campaignId 兜底
        _camp_id_of = {}
        for _c in cfg.get("campaigns") or []:
            try:
                _camp_id_of[int(_c.get("planet"))] = int(_c.get("id"))
            except (TypeError, ValueError):
                continue
        for e in cfg.get("events") or []:
            try:
                pidx = int(e.get("planet"))
            except (TypeError, ValueError):
                continue
            et = int(e.get("eventType") or 1)
            if any(isinstance(x, dict) and x.get("planetIndex") == pidx
                   and x.get("eventType") == et for x in ev):
                log_throttled("extra-ev-dup", "gwe-extra: 星球 %d 已有 eventType=%d 事件，跳过"
                              % (pidx, et), every=3600)
                continue
            entry = {
                "id": int(e.get("id") or 9001),
                "planetIndex": pidx,
                "eventType": et,
                "race": int(e.get("race") or 1),
                "health": int(e.get("health") or 1000000),
                "maxHealth": int(e.get("maxHealth") or 1000000),
                "startTime": now + int(e.get("startOffset") or -60),
                "expireTime": now + int(e.get("endOffset") or 86400),
                "campaignId": int(e.get("campaignId") or _camp_id_of.get(pidx) or 0),
                # 真实样本里这里是 [事件自己的 id]，不是空数组；空数组会让客户端解析失败
                "jointOperationIds": [int(e.get("id") or 9001)],
                # 真实样本里有这一格（值 0），缺了客户端可能不认这条事件
                "potentialBuildUp": int(e.get("potentialBuildUp") or 0),
            }
            ev.append(entry)
            changed += 1
            log("REWRITE-EXTRA 追加星球事件 %s" % _json.dumps(entry))
            # 配套的 jointOperations 条目：真实样本里每个 planetEvent 都有一条同 id 记录
            jo = doc.get("jointOperations")
            eid = entry["id"]
            if isinstance(jo, list) and not any(isinstance(x, dict) and x.get("id") == eid
                                                for x in jo):
                jo.append({
                    "id": eid,
                    "planetIndex": pidx,
                    "hqNodeIndex": int(e.get("hqNodeIndex") or 1),
                })
                changed += 1
                log("REWRITE-EXTRA 追加联合作战 id=%d planet=%d" % (eid, pidx))
    # 全局事件效果：{eventId: [effectId...]}。globalEvents[].effectIds 是"全局效果"通道
    # （武器实验就是这么挂的），不依赖星球。
    ge = doc.get("globalEvents")
    if isinstance(ge, list):
        for ev in ge:
            if not isinstance(ev, dict):
                continue
            key = str(ev.get("eventId"))
            for eid in (cfg.get("globalEffects") or {}).get(key) or []:
                ids = ev.get("effectIds")
                if not isinstance(ids, list):
                    ids = ev["effectIds"] = []
                if int(eid) not in ids:
                    ids.append(int(eid))
                    changed += 1
                    log("REWRITE-EXTRA 全局事件 %s += effect %d" % (key, int(eid)))
# DSH-CITY-REGIONS-V1
    # 分区状态：按原生 WarInfo 定义补齐缺失的 (planetIndex, regionIndex)。
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
    for k, v in (cfg.get("owner") or {}).items():
        for r in doc.get("planetStatus") or []:
            if not isinstance(r, dict):
                continue
            if str(r.get("index")) == str(k):
                try:
                    nv = int(v)
                except (TypeError, ValueError):
                    continue
                if r.get("owner") != nv:
                    log("REWRITE-EXTRA 星球 %s owner %s -> %s" % (k, r.get("owner"), nv))
                    r["owner"] = nv
                    changed += 1
                break
    return changed


if __name__ == "__main__":
    sys.exit(main())

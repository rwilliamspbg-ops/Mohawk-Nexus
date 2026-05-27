
import re
from collections import defaultdict

TIME_RE  = re.compile(r'time:\s+\[([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\]')
THRPT_RE = re.compile(r'thrpt:\s+\[([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\]')

def to_ns(v, u):
    u = str(u).strip()
    return float(v) * {'ns': 1, 'µs': 1e3, 'us': 1e3, 'ms': 1e6, 's': 1e9}.get(u, 1)

def fmt_t(ns):
    if ns < 1e3:  return f"{ns:.1f} ns"
    if ns < 1e6:  return f"{ns/1e3:.3f} µs"
    return f"{ns/1e6:.3f} ms"

rows = []
current = None
for line in bench_lines:
    stripped = line.strip()
    # "Benchmarking inplace_forwarder/baseline_vec/16: Warming up..."
    # "Benchmarking inplace_forwarder/baseline_vec/16"
    m_bench = re.match(r'^(?:Benchmarking\s+)?([\w]+/[\w]+/\d+)(?:\s+.*)?$', stripped)
    if m_bench and 'time:' not in stripped and 'thrpt:' not in stripped:
        candidate = m_bench.group(1)
        if re.match(r'^\w+/\w+/\d+$', candidate):
            current = candidate

    tm = TIME_RE.search(stripped)
    if tm and current:
        mid = to_ns(tm.group(3), tm.group(4))
        tp = THRPT_RE.search(stripped)
        thrpt = None
        if tp:
            tu = str(tp.group(4))
            mult = {'K': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12}
            scale = mult.get(tu[0], 1e6) if tu else 1e6
            thrpt = float(tp.group(3)) * scale
        rows.append({'bench': current, 'mid': mid, 'thrpt': thrpt})
        current = None

print(f"Total rows parsed: {len(rows)}")

# Group by group/variant/count
G = defaultdict(lambda: defaultdict(dict))
for r in rows:
    p = r['bench'].split('/')
    if len(p) >= 3:
        try: cnt = int(p[2])
        except: cnt = p[2]
        G[p[0]][cnt][p[1]] = r

VMAP = {
    "inplace_forwarder":      ["baseline_vec", "zerocopy_ring", "inplace_slices"],
    "inplace_poll_cost":      ["clone_poll", "ring_poll_slices", "zerocopy_transmute"],
    "inplace_forwarder_only": ["process_batch_vec", "process_batch_inplace"],
}

print(f"\n{'─'*108}")
for grp in ["inplace_forwarder", "inplace_poll_cost", "inplace_forwarder_only"]:
    if grp not in G:
        print(f"\n  GROUP: {grp}  (no data)")
        continue
    vars_ = VMAP[grp]
    print(f"\n  GROUP: {grp}")
    print(f"  {'Cnt':>5}  {'Variant':<35} {'Time (mid)':<20} {'Throughput (mid)':<22} {'vs baseline'}")
    print(f"  {'─'*5}  {'─'*35} {'─'*20} {'─'*22} {'─'*14}")
    for cnt in [16, 64, 256]:
        if cnt not in G[grp]: continue
        base = None
        for v in vars_:
            if v not in G[grp][cnt]: continue
            r = G[grp][cnt][v]
            ts = fmt_t(r['mid'])
            pv = r['thrpt'] if r['thrpt'] is not None else 1e9 / r['mid']
            pu = f"{pv/1e6:.2f} Mpps"
            if base is None:
                base = r['mid']
                rs = ""
            else:
                ratio = base / r['mid']
                rs = f"{ratio:.2f}x faster" if ratio > 1.05 else (f"{1/ratio:.2f}x slower" if ratio < 0.95 else "approx parity")
            print(f"  {cnt:>5}  {v:<35} {ts:<20} {pu:<22} {rs}")

print(f"\n{'─'*108}")

# ── Cumulative gain table ─────────────────────────────────────────────────────
# Pull actual measured numbers from our rows
def get_mid(grp, var, cnt):
    return G.get(grp, {}).get(cnt, {}).get(var, {}).get('mid', None)

b16 = get_mid("inplace_forwarder", "baseline_vec", 16)
z16 = get_mid("inplace_forwarder", "inplace_slices", 16)
b64 = get_mid("inplace_forwarder", "baseline_vec", 64)
z64 = get_mid("inplace_forwarder", "inplace_slices", 64)
b256 = get_mid("inplace_forwarder", "baseline_vec", 256)
z256 = get_mid("inplace_forwarder", "inplace_slices", 256)

print("\n=== CUMULATIVE OPTIMISATION GAINS — INPLACE_FORWARDER GROUP ===")
header = f"  {'Pkts':>5}  {'baseline_vec':>18}  {'inplace_slices':>18}  {'speedup':>10}"
print(header)
print("  " + "─" * (len(header)-2))
for cnt, b, z in [(16, b16, z16), (64, b64, z64), (256, b256, z256)]:
    if b and z:
        bpps = 1e9 / b / 1e6
        zpps = 1e9 / z / 1e6
        spd = b / z
        print(f"  {cnt:>5}  {fmt_t(b):>18}  {fmt_t(z):>18}  {spd:>8.2f}x  ({bpps:.2f} Mpps -> {zpps:.2f} Mpps)")

print("\n=== POLL PATH BREAKDOWN ===")
cp16 = get_mid("inplace_poll_cost", "clone_poll", 16)
zt16 = get_mid("inplace_poll_cost", "zerocopy_transmute", 16)
cp64 = get_mid("inplace_poll_cost", "clone_poll", 64)
zt64 = get_mid("inplace_poll_cost", "zerocopy_transmute", 64)
for cnt, cp, zt in [(16, cp16, zt16), (64, cp64, zt64)]:
    if cp and zt:
        print(f"  {cnt} pkts: clone_poll={fmt_t(cp)}  zerocopy_transmute={fmt_t(zt)}  poll speedup={cp/zt:.2f}x")

inplace_bench_results = rows

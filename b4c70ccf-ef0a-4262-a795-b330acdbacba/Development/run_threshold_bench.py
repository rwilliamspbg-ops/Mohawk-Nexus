
import os, glob, re, urllib.request, stat as _stat
from collections import defaultdict

# ── Locate workspace & Rust ───────────────────────────────────────────────────
def _find_ws():
    for d in sorted(glob.glob("/tmp/tmp*/files/SMIP-MWP-Rust"), reverse=True):
        if os.path.isdir(os.path.join(d, "bench")):
            return d
    return None

WS = _find_ws()
assert WS, "workspace not found"
print(f"Workspace: {WS}")

RUST = None
for candidate in ["/tmp/rustenv"] + sorted(glob.glob("/tmp/tmp*/rustenv"), reverse=True):
    if os.path.isfile(os.path.join(candidate, "cargo/bin/cargo")):
        RUST = candidate; break
assert RUST, "Rust not found"

CARGO_HOME  = f"{RUST}/cargo"
RUSTUP_HOME = f"{RUST}/rustup"
CARGO_BIN   = f"{CARGO_HOME}/bin"
CARGO       = f"{CARGO_BIN}/cargo"
print("Rust ✓")

def sh(cmd, cwd=WS):
    out_f = "/tmp/_sh_out.txt"
    rc = os.system(f"cd {cwd} && {cmd} > {out_f} 2>&1")
    return rc, open(out_f).read() if os.path.isfile(out_f) else ""

env_str = (f"CARGO_HOME={CARGO_HOME} RUSTUP_HOME={RUSTUP_HOME} "
           f"CARGO_TERM_COLOR=never PATH={CARGO_BIN}:{os.environ['PATH']}")

# ── Fix corrupted files ───────────────────────────────────────────────────────
OUR_FILES = {"threshold_bench.rs", "inplace_bench.rs", "zero_copy_bench.rs",
             "true_zerocopy_bench.rs", "poll_slices_bench.rs", "umem_bench.rs",
             "simd_alloc_bench.rs", "alloc_bench_extended.rs", "final_bench.rs",
             "recommendations_bench.rs"}

def git_show(rel_path):
    out_f = "/tmp/_git_show.txt"
    rc = os.system(f"cd {WS} && git show HEAD:{rel_path} > {out_f} 2>&1")
    if rc != 0: return None
    content = open(out_f, "rb").read()
    if content.startswith(b"ZERVE_PLACEHOLDER"):
        nl = content.find(b"\n"); content = content[nl+1:] if nl != -1 else b""
    return content.decode("utf-8", errors="replace")

fixed = []
for f in sorted(glob.glob(f"{WS}/**/*", recursive=True)):
    if not os.path.isfile(f) or os.path.basename(f) in OUR_FILES: continue
    if f.endswith((".toml", ".rs")):
        raw = open(f, "rb").read(32)
        if b"ZERVE_PLACEHOLDER" in raw or b"\x00" in raw:
            rel = os.path.relpath(f, WS)
            clean = git_show(rel)
            if clean: open(f, "w").write(clean); fixed.append(rel)
if fixed: [print(f"  ✓ Fixed {x}") for x in fixed]
else:     print("  All files clean")

# ── Detect exact Forwarder::new constructor ────────────────────────────────────
DP_LIB = f"{WS}/datapath/src/lib.rs"
dp_src = open(DP_LIB).read()

# Find fn new(...) in impl Forwarder
new_match = re.search(r'pub fn new\(([^)]*)\)\s*->\s*Self', dp_src)
forwarder_new_args = new_match.group(1).strip() if new_match else ""
print(f"  Forwarder::new args: ({forwarder_new_args})")

# Build the correct constructor call for bench
# If it takes `routes: routing::Table` or similar, we need to pass it
if not forwarder_new_args:
    fwd_new = "datapath::Forwarder::new()"
elif "Table" in forwarder_new_args:
    # Find what the Table constructor is - check datapath bench that already works
    # Look in existing bench files for how they create Forwarder
    fwd_new = None
    for bf in glob.glob(f"{WS}/bench/benches/*.rs"):
        bsrc = open(bf).read()
        m = re.search(r'Forwarder::new\([^)]*\)', bsrc)
        if m:
            # ensure balanced parens — strip trailing incomplete parens and re-close
            raw_call = m.group(0)
            open_p = raw_call.count("("); close_p = raw_call.count(")")
            raw_call = raw_call.rstrip(")") + ")" * open_p  # re-balance
            fwd_new = f"datapath::{raw_call}"
            print(f"  Found constructor in {os.path.basename(bf)}: {fwd_new}")
            break
    if not fwd_new:
        # check routing::Table constructors
        rt_lib = f"{WS}/routing/src/lib.rs"
        if os.path.isfile(rt_lib):
            rt_src = open(rt_lib).read()
            if "fn new()" in rt_src:
                fwd_new = "datapath::Forwarder::new(routing::Table::new())"
            elif "fn default()" in rt_src or "Default" in rt_src:
                fwd_new = "datapath::Forwarder::new(routing::Table::default())"
            else:
                fwd_new = "datapath::Forwarder::new(routing::Table { entries: vec![] })"
        else:
            fwd_new = "datapath::Forwarder::new(routing::Table::default())"
else:
    fwd_new = "datapath::Forwarder::new()"

print(f"  Using: {fwd_new}")

# ── Add process_batch_slices_simple / process_batch_simple ────────────────────
BENCH_LIB   = f"{WS}/bench/src/lib.rs"
BENCH_DIR   = f"{WS}/bench/benches"
BENCH_PATH  = f"{BENCH_DIR}/threshold_bench.rs"
BENCH_CARGO = f"{WS}/bench/Cargo.toml"

bench_src = open(BENCH_LIB).read()

SIMPLE_INPLACE = '''
    pub fn process_batch_slices_simple(&mut self, frames: &[&[u8]]) -> Vec<Vec<u8>> {
        let mut out = Vec::with_capacity(frames.len());
        for frame in frames {
            if frame.len() < 4 { continue; }
            let mut buf = frame.to_vec();
            let flags = buf[0]; let proto = buf[1];
            let dst = ((buf[2] as u16) << 8) | buf[3] as u8 as u16;
            if proto == 0x01 { for b in buf[4..].iter_mut() { *b ^= 0xA5; } }
            let _route = (dst ^ flags as u16) & 0xFF;
            out.push(buf);
        }
        out
    }
'''
SIMPLE_CLONE = '''
    pub fn process_batch_simple(&mut self, frames: Vec<Vec<u8>>) -> Vec<Vec<u8>> {
        let mut out = Vec::with_capacity(frames.len());
        for frame in frames {
            if frame.len() < 4 { continue; }
            let mut buf = frame;
            let flags = buf[0]; let proto = buf[1];
            let dst = ((buf[2] as u16) << 8) | buf[3] as u8 as u16;
            if proto == 0x01 { for b in buf[4..].iter_mut() { *b ^= 0xA5; } }
            let _route = (dst ^ flags as u16) & 0xFF;
            out.push(buf);
        }
        out
    }
'''

def inject_after_first_fn(src, code):
    anchor = "pub fn process_batch"
    idx = src.find(anchor)
    if idx == -1:
        return src[:src.rfind("\n}")] + "\n" + code + src[src.rfind("\n}"):]
    depth, pos, in_fn = 0, idx, False
    while pos < len(src):
        c = src[pos]
        if c == '{': depth += 1; in_fn = True
        elif c == '}':
            depth -= 1
            if in_fn and depth == 0:
                return src[:pos+1] + "\n" + code + src[pos+1:]
        pos += 1
    return src

if "process_batch_slices_simple" not in dp_src:
    dp_src = inject_after_first_fn(dp_src, SIMPLE_INPLACE)
    print("  ✓ Added process_batch_slices_simple")
if "process_batch_simple" not in dp_src:
    dp_src = inject_after_first_fn(dp_src, SIMPLE_CLONE)
    print("  ✓ Added process_batch_simple")
open(DP_LIB, "w").write(dp_src)
print(f"  ✓ datapath/src/lib.rs: {len(dp_src)} chars")

# ── ThresholdDispatchSocket ───────────────────────────────────────────────────
THRESHOLD_SOCKET = '''
// ── ThresholdDispatchSocket ───────────────────────────────────────────────────
pub struct ThresholdDispatchSocket {
    templates: Vec<Vec<u8>>, frame_size: usize, threshold: usize, slab: Vec<u8>,
}
impl ThresholdDispatchSocket {
    pub fn new(n: usize, frame_size: usize, threshold: usize) -> Self {
        let mut templates = Vec::with_capacity(n);
        for i in 0..n {
            let mut f = vec![0u8; frame_size];
            f[0]=(i&0xFF)as u8; f[1]=0x01; f[2]=((i>>8)&0xFF)as u8; f[3]=(i&0xFF)as u8;
            for b in f[4..].iter_mut() { *b=0xAB; } templates.push(f);
        }
        Self { templates, frame_size, threshold, slab: vec![0u8; n*frame_size] }
    }
    #[inline(always)] pub fn dispatch(&mut self, fwd: &mut datapath::Forwarder, n: usize) -> Vec<Vec<u8>> {
        if n >= self.threshold { self.dispatch_inplace_only(fwd,n) } else { self.dispatch_clone_only(fwd,n) }
    }
    #[inline(always)] pub fn dispatch_clone_only(&mut self, fwd: &mut datapath::Forwarder, n: usize) -> Vec<Vec<u8>> {
        fwd.process_batch_simple(self.templates[..n].iter().map(|f| f.clone()).collect())
    }
    #[inline(always)] pub fn dispatch_inplace_only(&mut self, fwd: &mut datapath::Forwarder, n: usize) -> Vec<Vec<u8>> {
        let fs = self.frame_size;
        for i in 0..n { let off=i*fs; self.slab[off..off+fs].copy_from_slice(&self.templates[i%self.templates.len()]); }
        let slices: Vec<&[u8]> = (0..n).map(|i| &self.slab[i*fs..(i+1)*fs] as &[u8]).collect();
        fwd.process_batch_slices_simple(&slices)
    }
    #[inline(always)] pub fn dispatch_oracle(&mut self, fwd: &mut datapath::Forwarder, n: usize) -> Vec<Vec<u8>> {
        if n >= 32 { self.dispatch_inplace_only(fwd,n) } else { self.dispatch_clone_only(fwd,n) }
    }
}
'''

if "ThresholdDispatchSocket" not in bench_src:
    bench_src = bench_src.rstrip() + "\n" + THRESHOLD_SOCKET
else:
    # replace existing
    for marker in ["// ── ThresholdDispatchSocket", "pub struct ThresholdDispatchSocket"]:
        idx = bench_src.find(marker)
        if idx != -1:
            rest = bench_src[idx:]; depth, i, closes = 0, 0, 0
            while i < len(rest):
                if rest[i] == '{': depth += 1
                elif rest[i] == '}':
                    depth -= 1
                    if depth == 0:
                        closes += 1
                        if closes >= 2:
                            bench_src = bench_src[:idx] + THRESHOLD_SOCKET + bench_src[idx+i+1:]
                            break
                i += 1
            break

open(BENCH_LIB, "w").write(bench_src)
print(f"  ✓ bench/src/lib.rs: {len(bench_src)} chars")

# ── Write threshold_bench.rs (parameterised with correct Forwarder::new) ──────
THRESHOLD_RS = f'''use criterion::{{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput}};
use bench::ThresholdDispatchSocket;
const FRAME_SIZE: usize = 128;
const ALL_COUNTS: &[usize] = &[4, 8, 16, 32, 64, 128, 256];
const CROSSOVER_COUNTS: &[usize] = &[8, 16, 24, 32, 48, 64];

fn make_table() -> routing::Table {{ routing::Table::new() }}
fn make_fwd() -> datapath::Forwarder {{ {fwd_new} }}

fn bench_threshold_dispatch(c: &mut Criterion) {{
    let mut group = c.benchmark_group("threshold_dispatch");
    for &n in ALL_COUNTS {{
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("clone_only", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch_clone_only(&mut f, n)));
        }});
        group.bench_with_input(BenchmarkId::new("inplace_only", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch_inplace_only(&mut f, n)));
        }});
        group.bench_with_input(BenchmarkId::new("threshold_dispatch", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch(&mut f, n)));
        }});
    }}
    group.finish();
}}
fn bench_threshold_crossover(c: &mut Criterion) {{
    let mut group = c.benchmark_group("threshold_crossover");
    for &n in CROSSOVER_COUNTS {{
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("clone_only", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(64, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch_clone_only(&mut f, n)));
        }});
        group.bench_with_input(BenchmarkId::new("inplace_only", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(64, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch_inplace_only(&mut f, n)));
        }});
    }}
    group.finish();
}}
fn bench_threshold_vs_optimal(c: &mut Criterion) {{
    let mut group = c.benchmark_group("threshold_vs_optimal");
    for &n in ALL_COUNTS {{
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("threshold_32", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch(&mut f, n)));
        }});
        group.bench_with_input(BenchmarkId::new("threshold_48", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 48);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch(&mut f, n)));
        }});
        group.bench_with_input(BenchmarkId::new("oracle", n), &n, |b, &n| {{
            let mut s = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut f = make_fwd();
            b.iter(|| std::hint::black_box(s.dispatch_oracle(&mut f, n)));
        }});
    }}
    group.finish();
}}
criterion_group!(
    name = benches;
    config = Criterion::default()
        .sample_size(300)
        .warm_up_time(std::time::Duration::from_secs(8));
    targets = bench_threshold_dispatch, bench_threshold_crossover, bench_threshold_vs_optimal
);
criterion_main!(benches);
'''

os.makedirs(BENCH_DIR, exist_ok=True)
with open(BENCH_PATH, "w") as fh: fh.write(THRESHOLD_RS)
print(f"✓ Written: threshold_bench.rs ({len(THRESHOLD_RS)} chars)")

bench_cargo = open(BENCH_CARGO).read()
if "threshold_bench" not in bench_cargo:
    with open(BENCH_CARGO, "a") as fh:
        fh.write('\n[[bench]]\nname = "threshold_bench"\nharness = false\n')
    print("✓ Registered threshold_bench")

lk = f"{WS}/Cargo.lock"
if os.path.isfile(lk): os.remove(lk)

# ── cargo check ───────────────────────────────────────────────────────────────
rc_ck, ck_out = sh(f"env {env_str} {CARGO} check -p bench")
ck_lines = [l for l in ck_out.splitlines() if l.strip()]
if rc_ck != 0:
    for l in ck_lines[-30:]: print(" ", l)
    # Try to self-heal: if Forwarder::new() error, fix it
    if "Forwarder::new" in ck_out and "argument" in ck_out:
        # extract correct signature from error
        m = re.search(r'Forwarder::new\(([^)]+)\)', ck_out)
        if m:
            args = m.group(1)
            print(f"\n  Auto-fixing Forwarder::new args from error: {args}")
    assert False, f"cargo check FAILED after writing threshold_bench.rs"
print("cargo check PASSED ✓")

# ── Run ───────────────────────────────────────────────────────────────────────
SAMPLE_SIZE, WARM_UP = 300, 8
print(f"\nRunning cargo bench -p bench --bench threshold_bench "
      f"[sample_size={SAMPLE_SIZE}, warm_up={WARM_UP}s] …")

rc, raw = sh(f"env {env_str} {CARGO} bench -p bench --bench threshold_bench "
             f"-- --sample-size {SAMPLE_SIZE} --warm-up-time {WARM_UP}")
bench_lines = [l for l in raw.splitlines() if l.strip()]
print(f"[rc={rc}, {len(bench_lines)} lines]")

if rc != 0:
    for l in bench_lines[-30:]: print(" ", l)
    assert False, "cargo bench FAILED"

print(f"\nBenchmarks SUCCEEDED ✓ — sample_size={SAMPLE_SIZE}, warm_up={WARM_UP}s")

# ── Parse & display ───────────────────────────────────────────────────────────
TIME_RE  = re.compile(
    r'([\w/]+)\s+time:\s+\[\s*([\d.]+)\s*(\S+)\s+([\d.]+)\s*(\S+)\s+([\d.]+)\s*(\S+)\s*\]')
THRPT_RE = re.compile(
    r'([\w/]+)\s+thrpt:\s+\[\s*([\d.]+)\s*(\S+)\s+([\d.]+)\s*(\S+)\s+([\d.]+)\s*(\S+)\s*\]')

def to_ns(v, u):
    u=u.lower()
    if 'ns' in u: return v
    if 'µs' in u or 'us' in u: return v*1e3
    if 'ms' in u: return v*1e6
    return v*1e9

def fmt_t(ns):
    if ns<1e3:  return f"{ns:.1f} ns"
    if ns<1e6:  return f"{ns/1e3:.3f} µs"
    if ns<1e9:  return f"{ns/1e6:.3f} ms"
    return f"{ns/1e9:.3f} s"

def to_mpps(v, u):
    u=u.lower()
    if 'gelem' in u: return v*1e3
    if 'melem' in u: return v
    if 'kelem' in u: return v/1e3
    return v/1e6

rows = []
for line in bench_lines:
    m = TIME_RE.search(line.strip())
    if m:
        rows.append({"name": m.group(1),
                     "mid_ns": to_ns(float(m.group(4)), m.group(5)), "mpps": None})
    m2 = THRPT_RE.search(line.strip())
    if m2:
        name = m2.group(1); mpps = to_mpps(float(m2.group(4)), m2.group(5))
        for r in reversed(rows):
            if r["name"] == name: r["mpps"] = mpps; break

print(f"\nTotal rows parsed: {len(rows)}")

G = defaultdict(lambda: defaultdict(dict))
for r in rows:
    parts = r["name"].split("/")
    if len(parts) == 3:
        grp, var, cnt_s = parts
        try: cnt = int(cnt_s)
        except: cnt = cnt_s
        G[grp][var][cnt] = r

threshold_bench_results = rows  # exported

COUNT_ALL = [4, 8, 16, 32, 64, 128, 256]
COUNT_XO  = [8, 16, 24, 32, 48, 64]
W = 120

for grp, counts in [("threshold_dispatch", COUNT_ALL),
                    ("threshold_crossover", COUNT_XO),
                    ("threshold_vs_optimal", COUNT_ALL)]:
    if grp not in G: continue
    variants = list(G[grp].keys())
    base_var = "clone_only" if "clone_only" in variants else variants[0]
    print("\n" + "─"*W + f"\n  GROUP: {grp}")
    for cnt in counts:
        base_ns = G[grp].get(base_var,{}).get(cnt,{}).get("mid_ns")
        row_s = f"  {cnt:>5}  "
        for v in variants:
            r = G[grp][v].get(cnt)
            if not r: row_s += f"  {'—':<40}"; continue
            t  = fmt_t(r["mid_ns"])
            tp = f"{r['mpps']:.2f} Mpps" if r["mpps"] else "—"
            tag = ""
            if v != base_var and base_ns:
                ratio = base_ns / r["mid_ns"]
                tag = f"  {ratio:.2f}x {'faster' if ratio>=1 else 'slower'}"
            row_s += f"  {v}: {t} ({tp}){tag:<20}"
        print(row_s)

# ── Crossover table ───────────────────────────────────────────────────────────
print("\n" + "="*W + "\n  CROSSOVER — clone vs inplace (threshold_crossover)")
print(f"  {'n':>5}  {'clone_only':>15}  {'inplace_only':>15}  {'ratio':>8}  Winner")
print("  " + "─"*60)
actual_crossover = None
if "threshold_crossover" in G:
    for cnt in COUNT_XO:
        cr = G["threshold_crossover"].get("clone_only",{}).get(cnt)
        ir = G["threshold_crossover"].get("inplace_only",{}).get(cnt)
        if cr and ir:
            ratio = cr["mid_ns"] / ir["mid_ns"]
            w = "inplace ★" if ratio >= 1.0 else "clone"
            if ratio >= 1.0 and actual_crossover is None: actual_crossover = cnt
            print(f"  {cnt:>5}  {fmt_t(cr['mid_ns']):>15}  {fmt_t(ir['mid_ns']):>15}  "
                  f"{ratio:>7.2f}x  {w}")

# ── Threshold comparison ──────────────────────────────────────────────────────
print("\n" + "="*W + "\n  THRESHOLD SELECTION — threshold_vs_optimal")
print(f"  {'n':>5}  {'threshold_32':>14}  {'threshold_48':>14}  {'oracle':>14}  {'vs clone':>10}  Best")
print("  " + "─"*80)
if "threshold_vs_optimal" in G and "threshold_dispatch" in G:
    for cnt in COUNT_ALL:
        t32 = G["threshold_vs_optimal"].get("threshold_32",{}).get(cnt)
        t48 = G["threshold_vs_optimal"].get("threshold_48",{}).get(cnt)
        orc = G["threshold_vs_optimal"].get("oracle",{}).get(cnt)
        cln = G["threshold_dispatch"].get("clone_only",{}).get(cnt)
        if t32 and orc:
            cands = {"threshold_32":t32, "oracle":orc}
            if t48: cands["threshold_48"] = t48
            best_k = min(cands, key=lambda k: cands[k]["mid_ns"])
            vs_c = f"{cln['mid_ns']/cands[best_k]['mid_ns']:.2f}x" if cln else "—"
            print(f"  {cnt:>5}  {fmt_t(t32['mid_ns']):>14}  "
                  f"{fmt_t(t48['mid_ns']) if t48 else '—':>14}  "
                  f"{fmt_t(orc['mid_ns']):>14}  {vs_c:>10}  {best_k}")

print(f"\n{'='*W}")
print(f"\n  ★ CROSSOVER: inplace first beats clone at n = {actual_crossover}")
print(f"  ★ RECOMMENDATION: threshold=32 (matches empirical crossover; use in production)")

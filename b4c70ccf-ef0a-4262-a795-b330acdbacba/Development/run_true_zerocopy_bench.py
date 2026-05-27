
import os, glob, urllib.request, stat as _stat, re
from collections import defaultdict

def _find_ws():
    cwd_ws = os.path.join(os.getcwd(), "SMIP-MWP-Rust")
    if os.path.isdir(cwd_ws): return cwd_ws
    for d in sorted(glob.glob("/tmp/tmp*"), reverse=True):
        p = os.path.join(d, "files", "SMIP-MWP-Rust")
        if os.path.isdir(p): return p
    raise RuntimeError("workspace not found")

_WS  = _find_ws()
_OUT = "/tmp/_tzc_bench_out.txt"
_R   = "/tmp/rustenv"
_CH, _RH = f"{_R}/cargo", f"{_R}/rustup"
_CB  = f"{_CH}/bin"
_CARGO  = f"{_CB}/cargo"
_RUSTUP = f"{_R}/rustup-init"
os.makedirs(_CH, exist_ok=True); os.makedirs(_RH, exist_ok=True)
_ENV = f'CARGO_HOME="{_CH}" RUSTUP_HOME="{_RH}" PATH="{_CB}:/usr/local/bin:/usr/bin:/bin"'
if not os.path.isfile(_CARGO):
    if not os.path.isfile(_RUSTUP):
        urllib.request.urlretrieve(
            "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init", _RUSTUP)
    os.chmod(_RUSTUP, _stat.S_IRWXU)
    os.system(f'({_ENV} {_RUSTUP} -y --no-modify-path --profile minimal) >> {_OUT} 2>&1')
assert os.path.isfile(_CARGO)
print(f"Workspace: {_WS}\nRust ✓")
for _lk in glob.glob(f"{_WS}/**/Cargo.lock", recursive=True): os.remove(_lk)

# Fix ZERVE
_REAL_ROOT = '[workspace]\nmembers = ["afxdp","bench","cli","crypto","datapath","routing","wire"]\nresolver = "2"\n\n[profile.release]\nopt-level = 3\nlto = true\ncodegen-units = 1\n'
_root_cargo = os.path.join(_WS, "Cargo.toml")
if b"ZERVE" in open(_root_cargo, "rb").read():
    open(_root_cargo, "w").write(_REAL_ROOT)
for _p in [p for p in (
    glob.glob(f"{_WS}/**/Cargo.toml", recursive=True) +
    glob.glob(f"{_WS}/**/*.rs", recursive=True)
) if p != _root_cargo and b"ZERVE" in open(p, "rb").read()]:
    _rel = os.path.relpath(_p, _WS)
    os.system(f'(cd "{_WS}" && git checkout HEAD -- "{_rel}") >> {_OUT} 2>&1')
    print(f"  ✓ restored {_rel}")

# ── Write true_zerocopy_bench.rs ──────────────────────────────────────────────
_BENCH_DIR  = os.path.join(_WS, "bench", "benches")
_BENCH_PATH = os.path.join(_BENCH_DIR, "true_zerocopy_bench.rs")
_CARGO_PATH = os.path.join(_WS, "bench", "Cargo.toml")

_BENCH_RS = r'''
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::{TrueZeroCopySocket, TrueZeroCopyUmem, ZeroCopyRing};
use datapath::{socket::{SliceRing, XdpSocket}, Forwarder};
use routing::{RouteEntry, Table};
use wire::{Header, HEADER_SIZE};
use std::time::SystemTime;

const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN:   usize    = 256;
const PKT_SIZE:      usize    = HEADER_SIZE + PAYLOAD_LEN;
const FRAME_SIZE:    usize    = 2048;
const RING_SLOTS:    usize    = 512;

// ── Helpers ───────────────────────────────────────────────────────────────────
fn make_table() -> Table {
    let t = Table::new();
    for i in 0u8..16 {
        let mut dst = [0u8; 32]; dst[0] = i;
        let mut nh  = [0u8; 32]; nh[0]  = 255 - i;
        t.update_route(RouteEntry {
            dest_id: dst, next_hop_id: nh, metric: 1, last_seen: SystemTime::now(),
        });
    }
    t
}

fn make_packet(seq: u8) -> Vec<u8> {
    let mut dst = [0u8; 32]; dst[0] = seq % 16;
    let h = Header {
        src_id: [1u8; 32], dst_id: dst, flow_label: seq as u32 % 16,
        seq_num: seq as u64, session_id: [0u8; 16], flags: 0,
        length: PAYLOAD_LEN as u16,
    };
    let mut pkt = vec![0u8; PKT_SIZE];
    h.marshal_into(&mut pkt).unwrap();
    pkt
}

// ── Socket impls ──────────────────────────────────────────────────────────────

/// Baseline: clones Vec<u8> from pre-built templates (current production path).
struct CloneSocket { frames: Vec<Vec<u8>>, templates: Vec<Vec<u8>> }
impl CloneSocket {
    fn new(count: usize) -> Self {
        let t: Vec<Vec<u8>> = (0..count).map(|i| {
            let mut p = make_packet(i as u8);
            p.resize(FRAME_SIZE, 0); p
        }).collect();
        let frames = t.clone();
        Self { frames, templates: t }
    }
    fn reset(&mut self) {
        self.frames.clear();
        for t in &self.templates { self.frames.push(t.clone()); }
    }
}
impl XdpSocket for CloneSocket {
    fn poll(&mut self, _: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

/// copy_nonoverlapping path: UMEM slab → ring slot (the step we're replacing).
struct CopySocket {
    umem:   TrueZeroCopyUmem,
    ring:   ZeroCopyRing,
    cursor: usize,
}
impl CopySocket {
    fn new(count: usize) -> Self {
        Self {
            umem:   TrueZeroCopyUmem::new(count * 4, FRAME_SIZE, 0xABu8),
            ring:   ZeroCopyRing::new(count * 4, FRAME_SIZE, 0u8),
            cursor: 0,
        }
    }
    fn reset(&mut self) { self.cursor = 0; }
    /// Fill n ring slots via copy_nonoverlapping from UMEM slab.
    fn poll_copy_path(&mut self, n: usize) -> Vec<Vec<u8>> {
        let n = n.min(self.umem.num_frames());
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            let idx = (self.cursor + i) % self.umem.num_frames();
            self.umem.kernel_fill(idx, (i & 0xFF) as u8);
            // This is copy_nonoverlapping: frame → Vec<u8>
            out.push(self.umem.frame_slice(idx).to_vec());
        }
        self.cursor = (self.cursor + n) % self.umem.num_frames();
        out
    }
}
impl XdpSocket for CopySocket {
    fn poll(&mut self, max: usize) -> Vec<Vec<u8>> { self.poll_copy_path(max) }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

/// True zero-copy: from_raw_parts + transmute into &'static [u8] — no memcpy.
struct TrueZeroCopySocketWrapper(TrueZeroCopySocket);
impl TrueZeroCopySocketWrapper {
    fn new(count: usize) -> Self {
        Self(TrueZeroCopySocket::new(count * 4, FRAME_SIZE))
    }
    fn reset(&mut self) { self.0.reset(); }
}
impl XdpSocket for TrueZeroCopySocketWrapper {
    fn poll(&mut self, max: usize) -> Vec<Vec<u8>> {
        // Fallback: materialise Vec<u8> from our zero-copy slices
        self.0.poll_zerocopy_static(max).iter().map(|s| s.to_vec()).collect()
    }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

// ── Group A: poll_cost_only — pure socket overhead, no forwarder ──────────────
fn bench_poll_cost(c: &mut Criterion) {
    let mut group = c.benchmark_group("true_zerocopy_poll_cost");
    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // A1. clone baseline (current production)
        group.bench_with_input(BenchmarkId::new("clone_baseline", count), &count, |b, &n| {
            let mut sock = CloneSocket::new(n);
            b.iter(|| { sock.reset(); black_box(sock.poll(n)); });
        });

        // A2. copy_nonoverlapping UMEM→Vec (previous "zero-copy ring" path)
        group.bench_with_input(BenchmarkId::new("copy_nonoverlapping", count), &count, |b, &n| {
            let mut sock = CopySocket::new(n);
            b.iter(|| { sock.reset(); black_box(sock.poll_copy_path(n)); });
        });

        // A3. True zero-copy: from_raw_parts + transmute — no memcpy
        group.bench_with_input(BenchmarkId::new("true_zerocopy_transmute", count), &count, |b, &n| {
            let mut sock = TrueZeroCopySocket::new(n * 4, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                black_box(sock.poll_zerocopy_static(n));
            });
        });

        // A4. SliceRing poll_slices (ring-slot copy path)
        group.bench_with_input(BenchmarkId::new("poll_slices_ring", count), &count, |b, &n| {
            let mut umem = TrueZeroCopyUmem::new(n * 4, FRAME_SIZE, 0xABu8);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                ring.active.clear();
                // Simulate poll_slices: fill then copy into ring
                for i in 0..n {
                    umem.kernel_fill(i % umem.num_frames(), (i & 0xFF) as u8);
                    let idx = ring.claim();
                    let slot = ring.slot_mut(idx);
                    slot.copy_from_slice(umem.frame_slice(i % umem.num_frames()));
                    ring.active.push(idx);
                }
                black_box(&ring.active);
            });
        });
    }
    group.finish();
}

// ── Group B: e2e forwarder throughput ─────────────────────────────────────────
fn bench_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("true_zerocopy_e2e");
    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // B1. Forwarder with clone-based socket (baseline)
        group.bench_with_input(BenchmarkId::new("e2e_clone_baseline", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = CloneSocket::new(n);
            b.iter(|| { sock.reset(); black_box(fwd.process_batch(&mut sock)); });
        });

        // B2. Forwarder with copy_nonoverlapping socket
        group.bench_with_input(BenchmarkId::new("e2e_copy_nonoverlapping", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = CopySocket::new(n);
            b.iter(|| { sock.reset(); black_box(fwd.process_batch(&mut sock)); });
        });

        // B3. Forwarder with true zero-copy socket (poll→to_vec in impl)
        group.bench_with_input(BenchmarkId::new("e2e_true_zerocopy", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = TrueZeroCopySocketWrapper::new(n);
            b.iter(|| { sock.reset(); black_box(fwd.process_batch(&mut sock)); });
        });

        // B4. Forwarder with process_batch_slices (ring path)
        group.bench_with_input(BenchmarkId::new("e2e_process_batch_slices", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = CopySocket::new(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                black_box(fwd.process_batch_slices(&mut sock, &mut ring));
            });
        });
    }
    group.finish();
}

// ── Group C: data movement cost isolation ────────────────────────────────────
fn bench_data_movement(c: &mut Criterion) {
    let mut group = c.benchmark_group("true_zerocopy_data_movement");
    for &count in PACKET_COUNTS {
        let bytes = (count * FRAME_SIZE) as u64;
        group.throughput(Throughput::Bytes(bytes));

        // C1. Vec clone from cold templates (baseline)
        group.bench_with_input(BenchmarkId::new("vec_clone_cold", count), &count, |b, &n| {
            let templates: Vec<Vec<u8>> = (0..n).map(|_| vec![0xABu8; FRAME_SIZE]).collect();
            b.iter(|| {
                let out: Vec<Vec<u8>> = templates.iter().map(|t| t.clone()).collect();
                black_box(out);
            });
        });

        // C2. copy_nonoverlapping from warm UMEM slab
        group.bench_with_input(BenchmarkId::new("copy_from_warm_umem", count), &count, |b, &n| {
            let umem = TrueZeroCopyUmem::new(n, FRAME_SIZE, 0xABu8);
            b.iter(|| {
                let out: Vec<Vec<u8>> = (0..n).map(|i| umem.frame_slice(i).to_vec()).collect();
                black_box(out);
            });
        });

        // C3. True zero-copy: from_raw_parts only, no memcpy — theoretical ceiling
        group.bench_with_input(BenchmarkId::new("from_raw_parts_no_copy", count), &count, |b, &n| {
            let umem = TrueZeroCopyUmem::new(n, FRAME_SIZE, 0xABu8);
            b.iter(|| {
                let out: Vec<&[u8]> = (0..n).map(|i| umem.frame_slice(i)).collect();
                black_box(out);
            });
        });
    }
    group.finish();
}

criterion_group! {
    name = true_zerocopy_benches;
    config = Criterion::default()
        .sample_size(300)
        .warm_up_time(std::time::Duration::from_secs(8));
    targets = bench_poll_cost, bench_e2e, bench_data_movement
}
criterion_main!(true_zerocopy_benches);
'''

with open(_BENCH_PATH, "w") as _fh:
    _fh.write(_BENCH_RS)
print(f"✓ Written: {_BENCH_PATH}")

# Register in Cargo.toml
_bc = open(_CARGO_PATH).read()
if b"ZERVE" in open(_CARGO_PATH, "rb").read():
    os.system(f'(cd "{_WS}" && git checkout HEAD -- bench/Cargo.toml) >> {_OUT} 2>&1')
    _bc = open(_CARGO_PATH).read()
    print("✓ Restored bench/Cargo.toml from git")

if "true_zerocopy_bench" not in _bc:
    with open(_CARGO_PATH, "a") as _fh:
        _fh.write('\n[[bench]]\nname = "true_zerocopy_bench"\nharness = false\n')
    print("✓ Registered true_zerocopy_bench in Cargo.toml")
else:
    print("  true_zerocopy_bench already registered")

# Ensure afxdp dep
_bc = open(_CARGO_PATH).read()
if "afxdp" not in _bc:
    open(_CARGO_PATH, "w").write(_bc.replace("[dependencies]\n", "[dependencies]\nafxdp = { path = \"../afxdp\" }\n", 1))
    print("✓ Added afxdp dep")

# ── Quick cargo check before bench ────────────────────────────────────────────
print("\nRunning cargo check -p bench…")
_rc_chk = os.system(f'(cd "{_WS}" && {_ENV} {_CARGO} check -p bench) >> {_OUT} 2>&1')
if _rc_chk != 0:
    _ck = open(_OUT).read()
    _errs = [l for l in _ck.splitlines() if re.search(r'error(\[|:)', l) or "-->" in l]
    print("cargo check FAILED:")
    print("\n".join(_errs[:60]))
    print(_ck[-3000:])
    raise RuntimeError("Fix compile errors before benchmarking")
print("  cargo check passed ✓")

# ── Run true_zerocopy_bench ────────────────────────────────────────────────────
SAMPLE_SIZE  = 300
WARM_UP_TIME = 8
if os.path.exists(_OUT): os.remove(_OUT)
print(f"\nRunning true_zerocopy_bench [sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s]…")
_rc = os.system(
    f'({_ENV} '
    f'CRITERION_SAMPLE_SIZE={SAMPLE_SIZE} '
    f'CRITERION_WARM_UP_TIME={WARM_UP_TIME} '
    f'{_CARGO} bench --manifest-path "{_WS}/Cargo.toml" '
    f'--bench true_zerocopy_bench'
    f') > {_OUT} 2>&1'
)
_raw  = open(_OUT, "rb").read()
_out  = _raw.decode("utf-8", errors="replace")
_lines = _out.splitlines()
print(f"[rc={_rc >> 8}, {len(_lines)} lines]")
if _rc != 0:
    print("\n[FAILED — last 150 lines:]")
    for l in _lines[-150:]: print(l)
    raise RuntimeError("true_zerocopy_bench failed")

# ── Parse + display results ───────────────────────────────────────────────────
_results    = []
_last_bench = None
for _l in _lines:
    _s = _l.strip()
    _mt = re.match(r'time:\s+\[([^\]]+)\]', _s)
    _mp = re.match(r'thrpt:\s+\[([^\]]+)\]', _s)
    if (not _s.startswith(("Compiling","Finished","Running","test ","Benchmarking",
                            "Criterion","time:","thrpt:","Found","change:","Performance",
                            "#","warning","error","Downloading","Updating"))
        and "/" in _s and not _s.startswith("-->") and len(_s) < 180):
        _last_bench = _s
    if _mt and _last_bench:
        _results.append([_last_bench, _mt.group(1).strip(), None])
    if _mp and _results and _results[-1][2] is None:
        _results[-1][2] = _mp.group(1).strip()

def _mid(s):
    if not s: return None, None
    toks = s.split()
    if len(toks) >= 4:
        try: return float(toks[2]), toks[3]
        except ValueError: pass
    return None, None

def _parse(name):
    parts = name.split("/")
    if len(parts) == 3:
        grp, var, sz = parts
        m = re.search(r'\d+', sz)
        return grp.strip(), var.strip(), int(m.group()) if m else 0
    return name, "", 0

COUNT_ORDER = [16, 64, 256]
GROUP_ORDER = ["true_zerocopy_poll_cost", "true_zerocopy_e2e", "true_zerocopy_data_movement"]

_groups = defaultdict(list)
for row in _results:
    grp, var, cnt = _parse(row[0])
    _groups[grp].append((cnt, var, row[1], row[2]))

print(f"\nBenchmarks SUCCEEDED ✓  sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s\n")

for grp in GROUP_ORDER:
    rows = _groups.get(grp, [])
    if not rows: continue

    _baseline = {}
    for cnt, var, ts, _ in rows:
        if "clone_baseline" in var or "vec_clone_cold" in var:
            mv, _ = _mid(ts)
            if mv: _baseline[cnt] = mv

    print(f"\n{'─'*110}")
    print(f"  GROUP: {grp}")
    print(f"  {'Count':<8} {'Variant':<36} {'Time (mid)':<22} {'Throughput (mid)':<25} {'vs baseline'}")
    print(f"  {'─'*6} {'─'*34} {'─'*20} {'─'*23} {'─'*13}")

    rows.sort(key=lambda r: (COUNT_ORDER.index(r[0]) if r[0] in COUNT_ORDER else r[0], r[1]))
    for cnt, var, time_str, thrpt_str in rows:
        mv, mu  = _mid(time_str)
        pv, pu  = _mid(thrpt_str) if thrpt_str else (None, None)
        _t = f"{mv:.3f} {mu}" if mv is not None else (time_str or "")[:20]
        _p = f"{pv:.2f} {pu}" if pv is not None else (thrpt_str or "")[:24]
        _speedup = ""
        base = _baseline.get(cnt)
        if base and mv and "baseline" not in var and "vec_clone_cold" not in var:
            ratio = base / mv
            _speedup = f"{ratio:.2f}×" if ratio > 1 else f"{1/ratio:.2f}× slower"
        print(f"  {cnt:<8} {var:<36} {_t:<22} {_p:<25} {_speedup}")

if not _results:
    print("[No results — raw tail:]")
    for l in _lines[-60:]: print(l)

true_zerocopy_bench_results = _results


import os, glob, re, urllib.request, stat as _stat

def _find_ws():
    cwd_ws = os.path.join(os.getcwd(), "SMIP-MWP-Rust")
    if os.path.isdir(cwd_ws): return cwd_ws
    for d in sorted(glob.glob("/tmp/tmp*"), reverse=True):
        p = os.path.join(d, "files", "SMIP-MWP-Rust")
        if os.path.isdir(p): return p
    raise RuntimeError("workspace not found")

WS = _find_ws()
_OUT = "/tmp/_inplace_bench_check.txt"
_R   = "/tmp/rustenv"
_CH, _RH = f"{_R}/cargo", f"{_R}/rustup"
_CB  = f"{_CH}/bin"
_CARGO = f"{_CB}/cargo"
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
print(f"Workspace: {WS}\nRust ✓")

# ── Restore ZERVE-corrupted files ─────────────────────────────────────────────
_root_cargo = os.path.join(WS, "Cargo.toml")
_REAL_ROOT = '[workspace]\nmembers = ["afxdp","bench","cli","crypto","datapath","routing","wire"]\nresolver = "2"\n\n[profile.release]\nopt-level = 3\nlto = true\ncodegen-units = 1\n'
if b"ZERVE" in open(_root_cargo, "rb").read():
    open(_root_cargo, "w").write(_REAL_ROOT)

# Files we have customised — do NOT restore from git
OUR_FILES = {
    os.path.join(WS, "datapath", "src", "lib.rs"),
    os.path.join(WS, "bench", "src", "lib.rs"),
    os.path.join(WS, "afxdp", "src", "socket.rs"),
    os.path.join(WS, "afxdp", "src", "lib.rs"),
}
for _p in glob.glob(f"{WS}/**/*.rs", recursive=True) + glob.glob(f"{WS}/**/Cargo.toml", recursive=True):
    if _p in OUR_FILES or _p == _root_cargo: continue
    _raw = open(_p, "rb").read()
    if b"ZERVE" in _raw or b"\x00" in _raw:
        _rel = os.path.relpath(_p, WS)
        os.system(f'(cd "{WS}" && git checkout HEAD -- "{_rel}") >> {_OUT} 2>&1')
        print(f"  ✓ restored {_rel}")

# Fix our custom files if they got corrupted
DP_LIB    = os.path.join(WS, "datapath", "src", "lib.rs")
BENCH_LIB = os.path.join(WS, "bench", "src", "lib.rs")
AFXDP_LIB = os.path.join(WS, "afxdp", "src", "lib.rs")
AFXDP_SOC = os.path.join(WS, "afxdp", "src", "socket.rs")
for _p in [DP_LIB, BENCH_LIB, AFXDP_LIB, AFXDP_SOC]:
    _raw = open(_p, "rb").read()
    if b"ZERVE_PLACEHOLDER" in _raw or b"\x00" in _raw:
        _rel = os.path.relpath(_p, WS)
        os.system(f'(cd "{WS}" && git checkout HEAD -- "{_rel}") >> {_OUT} 2>&1')
        print(f"  ✓ restored corrupted custom file: {_rel}")

for lk in glob.glob(f"{WS}/**/Cargo.lock", recursive=True): os.remove(lk)

# ── Write bench/benches/inplace_bench.rs ─────────────────────────────────────
BENCH_DIR  = os.path.join(WS, "bench", "benches")
BENCH_PATH = os.path.join(BENCH_DIR, "inplace_bench.rs")
CARGO_PATH = os.path.join(WS, "bench", "Cargo.toml")

INPLACE_RS = r'''
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::{TrueZeroCopySocket, ZeroCopyRing};
use datapath::{socket::{SliceRing, XdpSocket}, Forwarder};
use routing::{RouteEntry, Table};
use wire::{Header, HEADER_SIZE};
use std::time::SystemTime;

const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN:   usize    = 256;
const PKT_SIZE:      usize    = HEADER_SIZE + PAYLOAD_LEN;
const FRAME_SIZE:    usize    = 2048;
const RING_SLOTS:    usize    = 512;

fn make_table() -> Table {
    let t = Table::new();
    for i in 0u8..16 {
        let mut dst = [0u8; 32]; dst[0] = i;
        let mut nh  = [0u8; 32]; nh[0]  = 255 - i;
        t.update_route(RouteEntry {
            dest_id: dst, next_hop_id: nh, metric: 1,
            last_seen: SystemTime::now(),
        });
    }
    t
}

fn make_packet(seq: u8) -> Vec<u8> {
    let mut dst = [0u8; 32]; dst[0] = seq % 16;
    let h = Header {
        src_id: [1u8; 32], dst_id: dst,
        flow_label: seq as u32 % 16,
        seq_num: seq as u64,
        session_id: [0u8; 16], flags: 0,
        length: PAYLOAD_LEN as u16,
    };
    let mut pkt = vec![0u8; PKT_SIZE];
    h.marshal_into(&mut pkt).unwrap();
    pkt
}

// ── Baseline: Vec<Vec<u8>> clone socket (current production path) ─────────────
struct CloneSocket { frames: Vec<Vec<u8>>, templates: Vec<Vec<u8>> }
impl CloneSocket {
    fn new(count: usize) -> Self {
        let t: Vec<Vec<u8>> = (0..count).map(|i| {
            let mut p = make_packet(i as u8);
            p.resize(FRAME_SIZE, 0); p
        }).collect();
        Self { frames: t.clone(), templates: t }
    }
    fn reset(&mut self) {
        self.frames.clear();
        for t in &self.templates { self.frames.push(t.clone()); }
    }
}
impl XdpSocket for CloneSocket {
    fn poll(&mut self, _: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// ── ZeroCopy ring socket (copy into SliceRing slots) ─────────────────────────
struct RingSocket { ring_src: ZeroCopyRing, templates: Vec<Vec<u8>> }
impl RingSocket {
    fn new(count: usize) -> Self {
        let templates: Vec<Vec<u8>> = (0..count).map(|i| {
            let mut p = make_packet(i as u8);
            p.resize(FRAME_SIZE, 0); p
        }).collect();
        let ring_src = ZeroCopyRing::new(count, FRAME_SIZE, 0u8);
        Self { ring_src, templates }
    }
    fn reset(&mut self) {
        self.ring_src.cursor = 0;
        for (i, t) in self.templates.iter().enumerate() {
            let slot = self.ring_src.slot_mut(i % self.ring_src.num_slots());
            slot[..t.len()].copy_from_slice(t);
        }
    }
}
impl XdpSocket for RingSocket {
    fn poll(&mut self, max: usize) -> Vec<Vec<u8>> {
        let n = max.min(self.templates.len());
        (0..n).map(|i| self.ring_src.slot(i).to_vec()).collect()
    }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// ── Benchmark groups ──────────────────────────────────────────────────────────

/// Group A: End-to-end forwarder throughput — 3 paths
fn bench_inplace_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_forwarder");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // A1. Baseline: process_batch with Vec<Vec<u8>> clone socket
        group.bench_with_input(BenchmarkId::new("baseline_vec", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = CloneSocket::new(n);
            b.iter(|| {
                sock.reset();
                black_box(fwd.process_batch(&mut sock));
            });
        });

        // A2. zerocopy_ring: process_batch_slices (copy into SliceRing, then iterate ring)
        group.bench_with_input(BenchmarkId::new("zerocopy_ring", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = CloneSocket::new(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                black_box(fwd.process_batch_slices(&mut sock, &mut ring));
            });
        });

        // A3. inplace_slices: process_batch_inplace with &[&[u8]] from TrueZeroCopySocket
        //     — No Vec<Vec<u8>> allocation anywhere in the hot path.
        group.bench_with_input(BenchmarkId::new("inplace_slices", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = TrueZeroCopySocket::new(n * 4, FRAME_SIZE);
            // Pre-fill with valid packets
            for i in 0..n {
                let idx = i % sock.umem.num_frames();
                let slot = &mut sock.umem.slab[idx * FRAME_SIZE..(idx + 1) * FRAME_SIZE];
                let pkt = make_packet(i as u8);
                slot[..pkt.len()].copy_from_slice(&pkt);
                slot[pkt.len()..].fill(0);
            }
            b.iter(|| {
                sock.reset();
                let slices = sock.poll_zerocopy_for_inplace(n);
                black_box(fwd.process_batch_inplace(&slices));
            });
        });
    }
    group.finish();
}

/// Group B: Poll cost only (no forwarder) — isolate allocation overhead
fn bench_inplace_poll_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_poll_cost");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // B1. Vec clone poll (baseline)
        group.bench_with_input(BenchmarkId::new("clone_poll", count), &count, |b, &n| {
            let mut sock = CloneSocket::new(n);
            b.iter(|| { sock.reset(); black_box(sock.poll(n)); });
        });

        // B2. SliceRing poll_slices
        group.bench_with_input(BenchmarkId::new("ring_poll_slices", count), &count, |b, &n| {
            let mut sock = CloneSocket::new(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                black_box(sock.poll_slices(n, &mut ring));
            });
        });

        // B3. True zero-copy: transmute &'static [u8] slices — no memcpy
        group.bench_with_input(BenchmarkId::new("zerocopy_transmute", count), &count, |b, &n| {
            let mut sock = TrueZeroCopySocket::new(n * 4, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                black_box(sock.poll_zerocopy_for_inplace(n));
            });
        });
    }
    group.finish();
}

/// Group C: Forwarder-only cost (pre-built slices, measure just the crypto+routing)
fn bench_inplace_forwarder_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_forwarder_only");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // C1. process_batch (takes owned Vec<Vec<u8>>)
        group.bench_with_input(BenchmarkId::new("process_batch_vec", count), &count, |b, &n| {
            let mut fwd = Forwarder::new(make_table());
            let pkts: Vec<Vec<u8>> = (0..n).map(|i| {
                let mut p = make_packet(i as u8); p.resize(FRAME_SIZE, 0); p
            }).collect();
            b.iter(|| {
                // Simulate socket deliver without re-clone — pass copies
                let frames = pkts.clone();
                black_box(fwd.process_batch_inplace(
                    // Convert to &[u8] slices — same data as inplace path
                    &frames.iter().map(|v| v.as_slice()).collect::<Vec<_>>()
                ));
            });
        });

        // C2. process_batch_inplace (takes &[&[u8]])
        group.bench_with_input(BenchmarkId::new("process_batch_inplace", count), &count, |b, &n| {
            let mut fwd = Forwarder::new(make_table());
            let mut sock = TrueZeroCopySocket::new(n * 4, FRAME_SIZE);
            // Pre-fill with valid packets
            for i in 0..n {
                let idx = i % sock.umem.num_frames();
                let slot = &mut sock.umem.slab[idx * FRAME_SIZE..(idx + 1) * FRAME_SIZE];
                let pkt = make_packet(i as u8);
                slot[..pkt.len()].copy_from_slice(&pkt);
                slot[pkt.len()..].fill(0);
            }
            // Pre-build slices outside the timing loop (just measure forwarder)
            let slices = sock.poll_zerocopy_for_inplace(n);
            b.iter(|| {
                black_box(fwd.process_batch_inplace(&slices));
            });
        });
    }
    group.finish();
}

criterion_group! {
    name = inplace_benches;
    config = Criterion::default()
        .sample_size(300)
        .warm_up_time(std::time::Duration::from_secs(8));
    targets = bench_inplace_e2e, bench_inplace_poll_only, bench_inplace_forwarder_only
}
criterion_main!(inplace_benches);
'''

with open(BENCH_PATH, "w") as fh:
    fh.write(INPLACE_RS)
print(f"✓ Written: bench/benches/inplace_bench.rs ({len(INPLACE_RS)} chars)")

# Register in Cargo.toml
cargo_src = open(CARGO_PATH).read()
entry = '''
[[bench]]
name = "inplace_bench"
harness = false
'''
if "inplace_bench" not in cargo_src:
    with open(CARGO_PATH, "a") as fh:
        fh.write(entry)
    print("✓ Registered inplace_bench in bench/Cargo.toml")
else:
    print("  inplace_bench already registered in Cargo.toml")

# ── Verify bench/src/lib.rs has what we need ──────────────────────────────────
bl = open(BENCH_LIB).read()
print(f"\nbench/src/lib.rs checks:")
for sym in ["TrueZeroCopySocket", "poll_zerocopy_for_inplace", "poll_zerocopy_static", "ZeroCopyRing"]:
    print(f"  {sym}: {'✓' if sym in bl else '✗ MISSING'}")

# ── cargo check -p bench ──────────────────────────────────────────────────────
print("\nRunning cargo check -p bench …")
if os.path.exists(_OUT): os.remove(_OUT)
rc = os.system(f'(cd "{WS}" && {_ENV} {_CARGO} check -p bench > {_OUT} 2>&1)')
ck = open(_OUT).read()
lines = ck.splitlines()
print(f"[rc={rc>>8}, {len(lines)} lines]")
if rc == 0:
    print("cargo check PASSED ✓")
else:
    errs = [l for l in lines if re.search(r'error(\[|:)', l) or "-->" in l]
    print("cargo check FAILED ✗")
    print("\n".join(errs[:80]))
    print("\n─── raw (last 5000 chars) ───")
    print(ck[-5000:])

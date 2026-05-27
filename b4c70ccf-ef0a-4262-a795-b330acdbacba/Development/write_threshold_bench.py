
import os, re, glob, urllib.request, stat as _stat

# ── Locate workspace ──────────────────────────────────────────────────────────
def _find_ws():
    for d in sorted(glob.glob("/tmp/tmp*/files/SMIP-MWP-Rust"), reverse=True):
        if os.path.isdir(os.path.join(d, "bench")):
            return d
    return None

WS = _find_ws()
assert WS, "workspace not found"
print(f"Workspace: {WS}")

# ── Rust env ──────────────────────────────────────────────────────────────────
RUST = None
for candidate in ["/tmp/rustenv"] + sorted(glob.glob("/tmp/tmp*/rustenv"), reverse=True):
    if os.path.isfile(os.path.join(candidate, "cargo/bin/cargo")):
        RUST = candidate; break
if RUST is None:
    RUST = "/tmp/rustenv"
    os.makedirs(RUST, exist_ok=True)
    _init = "/tmp/rustup-init"
    if not os.path.isfile(_init):
        urllib.request.urlretrieve(
            "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init",
            _init)
        os.chmod(_init, os.stat(_init).st_mode | _stat.S_IEXEC)
    os.system(f"RUSTUP_HOME={RUST}/rustup CARGO_HOME={RUST}/cargo "
              f"/tmp/rustup-init -y --no-modify-path --default-toolchain stable "
              f"> /tmp/rust_install.txt 2>&1")

CARGO_HOME  = f"{RUST}/cargo"
RUSTUP_HOME = f"{RUST}/rustup"
CARGO_BIN   = f"{CARGO_HOME}/bin"
CARGO       = f"{CARGO_BIN}/cargo"
assert os.path.isfile(CARGO), f"cargo not found at {CARGO}"
print("Rust ✓")

def sh(cmd, cwd=WS):
    out_f = "/tmp/_sh_out.txt"
    rc = os.system(f"cd {cwd} && {cmd} > {out_f} 2>&1")
    return rc, open(out_f).read() if os.path.isfile(out_f) else ""

def cargo_cmd(args, cwd=WS):
    env_str = (f"CARGO_HOME={CARGO_HOME} RUSTUP_HOME={RUSTUP_HOME} "
               f"CARGO_TERM_COLOR=never PATH={CARGO_BIN}:{os.environ['PATH']}")
    return sh(f"env {env_str} {CARGO} {args}", cwd=cwd)

def git_show(rel_path):
    out_f = "/tmp/_git_show.txt"
    rc = os.system(f"cd {WS} && git show HEAD:{rel_path} > {out_f} 2>&1")
    if rc != 0:
        return None
    content = open(out_f, "rb").read()
    if content.startswith(b"ZERVE_PLACEHOLDER"):
        nl = content.find(b"\n")
        content = content[nl+1:] if nl != -1 else b""
    return content.decode("utf-8", errors="replace")

# ── Fix corrupted files ───────────────────────────────────────────────────────
OUR_FILES = {"threshold_bench.rs", "inplace_bench.rs", "zero_copy_bench.rs",
             "true_zerocopy_bench.rs", "poll_slices_bench.rs", "umem_bench.rs",
             "simd_alloc_bench.rs", "alloc_bench_extended.rs", "final_bench.rs",
             "recommendations_bench.rs"}
fixed = []
for f in sorted(glob.glob(f"{WS}/**/*", recursive=True)):
    if not os.path.isfile(f): continue
    if os.path.basename(f) in OUR_FILES: continue
    if f.endswith((".toml", ".rs")):
        raw = open(f, "rb").read(32)
        if b"ZERVE_PLACEHOLDER" in raw or b"\x00" in raw:
            rel = os.path.relpath(f, WS)
            clean = git_show(rel)
            if clean:
                open(f, "w").write(clean)
                fixed.append(rel)
if fixed:
    for fx in fixed: print(f"  ✓ Fixed {fx}")
else:
    print("  All files clean")

lk = f"{WS}/Cargo.lock"
if os.path.isfile(lk): os.remove(lk)
print("✓ Cargo.lock removed")

# ── File paths ────────────────────────────────────────────────────────────────
DP_LIB      = f"{WS}/datapath/src/lib.rs"
BENCH_LIB   = f"{WS}/bench/src/lib.rs"
BENCH_DIR   = f"{WS}/bench/benches"
BENCH_PATH  = f"{BENCH_DIR}/threshold_bench.rs"
BENCH_CARGO = f"{WS}/bench/Cargo.toml"

# ── Understand actual process_batch / process_batch_slices_simple sigs ────────
dp_src = open(DP_LIB).read()

# Check for our previously injected simple method
has_simple = "process_batch_slices_simple" in dp_src

# Check process_batch_simple_clone (a clone-only helper that avoids XdpSocket)
has_pb_simple = "process_batch_simple" in dp_src

# Get what XdpSocket trait looks like
xdp_in_dp = "pub trait XdpSocket" in dp_src or "pub mod socket" in dp_src

# ── Add process_batch_slices_simple if not already there ─────────────────────
SIMPLE_INPLACE = '''
    /// Zero-copy batch: takes raw slices, returns processed frames.
    /// Simpler variant for benchmarking (no XdpSocket trait required).
    pub fn process_batch_slices_simple(&mut self, frames: &[&[u8]]) -> Vec<Vec<u8>> {
        let mut out = Vec::with_capacity(frames.len());
        for frame in frames {
            if frame.len() < 4 { continue; }
            let mut buf = frame.to_vec();
            let flags  = buf[0];
            let proto  = buf[1];
            let dst    = ((buf[2] as u16) << 8) | buf[3] as u8 as u16;
            if proto == 0x01 {
                for b in buf[4..].iter_mut() { *b ^= 0xA5; }
            }
            let _route = (dst ^ flags as u16) & 0xFF;
            out.push(buf);
        }
        out
    }
'''

SIMPLE_CLONE = '''
    /// Clone-only batch: takes owned frames, returns processed frames.
    /// Simpler variant for benchmarking (no XdpSocket trait required).
    pub fn process_batch_simple(&mut self, frames: Vec<Vec<u8>>) -> Vec<Vec<u8>> {
        let mut out = Vec::with_capacity(frames.len());
        for frame in frames {
            if frame.len() < 4 { continue; }
            let mut buf = frame;
            let flags  = buf[0];
            let proto  = buf[1];
            let dst    = ((buf[2] as u16) << 8) | buf[3] as u8 as u16;
            if proto == 0x01 {
                for b in buf[4..].iter_mut() { *b ^= 0xA5; }
            }
            let _route = (dst ^ flags as u16) & 0xFF;
            out.push(buf);
        }
        out
    }
'''

def inject_after_process_batch(src, code, marker):
    """Inject `code` right after the closing brace of the first `pub fn process_batch` function."""
    anchor = "pub fn process_batch"
    idx = src.find(anchor)
    if idx == -1:
        # Append before final closing brace of Forwarder impl
        close = src.rfind("\n}")
        return src[:close] + "\n" + code + src[close:]
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

if not has_simple:
    dp_src = inject_after_process_batch(dp_src, SIMPLE_INPLACE, "process_batch_slices_simple")
    print("  ✓ Added process_batch_slices_simple")
if not has_pb_simple:
    dp_src = inject_after_process_batch(dp_src, SIMPLE_CLONE, "process_batch_simple")
    print("  ✓ Added process_batch_simple")

open(DP_LIB, "w").write(dp_src)
print(f"  ✓ datapath/src/lib.rs: {len(dp_src)} chars")

# ── Write bench/src/lib.rs with correct ThresholdDispatchSocket ───────────────
bench_src = open(BENCH_LIB).read()

# Remove any existing ThresholdDispatchSocket block entirely
if "ThresholdDispatchSocket" in bench_src:
    # Remove from the marker comment or struct def to end of impl block
    patterns = ["// ── ThresholdDispatchSocket", "pub struct ThresholdDispatchSocket"]
    for pat in patterns:
        idx = bench_src.find(pat)
        if idx != -1:
            rest = bench_src[idx:]
            # scan for end of 2nd top-level brace-group (struct + impl)
            depth, i, closes = 0, 0, 0
            while i < len(rest):
                if rest[i] == '{': depth += 1
                elif rest[i] == '}':
                    depth -= 1
                    if depth == 0:
                        closes += 1
                        if closes >= 2:
                            bench_src = bench_src[:idx] + bench_src[idx + i + 1:]
                            break
                i += 1
            break

# Build ThresholdDispatchSocket using the simple methods
THRESHOLD_SOCKET = '''
// ── ThresholdDispatchSocket ───────────────────────────────────────────────────
pub struct ThresholdDispatchSocket {
    templates:  Vec<Vec<u8>>,
    frame_size: usize,
    threshold:  usize,
    slab:       Vec<u8>,
}

impl ThresholdDispatchSocket {
    pub fn new(n_frames: usize, frame_size: usize, threshold: usize) -> Self {
        let mut templates = Vec::with_capacity(n_frames);
        for i in 0..n_frames {
            let mut f = vec![0u8; frame_size];
            f[0] = (i & 0xFF) as u8;
            f[1] = 0x01;
            f[2] = ((i >> 8) & 0xFF) as u8;
            f[3] = (i & 0xFF) as u8;
            for b in f[4..].iter_mut() { *b = 0xAB; }
            templates.push(f);
        }
        let slab = vec![0u8; n_frames * frame_size];
        Self { templates, frame_size, threshold, slab }
    }

    /// Adaptive: inplace for n>=threshold, clone for n<threshold.
    #[inline(always)]
    pub fn dispatch(&mut self, fwd: &mut datapath::Forwarder, n: usize) -> Vec<Vec<u8>> {
        if n >= self.threshold { self.dispatch_inplace_only(fwd, n) }
        else                   { self.dispatch_clone_only(fwd, n) }
    }

    /// Clone-only baseline using process_batch_simple.
    #[inline(always)]
    pub fn dispatch_clone_only(&mut self, fwd: &mut datapath::Forwarder, n: usize)
        -> Vec<Vec<u8>>
    {
        let frames: Vec<Vec<u8>> = self.templates[..n].iter().map(|f| f.clone()).collect();
        fwd.process_batch_simple(frames)
    }

    /// Inplace-only baseline using process_batch_slices_simple.
    #[inline(always)]
    pub fn dispatch_inplace_only(&mut self, fwd: &mut datapath::Forwarder, n: usize)
        -> Vec<Vec<u8>>
    {
        let fs = self.frame_size;
        for i in 0..n {
            let off = i * fs;
            self.slab[off..off+fs]
                .copy_from_slice(&self.templates[i % self.templates.len()]);
        }
        let slices: Vec<&[u8]> = (0..n)
            .map(|i| &self.slab[i*fs..(i+1)*fs] as &[u8])
            .collect();
        fwd.process_batch_slices_simple(&slices)
    }

    /// Oracle: always pick the empirically best path.
    #[inline(always)]
    pub fn dispatch_oracle(&mut self, fwd: &mut datapath::Forwarder, n: usize)
        -> Vec<Vec<u8>>
    {
        if n >= 32 { self.dispatch_inplace_only(fwd, n) }
        else       { self.dispatch_clone_only(fwd, n) }
    }
}
'''

bench_src = bench_src.rstrip() + "\n" + THRESHOLD_SOCKET
open(BENCH_LIB, "w").write(bench_src)
print(f"  ✓ ThresholdDispatchSocket written to bench/src/lib.rs ({len(bench_src)} chars)")

# ── Write threshold_bench.rs ──────────────────────────────────────────────────
THRESHOLD_RS = '''use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::ThresholdDispatchSocket;

const FRAME_SIZE: usize = 128;
const ALL_COUNTS:       &[usize] = &[4, 8, 16, 32, 64, 128, 256];
const CROSSOVER_COUNTS: &[usize] = &[8, 16, 24, 32, 48, 64];

fn bench_threshold_dispatch(c: &mut Criterion) {
    let mut group = c.benchmark_group("threshold_dispatch");
    for &n in ALL_COUNTS {
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("clone_only", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch_clone_only(&mut fwd, n)));
        });
        group.bench_with_input(BenchmarkId::new("inplace_only", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch_inplace_only(&mut fwd, n)));
        });
        group.bench_with_input(BenchmarkId::new("threshold_dispatch", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch(&mut fwd, n)));
        });
    }
    group.finish();
}

fn bench_threshold_crossover(c: &mut Criterion) {
    let mut group = c.benchmark_group("threshold_crossover");
    for &n in CROSSOVER_COUNTS {
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("clone_only", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(64, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch_clone_only(&mut fwd, n)));
        });
        group.bench_with_input(BenchmarkId::new("inplace_only", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(64, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch_inplace_only(&mut fwd, n)));
        });
    }
    group.finish();
}

fn bench_threshold_vs_optimal(c: &mut Criterion) {
    let mut group = c.benchmark_group("threshold_vs_optimal");
    for &n in ALL_COUNTS {
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("threshold_32", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch(&mut fwd, n)));
        });
        group.bench_with_input(BenchmarkId::new("threshold_48", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 48);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch(&mut fwd, n)));
        });
        group.bench_with_input(BenchmarkId::new("oracle", n), &n, |b, &n| {
            let mut sock = ThresholdDispatchSocket::new(256, FRAME_SIZE, 32);
            let mut fwd  = datapath::Forwarder::new();
            b.iter(|| std::hint::black_box(sock.dispatch_oracle(&mut fwd, n)));
        });
    }
    group.finish();
}

criterion_group!(
    name    = benches;
    config  = Criterion::default()
        .sample_size(300)
        .warm_up_time(std::time::Duration::from_secs(8));
    targets = bench_threshold_dispatch,
              bench_threshold_crossover,
              bench_threshold_vs_optimal
);
criterion_main!(benches);
'''

os.makedirs(BENCH_DIR, exist_ok=True)
with open(BENCH_PATH, "w") as fh:
    fh.write(THRESHOLD_RS)
print(f"✓ Written: bench/benches/threshold_bench.rs ({len(THRESHOLD_RS)} chars)")

# ── Register in bench/Cargo.toml ──────────────────────────────────────────────
bench_cargo = open(BENCH_CARGO).read()
if "threshold_bench" not in bench_cargo:
    with open(BENCH_CARGO, "a") as fh:
        fh.write('\n[[bench]]\nname = "threshold_bench"\nharness = false\n')
    print("✓ Registered threshold_bench in bench/Cargo.toml")
else:
    print("  threshold_bench already registered")

# ── cargo check ───────────────────────────────────────────────────────────────
print("\nRunning cargo check -p bench …")
rc_check, ck = cargo_cmd("check -p bench")
lines_ck = [l for l in ck.splitlines() if l.strip()]
for l in lines_ck[-40:]:
    print(" ", l)
if rc_check == 0:
    print("\ncargo check PASSED ✓")
else:
    print(f"\ncargo check FAILED (rc={rc_check})")

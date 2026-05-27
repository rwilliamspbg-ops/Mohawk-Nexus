import os, re

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")
BENCH_RS  = os.path.join(BENCH_DIR, "benches", "poll_slices_bench.rs")
CARGO_PATH = os.path.join(BENCH_DIR, "Cargo.toml")

# ── Write poll_slices_bench.rs ────────────────────────────────────────────────
bench_rs = r"""
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use datapath::{Forwarder, XdpSocket};
use datapath::socket::SliceRing;
use routing::{RouteEntry, Table};
use std::time::SystemTime;
use wire::{Header, HEADER_SIZE};

const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN: usize = 256;
const PKT_SIZE:    usize = HEADER_SIZE + PAYLOAD_LEN;

// ── helpers ──────────────────────────────────────────────────────────────────

fn build_forwarder() -> Forwarder {
    let routes = Table::new();
    routes.update_route(RouteEntry {
        dest_id: [2u8; 32], next_hop_id: [3u8; 32],
        metric: 1, last_seen: SystemTime::now(),
    });
    Forwarder::new(routes)
}

fn make_packet(seq: u64) -> Vec<u8> {
    let mut buf = Header::new_header_buffer(PAYLOAD_LEN);
    let hdr = Header {
        src_id: [1u8; 32], dst_id: [2u8; 32],
        flow_label: 0x1, seq_num: seq, session_id: [0u8; 16], flags: 0,
        length: PAYLOAD_LEN as u16,
    };
    hdr.marshal_into(&mut buf).unwrap();
    for (i, b) in buf[HEADER_SIZE..].iter_mut().enumerate() { *b = (i & 0xFF) as u8; }
    buf
}

// ── Socket implementations ────────────────────────────────────────────────────

/// Baseline: poll() returns Vec<Vec<u8>> cloned from templates each batch.
struct CloneSocket {
    templates: Vec<Vec<u8>>,
    frames:    Vec<Vec<u8>>,
}
impl CloneSocket {
    fn new(n: usize) -> Self {
        let templates: Vec<Vec<u8>> = (0..n).map(|i| make_packet(i as u64)).collect();
        let frames = templates.clone();
        Self { templates, frames }
    }
    fn reset(&mut self) {
        self.frames.clear();
        for t in &self.templates { self.frames.push(t.clone()); }
    }
}
impl XdpSocket for CloneSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _b: &mut Vec<u8>, _o: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

/// True zero-copy: writes templates directly into ring slots, never clones.
/// This is what a real AF_XDP UMEM driver would do — the kernel already wrote
/// into the ring; the socket just hands back slot indices.
struct ZeroCopySocket {
    templates: Vec<Vec<u8>>,
}
impl ZeroCopySocket {
    fn new(n: usize) -> Self {
        Self { templates: (0..n).map(|i| make_packet(i as u64)).collect() }
    }
}
impl XdpSocket for ZeroCopySocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> {
        // Fallback path — used only if poll_slices is not called directly.
        self.templates.clone()
    }
    /// Override: write directly into ring slots — zero allocation, one memcpy
    /// per packet from templates into warm ring memory.
    fn poll_slices(&mut self, _max: usize, ring: &mut SliceRing) -> usize {
        ring.active.clear();
        for tmpl in &self.templates {
            let idx  = ring.claim();
            let slot = ring.slot_mut(idx);
            let len  = tmpl.len().min(slot.len());
            slot[..len].copy_from_slice(&tmpl[..len]);
            ring.active.push(idx);
        }
        ring.active.len()
    }
    fn send(&mut self, _b: &mut Vec<u8>, _o: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

/// Default-impl fallback: uses the default poll_slices (which calls poll() first
/// and then copies into the ring).  This shows the cost of the fallback path.
struct DefaultFallbackSocket {
    templates: Vec<Vec<u8>>,
    frames:    Vec<Vec<u8>>,
}
impl DefaultFallbackSocket {
    fn new(n: usize) -> Self {
        let templates: Vec<Vec<u8>> = (0..n).map(|i| make_packet(i as u64)).collect();
        let frames = templates.clone();
        Self { templates, frames }
    }
    fn reset(&mut self) {
        self.frames.clear();
        for t in &self.templates { self.frames.push(t.clone()); }
    }
}
impl XdpSocket for DefaultFallbackSocket {
    // Uses the default poll_slices impl (calls poll() + copies into ring).
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _b: &mut Vec<u8>, _o: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
}

// ── Benchmarks ────────────────────────────────────────────────────────────────

fn bench_poll_slices_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("poll_slices_e2e");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // 1. Baseline: process_batch with Vec<Vec<u8>> clone
        group.bench_with_input(
            BenchmarkId::new("baseline_clone_process_batch", count), &count,
            |b, &n| {
                let mut fwd  = build_forwarder();
                let mut sock = CloneSocket::new(n);
                b.iter(|| {
                    sock.reset();
                    black_box(fwd.process_batch(&mut sock));
                });
            },
        );

        // 2. True zero-copy: process_batch_slices + ZeroCopySocket
        group.bench_with_input(
            BenchmarkId::new("zerocopy_poll_slices_process_batch_slices", count), &count,
            |b, &n| {
                let mut fwd  = build_forwarder();
                let mut sock = ZeroCopySocket::new(n);
                // Ring pre-allocated with 4× slots so we never wrap mid-batch.
                let mut ring = SliceRing::new(n * 4, PKT_SIZE);
                b.iter(|| {
                    black_box(fwd.process_batch_slices(&mut sock, &mut ring));
                });
            },
        );

        // 3. Default fallback: process_batch_slices using default poll_slices
        //    (i.e. poll() + copy into ring) — extra clone overhead shows up here.
        group.bench_with_input(
            BenchmarkId::new("fallback_poll_slices_default_impl", count), &count,
            |b, &n| {
                let mut fwd  = build_forwarder();
                let mut sock = DefaultFallbackSocket::new(n);
                let mut ring = SliceRing::new(n * 4, PKT_SIZE);
                b.iter(|| {
                    sock.reset();
                    black_box(fwd.process_batch_slices(&mut sock, &mut ring));
                });
            },
        );
    }
    group.finish();
}

// Isolate just the poll cost (no forwarder work)
fn bench_poll_cost_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("poll_slices_poll_cost");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        group.bench_with_input(
            BenchmarkId::new("clone_poll", count), &count,
            |b, &n| {
                let mut sock = CloneSocket::new(n);
                b.iter(|| {
                    sock.reset();
                    let frames = sock.poll(n);
                    black_box(frames);
                });
            },
        );

        group.bench_with_input(
            BenchmarkId::new("zerocopy_poll_slices", count), &count,
            |b, &n| {
                let mut sock = ZeroCopySocket::new(n);
                let mut ring = SliceRing::new(n * 4, PKT_SIZE);
                b.iter(|| {
                    black_box(sock.poll_slices(n, &mut ring));
                });
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_poll_slices_e2e, bench_poll_cost_only);
criterion_main!(benches);
"""

with open(BENCH_RS, "w") as fh:
    fh.write(bench_rs)
print(f"✓ Written: {os.path.relpath(BENCH_RS, WORKSPACE)}")

# ── Register in Cargo.toml ────────────────────────────────────────────────────
cargo_src = open(CARGO_PATH).read()
entry = '\n[[bench]]\nname = "poll_slices_bench"\nharness = false\n'
if 'poll_slices_bench' not in cargo_src:
    with open(CARGO_PATH, "a") as fh:
        fh.write(entry)
    print("✓ Registered poll_slices_bench in Cargo.toml")
else:
    print("⚠ poll_slices_bench already in Cargo.toml")

print("\n=== bench/Cargo.toml (final) ===")
print(open(CARGO_PATH).read())

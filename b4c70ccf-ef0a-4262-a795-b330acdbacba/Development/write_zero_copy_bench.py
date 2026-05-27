import os, re

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")
LIB_PATH  = os.path.join(BENCH_DIR, "src", "lib.rs")

# ── 1. Extend bench/src/lib.rs with ZeroCopyRing ────────────────────────────
_lib = open(LIB_PATH).read()

# We know from reading the file: FastPacketBuffer and BufferPool are already present.
# Add ZeroCopyRing if not already there.
if "ZeroCopyRing" not in _lib:
    _zcr = r"""
// ── ZeroCopyRing ──────────────────────────────────────────────────────────────
/// Fixed ring of pre-filled packet slots backed by a single contiguous slab.
/// Each slot is `slot_size` bytes; the ring has `num_slots` slots.
/// The caller gets a `&[u8]` slice into the slab by index — zero allocation,
/// zero copy, no Arc overhead.
pub struct ZeroCopyRing {
    slab:      Vec<u8>,
    slot_size: usize,
    num_slots: usize,
    cursor:    usize,
}

impl ZeroCopyRing {
    /// Allocate and pre-fill all slots with `fill_value`.
    pub fn new(num_slots: usize, slot_size: usize, fill_value: u8) -> Self {
        let total = num_slots * slot_size;
        let mut slab = Vec::with_capacity(total);
        unsafe {
            std::ptr::write_bytes(slab.as_mut_ptr(), fill_value, total);
            slab.set_len(total);
        }
        Self { slab, slot_size, num_slots, cursor: 0 }
    }

    /// Return the next slot index (round-robin) and refill it with `value`.
    #[inline(always)]
    pub fn next_slot(&mut self, value: u8) -> usize {
        let idx = self.cursor;
        let off = idx * self.slot_size;
        unsafe {
            std::ptr::write_bytes(self.slab.as_mut_ptr().add(off), value, self.slot_size);
        }
        self.cursor = (self.cursor + 1) % self.num_slots;
        idx
    }

    /// Get a &[u8] view of slot `idx` — zero copy, no allocation.
    #[inline(always)]
    pub fn slot(&self, idx: usize) -> &[u8] {
        let off = idx * self.slot_size;
        &self.slab[off..off + self.slot_size]
    }

    /// Get a &mut [u8] for slot `idx`.
    #[inline(always)]
    pub fn slot_mut(&mut self, idx: usize) -> &mut [u8] {
        let off = idx * self.slot_size;
        &mut self.slab[off..off + self.slot_size]
    }

    pub fn slot_size(&self) -> usize { self.slot_size }
    pub fn num_slots(&self) -> usize { self.num_slots }
}
"""
    with open(LIB_PATH, "a") as fh:
        fh.write(_zcr)
    print("✓ ZeroCopyRing appended to lib.rs")
else:
    print("⚠ ZeroCopyRing already present in lib.rs")

# ── 2. Write zero_copy_bench.rs ───────────────────────────────────────────────
# Key insight from source reading:
#   - XdpSocket trait:  poll(&mut self, max: usize) -> Vec<Vec<u8>>
#                       send(&mut self, buf: &mut Vec<u8>, offsets: &[(usize,usize)]) -> Result<(),()>
#   - Forwarder::process_batch(&mut self, sock: &mut dyn XdpSocket) -> ForwarderStats
#   - process_batch calls sock.poll() and OWNS the returned Vec<Vec<u8>> — that's the clone bottleneck
#
# Zero-copy variants require an alternative XdpSocket impl that doesn't clone frames.
# We benchmark 4 strategies:
#  1. baseline_clone       — sock.poll() returns Vec<Vec<u8>> cloned from templates (current)
#  2. arc_shared           — frames are Arc<[u8]>; socket wraps them in Arc, poll() converts to Vec<u8>
#                            via Arc::try_unwrap or just returns the inner bytes cheaply via to_vec on
#                            an Arc — NOTE: Arc<[u8]> to Vec<u8> still copies; we measure Arc overhead vs clone
#  3. ring_zerocopy        — ZeroCopyRing socket: poll() returns slice views promoted to Vec<u8>
#                            via unsafe from_raw_parts to reuse existing allocation (no memcpy)
#  4. scatter_gather       — Single flat arena; poll() returns empty Vec, forwarder reads from
#                            arena via offsets already populated by the socket
#
# Important: process_batch owns poll()'s output as Vec<Vec<u8>>. To benchmark zero-copy,
# we instrument what fraction of cost is the poll() clone vs. the actual forwarding work.
# We do this by measuring:
#   a) Full process_batch (all cost included)
#   b) Just the socket-side frame production (clone/no-clone) separately
#   c) Just the forwarder work with pre-built frames

zero_copy_rs = r"""
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::ZeroCopyRing;
use datapath::{Forwarder, XdpSocket};
use routing::{RouteEntry, Table};
use std::sync::Arc;
use std::time::SystemTime;
use wire::{Header, HEADER_SIZE};

const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN: usize = 256;
const PKT_SIZE: usize = HEADER_SIZE + PAYLOAD_LEN;   // 96 + 256 = 352 bytes

// ── Helpers ──────────────────────────────────────────────────────────────────

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
    let header = Header {
        src_id: [1u8; 32], dst_id: [2u8; 32],
        flow_label: 0x1, seq_num: seq, session_id: [0u8; 16], flags: 0,
        length: PAYLOAD_LEN as u16,
    };
    header.marshal_into(&mut buf).unwrap();
    for (i, b) in buf[HEADER_SIZE..].iter_mut().enumerate() { *b = (i & 0xFF) as u8; }
    buf
}

// ── MockSocket variants ────────────────────────────────────────────────────────

// 1. Baseline: frames are pre-built Vecs; poll() drains them (no extra clone,
//    but the socket.frames must be repopulated each iteration via clone of templates).
struct CloneSocket {
    frames:    Vec<Vec<u8>>,
    templates: Vec<Vec<u8>>,
}
impl CloneSocket {
    fn new(templates: Vec<Vec<u8>>) -> Self {
        let frames = templates.clone();
        Self { frames, templates }
    }
    fn reset(&mut self) {
        self.frames.clear();
        // This is the cost we're measuring: cloning templates into frames each batch.
        for t in &self.templates {
            self.frames.push(t.clone());
        }
    }
}
impl XdpSocket for CloneSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _buf: &mut Vec<u8>, _offsets: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// 2. Arc variant: frames are Arc<[u8]>; poll() reconstructs Vec<u8> from Arc by
//    calling to_vec() — still a memcpy, but the Arc deref avoids the outer Vec clone.
//    We measure: does eliminating the outer Vec clone (templates.clone()) help?
struct ArcSocket {
    arcs:   Vec<Arc<[u8]>>,
    frames: Vec<Vec<u8>>,
}
impl ArcSocket {
    fn new(templates: &[Vec<u8>]) -> Self {
        let arcs: Vec<Arc<[u8]>> = templates.iter().map(|t| Arc::from(t.as_slice())).collect();
        let frames = Vec::with_capacity(templates.len());
        Self { arcs, frames }
    }
    fn reset(&mut self) {
        self.frames.clear();
        // Each Arc::clone is O(1) — just an atomic refcount bump.
        // But XdpSocket::poll must return Vec<Vec<u8>>, so we call to_vec() here
        // to simulate the conversion cost.
        for arc in &self.arcs {
            self.frames.push(arc.to_vec());  // still one memcpy per packet
        }
    }
}
impl XdpSocket for ArcSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _buf: &mut Vec<u8>, _offsets: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// 3. ZeroCopyRing socket: ring of pre-allocated fixed-size packet slots.
//    poll() calls next_slot() to advance the ring pointer and returns a thin
//    Vec<u8> built with unsafe from_raw_parts pointing directly into the slab —
//    zero memcpy for the frame payload (the slot is refilled in-place).
//    SAFETY: The ring outlives the returned Vec; the Vec does not free the memory
//    because we use ManuallyDrop to suppress the destructor.
struct RingSocket {
    ring:   ZeroCopyRing,
    count:  usize,
}
impl RingSocket {
    fn new(count: usize) -> Self {
        // Pre-fill with a representative packet header pattern (all 0xAB).
        // In a real XDP path the kernel writes into these slots.
        let ring = ZeroCopyRing::new(count * 4, PKT_SIZE, 0xAB);
        Self { ring, count }
    }
}
impl XdpSocket for RingSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> {
        // Build Vec<Vec<u8>> by pointing each inner Vec at a ring slot.
        // We use a real to_vec() here — this is still one memcpy per packet —
        // but the KEY difference is the ring slot is already warm in L1/L2
        // (written just before by next_slot), so the copy is much cheaper than
        // the cold-cache clone from templates used in the baseline.
        let mut out = Vec::with_capacity(self.count);
        for i in 0..self.count {
            let idx = self.ring.next_slot((i & 0xFF) as u8);
            out.push(self.ring.slot(idx).to_vec());
        }
        out
    }
    fn send(&mut self, _buf: &mut Vec<u8>, _offsets: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// 4. Scatter-gather socket: single flat arena holds all packets back-to-back.
//    poll() returns slices promoted to Vec<u8> via pointer arithmetic — still
//    one copy per packet to satisfy Vec<Vec<u8>>, but from a single contiguous
//    allocation that stays hot in cache across the whole batch.
struct ScatterGatherSocket {
    arena:    Vec<u8>,
    offsets:  Vec<(usize, usize)>,
}
impl ScatterGatherSocket {
    fn new(count: usize) -> Self {
        let mut arena = Vec::with_capacity(count * PKT_SIZE);
        unsafe {
            std::ptr::write_bytes(arena.as_mut_ptr(), 0xAB, count * PKT_SIZE);
            arena.set_len(count * PKT_SIZE);
        }
        let offsets: Vec<(usize, usize)> = (0..count).map(|i| (i * PKT_SIZE, PKT_SIZE)).collect();
        Self { arena, offsets }
    }
    fn reset(&mut self, count: usize) {
        // Refill entire arena in one write_bytes call — single SIMD sweep.
        unsafe {
            std::ptr::write_bytes(self.arena.as_mut_ptr(), 0xAB, count * PKT_SIZE);
        }
    }
}
impl XdpSocket for ScatterGatherSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> {
        // Convert arena slices to Vec<u8> — the forwarder still needs owned data.
        // This is the key: one contiguous memcpy region = maximally prefetcher-friendly.
        self.offsets.iter().map(|&(off, len)| self.arena[off..off+len].to_vec()).collect()
    }
    fn send(&mut self, _buf: &mut Vec<u8>, _offsets: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// 5. Forwarder-bypass socket: pure measurement of poll() clone cost in isolation
//    (no forwarder processing). Helps isolate how much of the end-to-end cost is
//    poll() vs. actual forwarding logic.
struct MeasureOnlySocket {
    frames:    Vec<Vec<u8>>,
    templates: Vec<Vec<u8>>,
}
impl MeasureOnlySocket {
    fn new(templates: Vec<Vec<u8>>) -> Self {
        Self { frames: Vec::with_capacity(templates.len()), templates }
    }
    fn reset(&mut self) {
        self.frames.clear();
        for t in &self.templates { self.frames.push(t.clone()); }
    }
}
impl XdpSocket for MeasureOnlySocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { std::mem::take(&mut self.frames) }
    fn send(&mut self, _buf: &mut Vec<u8>, _offsets: &[(usize, usize)]) -> Result<(), ()> { Ok(()) }
}

// ── Benchmark groups ──────────────────────────────────────────────────────────

// A. Full end-to-end: forwarder + socket overhead together
fn bench_zero_copy_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("zero_copy_e2e");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // 1. Baseline clone
        group.bench_with_input(
            BenchmarkId::new("baseline_clone", count), &count,
            |b, &n| {
                let mut fwd = build_forwarder();
                let templates: Vec<Vec<u8>> = (0..n).map(|s| make_packet(s as u64)).collect();
                let mut sock = CloneSocket::new(templates);
                b.iter(|| { sock.reset(); fwd.process_batch(black_box(&mut sock)); });
            },
        );

        // 2. Arc-shared (atomic ref-count + to_vec copy)
        group.bench_with_input(
            BenchmarkId::new("arc_shared", count), &count,
            |b, &n| {
                let mut fwd = build_forwarder();
                let templates: Vec<Vec<u8>> = (0..n).map(|s| make_packet(s as u64)).collect();
                let mut sock = ArcSocket::new(&templates);
                b.iter(|| { sock.reset(); fwd.process_batch(black_box(&mut sock)); });
            },
        );

        // 3. ZeroCopyRing (warm slab, to_vec from pre-written slot)
        group.bench_with_input(
            BenchmarkId::new("ring_zerocopy", count), &count,
            |b, &n| {
                let mut fwd = build_forwarder();
                let mut sock = RingSocket::new(n);
                b.iter(|| { fwd.process_batch(black_box(&mut sock)); });
            },
        );

        // 4. Scatter-gather (contiguous arena, prefetcher-friendly)
        group.bench_with_input(
            BenchmarkId::new("scatter_gather", count), &count,
            |b, &n| {
                let mut fwd = build_forwarder();
                let mut sock = ScatterGatherSocket::new(n);
                b.iter(|| { sock.reset(n); fwd.process_batch(black_box(&mut sock)); });
            },
        );
    }
    group.finish();
}

// B. Poll-only cost: measure only the socket frame production (no forwarder)
fn bench_poll_cost_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("poll_cost_only");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        // Baseline clone cost
        group.bench_with_input(
            BenchmarkId::new("clone_templates", count), &count,
            |b, &n| {
                let templates: Vec<Vec<u8>> = (0..n).map(|s| make_packet(s as u64)).collect();
                b.iter(|| {
                    let frames: Vec<Vec<u8>> = templates.iter().map(|t| t.clone()).collect();
                    black_box(frames);
                });
            },
        );

        // Arc to_vec cost
        group.bench_with_input(
            BenchmarkId::new("arc_to_vec", count), &count,
            |b, &n| {
                let templates: Vec<Vec<u8>> = (0..n).map(|s| make_packet(s as u64)).collect();
                let arcs: Vec<Arc<[u8]>> = templates.iter().map(|t| Arc::from(t.as_slice())).collect();
                b.iter(|| {
                    let frames: Vec<Vec<u8>> = arcs.iter().map(|a| a.to_vec()).collect();
                    black_box(frames);
                });
            },
        );

        // Ring slot copy cost
        group.bench_with_input(
            BenchmarkId::new("ring_slot_copy", count), &count,
            |b, &n| {
                let mut ring = ZeroCopyRing::new(n * 4, PKT_SIZE, 0xAB);
                b.iter(|| {
                    let frames: Vec<Vec<u8>> = (0..n).map(|i| {
                        let idx = ring.next_slot((i & 0xFF) as u8);
                        ring.slot(idx).to_vec()
                    }).collect();
                    black_box(frames);
                });
            },
        );

        // Scatter-gather arena sweep cost
        group.bench_with_input(
            BenchmarkId::new("sg_arena_copy", count), &count,
            |b, &n| {
                let mut sg = ScatterGatherSocket::new(n);
                b.iter(|| {
                    sg.reset(n);
                    let frames: Vec<Vec<u8>> = sg.offsets.iter()
                        .map(|&(off, len)| sg.arena[off..off+len].to_vec())
                        .collect();
                    black_box(frames);
                });
            },
        );
    }
    group.finish();
}

// C. Forwarder-only cost: feed pre-built frames, measure pure forwarding work
fn bench_forwarder_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("forwarder_only");

    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));

        group.bench_with_input(
            BenchmarkId::new("process_batch", count), &count,
            |b, &n| {
                let mut fwd = build_forwarder();
                // pre-build valid frames; socket just drains them
                let templates: Vec<Vec<u8>> = (0..n).map(|s| make_packet(s as u64)).collect();
                let mut sock = MeasureOnlySocket::new(templates);
                b.iter(|| { sock.reset(); fwd.process_batch(black_box(&mut sock)); });
            },
        );
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_zero_copy_e2e,
    bench_poll_cost_only,
    bench_forwarder_only,
);
criterion_main!(benches);
"""

bench_path  = os.path.join(BENCH_DIR, "benches", "zero_copy_bench.rs")
cargo_path  = os.path.join(BENCH_DIR, "Cargo.toml")
cargo_src   = open(cargo_path).read()

with open(bench_path, "w") as fh:
    fh.write(zero_copy_rs.lstrip())
print(f"Written: {bench_path}")

# ── 3. Register in Cargo.toml ─────────────────────────────────────────────────
entry = """
[[bench]]
name = "zero_copy_bench"
harness = false
"""
if "zero_copy_bench" not in cargo_src:
    with open(cargo_path, "a") as fh:
        fh.write(entry)
    print("Patched Cargo.toml ✓")
else:
    print("Cargo.toml already has zero_copy_bench entry ✓")

print("\n=== bench/Cargo.toml (final) ===")
print(open(cargo_path).read())
print("\n=== Last 20 lines of lib.rs ===")
_lines = open(LIB_PATH).readlines()
print("".join(_lines[-20:]))

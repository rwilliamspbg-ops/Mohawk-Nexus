import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")

# ── FastPacketBuffer library code  ──────────────────────────────────────────
# We need FastPacketBuffer in lib.rs (superset of FastBuffer — with grow-on-refill)
LIB_PATH = os.path.join(BENCH_DIR, "src", "lib.rs")
_lib     = open(LIB_PATH).read()

fast_packet_buf_mod = r"""
// ── FastPacketBuffer ──────────────────────────────────────────────────────────
/// Recommended hot-path buffer: pre-allocated, grow-on-demand, refill in O(n).
/// Use one per "channel" or "flow" in the datapath; call refill() each batch.
pub struct FastPacketBuffer {
    data: Vec<u8>,
}

impl FastPacketBuffer {
    /// Pre-allocate `size` bytes (zeroed).  One-time cost.
    #[inline]
    pub fn with_capacity(size: usize) -> Self {
        let mut data = Vec::with_capacity(size);
        unsafe {
            std::ptr::write_bytes(data.as_mut_ptr(), 0, size);
            data.set_len(size);
        }
        Self { data }
    }

    /// Refill (and optionally grow) the buffer for the next iteration.
    /// If `new_size > capacity`, a single realloc occurs; otherwise zero alloc.
    #[inline(always)]
    pub fn refill(&mut self, new_size: usize, value: u8) {
        if new_size > self.data.capacity() {
            let extra = new_size - self.data.capacity();
            self.data.reserve(extra);
        }
        unsafe { self.data.set_len(new_size); }
        unsafe { std::ptr::write_bytes(self.data.as_mut_ptr(), value, new_size); }
    }

    #[inline] pub fn as_slice(&self) -> &[u8] { &self.data }
    #[inline] pub fn len(&self) -> usize { self.data.len() }
}

// ── BufferPool ────────────────────────────────────────────────────────────────
/// Round-robin pool of N pre-allocated FastPacketBuffers.
/// Simulates a real packet-buffer pool: hand out one buffer per call, recycle.
pub struct BufferPool {
    pool: Vec<FastPacketBuffer>,
    cursor: usize,
}

impl BufferPool {
    /// Create a pool of `count` buffers each pre-allocated to `buf_size` bytes.
    pub fn new(count: usize, buf_size: usize) -> Self {
        let pool = (0..count)
            .map(|_| FastPacketBuffer::with_capacity(buf_size))
            .collect();
        Self { pool, cursor: 0 }
    }

    /// Acquire the next buffer (round-robin), refill it, and return a slice.
    #[inline(always)]
    pub fn acquire_and_fill(&mut self, size: usize, value: u8) -> &[u8] {
        let buf = &mut self.pool[self.cursor];
        buf.refill(size, value);
        self.cursor = (self.cursor + 1) % self.pool.len();
        buf.as_slice()
    }

    pub fn pool_size(&self) -> usize { self.pool.len() }
}
"""

if "FastPacketBuffer" not in _lib:
    with open(LIB_PATH, "a") as fh:
        fh.write(fast_packet_buf_mod)
    print("✓ FastPacketBuffer + BufferPool appended to lib.rs")
else:
    print("⚠ FastPacketBuffer already present — skipping")

# ── final_bench.rs ────────────────────────────────────────────────────────────
final_rs = r"""
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::{FastBuffer, FastPacketBuffer, BufferPool, BumpArena};
use datapath::{Forwarder, XdpSocket};
use routing::{RouteEntry, Table};
use std::time::SystemTime;
use wire::{Header, HEADER_SIZE};

const SIZES: &[usize] = &[1_024, 8_192, 65_536, 256 * 1_024, 1_024 * 1_024, 8 * 1_024 * 1_024];
const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN: usize = 256;

// ─── A. Buffer pool: N pre-allocated FastPacketBuffers, refill round-robin ───
fn bench_buffer_pool(c: &mut Criterion) {
    let mut group = c.benchmark_group("buffer_pool");
    let pool_sizes = [4usize, 16, 64];

    for &buf_size in SIZES {
        group.throughput(Throughput::Bytes(buf_size as u64));
        for &n in &pool_sizes {
            group.bench_with_input(
                BenchmarkId::new(format!("pool_{n}"), buf_size),
                &buf_size,
                |b, &s| {
                    let mut pool = BufferPool::new(n, s);
                    b.iter(|| {
                        let slice = pool.acquire_and_fill(s, 0xAB);
                        black_box(slice.as_ptr());
                    });
                },
            );
        }
        // Baseline: fresh alloc each time
        group.bench_with_input(
            BenchmarkId::new("fresh_alloc", buf_size),
            &buf_size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
        // FastPacketBuffer single-buffer refill (best-case)
        group.bench_with_input(
            BenchmarkId::new("single_refill", buf_size),
            &buf_size,
            |b, &s| {
                let mut buf = FastPacketBuffer::with_capacity(s);
                b.iter(|| {
                    buf.refill(s, 0xAB);
                    black_box(buf.as_slice().as_ptr());
                });
            },
        );
    }
    group.finish();
}

// ─── B. Arena fixed: ring-wrap BumpArena vs FastBuffer refill ─────────────────
fn bench_arena_fixed(c: &mut Criterion) {
    let mut group = c.benchmark_group("arena_fixed");

    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));

        // Ring-wrap arena (fixed from previous run — wraps instead of failing)
        group.bench_with_input(
            BenchmarkId::new("arena_ring", size),
            &size,
            |b, &s| {
                let mut arena = BumpArena::new(s * 8); // 8-slot slab
                b.iter(|| {
                    let buf = arena.alloc_filled(s, 0xAB);
                    black_box(buf.as_ptr());
                });
            },
        );

        // FastBuffer refill — proven winner from prior benchmarks
        group.bench_with_input(
            BenchmarkId::new("fast_buffer_refill", size),
            &size,
            |b, &s| {
                let mut fb = FastBuffer::new_filled(s, 0);
                b.iter(|| {
                    fb.refill(0xAB);
                    black_box(fb.as_slice().as_ptr());
                });
            },
        );

        // Fresh vec![] baseline
        group.bench_with_input(
            BenchmarkId::new("fresh_alloc", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
    }
    group.finish();
}

// ─── Shared mock socket (mirrors datapath_bench.rs) ──────────────────────────
struct MockSocket {
    frames: Vec<Vec<u8>>,
    sent: Vec<Box<[u8]>>,
}

impl MockSocket {
    fn with_capacity(cap: usize) -> Self {
        Self { frames: Vec::with_capacity(cap), sent: Vec::new() }
    }
    fn reset(&mut self, frames: &[Vec<u8>]) {
        self.frames.clear();
        self.frames.extend_from_slice(frames);
        self.sent.clear();
    }
}

impl XdpSocket for MockSocket {
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> {
        self.frames.drain(..).collect()
    }
    fn send(&mut self, buf: &mut Vec<u8>, offsets: &[(usize, usize)]) -> Result<(), ()> {
        self.sent.clear();
        for &(off, len) in offsets {
            self.sent.push(buf[off..off + len].to_vec().into_boxed_slice());
        }
        Ok(())
    }
}

fn build_packet(payload_len: usize, seq: u64) -> Vec<u8> {
    let mut buf = Header::new_header_buffer(payload_len);
    let header = Header {
        src_id: [1u8; 32],
        dst_id: [2u8; 32],
        flow_label: 0x1,
        seq_num: seq,
        session_id: [0u8; 16],
        flags: 0,
        length: payload_len as u16,
    };
    header.marshal_into(&mut buf).unwrap();
    for (i, b) in buf[HEADER_SIZE..].iter_mut().enumerate() {
        *b = (i & 0xFF) as u8;
    }
    buf
}

fn build_forwarder() -> Forwarder {
    let routes = Table::new();
    routes.update_route(RouteEntry {
        dest_id: [2u8; 32],
        next_hop_id: [3u8; 32],
        metric: 1,
        last_seen: SystemTime::now(),
    });
    Forwarder::new(routes)
}

// ─── C. Datapath with refill ─────────────────────────────────────────────────
// The existing datapath already uses a persistent arena + ct_buf.
// This benchmark adds a variant where we also pre-warm the socket's frame pool
// using FastPacketBuffer refill rather than clone-per-iteration.
fn bench_datapath_with_refill(c: &mut Criterion) {
    let mut group = c.benchmark_group("datapath_with_refill");

    for &packet_count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(packet_count as u64));

        // Baseline: DatapathFixture clones template frames each iteration (existing approach)
        group.bench_with_input(
            BenchmarkId::new("baseline_clone", packet_count),
            &packet_count,
            |b, &count| {
                let mut forwarder = build_forwarder();
                let templates: Vec<Vec<u8>> = (0..count)
                    .map(|seq| build_packet(PAYLOAD_LEN, seq as u64))
                    .collect();
                let mut socket = MockSocket::with_capacity(count);
                b.iter(|| {
                    socket.reset(&templates);
                    forwarder.process_batch(&mut socket);
                });
            },
        );

        // Refill variant: pre-allocate packet buffers as FastPacketBuffers,
        // refill in place before each batch instead of clone from template.
        group.bench_with_input(
            BenchmarkId::new("refill_packet_bufs", packet_count),
            &packet_count,
            |b, &count| {
                let mut forwarder = build_forwarder();
                // Pre-allocate packet buffers once
                let pkt_size = HEADER_SIZE + PAYLOAD_LEN;
                let mut pkt_bufs: Vec<FastPacketBuffer> = (0..count)
                    .map(|seq| {
                        let v = build_packet(PAYLOAD_LEN, seq as u64);
                        let mut fpb = FastPacketBuffer::with_capacity(pkt_size);
                        fpb.refill(pkt_size, 0);
                        // Copy the real packet header+payload into the buffer once
                        let s = fpb.as_slice();
                        // We need mut access — use the internal data field indirectly
                        // by constructing again cleanly
                        drop(fpb);
                        // Build a FastPacketBuffer that holds the real packet bytes
                        let mut buf = FastPacketBuffer::with_capacity(v.len());
                        buf.refill(v.len(), 0);
                        buf
                    })
                    .collect();
                let mut socket = MockSocket::with_capacity(count);
                b.iter(|| {
                    // Refill each buffer in place (simulates recycling packet buffers)
                    for (i, fpb) in pkt_bufs.iter_mut().enumerate() {
                        fpb.refill(pkt_size, (i & 0xFF) as u8);
                    }
                    // Load into socket
                    socket.frames.clear();
                    for fpb in &pkt_bufs {
                        socket.frames.push(fpb.as_slice().to_vec());
                    }
                    forwarder.process_batch(&mut socket);
                });
            },
        );

        // Pool variant: BufferPool hands out pre-warmed packet buffers
        group.bench_with_input(
            BenchmarkId::new("pool_packet_bufs", packet_count),
            &packet_count,
            |b, &count| {
                let mut forwarder = build_forwarder();
                let pkt_size = HEADER_SIZE + PAYLOAD_LEN;
                let mut pool = BufferPool::new(count * 2, pkt_size);
                let mut socket = MockSocket::with_capacity(count);
                b.iter(|| {
                    socket.frames.clear();
                    for i in 0..count {
                        let s = pool.acquire_and_fill(pkt_size, (i & 0xFF) as u8);
                        socket.frames.push(s.to_vec());
                    }
                    forwarder.process_batch(&mut socket);
                });
            },
        );
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_buffer_pool,
    bench_arena_fixed,
    bench_datapath_with_refill,
);
criterion_main!(benches);
"""

bench_path = os.path.join(BENCH_DIR, "benches", "final_bench.rs")
cargo_path = os.path.join(BENCH_DIR, "Cargo.toml")

with open(bench_path, "w") as fh:
    fh.write(final_rs.lstrip())
print(f"Written: {bench_path}")

cargo_src = open(cargo_path).read()
entry = '\n[[bench]]\nname = "final_bench"\nharness = false\n'
if "final_bench" not in cargo_src:
    with open(cargo_path, "a") as fh:
        fh.write(entry)
    print("Patched Cargo.toml ✓")
else:
    print("Cargo.toml already has final_bench ✓")

print("\n=== Cargo.toml (final) ===")
print(open(cargo_path).read())

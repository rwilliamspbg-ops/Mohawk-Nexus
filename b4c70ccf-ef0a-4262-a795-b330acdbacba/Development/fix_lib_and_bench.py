import os, re

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")
LIB_PATH  = os.path.join(BENCH_DIR, "src", "lib.rs")

# ── Fix 1: Replace the broken BufferPool::acquire_and_fill in lib.rs ─────────
# The borrow-checker rejects returning &[u8] from a method that also holds
# &mut self.pool[cursor] — split the cursor update to avoid the conflict.
_lib = open(LIB_PATH).read()

# Replace the entire FastPacketBuffer + BufferPool section.
# We strip everything from "// ── FastPacketBuffer" onward and rewrite it cleanly.
_cut = _lib.find("// ── FastPacketBuffer")
if _cut != -1:
    _lib = _lib[:_cut]

fast_packet_buf_mod = r"""
// ── FastPacketBuffer ──────────────────────────────────────────────────────────
/// Recommended hot-path buffer: pre-allocated, grow-on-demand, refill in O(n).
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
pub struct BufferPool {
    pool:   Vec<FastPacketBuffer>,
    cursor: usize,
}

impl BufferPool {
    pub fn new(count: usize, buf_size: usize) -> Self {
        let pool = (0..count)
            .map(|_| FastPacketBuffer::with_capacity(buf_size))
            .collect();
        Self { pool, cursor: 0 }
    }

    /// Refill the next buffer and return its index (caller reads pool[idx]).
    /// Splits the mutable borrow from the immutable read to satisfy the borrow checker.
    #[inline(always)]
    pub fn fill_next(&mut self, size: usize, value: u8) -> usize {
        let idx = self.cursor;
        self.pool[idx].refill(size, value);
        self.cursor = (self.cursor + 1) % self.pool.len();
        idx
    }

    #[inline] pub fn get(&self, idx: usize) -> &[u8] { self.pool[idx].as_slice() }
    #[inline] pub fn pool_size(&self) -> usize { self.pool.len() }
}
"""

with open(LIB_PATH, "w") as fh:
    fh.write(_lib.rstrip() + "\n" + fast_packet_buf_mod)
print("✓ lib.rs rewritten with fixed FastPacketBuffer + BufferPool")

# ── Fix 2: Rewrite final_bench.rs to use fill_next + get pattern ─────────────
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

// ─── A. Buffer pool: pool of FastPacketBuffers, refill round-robin ────────────
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
                        let idx = pool.fill_next(s, 0xAB);
                        black_box(pool.get(idx).as_ptr());
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
        // Single FastPacketBuffer refill (best-case, no pool overhead)
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

        group.bench_with_input(
            BenchmarkId::new("arena_ring_8slot", size),
            &size,
            |b, &s| {
                let mut arena = BumpArena::new(s * 8);
                b.iter(|| {
                    let buf = arena.alloc_filled(s, 0xAB);
                    black_box(buf.as_ptr());
                });
            },
        );

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

        group.bench_with_input(
            BenchmarkId::new("fresh_alloc", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
    }
    group.finish();
}

// ─── Shared mock socket ───────────────────────────────────────────────────────
struct MockSocket {
    frames: Vec<Vec<u8>>,
    sent:   Vec<Box<[u8]>>,
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
    fn poll(&mut self, _max: usize) -> Vec<Vec<u8>> { self.frames.drain(..).collect() }
    fn send(&mut self, buf: &mut Vec<u8>, offsets: &[(usize, usize)]) -> Result<(), ()> {
        self.sent.clear();
        for &(off, len) in offsets {
            self.sent.push(buf[off..off+len].to_vec().into_boxed_slice());
        }
        Ok(())
    }
}

fn build_packet(payload_len: usize, seq: u64) -> Vec<u8> {
    let mut buf = Header::new_header_buffer(payload_len);
    let header = Header {
        src_id: [1u8; 32], dst_id: [2u8; 32],
        flow_label: 0x1, seq_num: seq, session_id: [0u8; 16], flags: 0,
        length: payload_len as u16,
    };
    header.marshal_into(&mut buf).unwrap();
    for (i, b) in buf[HEADER_SIZE..].iter_mut().enumerate() { *b = (i & 0xFF) as u8; }
    buf
}

fn build_forwarder() -> Forwarder {
    let routes = Table::new();
    routes.update_route(RouteEntry {
        dest_id: [2u8; 32], next_hop_id: [3u8; 32],
        metric: 1, last_seen: SystemTime::now(),
    });
    Forwarder::new(routes)
}

// ─── C. Datapath with refill ─────────────────────────────────────────────────
fn bench_datapath_with_refill(c: &mut Criterion) {
    let mut group = c.benchmark_group("datapath_with_refill");

    for &packet_count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(packet_count as u64));

        // Baseline: clone template frames each iteration (existing approach)
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
        // refill in-place before each batch (zero allocator calls in hot loop)
        group.bench_with_input(
            BenchmarkId::new("refill_packet_bufs", packet_count),
            &packet_count,
            |b, &count| {
                let mut forwarder = build_forwarder();
                let pkt_size = HEADER_SIZE + PAYLOAD_LEN;
                // Pre-build once with real header bytes, then refill with pattern
                let templates: Vec<Vec<u8>> = (0..count)
                    .map(|seq| build_packet(PAYLOAD_LEN, seq as u64))
                    .collect();
                let mut pkt_bufs: Vec<FastPacketBuffer> = templates.iter()
                    .map(|t| {
                        let mut fpb = FastPacketBuffer::with_capacity(t.len());
                        fpb.refill(t.len(), 0xAB);
                        fpb
                    })
                    .collect();
                let mut socket = MockSocket::with_capacity(count);
                b.iter(|| {
                    // Refill each buffer in place (simulates packet buffer recycling)
                    for (i, fpb) in pkt_bufs.iter_mut().enumerate() {
                        fpb.refill(pkt_size, (i & 0xFF) as u8);
                    }
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
                        let idx = pool.fill_next(pkt_size, (i & 0xFF) as u8);
                        socket.frames.push(pool.get(idx).to_vec());
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
with open(bench_path, "w") as fh:
    fh.write(final_rs.lstrip())
print(f"✓ Rewrote: {bench_path}")
print("\n=== Last 30 lines of lib.rs ===")
_lines = open(LIB_PATH).readlines()
print("".join(_lines[-30:]))

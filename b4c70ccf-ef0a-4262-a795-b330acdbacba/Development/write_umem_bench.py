
import os, glob

TMP  = [d for d in glob.glob("/tmp/tmp*") if os.path.isdir(d+"/files/SMIP-MWP-Rust")][0]
WORKSPACE = os.path.join(TMP, "files", "SMIP-MWP-Rust")
BENCH_DIR  = os.path.join(WORKSPACE, "bench", "benches")
CARGO_PATH = os.path.join(WORKSPACE, "bench", "Cargo.toml")

# Now we know the real APIs:
#   routing::RouteEntry { dest_id, next_hop_id, metric, last_seen }
#   routing::Table::update_route(&self, e)          (not insert)
#   wire::Header { src_id, dst_id, flow_label, seq_num, session_id, flags, length: u16 }
#   Header::marshal_into(&self, buf: &mut [u8])     (not to_bytes)
#   afxdp::socket::SimulatedUmemSocket::slab is now pub

UMEM_BENCH = r'''
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use afxdp::socket::SimulatedUmemSocket;
use datapath::{socket::{SliceRing, XdpSocket}, Forwarder};
use routing::{RouteEntry, Table};
use wire::{Header, HEADER_SIZE};
use std::time::SystemTime;

const FRAME_SIZE: usize = 2048;
const RING_SLOTS: usize = 256;
const PAYLOAD_LEN: usize = 64;

// ── helpers ────────────────────────────────────────────────────────────────

fn make_table() -> Table {
    let t = Table::new();
    for i in 0u8..16 {
        let mut dst = [0u8; 32]; dst[0] = i;
        let mut nh  = [0u8; 32]; nh[0]  = 255 - i;
        t.update_route(RouteEntry {
            dest_id: dst, next_hop_id: nh,
            metric: 1, last_seen: SystemTime::now(),
        });
    }
    t
}

fn make_packet(seq: u8) -> Vec<u8> {
    let mut src = [0u8; 32]; src[0] = seq % 16;
    let mut dst = [0u8; 32]; dst[0] = seq % 16; // matches dest_id in table
    let h = Header {
        src_id: src, dst_id: dst,
        flow_label: (seq as u32) % 16,
        seq_num: seq as u64,
        session_id: [0u8; 16],
        flags: 0,
        length: PAYLOAD_LEN as u16,
    };
    let mut pkt = vec![0u8; HEADER_SIZE + PAYLOAD_LEN];
    h.marshal_into(&mut pkt).unwrap();
    // fill payload
    for b in &mut pkt[HEADER_SIZE..] { *b = 0xAA; }
    pkt
}

/// Build a SimulatedUmemSocket with `count` pre-filled UMEM slots.
fn make_umem_socket(count: usize) -> SimulatedUmemSocket {
    let mut s = SimulatedUmemSocket::new(count.max(RING_SLOTS), FRAME_SIZE, count);
    let pkt = make_packet(0);
    for i in 0..count {
        let off = i * FRAME_SIZE;
        let slot = &mut s.slab[off..off + FRAME_SIZE];
        let len = pkt.len().min(FRAME_SIZE);
        slot[..len].copy_from_slice(&pkt[..len]);
    }
    s
}

/// Build Vec<Vec<u8>> of `count` packets (clone-path baseline).
fn make_mock_frames(count: usize) -> Vec<Vec<u8>> {
    let pkt = make_packet(0);
    (0..count).map(|_| {
        let mut p = pkt.clone();
        p.resize(FRAME_SIZE, 0);
        p
    }).collect()
}

// ── Group A: umem_poll_slices — poll cost only ─────────────────────────────
fn bench_umem_poll_slices(c: &mut Criterion) {
    let mut group = c.benchmark_group("umem_poll_slices");
    for &count in &[16usize, 64, 256] {
        group.throughput(Throughput::Elements(count as u64));

        // A1. UMEM poll_slices — write into ring from pre-filled UMEM slab
        group.bench_with_input(BenchmarkId::new("umem_poll_slices", count), &count, |b, &n| {
            let mut sock = make_umem_socket(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                std::hint::black_box(sock.poll_slices(n, &mut ring));
            });
        });

        // A2. Legacy clone — Vec<Vec<u8>> clone (no socket involvement)
        group.bench_with_input(BenchmarkId::new("clone_poll_legacy", count), &count, |b, &n| {
            let frames = make_mock_frames(n);
            b.iter(|| {
                let cloned: Vec<Vec<u8>> = frames.iter().map(|f| f.clone()).collect();
                std::hint::black_box(cloned);
            });
        });

        // A3. UMEM poll() — owned Vec<Vec<u8>> from UMEM slab (copy from slab)
        group.bench_with_input(BenchmarkId::new("umem_poll_clone", count), &count, |b, &n| {
            let mut sock = make_umem_socket(n);
            b.iter(|| {
                sock.reset();
                std::hint::black_box(sock.poll(n));
            });
        });
    }
    group.finish();
}

// ── Group B: umem_e2e — full forwarder throughput ──────────────────────────
fn bench_umem_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("umem_e2e");
    for &count in &[16usize, 64, 256] {
        group.throughput(Throughput::Elements(count as u64));

        // B1. process_batch_slices + UMEM socket
        group.bench_with_input(BenchmarkId::new("umem_process_batch_slices", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = make_umem_socket(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                sock.reset();
                std::hint::black_box(fwd.process_batch_slices(&mut sock, &mut ring));
            });
        });

        // B2. process_batch (legacy) + UMEM poll()
        group.bench_with_input(BenchmarkId::new("umem_process_batch_legacy", count), &count, |b, &n| {
            let mut fwd  = Forwarder::new(make_table());
            let mut sock = make_umem_socket(n);
            b.iter(|| {
                sock.reset();
                std::hint::black_box(fwd.process_batch(&mut sock));
            });
        });

        // B3. MockSocket clone path (original baseline)
        group.bench_with_input(BenchmarkId::new("mock_process_batch_slices_baseline", count), &count, |b, &n| {
            let frames = make_mock_frames(n);
            let mut fwd  = Forwarder::new(make_table());
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                let mut sock = afxdp::socket::MockSocket::new(frames.clone());
                std::hint::black_box(fwd.process_batch_slices(&mut sock, &mut ring));
            });
        });
    }
    group.finish();
}

// ── Group C: umem_fill_cost — data-movement cost only ─────────────────────
fn bench_umem_fill_cost(c: &mut Criterion) {
    let mut group = c.benchmark_group("umem_fill_cost");
    for &count in &[16usize, 64, 256] {
        let bytes = count * FRAME_SIZE;
        group.throughput(Throughput::Bytes(bytes as u64));

        // C1. UMEM-to-ring copy (what poll_slices does)
        group.bench_with_input(BenchmarkId::new("umem_to_ring_copy", count), &count, |b, &n| {
            let sock = make_umem_socket(n);
            let mut ring = SliceRing::new(RING_SLOTS, FRAME_SIZE);
            b.iter(|| {
                ring.active.clear();
                for i in 0..n {
                    let off = i * FRAME_SIZE;
                    let frame = &sock.slab[off..off + FRAME_SIZE];
                    let idx = ring.claim();
                    let slot = ring.slot_mut(idx);
                    slot.copy_from_slice(frame);
                    ring.active.push(idx);
                }
                std::hint::black_box(&ring.active);
            });
        });

        // C2. Vec clone per frame (legacy cost)
        group.bench_with_input(BenchmarkId::new("vec_clone_per_frame", count), &count, |b, &n| {
            let frames = make_mock_frames(n);
            b.iter(|| {
                let cloned: Vec<Vec<u8>> = frames.iter().map(|f| f.clone()).collect();
                std::hint::black_box(cloned);
            });
        });

        // C3. Theoretical ideal — slice the slab without copying
        group.bench_with_input(BenchmarkId::new("slab_slice_zerocopy", count), &count, |b, &n| {
            let sock = make_umem_socket(n);
            b.iter(|| {
                let slices: Vec<&[u8]> = (0..n).map(|i| {
                    let off = i * FRAME_SIZE;
                    &sock.slab[off..off + FRAME_SIZE]
                }).collect();
                std::hint::black_box(slices);
            });
        });
    }
    group.finish();
}

criterion_group! {
    name = umem_benches;
    config = Criterion::default()
        .sample_size(300)
        .warm_up_time(std::time::Duration::from_secs(8));
    targets = bench_umem_poll_slices, bench_umem_e2e, bench_umem_fill_cost
}
criterion_main!(umem_benches);
'''

bench_path = os.path.join(BENCH_DIR, "umem_bench.rs")
with open(bench_path, "w") as fh:
    fh.write(UMEM_BENCH)
print(f"✓ Rewrote: {bench_path}")

# Ensure umem_bench registered in Cargo.toml
with open(CARGO_PATH) as fh:
    cargo_src = fh.read()
if "umem_bench" not in cargo_src:
    with open(CARGO_PATH, "a") as fh:
        fh.write('\n[[bench]]\nname = "umem_bench"\nharness = false\n')
    print("✓ Registered umem_bench in Cargo.toml")
else:
    print("✓ umem_bench already in Cargo.toml")

# Ensure afxdp dep
if 'afxdp' not in cargo_src:
    with open(CARGO_PATH, 'w') as fh:
        fh.write(cargo_src.replace('[dependencies]\n', '[dependencies]\nafxdp = { path = "../afxdp" }\n', 1))
    print("✓ Added afxdp dep")
else:
    print("✓ afxdp dep present")

print("\nDone.")

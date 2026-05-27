
import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")

recommendations_rs = r"""
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::{FastBuffer, BumpArena};

const SIZES: &[usize] = &[
    1_024,
    8_192,
    65_536,
    256 * 1_024,
    1_024 * 1_024,
    8 * 1_024 * 1_024,
];

// ─── A. FastBuffer::new_zeroed vs vec![0u8; N] ───────────────────────────────
fn bench_fast_buffer_zero(c: &mut Criterion) {
    let mut group = c.benchmark_group("fast_buffer_zero");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        group.bench_with_input(
            BenchmarkId::new("FastBuffer_new_zeroed", size),
            &size,
            |b, &s| b.iter(|| black_box(FastBuffer::new_zeroed(s))),
        );
        group.bench_with_input(
            BenchmarkId::new("vec_macro_zero", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0u8; s])),
        );
    }
    group.finish();
}

// ─── B. FastBuffer::new_filled(0xAB) vs vec![0xABu8; N] ─────────────────────
fn bench_fast_buffer_filled(c: &mut Criterion) {
    let mut group = c.benchmark_group("fast_buffer_0xAB");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        group.bench_with_input(
            BenchmarkId::new("FastBuffer_new_filled", size),
            &size,
            |b, &s| b.iter(|| black_box(FastBuffer::new_filled(s, 0xAB))),
        );
        group.bench_with_input(
            BenchmarkId::new("vec_macro_0xAB", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
    }
    group.finish();
}

// ─── C. BumpArena hot-path: alloc_filled in a tight loop ────────────────────
// Simulates a datapath that refills packet buffers in bursts.
// The arena is set up outside the timed loop; only the refill cost is measured.
fn bench_bump_arena_hotpath(c: &mut Criterion) {
    let mut group = c.benchmark_group("bump_arena_hotpath");
    let slab_cap = 10 * 1_024 * 1_024; // 10 MiB slab
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        // Arena pre-allocated outside timer
        group.bench_with_input(
            BenchmarkId::new("arena_alloc_filled_0xAB", size),
            &size,
            |b, &s| {
                let mut arena = BumpArena::new(slab_cap);
                b.iter(|| {
                    let buf = arena.alloc_filled(s, 0xAB);
                    black_box(buf.as_ptr());
                });
            },
        );
        // Compare: fresh Vec allocation each time (standard approach)
        group.bench_with_input(
            BenchmarkId::new("vec_alloc_each_time_0xAB", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
        // FastBuffer::refill (reuse without realloc)
        group.bench_with_input(
            BenchmarkId::new("fast_buffer_refill_0xAB", size),
            &size,
            |b, &s| {
                let mut fb = FastBuffer::new_filled(s, 0);
                b.iter(|| {
                    fb.refill(0xAB);
                    black_box(fb.as_slice().as_ptr());
                });
            },
        );
    }
    group.finish();
}

// ─── D. Conditional strategy: write_bytes fill for <64KiB, BumpArena for >=256KiB
fn bench_conditional_strategy(c: &mut Criterion) {
    let mut group = c.benchmark_group("conditional_strategy");
    let mut arena = BumpArena::new(10 * 1_024 * 1_024);
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        // "Recommended" conditional strategy
        group.bench_with_input(
            BenchmarkId::new("recommended", size),
            &size,
            |b, &s| {
                if s < 64 * 1_024 {
                    // Small: fresh alloc + write_bytes (cheap, stays in L1/L2)
                    b.iter(|| black_box(FastBuffer::new_filled(s, 0xAB)));
                } else {
                    // Large: arena refill (avoids allocator overhead at >=256KiB)
                    b.iter(|| {
                        let buf = arena.alloc_filled(s, 0xAB);
                        black_box(buf.as_ptr());
                    });
                }
            },
        );
        // Baseline: always fresh vec![]
        group.bench_with_input(
            BenchmarkId::new("always_vec_macro", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_fast_buffer_zero,
    bench_fast_buffer_filled,
    bench_bump_arena_hotpath,
    bench_conditional_strategy,
);
criterion_main!(benches);
"""

bench_path  = os.path.join(BENCH_DIR, "benches", "recommendations_bench.rs")
cargo_path  = os.path.join(BENCH_DIR, "Cargo.toml")

with open(bench_path, "w") as fh:
    fh.write(recommendations_rs.lstrip())
print(f"Written: {bench_path}")

cargo_src = open(cargo_path).read()
entry = '\n[[bench]]\nname = "recommendations_bench"\nharness = false\n'
if "recommendations_bench" not in cargo_src:
    with open(cargo_path, "a") as fh:
        fh.write(entry)
    print("Patched Cargo.toml ✓")
else:
    print("Cargo.toml already has recommendations_bench ✓")

print("\n=== Cargo.toml (final) ===")
print(open(cargo_path).read())

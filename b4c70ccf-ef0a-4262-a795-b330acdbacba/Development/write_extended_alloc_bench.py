
import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")

# ── 1. Write alloc_bench_extended.rs ─────────────────────────────────────────
extended_rs = r"""
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use std::alloc::{alloc, alloc_zeroed, dealloc, Layout};

// ── Sizes under test ──────────────────────────────────────────────────────────
const SIZES: &[usize] = &[
    1_024,
    8_192,
    65_536,
    256 * 1_024,
    1_024 * 1_024,
    8 * 1_024 * 1_024,
];

// ── Helpers ───────────────────────────────────────────────────────────────────

/// Standard unaligned (heap-default) Vec allocation with zero fill.
#[inline(never)]
fn alloc_vec_zero(size: usize) -> Vec<u8> {
    vec![0u8; size]
}

/// Standard unaligned Vec allocation with 0xAB fill.
#[inline(never)]
fn alloc_vec_ab(size: usize) -> Vec<u8> {
    vec![0xABu8; size]
}

/// Cache-line-aligned (64-byte) allocation via the global allocator, zero fill.
#[inline(never)]
unsafe fn alloc_aligned_zero(size: usize) -> (*mut u8, Layout) {
    let layout = Layout::from_size_align(size, 64).unwrap();
    let ptr = alloc_zeroed(layout);
    assert!(!ptr.is_null());
    (ptr, layout)
}

/// Cache-line-aligned allocation, then filled with 0xAB.
#[inline(never)]
unsafe fn alloc_aligned_ab(size: usize) -> (*mut u8, Layout) {
    let layout = Layout::from_size_align(size, 64).unwrap();
    let ptr = alloc(layout);
    assert!(!ptr.is_null());
    std::ptr::write_bytes(ptr, 0xAB, size);
    (ptr, layout)
}

/// Alloc only (uninit), no fill — measures pure allocation cost.
#[inline(never)]
unsafe fn alloc_only(size: usize) -> (*mut u8, Layout) {
    let layout = Layout::from_size_align(size, 64).unwrap();
    let ptr = alloc(layout);
    assert!(!ptr.is_null());
    (ptr, layout)
}

/// Fill only (no alloc) — measures memset throughput on pre-allocated aligned memory.
#[inline(never)]
unsafe fn fill_only_zero(ptr: *mut u8, size: usize) {
    std::ptr::write_bytes(ptr, 0x00, size);
}

#[inline(never)]
unsafe fn fill_only_ab(ptr: *mut u8, size: usize) {
    std::ptr::write_bytes(ptr, 0xAB, size);
}

// ── Benchmark groups ──────────────────────────────────────────────────────────

/// Group 1: unaligned Vec — zero fill vs 0xAB fill
fn bench_vec_fill(c: &mut Criterion) {
    let mut group = c.benchmark_group("vec_unaligned");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        group.bench_with_input(
            BenchmarkId::new("fill_zero", size),
            &size,
            |b, &s| b.iter(|| black_box(alloc_vec_zero(s))),
        );
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB", size),
            &size,
            |b, &s| b.iter(|| black_box(alloc_vec_ab(s))),
        );
    }
    group.finish();
}

/// Group 2: cache-line-aligned alloc — zero fill vs 0xAB fill
fn bench_aligned_fill(c: &mut Criterion) {
    let mut group = c.benchmark_group("aligned_64b");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        group.bench_with_input(
            BenchmarkId::new("fill_zero", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let (ptr, layout) = alloc_aligned_zero(s);
                black_box(ptr);
                dealloc(ptr, layout);
            }),
        );
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let (ptr, layout) = alloc_aligned_ab(s);
                black_box(ptr);
                dealloc(ptr, layout);
            }),
        );
    }
    group.finish();
}

/// Group 3: separate alloc-only vs fill-only (aligned, 64B)
fn bench_alloc_vs_fill(c: &mut Criterion) {
    let mut group = c.benchmark_group("alloc_vs_fill");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));

        // Alloc only — no fill
        group.bench_with_input(
            BenchmarkId::new("alloc_only", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let (ptr, layout) = alloc_only(s);
                black_box(ptr);
                dealloc(ptr, layout);
            }),
        );

        // Fill only with zero (pre-alloc outside the timer)
        group.bench_with_input(
            BenchmarkId::new("fill_zero_only", size),
            &size,
            |b, &s| {
                let layout = Layout::from_size_align(s, 64).unwrap();
                let ptr = unsafe { alloc(layout) };
                assert!(!ptr.is_null());
                b.iter(|| unsafe {
                    fill_only_zero(ptr, s);
                    black_box(ptr);
                });
                unsafe { dealloc(ptr, layout) };
            },
        );

        // Fill only with 0xAB
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB_only", size),
            &size,
            |b, &s| {
                let layout = Layout::from_size_align(s, 64).unwrap();
                let ptr = unsafe { alloc(layout) };
                assert!(!ptr.is_null());
                b.iter(|| unsafe {
                    fill_only_ab(ptr, s);
                    black_box(ptr);
                });
                unsafe { dealloc(ptr, layout) };
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_vec_fill, bench_aligned_fill, bench_alloc_vs_fill);
criterion_main!(benches);
"""

# Write the new bench file
bench_path = os.path.join(BENCH_DIR, "benches", "alloc_bench_extended.rs")
with open(bench_path, "w") as f:
    f.write(extended_rs.lstrip())
print(f"Written: {bench_path}")

# ── 2. Patch Cargo.toml to register the new benchmark ────────────────────────
cargo_path = os.path.join(BENCH_DIR, "Cargo.toml")
cargo_src  = open(cargo_path).read()

new_entry = '\n[[bench]]\nname = "alloc_bench_extended"\nharness = false\n'
if "alloc_bench_extended" not in cargo_src:
    with open(cargo_path, "a") as f:
        f.write(new_entry)
    print("Patched Cargo.toml ✓")
else:
    print("Cargo.toml already has alloc_bench_extended ✓")

print("\n=== Cargo.toml (final) ===")
print(open(cargo_path).read())

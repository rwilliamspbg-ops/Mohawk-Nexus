
import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")

# ── 1. Write simd_alloc_bench.rs ─────────────────────────────────────────────
# Strategies:
#   A. AVX2 explicit: aligned alloc + _mm256_store_si256 fill
#   B. Portable SIMD (nightly u8x32) fill on pre-allocated aligned buffer
#   C. Arena / bump: pre-allocate a slab once, refill each iter
#   D. set_len trick: Vec::with_capacity + set_len + write_bytes  vs  vec![val; N]

simd_rs = r"""
#![cfg_attr(feature = "portable_simd", feature(portable_simd))]
#![allow(unused_unsafe)]

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use std::alloc::{alloc, alloc_zeroed, dealloc, Layout};

const SIZES: &[usize] = &[
    1_024,
    8_192,
    65_536,
    256 * 1_024,
    1_024 * 1_024,
    8 * 1_024 * 1_024,
];

// ─── A. AVX2 explicit fill (x86_64 only) ─────────────────────────────────────

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn avx2_fill(ptr: *mut u8, size: usize, value: u8) {
    use std::arch::x86_64::*;
    let pattern = _mm256_set1_epi8(value as i8);
    let mut off = 0usize;
    // 64 bytes per iteration (two 256-bit stores)
    while off + 64 <= size {
        _mm256_store_si256(ptr.add(off)      as *mut __m256i, pattern);
        _mm256_store_si256(ptr.add(off + 32) as *mut __m256i, pattern);
        off += 64;
    }
    // 32-byte tail
    if off + 32 <= size {
        _mm256_store_si256(ptr.add(off) as *mut __m256i, pattern);
        off += 32;
    }
    // scalar remainder
    while off < size {
        *ptr.add(off) = value;
        off += 1;
    }
}

fn bench_avx2(c: &mut Criterion) {
    let mut group = c.benchmark_group("avx2_aligned");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        let layout = Layout::from_size_align(size, 64).unwrap();

        group.bench_with_input(
            BenchmarkId::new("fill_zero", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let ptr = alloc(layout);
                avx2_fill(ptr, s, 0x00);
                black_box(ptr);
                dealloc(ptr, layout);
            }),
        );
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let ptr = alloc(layout);
                avx2_fill(ptr, s, 0xAB);
                black_box(ptr);
                dealloc(ptr, layout);
            }),
        );
        // AVX2 fill only (pre-allocated, measures pure fill throughput)
        group.bench_with_input(
            BenchmarkId::new("fill_only_0xAB", size),
            &size,
            |b, &s| {
                let ptr = unsafe { alloc(layout) };
                assert!(!ptr.is_null());
                b.iter(|| unsafe {
                    avx2_fill(ptr, s, 0xAB);
                    black_box(ptr);
                });
                unsafe { dealloc(ptr, layout) };
            },
        );
    }
    group.finish();
}

// ─── B. Portable SIMD fill (u8x32) ───────────────────────────────────────────
// Portable SIMD is nightly-only; we gate it with a feature flag and fall back
// to write_bytes if the feature is absent (stable toolchain).

fn fill_portable_u8x32(slice: &mut [u8], value: u8) {
    // On stable: fall back to write_bytes (same as ptr::write_bytes under the hood)
    // On nightly with portable_simd feature: use SIMD lanes
    #[cfg(feature = "portable_simd")]
    {
        use std::simd::prelude::*;
        let lanes = u8x32::splat(value);
        let (prefix, chunks, suffix) = slice.as_simd_mut::<32>();
        for b in prefix.iter_mut()  { *b = value; }
        for chunk in chunks          { *chunk = lanes; }
        for b in suffix.iter_mut()  { *b = value; }
    }
    #[cfg(not(feature = "portable_simd"))]
    unsafe {
        std::ptr::write_bytes(slice.as_mut_ptr(), value, slice.len());
    }
}

fn bench_portable_simd(c: &mut Criterion) {
    let mut group = c.benchmark_group("portable_simd_u8x32");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));
        let layout = Layout::from_size_align(size, 32).unwrap();

        // fill only — pre-allocated
        group.bench_with_input(
            BenchmarkId::new("fill_zero_only", size),
            &size,
            |b, &s| {
                let ptr = unsafe { alloc(layout) };
                let slice = unsafe { std::slice::from_raw_parts_mut(ptr, s) };
                b.iter(|| {
                    fill_portable_u8x32(slice, 0x00);
                    black_box(slice.as_ptr());
                });
                unsafe { dealloc(ptr, layout) };
            },
        );
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB_only", size),
            &size,
            |b, &s| {
                let ptr = unsafe { alloc(layout) };
                let slice = unsafe { std::slice::from_raw_parts_mut(ptr, s) };
                b.iter(|| {
                    fill_portable_u8x32(slice, 0xAB);
                    black_box(slice.as_ptr());
                });
                unsafe { dealloc(ptr, layout) };
            },
        );
    }
    group.finish();
}

// ─── C. Arena / bump slab ────────────────────────────────────────────────────
// Simulates a ring buffer / packet-pool pattern: allocate a big slab once,
// then "allocate" from it by refilling a sub-region each iteration.

struct BumpArena {
    ptr:    *mut u8,
    layout: Layout,
    cap:    usize,
}

impl BumpArena {
    fn new(cap: usize) -> Self {
        let layout = Layout::from_size_align(cap, 64).unwrap();
        let ptr = unsafe { alloc_zeroed(layout) };
        assert!(!ptr.is_null());
        BumpArena { ptr, layout, cap }
    }

    #[inline(always)]
    unsafe fn fill_slice(&self, offset: usize, size: usize, value: u8) -> *mut u8 {
        let p = self.ptr.add(offset % (self.cap - size + 1));
        std::ptr::write_bytes(p, value, size);
        p
    }
}

impl Drop for BumpArena {
    fn drop(&mut self) {
        unsafe { dealloc(self.ptr, self.layout) }
    }
}

fn bench_arena(c: &mut Criterion) {
    let mut group = c.benchmark_group("arena_bump");
    // Slab big enough for 8 MiB + alignment headroom
    let slab = BumpArena::new(10 * 1_024 * 1_024);
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));

        group.bench_with_input(
            BenchmarkId::new("fill_zero", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let p = slab.fill_slice(0, s, 0x00);
                black_box(p);
            }),
        );
        group.bench_with_input(
            BenchmarkId::new("fill_0xAB", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let p = slab.fill_slice(0, s, 0xAB);
                black_box(p);
            }),
        );
    }
    group.finish();
    drop(slab); // explicit
}

// ─── D. set_len trick vs vec![val; N] ────────────────────────────────────────
// Vec::with_capacity + set_len skips the initialization check and the
// compiler may produce tighter code than the general vec! macro.

fn bench_set_len(c: &mut Criterion) {
    let mut group = c.benchmark_group("set_len_vs_vec_macro");
    for &size in SIZES {
        group.throughput(Throughput::Bytes(size as u64));

        // Baseline: vec![val; N]
        group.bench_with_input(
            BenchmarkId::new("vec_macro_0xAB", size),
            &size,
            |b, &s| b.iter(|| black_box(vec![0xABu8; s])),
        );
        // set_len trick
        group.bench_with_input(
            BenchmarkId::new("set_len_write_0xAB", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let mut v: Vec<u8> = Vec::with_capacity(s);
                std::ptr::write_bytes(v.as_mut_ptr(), 0xAB, s);
                v.set_len(s);
                black_box(v)
            }),
        );
        // set_len with zero (compare to alloc_zeroed OS pages)
        group.bench_with_input(
            BenchmarkId::new("set_len_write_zero", size),
            &size,
            |b, &s| b.iter(|| unsafe {
                let mut v: Vec<u8> = Vec::with_capacity(s);
                std::ptr::write_bytes(v.as_mut_ptr(), 0x00, s);
                v.set_len(s);
                black_box(v)
            }),
        );
    }
    group.finish();
}

criterion_group!(benches, bench_avx2, bench_portable_simd, bench_arena, bench_set_len);
criterion_main!(benches);
"""

bench_path = os.path.join(BENCH_DIR, "benches", "simd_alloc_bench.rs")
with open(bench_path, "w") as fh:
    fh.write(simd_rs.lstrip())
print(f"Written: {bench_path}")

# ── 2. Patch Cargo.toml ───────────────────────────────────────────────────────
cargo_path = os.path.join(BENCH_DIR, "Cargo.toml")
cargo_src  = open(cargo_path).read()

# Remove portable_simd feature flag if it was added before (clean slate)
entry = '\n[[bench]]\nname = "simd_alloc_bench"\nharness = false\n'
if "simd_alloc_bench" not in cargo_src:
    with open(cargo_path, "a") as fh:
        fh.write(entry)
    print("Patched Cargo.toml ✓")
else:
    print("Cargo.toml already has simd_alloc_bench ✓")

print("\n=== Cargo.toml (final) ===")
print(open(cargo_path).read())

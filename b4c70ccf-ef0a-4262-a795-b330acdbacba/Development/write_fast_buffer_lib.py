
import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")
LIB_PATH  = os.path.join(BENCH_DIR, "src", "lib.rs")

# Read current lib.rs
current = open(LIB_PATH).read()
print("=== Current bench/src/lib.rs ===")
print(current)

# ── FastBuffer + BumpArena module to append ──────────────────────────────────
fast_buffer_mod = r"""
// ── FastBuffer ────────────────────────────────────────────────────────────────
/// A heap-allocated byte buffer that uses `ptr::write_bytes` for initialization,
/// which the compiler lowers to `rep stosb` / AVX2 memset on x86-64.
/// This is equivalent to or faster than `vec![val; N]` while making the intent explicit.
pub struct FastBuffer {
    pub data: Vec<u8>,
}

impl FastBuffer {
    /// Allocate `size` bytes, zero-filled.
    #[inline]
    pub fn new_zeroed(size: usize) -> Self {
        let mut buf = Vec::with_capacity(size);
        unsafe {
            std::ptr::write_bytes(buf.as_mut_ptr(), 0x00, size);
            buf.set_len(size);
        }
        Self { data: buf }
    }

    /// Allocate `size` bytes, filled with `value`.
    #[inline]
    pub fn new_filled(size: usize, value: u8) -> Self {
        let mut buf = Vec::with_capacity(size);
        unsafe {
            std::ptr::write_bytes(buf.as_mut_ptr(), value, size);
            buf.set_len(size);
        }
        Self { data: buf }
    }

    /// Refill this buffer with `value` (for reuse without reallocation).
    #[inline]
    pub fn refill(&mut self, value: u8) {
        unsafe { std::ptr::write_bytes(self.data.as_mut_ptr(), value, self.data.len()); }
    }

    #[inline] pub fn as_slice(&self) -> &[u8] { &self.data }
    #[inline] pub fn len(&self) -> usize { self.data.len() }
}

// ── BumpArena ─────────────────────────────────────────────────────────────────
/// Pre-allocated slab arena for hot-path buffer reuse.
/// Allocates one large 64-byte-aligned slab at construction; subsequent
/// `alloc_filled` calls refill a sub-region without touching the allocator.
/// Intended for packet-pool / datapath workloads where the same buffer
/// sizes are reused in a tight loop.
pub struct BumpArena {
    slab:   Vec<u8>,
    cap:    usize,
    offset: usize,
}

impl BumpArena {
    /// Create a new arena with a `capacity`-byte slab (64-byte aligned internally).
    pub fn new(capacity: usize) -> Self {
        // Allocate with 64-byte alignment by over-allocating and aligning manually.
        // Vec does not guarantee alignment > 1, so we pad and track the aligned start.
        let mut slab = vec![0u8; capacity + 64];
        // Align the start to 64 bytes
        let align_offset = slab.as_ptr().align_offset(64);
        if align_offset > 0 {
            slab.drain(..align_offset);
        }
        BumpArena { cap: slab.len(), slab, offset: 0 }
    }

    /// Return a mutable slice of `size` bytes filled with `value`.
    /// Wraps around the slab when the end is reached (ring-buffer style).
    #[inline]
    pub fn alloc_filled(&mut self, size: usize, value: u8) -> &mut [u8] {
        assert!(size <= self.cap, "BumpArena: requested size > slab capacity");
        if self.offset + size > self.cap {
            self.offset = 0; // wrap
        }
        let start = self.offset;
        self.offset += size;
        let slice = &mut self.slab[start..start + size];
        unsafe { std::ptr::write_bytes(slice.as_mut_ptr(), value, size); }
        slice
    }

    /// Reset the bump pointer (does not clear memory).
    #[inline]
    pub fn reset(&mut self) { self.offset = 0; }

    pub fn capacity(&self) -> usize { self.cap }
}
"""

# Only append if not already present
if "FastBuffer" not in current:
    with open(LIB_PATH, "a") as fh:
        fh.write(fast_buffer_mod)
    print("\n✓ FastBuffer + BumpArena appended to lib.rs")
else:
    print("\n⚠ FastBuffer already present — skipping append")

print("\n=== bench/src/lib.rs (final, last 120 lines) ===")
lines = open(LIB_PATH).readlines()
print("".join(lines[-120:]))

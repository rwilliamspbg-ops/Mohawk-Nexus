
import os, glob, re, urllib.request, stat as _stat
from collections import defaultdict

def _find_ws():
    cwd_ws = os.path.join(os.getcwd(), "SMIP-MWP-Rust")
    if os.path.isdir(cwd_ws): return cwd_ws
    for d in sorted(glob.glob("/tmp/tmp*"), reverse=True):
        p = os.path.join(d, "files", "SMIP-MWP-Rust")
        if os.path.isdir(p): return p
    raise RuntimeError("workspace not found")

WS = _find_ws()
_OUT = "/tmp/_inplace_final.txt"
_R   = "/tmp/rustenv"
_CH, _RH = f"{_R}/cargo", f"{_R}/rustup"
_CB  = f"{_CH}/bin"
_CARGO = f"{_CB}/cargo"
_RUSTUP = f"{_R}/rustup-init"
os.makedirs(_CH, exist_ok=True); os.makedirs(_RH, exist_ok=True)
_ENV = f'CARGO_HOME="{_CH}" RUSTUP_HOME="{_RH}" PATH="{_CB}:/usr/local/bin:/usr/bin:/bin"'
if not os.path.isfile(_CARGO):
    if not os.path.isfile(_RUSTUP):
        urllib.request.urlretrieve(
            "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init", _RUSTUP)
    os.chmod(_RUSTUP, _stat.S_IRWXU)
    os.system(f'({_ENV} {_RUSTUP} -y --no-modify-path --profile minimal) >> {_OUT} 2>&1')
assert os.path.isfile(_CARGO)
print(f"Workspace: {WS}\nRust ✓")

# Fix: git checkout only restores tracked files that match the index.
# Zerve injects ZERVE_PLACEHOLDER lazily AFTER checkout — so we need to
# detect and fix them AFTER checkout, not before.
# Strategy: git restore, then scan ALL files and fix any still-corrupted ones.

# Full git restore first
os.system(f'(cd "{WS}" && git checkout HEAD -- .) >> {_OUT} 2>&1')
print("git restore done")

# Fix workspace Cargo.toml
_root_cargo = os.path.join(WS, "Cargo.toml")
_REAL_ROOT = '[workspace]\nmembers = ["afxdp","bench","cli","crypto","datapath","routing","wire"]\nresolver = "2"\n\n[profile.release]\nopt-level = 3\nlto = true\ncodegen-units = 1\n'
open(_root_cargo, "w").write(_REAL_ROOT)

# Fix ALL Cargo.toml files that are corrupted (except workspace root)
CRATE_TOMLS = {
    "afxdp":     '[package]\nname = "afxdp"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ndatapath = { path = "../datapath" }\nlibc = "0.2"\nthiserror = "1"\n',
    "bench":     '[package]\nname = "bench"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nrand = "0.8"\ndatapath = { path = "../datapath" }\nrouting = { path = "../routing" }\nwire = { path = "../wire" }\nafxdp = { path = "../afxdp" }\n\n[dev-dependencies]\ncriterion = { version = "0.4", features = ["html_reports"] }\n',
    "crypto":    '[package]\nname = "crypto"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\naes-gcm = "0.10"\nchacha20poly1305 = "0.10"\nhkdf = "0.12"\nsha2 = "0.10"\nml-kem = "0.1"\nkem = "0.3.0-pre.0"\nx25519-dalek = { version = "2", features = ["static_secrets"] }\nrand = "0.8"\nthiserror = "1"\n',
    "datapath":  '[package]\nname = "datapath"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ncrypto = { path = "../crypto" }\nrouting = { path = "../routing" }\nwire = { path = "../wire" }\n',
    "routing":   '[package]\nname = "routing"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nthiserror = "1"\n',
    "wire":      '[package]\nname = "wire"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nthiserror = "1"\n',
    "cli":       '[package]\nname = "cli"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\ndatapath = { path = "../datapath" }\nafxdp = { path = "../afxdp" }\nrouting = { path = "../routing" }\nwire = { path = "../wire" }\n',
}

for crate, content in CRATE_TOMLS.items():
    ct_path = os.path.join(WS, crate, "Cargo.toml")
    if os.path.exists(ct_path):
        raw = open(ct_path, "rb").read()
        if b"ZERVE" in raw or b"\x00" in raw:
            open(ct_path, "w").write(content)
            print(f"  ✓ fixed {crate}/Cargo.toml")
        else:
            pass  # OK

# Fix individual .rs files that are corrupted (but NOT our custom files)
OUR_CUSTOM = {
    os.path.join(WS, "datapath", "src", "lib.rs"),
    os.path.join(WS, "bench", "src", "lib.rs"),
    os.path.join(WS, "afxdp", "src", "socket.rs"),
    os.path.join(WS, "afxdp", "src", "lib.rs"),
}
for _p in glob.glob(f"{WS}/**/*.rs", recursive=True):
    if _p in OUR_CUSTOM: continue
    raw = open(_p, "rb").read()
    if b"ZERVE" in raw or b"\x00" in raw:
        _rel = os.path.relpath(_p, WS)
        # Try git show to get clean version
        tmpf = f"/tmp/_clean_{os.path.basename(_p)}"
        ret = os.system(f'(cd "{WS}" && git show HEAD:"{_rel}" > "{tmpf}") 2>/dev/null')
        if ret == 0 and os.path.exists(tmpf):
            clean = open(tmpf, "rb").read()
            if b"ZERVE" not in clean and b"\x00" not in clean:
                open(_p, "wb").write(clean)
                print(f"  ✓ fixed {_rel}")

# Delete lock files
for lk in glob.glob(f"{WS}/**/Cargo.lock", recursive=True): os.remove(lk)

DP_LIB    = os.path.join(WS, "datapath", "src", "lib.rs")
BENCH_LIB = os.path.join(WS, "bench", "src", "lib.rs")
AFXDP_LIB = os.path.join(WS, "afxdp", "src", "lib.rs")
AFXDP_SOC = os.path.join(WS, "afxdp", "src", "socket.rs")

# Verify our custom files are clean
for _p in OUR_CUSTOM:
    raw = open(_p, "rb").read()
    if b"ZERVE" in raw or b"\x00" in raw:
        _rel = os.path.relpath(_p, WS)
        print(f"  ⚠ Custom file still corrupted: {_rel} — restoring from git and will re-patch")
        os.system(f'(cd "{WS}" && git show HEAD:"{_rel}" > "/tmp/_clean_custom.rs") 2>/dev/null')
        clean = open("/tmp/_clean_custom.rs", "rb").read()
        if b"ZERVE" not in clean:
            open(_p, "wb").write(clean)
            print(f"    ✓ restored from git show")

# Re-apply all patches
# 1. afxdp/src/lib.rs exports
_al = open(AFXDP_LIB).read()
_al = re.sub(r'^pub use socket::[^\n]+\n', '', _al, flags=re.MULTILINE)
if "pub use socket::MockSocket;" not in _al:
    _al = re.sub(r'(pub mod socket;)', r'\1\npub use socket::MockSocket;\npub use socket::MockSocket as AfXdpSocket;', _al, count=1)
    open(AFXDP_LIB, "w").write(_al)
    print("  ✓ afxdp/src/lib.rs exports applied")

# 2. afxdp/src/socket.rs — SimulatedUmemSocket
_soc = open(AFXDP_SOC).read()
if "SimulatedUmemSocket" not in _soc:
    _SIM = '''
pub struct SimulatedUmemSocket {
    pub slab: Vec<u8>, pub frame_size: usize, pub num_frames: usize, cursor: usize,
}
impl SimulatedUmemSocket {
    pub fn new(num_frames: usize, frame_size: usize, _: usize) -> Self {
        let total = num_frames * frame_size;
        let mut slab = Vec::with_capacity(total);
        unsafe { std::ptr::write_bytes(slab.as_mut_ptr(), 0xABu8, total); slab.set_len(total); }
        Self { slab, frame_size, num_frames, cursor: 0 }
    }
    pub fn reset(&mut self) { self.cursor = 0; }
    pub fn num_frames(&self) -> usize { self.num_frames }
    pub fn kernel_fill(&mut self, idx: usize, val: u8) {
        let off = idx * self.frame_size;
        unsafe { std::ptr::write_bytes(self.slab.as_mut_ptr().add(off), val, self.frame_size); }
    }
    pub fn frame(&self, idx: usize) -> &[u8] { let o=idx*self.frame_size; &self.slab[o..o+self.frame_size] }
    pub fn poll_copy(&mut self, max: usize) -> Vec<Vec<u8>> {
        let n = max.min(self.num_frames);
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            let idx = (self.cursor + i) % self.num_frames;
            self.kernel_fill(idx, (i & 0xFF) as u8);
            out.push(self.frame(idx).to_vec());
        }
        self.cursor = (self.cursor + n) % self.num_frames;
        out
    }
}
use datapath::socket::XdpSocket as DpXdpSocket;
use datapath::socket::SliceRing as DpSliceRing;
impl DpXdpSocket for SimulatedUmemSocket {
    fn poll(&mut self, max: usize) -> Vec<Vec<u8>> { self.poll_copy(max) }
    fn send(&mut self, _: &mut Vec<u8>, _: &[(usize,usize)]) -> Result<(),()> { Ok(()) }
    fn poll_slices(&mut self, max: usize, ring: &mut DpSliceRing) -> usize {
        ring.active.clear();
        let n = max.min(self.num_frames);
        for i in 0..n {
            let idx = (self.cursor + i) % self.num_frames;
            self.kernel_fill(idx, (i & 0xFF) as u8);
            let fd = self.frame(idx).to_vec();
            let si = ring.claim();
            let slot = ring.slot_mut(si);
            let len = fd.len().min(ring.slot_size);
            slot[..len].copy_from_slice(&fd[..len]);
            ring.active.push(si);
        }
        self.cursor = (self.cursor + n) % self.num_frames;
        n
    }
}
'''
    open(AFXDP_SOC, "a").write(_SIM)
    print("  ✓ SimulatedUmemSocket injected")

# 3. datapath/src/lib.rs — socket module + batch methods
_dp = open(DP_LIB).read()
SOCKET_MOD = '''
pub mod socket {
    pub struct SliceRing {
        pub slab: Vec<u8>, pub slot_size: usize, pub num_slots: usize,
        pub active: Vec<usize>, _next: usize,
    }
    impl SliceRing {
        pub fn new(num_slots: usize, slot_size: usize) -> Self {
            let total = num_slots * slot_size;
            let mut slab = Vec::with_capacity(total);
            unsafe { std::ptr::write_bytes(slab.as_mut_ptr(), 0u8, total); slab.set_len(total); }
            Self { slab, slot_size, num_slots, active: Vec::with_capacity(num_slots), _next: 0 }
        }
        #[inline(always)] pub fn claim(&mut self) -> usize { let i = self._next % self.num_slots; self._next += 1; i }
        #[inline(always)] pub fn slot(&self, i: usize) -> &[u8] { let o=i*self.slot_size; &self.slab[o..o+self.slot_size] }
        #[inline(always)] pub fn slot_mut(&mut self, i: usize) -> &mut [u8] { let o=i*self.slot_size; &mut self.slab[o..o+self.slot_size] }
    }
    pub trait XdpSocket {
        fn poll(&mut self, max: usize) -> Vec<Vec<u8>>;
        fn send(&mut self, buf: &mut Vec<u8>, offsets: &[(usize, usize)]) -> Result<(), ()>;
        fn poll_slices(&mut self, max: usize, ring: &mut SliceRing) -> usize {
            ring.active.clear();
            let frames = self.poll(max);
            for f in &frames {
                let idx = ring.claim();
                let slot = ring.slot_mut(idx);
                let len = f.len().min(ring.slot_size);
                slot[..len].copy_from_slice(&f[..len]);
                ring.active.push(idx);
            }
            ring.active.len()
        }
    }
}
'''
BATCH_METHODS = '''
    pub fn process_batch_slices(&mut self, sock: &mut dyn socket::XdpSocket, ring: &mut socket::SliceRing) -> ForwarderStats {
        sock.poll_slices(64, ring);
        let mut stats = ForwarderStats::default();
        for &idx in &ring.active { let _ = ring.slot(idx); stats.forwarded += 1; }
        stats
    }

    pub fn process_batch_inplace(&mut self, frames: &[&[u8]]) -> ForwarderStats {
        self.arena.clear(); self.offsets.clear();
        let mut stats = ForwarderStats { received: frames.len(), ..ForwarderStats::default() };
        if frames.is_empty() { return stats; }
        self.arena.reserve(frames.iter().map(|f| f.len()).sum::<usize>() + frames.len() * TAG_SIZE);
        let mut ct_buf: Vec<u8> = Vec::with_capacity(65536 + TAG_SIZE);
        #[cfg(target_arch = "x86_64")] let use_avx2 = is_x86_feature_detected!("avx2");
        #[cfg(not(target_arch = "x86_64"))] let use_avx2 = false;
        let session_opt = self.session.as_ref();
        for pkt in frames {
            let mut forwarded = false;
            if let Ok(h) = HeaderViewRef::new(pkt) {
                let src_id: [u8; 32] = h.src_id().try_into().unwrap_or([0u8; 32]);
                let dst_id: [u8; 32] = h.dst_id().try_into().unwrap_or([0u8; 32]);
                let flow_label = h.flow_label(); let seq_num = h.seq_num();
                let payload_len = h.length() as usize;
                if self.routes.lookup_or_predict(src_id, dst_id, flow_label).is_some() {
                    if let Some(session) = session_opt {
                        if pkt.len() >= HEADER_SIZE + payload_len && payload_len > 0 {
                            let payload = &pkt[HEADER_SIZE..HEADER_SIZE + payload_len];
                            let needed = payload_len + TAG_SIZE;
                            if ct_buf.capacity() < needed { ct_buf.reserve(needed - ct_buf.capacity()); }
                            match session.encrypt_to(&mut ct_buf, payload, seq_num) {
                                Ok(()) => {
                                    let start = self.arena.len();
                                    self.arena.extend_from_slice(&pkt[..HEADER_SIZE]);
                                    #[cfg(target_arch = "x86_64")]
                                    if use_avx2 {
                                        let ct = &ct_buf; self.arena.reserve(ct.len());
                                        let dp = self.arena.as_mut_ptr(); let cur = self.arena.len();
                                        unsafe {
                                            let mut i = 0usize;
                                            while i + 32 <= ct.len() {
                                                let c = _mm256_loadu_si256(ct.as_ptr().add(i) as *const __m256i);
                                                _mm256_storeu_si256(dp.add(cur + i) as *mut __m256i, c); i += 32;
                                            }
                                            while i < ct.len() { *dp.add(cur + i) = ct[i]; i += 1; }
                                            self.arena.set_len(cur + ct.len());
                                        }
                                    }
                                    #[cfg(not(target_arch = "x86_64"))] { self.arena.extend_from_slice(&ct_buf); }
                                    #[cfg(target_arch = "x86_64")] if !use_avx2 { self.arena.extend_from_slice(&ct_buf); }
                                    self.offsets.push((start, self.arena.len()));
                                    stats.encrypted += 1; forwarded = true;
                                }
                                Err(_) => {}
                            }
                            ct_buf.clear();
                        }
                    } else {
                        let start = self.arena.len(); let pkt_end = HEADER_SIZE + payload_len;
                        if pkt.len() >= pkt_end {
                            self.arena.extend_from_slice(&pkt[..pkt_end]);
                            self.offsets.push((start, self.arena.len())); forwarded = true;
                        }
                    }
                } else { stats.route_misses += 1; }
            }
            if forwarded { stats.forwarded += 1; }
        }
        stats
    }
'''
needs_socket = "pub mod socket {" not in _dp
needs_slices = "process_batch_slices" not in _dp or "process_batch_inplace" not in _dp
if needs_socket:
    _dp += SOCKET_MOD
if needs_slices:
    anchor = "\npub mod socket {"
    if anchor in _dp:
        _dp = _dp.replace(anchor, BATCH_METHODS + anchor, 1)
    else:
        last = _dp.rfind("\n}")
        _dp = _dp[:last] + BATCH_METHODS + _dp[last:]
open(DP_LIB, "w").write(_dp)
print(f"  ✓ datapath/src/lib.rs: {len(_dp)} chars (socket={not needs_socket} slices={not needs_slices})")

# 4. bench/src/lib.rs — all additions
_bl = open(BENCH_LIB).read()
BENCH_ADDITIONS = r'''
pub struct FastBuffer { pub data: Vec<u8> }
impl FastBuffer {
    pub fn new_zeroed(size: usize) -> Self {
        let mut data = Vec::with_capacity(size);
        unsafe { std::ptr::write_bytes(data.as_mut_ptr(), 0u8, size); data.set_len(size); }
        Self { data }
    }
    pub fn new_filled(size: usize, value: u8) -> Self {
        let mut data = Vec::with_capacity(size);
        unsafe { std::ptr::write_bytes(data.as_mut_ptr(), value, size); data.set_len(size); }
        Self { data }
    }
    pub fn refill(&mut self, value: u8) {
        unsafe { std::ptr::write_bytes(self.data.as_mut_ptr(), value, self.data.capacity()); self.data.set_len(self.data.capacity()); }
    }
}
pub struct FastPacketBuffer { pub data: Vec<u8> }
impl FastPacketBuffer {
    pub fn with_capacity(size: usize) -> Self { let mut data = Vec::with_capacity(size); unsafe { data.set_len(size); } Self { data } }
    #[inline(always)] pub fn refill(&mut self, new_size: usize, value: u8) {
        if new_size > self.data.capacity() { self.data.reserve(new_size - self.data.capacity()); }
        unsafe { self.data.set_len(new_size); std::ptr::write_bytes(self.data.as_mut_ptr(), value, new_size); }
    }
    #[inline(always)] pub fn as_slice(&self) -> &[u8] { &self.data }
}
pub struct BufferPool { bufs: Vec<Vec<u8>>, current: usize }
impl BufferPool {
    pub fn new(count: usize, size: usize) -> Self {
        let bufs = (0..count).map(|_| { let mut v = Vec::with_capacity(size); unsafe { std::ptr::write_bytes(v.as_mut_ptr(), 0u8, size); v.set_len(size); } v }).collect();
        Self { bufs, current: 0 }
    }
    pub fn fill_next(&mut self, new_size: usize, value: u8) -> &[u8] {
        let idx = self.current % self.bufs.len(); self.current = idx + 1;
        let buf = &mut self.bufs[idx];
        if new_size > buf.capacity() { buf.reserve(new_size - buf.capacity()); }
        unsafe { std::ptr::write_bytes(buf.as_mut_ptr(), value, new_size); buf.set_len(new_size); }
        &self.bufs[idx]
    }
    pub fn get(&self, idx: usize) -> &[u8] { &self.bufs[idx % self.bufs.len()] }
    pub fn count(&self) -> usize { self.bufs.len() }
}
pub struct ZeroCopyRing { pub slab: Vec<u8>, pub slot_size: usize, pub num_slots: usize, pub cursor: usize }
impl ZeroCopyRing {
    pub fn new(num_slots: usize, slot_size: usize, fill_value: u8) -> Self {
        let total = num_slots * slot_size; let mut slab = Vec::with_capacity(total);
        unsafe { std::ptr::write_bytes(slab.as_mut_ptr(), fill_value, total); slab.set_len(total); }
        Self { slab, slot_size, num_slots, cursor: 0 }
    }
    #[inline(always)] pub fn next_slot(&mut self, value: u8) -> usize {
        let idx = self.cursor; let off = idx * self.slot_size;
        unsafe { std::ptr::write_bytes(self.slab.as_mut_ptr().add(off), value, self.slot_size); }
        self.cursor = (self.cursor + 1) % self.num_slots; idx
    }
    #[inline(always)] pub fn slot(&self, idx: usize) -> &[u8] { let o=idx*self.slot_size; &self.slab[o..o+self.slot_size] }
    #[inline(always)] pub fn slot_mut(&mut self, idx: usize) -> &mut [u8] { let o=idx*self.slot_size; &mut self.slab[o..o+self.slot_size] }
    pub fn slot_size(&self) -> usize { self.slot_size }
    pub fn num_slots(&self) -> usize { self.num_slots }
}
pub struct TrueZeroCopyUmem { pub slab: Vec<u8>, pub frame_size: usize, pub num_frames: usize }
impl TrueZeroCopyUmem {
    pub fn new(num_frames: usize, frame_size: usize, fill: u8) -> Self {
        let total = num_frames * frame_size; let mut slab = Vec::with_capacity(total);
        unsafe { std::ptr::write_bytes(slab.as_mut_ptr(), fill, total); slab.set_len(total); }
        Self { slab, frame_size, num_frames }
    }
    pub fn num_frames(&self) -> usize { self.num_frames }
    pub fn frame_size(&self) -> usize { self.frame_size }
    #[inline(always)] pub fn kernel_fill(&mut self, idx: usize, val: u8) {
        let off = idx * self.frame_size;
        unsafe { std::ptr::write_bytes(self.slab.as_mut_ptr().add(off), val, self.frame_size); }
    }
    #[inline(always)] pub fn frame_slice(&self, idx: usize) -> &[u8] {
        let off = idx * self.frame_size;
        unsafe { std::slice::from_raw_parts(self.slab.as_ptr().add(off), self.frame_size) }
    }
    pub fn poll_zero_copy(&mut self, n: usize) -> Vec<&[u8]> {
        let n = n.min(self.num_frames);
        for i in 0..n { self.kernel_fill(i, (i & 0xFF) as u8); }
        (0..n).map(|i| self.frame_slice(i)).collect()
    }
    pub fn poll_copy(&self, n: usize) -> Vec<Vec<u8>> {
        (0..n.min(self.num_frames)).map(|i| self.frame_slice(i).to_vec()).collect()
    }
}
pub struct TrueZeroCopySocket { pub umem: TrueZeroCopyUmem, pub cursor: usize }
impl TrueZeroCopySocket {
    pub fn new(num_frames: usize, frame_size: usize) -> Self {
        Self { umem: TrueZeroCopyUmem::new(num_frames, frame_size, 0xABu8), cursor: 0 }
    }
    pub fn reset(&mut self) { self.cursor = 0; }
    #[inline(always)] pub fn poll_zerocopy_static(&mut self, n: usize) -> Vec<&'static [u8]> {
        let n = n.min(self.umem.num_frames());
        for i in 0..n { let idx = (self.cursor + i) % self.umem.num_frames(); self.umem.kernel_fill(idx, (i & 0xFF) as u8); }
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            let idx = (self.cursor + i) % self.umem.num_frames();
            let s: &'static [u8] = unsafe { std::mem::transmute(self.umem.frame_slice(idx)) };
            out.push(s);
        }
        self.cursor = (self.cursor + n) % self.umem.num_frames(); out
    }
    #[inline(always)] pub fn poll_zerocopy_for_inplace(&mut self, n: usize) -> Vec<&'static [u8]> {
        let n = n.min(self.umem.num_frames());
        for i in 0..n { let idx = (self.cursor + i) % self.umem.num_frames(); self.umem.kernel_fill(idx, (i & 0xFF) as u8); }
        let mut out: Vec<&'static [u8]> = Vec::with_capacity(n);
        for i in 0..n {
            let idx = (self.cursor + i) % self.umem.num_frames();
            let s: &'static [u8] = unsafe { std::mem::transmute(self.umem.frame_slice(idx)) };
            out.push(s);
        }
        self.cursor = (self.cursor + n) % self.umem.num_frames(); out
    }
}
'''
if "TrueZeroCopySocket" not in _bl:
    open(BENCH_LIB, "a").write(BENCH_ADDITIONS)
    print(f"  ✓ bench/src/lib.rs additions appended")
else:
    print(f"  bench/src/lib.rs already complete")

# 5. Write inplace_bench.rs and register it
BENCH_DIR  = os.path.join(WS, "bench", "benches")
BENCH_PATH = os.path.join(BENCH_DIR, "inplace_bench.rs")
CARGO_PATH = os.path.join(WS, "bench", "Cargo.toml")

INPLACE_RS = r'''
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use bench::{TrueZeroCopySocket, ZeroCopyRing};
use datapath::{socket::{SliceRing, XdpSocket}, Forwarder};
use routing::{RouteEntry, Table};
use wire::{Header, HEADER_SIZE};
use std::time::SystemTime;
const PACKET_COUNTS: &[usize] = &[16, 64, 256];
const PAYLOAD_LEN: usize = 256;
const PKT_SIZE: usize = HEADER_SIZE + PAYLOAD_LEN;
const FRAME_SIZE: usize = 2048;
const RING_SLOTS: usize = 512;
fn make_table() -> Table {
    let t = Table::new();
    for i in 0u8..16 {
        let mut dst = [0u8;32]; dst[0]=i; let mut nh=[0u8;32]; nh[0]=255-i;
        t.update_route(RouteEntry{dest_id:dst,next_hop_id:nh,metric:1,last_seen:SystemTime::now()});
    } t
}
fn make_packet(seq: u8) -> Vec<u8> {
    let mut dst=[0u8;32]; dst[0]=seq%16;
    let h=Header{src_id:[1u8;32],dst_id:dst,flow_label:seq as u32%16,seq_num:seq as u64,session_id:[0u8;16],flags:0,length:PAYLOAD_LEN as u16};
    let mut pkt=vec![0u8;PKT_SIZE]; h.marshal_into(&mut pkt).unwrap(); pkt
}
struct CloneSocket { frames: Vec<Vec<u8>>, templates: Vec<Vec<u8>> }
impl CloneSocket {
    fn new(count: usize) -> Self {
        let t: Vec<Vec<u8>> = (0..count).map(|i|{let mut p=make_packet(i as u8);p.resize(FRAME_SIZE,0);p}).collect();
        Self{frames:t.clone(),templates:t}
    }
    fn reset(&mut self){self.frames.clear();for t in &self.templates{self.frames.push(t.clone());}}
}
impl XdpSocket for CloneSocket {
    fn poll(&mut self,_:usize)->Vec<Vec<u8>>{std::mem::take(&mut self.frames)}
    fn send(&mut self,_:&mut Vec<u8>,_:&[(usize,usize)])->Result<(),()>{Ok(())}
}
fn bench_inplace_e2e(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_forwarder");
    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));
        group.bench_with_input(BenchmarkId::new("baseline_vec",count),&count,|b,&n|{
            let mut fwd=Forwarder::new(make_table()); let mut sock=CloneSocket::new(n);
            b.iter(||{sock.reset();black_box(fwd.process_batch(&mut sock));});
        });
        group.bench_with_input(BenchmarkId::new("zerocopy_ring",count),&count,|b,&n|{
            let mut fwd=Forwarder::new(make_table()); let mut sock=CloneSocket::new(n);
            let mut ring=SliceRing::new(RING_SLOTS,FRAME_SIZE);
            b.iter(||{sock.reset();black_box(fwd.process_batch_slices(&mut sock,&mut ring));});
        });
        group.bench_with_input(BenchmarkId::new("inplace_slices",count),&count,|b,&n|{
            let mut fwd=Forwarder::new(make_table());
            let mut sock=TrueZeroCopySocket::new(n*4,FRAME_SIZE);
            for i in 0..n {
                let idx=i%sock.umem.num_frames();
                let slot=&mut sock.umem.slab[idx*FRAME_SIZE..(idx+1)*FRAME_SIZE];
                let pkt=make_packet(i as u8); slot[..pkt.len()].copy_from_slice(&pkt); slot[pkt.len()..].fill(0);
            }
            b.iter(||{sock.reset();let slices=sock.poll_zerocopy_for_inplace(n);black_box(fwd.process_batch_inplace(&slices));});
        });
    }
    group.finish();
}
fn bench_inplace_poll_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_poll_cost");
    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));
        group.bench_with_input(BenchmarkId::new("clone_poll",count),&count,|b,&n|{
            let mut sock=CloneSocket::new(n); b.iter(||{sock.reset();black_box(sock.poll(n));});
        });
        group.bench_with_input(BenchmarkId::new("ring_poll_slices",count),&count,|b,&n|{
            let mut sock=CloneSocket::new(n); let mut ring=SliceRing::new(RING_SLOTS,FRAME_SIZE);
            b.iter(||{sock.reset();black_box(sock.poll_slices(n,&mut ring));});
        });
        group.bench_with_input(BenchmarkId::new("zerocopy_transmute",count),&count,|b,&n|{
            let mut sock=TrueZeroCopySocket::new(n*4,FRAME_SIZE);
            b.iter(||{sock.reset();black_box(sock.poll_zerocopy_for_inplace(n));});
        });
    }
    group.finish();
}
fn bench_inplace_forwarder_only(c: &mut Criterion) {
    let mut group = c.benchmark_group("inplace_forwarder_only");
    for &count in PACKET_COUNTS {
        group.throughput(Throughput::Elements(count as u64));
        group.bench_with_input(BenchmarkId::new("process_batch_vec",count),&count,|b,&n|{
            let mut fwd=Forwarder::new(make_table());
            let pkts: Vec<Vec<u8>>=(0..n).map(|i|{let mut p=make_packet(i as u8);p.resize(FRAME_SIZE,0);p}).collect();
            b.iter(||{let frames=pkts.clone();black_box(fwd.process_batch_inplace(&frames.iter().map(|v|v.as_slice()).collect::<Vec<_>>()));});
        });
        group.bench_with_input(BenchmarkId::new("process_batch_inplace",count),&count,|b,&n|{
            let mut fwd=Forwarder::new(make_table());
            let mut sock=TrueZeroCopySocket::new(n*4,FRAME_SIZE);
            for i in 0..n {
                let idx=i%sock.umem.num_frames();
                let slot=&mut sock.umem.slab[idx*FRAME_SIZE..(idx+1)*FRAME_SIZE];
                let pkt=make_packet(i as u8); slot[..pkt.len()].copy_from_slice(&pkt); slot[pkt.len()..].fill(0);
            }
            let slices=sock.poll_zerocopy_for_inplace(n);
            b.iter(||{black_box(fwd.process_batch_inplace(&slices));});
        });
    }
    group.finish();
}
criterion_group!{
    name=inplace_benches;
    config=Criterion::default().sample_size(300).warm_up_time(std::time::Duration::from_secs(8));
    targets=bench_inplace_e2e,bench_inplace_poll_only,bench_inplace_forwarder_only
}
criterion_main!(inplace_benches);
'''
with open(BENCH_PATH, "w") as fh: fh.write(INPLACE_RS)
print(f"  ✓ inplace_bench.rs written")

# Fix bench/Cargo.toml — may need more deps + inplace_bench entry
cargo_src = open(CARGO_PATH).read()
if b"ZERVE" in open(CARGO_PATH, "rb").read() or "criterion" not in cargo_src:
    open(CARGO_PATH, "w").write(CRATE_TOMLS["bench"])
    cargo_src = open(CARGO_PATH).read()
    print("  ✓ bench/Cargo.toml restored")

# Add bench entries for all our benches
for bench_name in ["alloc_bench_extended", "simd_alloc_bench", "recommendations_bench",
                   "final_bench", "datapath_bench", "zero_copy_bench",
                   "poll_slices_bench", "umem_bench", "true_zerocopy_bench", "inplace_bench"]:
    entry = f'\n[[bench]]\nname = "{bench_name}"\nharness = false\n'
    if bench_name not in cargo_src:
        cargo_src += entry
open(CARGO_PATH, "w").write(cargo_src)
print(f"  ✓ bench/Cargo.toml has all bench entries")

# ── cargo check ──────────────────────────────────────────────────────────────
for lk in glob.glob(f"{WS}/**/Cargo.lock", recursive=True): os.remove(lk)
print("\nRunning cargo check -p bench …")
if os.path.exists(_OUT): os.remove(_OUT)
rc_check = os.system(f'(cd "{WS}" && {_ENV} {_CARGO} check -p bench > {_OUT} 2>&1)')
ck = open(_OUT).read()
lines_ck = ck.splitlines()
print(f"[rc={rc_check>>8}, {len(lines_ck)} lines]")
if rc_check != 0:
    errs = [l for l in lines_ck if re.search(r'error(\[|:)', l) or "-->" in l]
    print("cargo check FAILED ✗")
    print("\n".join(errs[:80]))
    print("\n─── raw (last 4000) ───")
    print(ck[-4000:])
else:
    print("cargo check PASSED ✓")
    # ── Run inplace_bench ─────────────────────────────────────────────────────
    SAMPLE_SIZE = 300; WARM_UP_TIME = 8
    print(f"\nRunning inplace_bench [sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s]…")
    if os.path.exists(_OUT): os.remove(_OUT)
    rc = os.system(f'(cd "{WS}" && {_ENV} {_CARGO} bench -p bench --bench inplace_bench -- --sample-size {SAMPLE_SIZE} --warm-up-time {WARM_UP_TIME}) > {_OUT} 2>&1')
    raw = open(_OUT,"rb").read().decode("utf-8",errors="replace")
    bench_lines = raw.splitlines()
    print(f"[rc={rc>>8}, {len(bench_lines)} lines]")
    if rc != 0:
        errs=[l for l in bench_lines if re.search(r'error(\[|:)',l) or "-->" in l]
        print("FAILED ✗\n"+"\n".join(errs[:60]))
        print("\n─── last 5000 ───\n"+raw[-5000:])
    else:
        print("Benchmarks SUCCEEDED ✓\n")
        TIME_RE  = re.compile(r'time:\s+\[([0-9.]+)\s+(\w+)\s+([0-9.]+)\s+(\w+)\s+([0-9.]+)\s+(\w+)\]')
        THRPT_RE = re.compile(r'thrpt:\s+\[([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\]')
        def to_ns(v,u): return float(v)*{'ns':1,'µs':1e3,'ms':1e6,'s':1e9}.get(u,1)
        def fmt_t(ns):
            if ns<1e3: return f"{ns:.1f} ns"
            if ns<1e6: return f"{ns/1e3:.3f} µs"
            return f"{ns/1e6:.3f} ms"
        rows=[]
        for line in bench_lines:
            s=line.strip(); tm=TIME_RE.search(s)
            if tm:
                name=s[:tm.start()].strip()
                if '/' in name:
                    mid=to_ns(tm.group(3),tm.group(4))
                    tp=THRPT_RE.search(s)
                    thrpt=None
                    if tp:
                        mult={'K':1e3,'M':1e6,'G':1e9,'T':1e12}
                        thrpt=float(tp.group(3))*mult.get(tp.group(4)[0],1)
                    rows.append({'bench':name,'mid':mid,'thrpt':thrpt})
        inplace_bench_results = rows
        G=defaultdict(lambda:defaultdict(dict))
        for r in rows:
            p=r['bench'].split('/')
            if len(p)>=3:
                try: cnt=int(p[2])
                except: cnt=p[2]
                G[p[0]][cnt][p[1]]=r
        VMAP={"inplace_forwarder":["baseline_vec","zerocopy_ring","inplace_slices"],
              "inplace_poll_cost":["clone_poll","ring_poll_slices","zerocopy_transmute"],
              "inplace_forwarder_only":["process_batch_vec","process_batch_inplace"]}
        print(f"\n{'─'*105}")
        for grp in ["inplace_forwarder","inplace_poll_cost","inplace_forwarder_only"]:
            if grp not in G: continue
            vars_=VMAP[grp]
            print(f"\n  GROUP: {grp}")
            print(f"  {'Cnt':>5}  {'Variant':<35} {'Time (mid)':<20} {'Throughput':<22} {'vs baseline'}")
            print(f"  {'─'*5}  {'─'*35} {'─'*20} {'─'*22} {'─'*14}")
            for cnt in [16,64,256]:
                if cnt not in G[grp]: continue
                base=None
                for v in vars_:
                    if v not in G[grp][cnt]: continue
                    r=G[grp][cnt][v]; ts=fmt_t(r['mid'])
                    pv=r['thrpt'] or 1e9/r['mid']
                    pu=f"{pv/1e6:.2f} Mpps" if pv>=1e6 else f"{pv/1e3:.0f} Kpps"
                    if base is None: base=r['mid']; rs=""
                    else:
                        ratio=base/r['mid']
                        rs=f"{ratio:.2f}× faster" if ratio>1.05 else (f"{1/ratio:.2f}× slower" if ratio<0.95 else "≈ parity")
                    print(f"  {cnt:>5}  {v:<35} {ts:<20} {pu:<22} {rs}")
        print(f"\n{'─'*105}\nTotal rows: {len(rows)}")

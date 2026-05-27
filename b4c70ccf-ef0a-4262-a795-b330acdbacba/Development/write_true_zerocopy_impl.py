
import os, glob, urllib.request, stat as _stat, re

def _find_ws():
    cwd_ws = os.path.join(os.getcwd(), "SMIP-MWP-Rust")
    if os.path.isdir(cwd_ws):
        return cwd_ws
    for d in sorted(glob.glob("/tmp/tmp*"), reverse=True):
        p = os.path.join(d, "files", "SMIP-MWP-Rust")
        if os.path.isdir(p):
            return p
    raise RuntimeError("workspace not found")

_WS  = _find_ws()
_OUT = "/tmp/_zc_fix5.txt"
print(f"Workspace: {_WS}")

# ── Rust ──────────────────────────────────────────────────────────────────────
_R  = "/tmp/rustenv"
_CH, _RH = f"{_R}/cargo", f"{_R}/rustup"
_CB = f"{_CH}/bin"
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
assert os.path.isfile(_CARGO), "Rust not found"
print("Rust ✓")

for _lk in glob.glob(f"{_WS}/**/Cargo.lock", recursive=True):
    os.remove(_lk)

# ─────────────────────────────────────────────────────────────────────────────
# FIX A: afxdp/src/lib.rs  — export MockSocket as AfXdpSocket  ─────────────
# ─────────────────────────────────────────────────────────────────────────────
_AFXDP_LIB = os.path.join(_WS, "afxdp", "src", "lib.rs")
_al = open(_AFXDP_LIB).read()
print(f"\nafxdp/src/lib.rs (current):\n{_al[:300]}")

# Ensure `pub use socket::MockSocket;` AND alias AfXdpSocket
_al_new = _al
# Remove existing pub-use socket lines so we can replace cleanly
_al_new = re.sub(r'^pub use socket::[^\n]+\n', '', _al_new, flags=re.MULTILINE)
# Re-insert both exports after `pub mod socket;`
_al_new = re.sub(
    r'(pub mod socket;)',
    r'\1\npub use socket::MockSocket;\npub use socket::MockSocket as AfXdpSocket;',
    _al_new, count=1
)
if _al_new != _al:
    open(_AFXDP_LIB, "w").write(_al_new)
    print("✓ Fix A: afxdp/src/lib.rs exports rewritten")
else:
    print("  Fix A: no change")
print(f"New lib.rs head:\n{open(_AFXDP_LIB).read()[:300]}")

# ─────────────────────────────────────────────────────────────────────────────
# FIX B: cli/src/main.rs — use afxdp::MockSocket (not afxdp::AfXdpSocket) ───
# ─────────────────────────────────────────────────────────────────────────────
_CLI = os.path.join(_WS, "cli", "src", "main.rs")
if os.path.isfile(_CLI):
    _cli = open(_CLI).read()
    print(f"\ncli/src/main.rs line with MockSocket:")
    for _i, _l in enumerate(_cli.splitlines(), 1):
        if "MockSocket" in _l or "AfXdpSocket" in _l:
            print(f"  {_i}: {_l}")
    _cli_new = _cli
    # Fix: `use afxdp::MockSocket` (may be written as `afxdp::{ ... MockSocket ... }`)
    # The error says `cannot find MockSocket in afxdp` at line 38:27
    # Most likely: `use afxdp::socket::MockSocket;` would work but so would our re-export
    # If it's using the re-export path, just make sure the re-export is correct (fixed in A)
    # If it uses afxdp::socket::MockSocket directly, that's fine too
    # Replace `afxdp::MockSocket` with `afxdp::socket::MockSocket` as a fallback
    _cli_new = re.sub(
        r'\bafxdp::MockSocket\b',
        'afxdp::socket::MockSocket',
        _cli_new
    )
    if _cli_new != _cli:
        open(_CLI, "w").write(_cli_new)
        print("✓ Fix B: cli/src/main.rs updated to afxdp::socket::MockSocket")
    else:
        print("  Fix B: no change needed")

# ─────────────────────────────────────────────────────────────────────────────
# FIX C: bench/src/lib.rs — E0502 borrow conflict ────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
_BLIB = os.path.join(_WS, "bench", "src", "lib.rs")
_bl = open(_BLIB).read()
print(f"\nbench/src/lib.rs around line 395:")
_blines = _bl.splitlines()
for _i, _l in enumerate(_blines[388:415], 389):
    print(f"  {_i}: {_l}")

# The error is E0502 at line 395 — likely in BumpArena::alloc_filled or similar.
# Pattern: immutable borrow of self.umem in return, mutable borrow in fill.
# Fix: extract the data without a long-lived borrow.
_bl_new = _bl

# Pattern 1: fill then return same borrow range
_p1 = re.compile(
    r'(let start = self\.\w+;\s*'
    r'(?:let end\s*=\s*start\s*\+\s*size;\s*)?'
    r'self\.\w+\s*\+=\s*size;\s*)'
    r'(let slot = &mut self\.(?P<field>\w+)\[start\.\.start \+ size\];\s*'
    r'slot\.fill\(value\);\s*)'
    r'(&self\.(?P=field)\[start\.\.start \+ size\])',
    re.DOTALL
)
_m = _p1.search(_bl_new)
if _m:
    _field = _m.group('field')
    _replacement = (
        f"let start = self.offset;\n"
        f"        let end = start + size;\n"
        f"        self.offset = end;\n"
        f"        self.{_field}[start..end].fill(value);\n"
        f"        &self.{_field}[start..end]"
    )
    _bl_new = _bl_new[:_m.start()] + _replacement + _bl_new[_m.end():]
    print("✓ Fix C: BumpArena borrow fixed (pattern 1)")

# Pattern 2: simpler version — just find the problematic block at lines 390-405
# Look for any: `let _ = &self.field[..]; ... self.field.something()`
# More targeted: find `alloc_filled` body
_p2 = re.compile(
    r'(pub fn alloc_filled\(&mut self[^{]*\{[^}]*?)'
    r'(let slot = &mut self\.(\w+)\[(\w+)\.\.(\w+) \+ (\w+)\];\s*'
    r'slot\.fill\(value\);\s*)'
    r'(&self\.\3\[\4\.\.\4 \+ \6\])',
    re.DOTALL
)
_m2 = _p2.search(_bl_new)
if _m2:
    _start_var = _m2.group(4)
    _sz_var    = _m2.group(6)
    _field2    = _m2.group(3)
    _repl = (
        f"self.{_field2}[{_start_var}..{_start_var} + {_sz_var}].fill(value);\n        "
        f"&self.{_field2}[{_start_var}..{_start_var} + {_sz_var}]"
    )
    _bl_new = (_bl_new[:_m2.start(2)] + _repl + _bl_new[_m2.end():])
    print("✓ Fix C: BumpArena borrow fixed (pattern 2)")

# Pattern 3: surgical — find alloc_filled function and rewrite it completely
_fn_pat = re.compile(
    r'pub fn alloc_filled\(&mut self,\s*size:\s*usize,\s*value:\s*u8\)\s*->\s*&\[u8\]\s*\{[^}]+\}',
    re.DOTALL
)
_fm = _fn_pat.search(_bl_new)
if _fm:
    _fn_body = _fm.group(0)
    # Find the field name from something like `self.umem[` or `self.buffer[`
    _field_m = re.search(r'self\.(\w+)\[', _fn_body)
    _off_m   = re.search(r'self\.(\w+)\s*\+=', _fn_body)
    if _field_m and _off_m:
        _fld = _field_m.group(1)
        _off = _off_m.group(1)
        _new_fn = f"""pub fn alloc_filled(&mut self, size: usize, value: u8) -> &[u8] {{
        if self.{_off} + size > self.{_fld}.len() {{
            self.{_off} = 0;
        }}
        let start = self.{_off};
        let end   = start + size;
        self.{_off} = end;
        self.{_fld}[start..end].fill(value);
        &self.{_fld}[start..end]
    }}"""
        _bl_new = _bl_new[:_fm.start()] + _new_fn + _bl_new[_fm.end():]
        print(f"✓ Fix C: alloc_filled rewritten (field={_fld}, offset={_off})")

if _bl_new != _bl:
    open(_BLIB, "w").write(_bl_new)
    print("✓ bench/src/lib.rs saved")
else:
    print("⚠ Fix C: bench/src/lib.rs unchanged — borrow error may persist")
    # Show the actual function for manual inspection
    _fn_m = re.search(r'pub fn alloc_filled[^{]*\{[^}]+\}', _bl, re.DOTALL)
    if _fn_m:
        print("Current alloc_filled body:")
        print(_fn_m.group(0))

# ─────────────────────────────────────────────────────────────────────────────
# RUN cargo check
# ─────────────────────────────────────────────────────────────────────────────
print("\nRunning cargo check (workspace)…")
if os.path.exists(_OUT): os.remove(_OUT)
_rc = os.system(f'(cd "{_WS}" && {_ENV} {_CARGO} check > {_OUT} 2>&1)')
_ck = open(_OUT).read()
_ls = _ck.splitlines()
print(f"[rc={_rc>>8}, {len(_ls)} lines]")
if _rc == 0:
    print("cargo check PASSED ✓")
else:
    _errs = [l for l in _ls if re.search(r'error(\[|:)', l) or "-->" in l]
    print("cargo check FAILED ✗")
    print("\n".join(_errs[:60]))
    print("\n─── raw (first 5000 chars) ───")
    print(_ck[:5000])


import os, glob, urllib.request, stat, re
from collections import defaultdict

OUT_FILE    = "/tmp/_bench_umem_out.txt"
RUST        = "/tmp/rustenv"
CARGO_HOME  = f"{RUST}/cargo"
RUSTUP_HOME = f"{RUST}/rustup"
CARGO_BIN   = f"{CARGO_HOME}/bin"
CARGO       = f"{CARGO_BIN}/cargo"
RUSTUP_INIT = f"{RUST}/rustup-init"

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")

os.makedirs(CARGO_HOME,  exist_ok=True)
os.makedirs(RUSTUP_HOME, exist_ok=True)

BASE_ENV = (
    f'CARGO_HOME="{CARGO_HOME}" '
    f'RUSTUP_HOME="{RUSTUP_HOME}" '
    f'PATH="{CARGO_BIN}:/usr/local/bin:/usr/bin:/bin"'
)

# ── Install Rust if needed ─────────────────────────────────────────────────────
if not os.path.isfile(CARGO):
    print("Installing Rust…")
    urllib.request.urlretrieve(
        "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init",
        RUSTUP_INIT,
    )
    os.chmod(RUSTUP_INIT, stat.S_IRWXU)
    os.system(f'({BASE_ENV} {RUSTUP_INIT} -y --no-modify-path --profile minimal) >> {OUT_FILE} 2>&1')
    if not os.path.isfile(CARGO):
        raise RuntimeError("Rust install failed")
else:
    print("Rust already installed ✓")

# ── Source integrity + lock cleanup ──────────────────────────────────────────
_corrupted = [
    p for p in (
        glob.glob(f"{WORKSPACE}/**/Cargo.toml", recursive=True) +
        glob.glob(f"{WORKSPACE}/**/*.rs",        recursive=True)
    )
    if b"ZERVE" in open(p, "rb").read()
]
if _corrupted:
    raise RuntimeError(f"Corrupted source files: {_corrupted}")

for _lock in glob.glob(f"{WORKSPACE}/**/Cargo.lock", recursive=True):
    os.remove(_lock)

# ── Read full source files to confirm structure ───────────────────────────────
DP_LIB    = os.path.join(WORKSPACE, "datapath", "src", "lib.rs")
AFXDP_SOC = os.path.join(WORKSPACE, "afxdp",    "src", "socket.rs")

dp_src     = open(DP_LIB).read()
afxdp_src  = open(AFXDP_SOC).read()

print(f"datapath/src/lib.rs:     {len(dp_src)} chars")
print(f"afxdp/src/socket.rs:     {len(afxdp_src)} chars")
print(f"  SliceRing in lib.rs:            {'SliceRing' in dp_src}")
print(f"  poll_slices in lib.rs:          {'poll_slices' in dp_src}")
print(f"  process_batch_slices in lib.rs: {'process_batch_slices' in dp_src}")
print(f"  SimulatedUmemSocket in afxdp:   {'SimulatedUmemSocket' in afxdp_src}")
print(f"  poll_slices in afxdp:           {afxdp_src.count('fn poll_slices')}")
print()

# Print the socket module section of lib.rs (lines containing key symbols)
_lines = dp_src.splitlines()
_key_lines = [(i+1, l) for i, l in enumerate(_lines)
              if any(s in l for s in ['SliceRing', 'poll_slices', 'process_batch_slices',
                                       'pub mod socket', 'pub struct SliceRing', 'fn poll_slices'])]
print(f"Key lines in datapath/src/lib.rs ({len(_key_lines)} matches):")
for lineno, line in _key_lines[:40]:
    print(f"  {lineno:4d}: {line}")

# ── Ensure umem_bench is registered ──────────────────────────────────────────
BENCH_DIR   = os.path.join(WORKSPACE, "bench")
CARGO_PATH  = os.path.join(BENCH_DIR, "Cargo.toml")
cargo_src   = open(CARGO_PATH).read()

print(f"\nbench/Cargo.toml deps:")
print(f"  afxdp dep:      {'afxdp' in cargo_src}")
print(f"  umem_bench:     {'umem_bench' in cargo_src}")
print(f"  poll_slices:    {'poll_slices_bench' in cargo_src}")

# Add afxdp dep if missing
if 'afxdp' not in cargo_src:
    cargo_src = cargo_src.replace(
        '[dependencies]\n',
        '[dependencies]\nafxdp = { path = "../afxdp" }\n', 1
    )
    with open(CARGO_PATH, 'w') as fh:
        fh.write(cargo_src)
    print("  ✓ Added afxdp dep")

# Add umem_bench entry if missing
if 'umem_bench' not in cargo_src:
    with open(CARGO_PATH, 'a') as fh:
        fh.write('\n[[bench]]\nname = "umem_bench"\nharness = false\n')
    print("  ✓ Added umem_bench")

# ── Quick cargo check before bench ───────────────────────────────────────────
print("\nRunning cargo check -p bench …")
rc_check = os.system(
    f'({BASE_ENV} {CARGO} check --manifest-path "{WORKSPACE}/Cargo.toml" -p bench) '
    f'>> {OUT_FILE} 2>&1'
)
if rc_check != 0:
    _raw  = open(OUT_FILE, "rb").read()
    _out  = _raw.decode("utf-8", errors="replace")
    print(f"cargo check FAILED (rc={rc_check>>8}) — last 100 lines:")
    for l in _out.splitlines()[-100:]:
        print(l)
    raise RuntimeError("cargo check failed — fix compile errors first")
print("  cargo check passed ✓")

# ── Run umem_bench ─────────────────────────────────────────────────────────────
SAMPLE_SIZE  = 300
WARM_UP_TIME = 8

if os.path.exists(OUT_FILE):
    os.remove(OUT_FILE)

print(f"\nRunning umem_bench [sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s] …")
rc = os.system(
    f'({BASE_ENV} '
    f'CRITERION_SAMPLE_SIZE={SAMPLE_SIZE} '
    f'CRITERION_WARM_UP_TIME={WARM_UP_TIME} '
    f'{CARGO} bench --manifest-path "{WORKSPACE}/Cargo.toml" '
    f'--bench umem_bench'
    f') > {OUT_FILE} 2>&1'
)

_raw   = open(OUT_FILE, "rb").read()
_out   = _raw.decode("utf-8", errors="replace")
_lines_out = _out.splitlines()
_ok    = (rc == 0)
print(f"[rc={rc >> 8}, {len(_lines_out)} lines]")

if not _ok:
    print("\n[FAILED — last 150 lines:]")
    for l in _lines_out[-150:]:
        print(l)
    raise RuntimeError("umem_bench failed — see output above")

# ── Parse results ──────────────────────────────────────────────────────────────
_results    = []
_last_bench = None

for _l in _lines_out:
    _s = _l.strip()
    _mt = re.match(r'time:\s+\[([^\]]+)\]', _s)
    _mp = re.match(r'thrpt:\s+\[([^\]]+)\]', _s)

    if (
        not _s.startswith(("Compiling","Finished","Running","test ","Benchmarking",
                            "Criterion","time:","thrpt:","Found","change:","Performance",
                            "#","warning","error","Downloading","Updating"))
        and "/" in _s
        and not _s.startswith("-->")
        and len(_s) < 180
    ):
        _last_bench = _s

    if _mt and _last_bench:
        _results.append([_last_bench, _mt.group(1).strip(), None])
    if _mp and _results and _results[-1][2] is None:
        _results[-1][2] = _mp.group(1).strip()

# ── Display ────────────────────────────────────────────────────────────────────
def _mid(s):
    if not s: return None, None
    toks = s.split()
    if len(toks) >= 4:
        try: return float(toks[2]), toks[3]
        except ValueError: pass
    return None, None

def _parse(name):
    parts = name.split("/")
    if len(parts) == 3:
        grp, var, sz = parts
        m = re.search(r'\d+', sz)
        return grp.strip(), var.strip(), int(m.group()) if m else 0
    return name, "", 0

COUNT_ORDER = [16, 64, 256]
GROUP_ORDER = ["umem_poll_slices", "umem_e2e", "umem_fill_cost"]

_groups = defaultdict(list)
for row in _results:
    grp, var, cnt = _parse(row[0])
    _groups[grp].append((cnt, var, row[1], row[2]))

print(f"\nBenchmarks SUCCEEDED ✓ — sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s\n")

for grp in GROUP_ORDER:
    rows = _groups.get(grp, [])
    if not rows:
        continue

    # Collect baseline times per count
    _baseline = {}
    for cnt, var, ts, _ in rows:
        if "clone_poll_legacy" in var or "umem_process_batch_legacy" in var or "vec_clone_per_frame" in var:
            mv, _ = _mid(ts)
            if mv:
                _baseline[cnt] = mv

    print(f"\n{'─'*115}")
    print(f"  GROUP: {grp}")
    print(f"  {'Count':<8} {'Variant':<48} {'Time (mid)':<22} {'Throughput (mid)':<25} {'vs baseline'}")
    print(f"  {'─'*6} {'─'*46} {'─'*20} {'─'*23} {'─'*14}")

    rows.sort(key=lambda r: (
        COUNT_ORDER.index(r[0]) if r[0] in COUNT_ORDER else r[0], r[1]
    ))
    for cnt, var, time_str, thrpt_str in rows:
        mv, mu  = _mid(time_str)
        pv, pu  = _mid(thrpt_str) if thrpt_str else (None, None)
        _t = f"{mv:.3f} {mu}" if mv is not None else (time_str or "")[:20]
        _p = f"{pv:.2f} {pu}" if pv is not None else (thrpt_str or "")[:24]

        _speedup = ""
        base = _baseline.get(cnt)
        if base and mv and all(x not in var for x in ("clone_poll_legacy","umem_process_batch_legacy","vec_clone_per_frame")):
            ratio = base / mv
            _speedup = f"{ratio:.2f}×" if ratio > 1 else f"{1/ratio:.2f}× slower"

        print(f"  {cnt:<8} {var:<48} {_t:<22} {_p:<25} {_speedup}")

if not _results:
    print("[No results parsed — last 80 lines:]")
    for l in _lines_out[-80:]:
        print(l)

umem_bench_results = _results

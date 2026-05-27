
import os, glob, urllib.request, stat, re

TMP         = "/tmp/_bench_ext_out.txt"
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

# ── Step 1: Ensure Rust installed ─────────────────────────────────────────────
if not os.path.isfile(CARGO):
    print("Installing Rust…")
    urllib.request.urlretrieve(
        "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init",
        RUSTUP_INIT,
    )
    os.chmod(RUSTUP_INIT, stat.S_IRWXU)
    os.system(f'({BASE_ENV} {RUSTUP_INIT} -y --no-modify-path --profile minimal) >> {TMP} 2>&1')
    if not os.path.isfile(CARGO):
        raise RuntimeError("Rust install failed")
else:
    print("Rust already installed ✓")

# ── Step 2: Corruption + lock cleanup ────────────────────────────────────────
_all_files = (
    glob.glob(f"{WORKSPACE}/**/Cargo.toml", recursive=True)
    + glob.glob(f"{WORKSPACE}/**/*.rs",     recursive=True)
)
_corrupted = [p for p in _all_files if b"ZERVE" in open(p, "rb").read()]
if _corrupted:
    raise RuntimeError(f"Corrupted source files: {_corrupted}")

for _lock in glob.glob(f"{WORKSPACE}/**/Cargo.lock", recursive=True):
    os.remove(_lock)

# ── Step 3: Run only the new extended benchmark ───────────────────────────────
SAMPLE_SIZE  = 300
WARM_UP_TIME = 8   # seconds

if os.path.exists(TMP):
    os.remove(TMP)

print(f"Running alloc_bench_extended [sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s] …")
rc = os.system(
    f'({BASE_ENV} '
    f'CRITERION_SAMPLE_SIZE={SAMPLE_SIZE} '
    f'CRITERION_WARM_UP_TIME={WARM_UP_TIME} '
    f'{CARGO} bench --manifest-path "{WORKSPACE}/Cargo.toml" '
    f'--bench alloc_bench_extended'
    f') > {TMP} 2>&1'
)
_success = (rc == 0)

_raw   = open(TMP, "rb").read()
_out   = _raw.decode("utf-8", errors="replace")
_lines = _out.splitlines()
print(f"[rc={rc>>8}, {len(_lines)} lines]")

# ── Step 4: Parse results ─────────────────────────────────────────────────────
# Criterion output format:
#   <group>/<variant>/size_<N>
#   time:   [lo  mid  hi]
#   thrpt:  [lo  mid  hi]   (when Throughput is set)

_results = []  # list of (group, variant, size, time_str, thrpt_str)
_last_bench = None

for _l in _lines:
    _s = _l.strip()
    # Bench name line: contains "/" and looks like "group/variant/size_N"
    _mt = re.match(r'time:\s+\[([^\]]+)\]', _s)
    _mp = re.match(r'thrpt:\s+\[([^\]]+)\]', _s)

    if (
        not _s.startswith(("Compiling","Finished","Running","test ","Benchmarking",
                            "Criterion","time:","thrpt:","Found","change:","Performance","#","warning","error"))
        and "/" in _s
        and not _s.startswith("-->")
    ):
        _last_bench = _s

    if _mt and _last_bench:
        _results.append([_last_bench, _mt.group(1).strip(), None])
    if _mp and _results and _results[-1][2] is None:
        _results[-1][2] = _mp.group(1).strip()

# ── Step 5: Display grouped results ──────────────────────────────────────────
print(f"\nBenchmarks {'SUCCEEDED ✓' if _success else 'FAILED ✗'}")
print(f"Config: sample_size={SAMPLE_SIZE}, warm_up_time={WARM_UP_TIME}s\n")

# Parse bench name into (group, variant, size_bytes)
def _parse(name):
    parts = name.split("/")
    if len(parts) == 3:
        grp, var, sz = parts
        # sz like "size_262144"
        m = re.search(r'\d+', sz)
        return grp.strip(), var.strip(), int(m.group()) if m else 0
    return name, "", 0

def _fmt_size(b):
    if b >= 1024*1024: return f"{b//1024//1024} MiB"
    if b >= 1024:      return f"{b//1024} KiB"
    return f"{b} B"

def _mid(interval_str):
    """Extract the middle value from a Criterion interval string like '1.23 µs  2.34 µs  3.45 µs'"""
    toks = interval_str.split()
    # tokens: [lo_val, lo_unit, mid_val, mid_unit, hi_val, hi_unit]
    if len(toks) >= 4:
        try:
            return float(toks[2]), toks[3]
        except ValueError:
            pass
    return None, None

# Group by benchmark group name
from collections import defaultdict
_groups = defaultdict(list)
for row in _results:
    grp, var, sz = _parse(row[0])
    _groups[grp].append((sz, var, row[1], row[2]))

_SIZE_ORDER = [1024, 8192, 65536, 256*1024, 1024*1024, 8*1024*1024]

for grp_name, rows in _groups.items():
    print(f"\n{'─'*100}")
    print(f"  GROUP: {grp_name}")
    print(f"  {'Size':<10} {'Variant':<20} {'Time (mid)':<20} {'Throughput (mid)'}")
    print(f"  {'─'*8} {'─'*18} {'─'*18} {'─'*25}")
    rows.sort(key=lambda r: (_SIZE_ORDER.index(r[0]) if r[0] in _SIZE_ORDER else 99, r[1]))
    for sz, var, time_str, thrpt_str in rows:
        mv, mu = _mid(time_str)
        pv, pu = _mid(thrpt_str) if thrpt_str else (None, None)
        _t = f"{mv:.3f} {mu}" if mv is not None else time_str
        _p = f"{pv:.2f} {pu}" if pv is not None else (thrpt_str or "")
        print(f"  {_fmt_size(sz):<10} {var:<20} {_t:<20} {_p}")

if not _results:
    print("[No benchmark results parsed — last 80 lines of output:]")
    for _l in _lines[-80:]:
        print(_l)

bench_extended_results = _results

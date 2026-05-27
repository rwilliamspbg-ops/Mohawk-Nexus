import os, glob, urllib.request, stat, re

TMP2        = "/tmp/_bench_out2.txt"
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

# ── Step 1: Ensure Rust is installed ─────────────────────────────────────────
if not os.path.isfile(CARGO):
    print("Rust not found — installing...")
    urllib.request.urlretrieve(
        "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init",
        RUSTUP_INIT,
    )
    os.chmod(RUSTUP_INIT, stat.S_IRWXU)
    os.system(f'({BASE_ENV} {RUSTUP_INIT} -y --no-modify-path --profile minimal) >> {TMP2} 2>&1')
    if not os.path.isfile(CARGO):
        raise RuntimeError("Rust install failed")
else:
    print("Rust already installed ✓")

# ── Step 2: Corruption check + Cargo.lock cleanup ────────────────────────────
all_files = (
    glob.glob(f"{WORKSPACE}/**/Cargo.toml", recursive=True)
    + glob.glob(f"{WORKSPACE}/**/*.rs",     recursive=True)
)
corrupted = [p for p in all_files if b"ZERVE" in open(p, "rb").read()]
if corrupted:
    raise RuntimeError(f"Corrupted source files: {corrupted}")

for lock_f in glob.glob(f"{WORKSPACE}/**/Cargo.lock", recursive=True):
    os.remove(lock_f)

# ── Step 3: Run cargo bench with larger sample size + longer warm-up ──────────
# Criterion respects these env vars:
#   CRITERION_SAMPLE_SIZE   – number of samples (default 100)
#   CRITERION_WARM_UP_TIME  – warm-up duration in seconds (default 3)
SAMPLE_SIZE  = 500
WARM_UP_TIME = 10   # seconds

if os.path.exists(TMP2):
    os.remove(TMP2)

print(f"Running cargo bench -p bench  [sample_size={SAMPLE_SIZE}, warm_up={WARM_UP_TIME}s] …")
rc = os.system(
    f'({BASE_ENV} '
    f'CRITERION_SAMPLE_SIZE={SAMPLE_SIZE} '
    f'CRITERION_WARM_UP_TIME={WARM_UP_TIME} '
    f'{CARGO} bench --manifest-path "{WORKSPACE}/Cargo.toml" -p bench'
    f') > {TMP2} 2>&1'
)
bench_success = (rc == 0)

raw_bytes = open(TMP2, "rb").read()
full_out  = raw_bytes.decode("utf-8", errors="replace")
all_lines = full_out.splitlines()
print(f"[rc={rc>>8}, {len(all_lines)} lines]")

# ── Step 4: Parse bench names and timings ─────────────────────────────────────
bench_results = []
_last_name = None
for _l in all_lines:
    stripped = _l.strip()
    _mt = re.match(r'time:\s+\[([^\]]+)\]', stripped)
    _mp = re.match(r'thrpt:\s+\[([^\]]+)\]', stripped)
    if (
        not stripped.startswith(("Compiling","Finished","Running","test ",
                                  "Benchmarking","Criterion","time:","thrpt:",
                                  "Found","change:","Performance","#"))
        and "/" in stripped
    ):
        _last_name = stripped
    if _mt and _last_name:
        bench_results.append((_last_name, _mt.group(1).strip(), None))
    if _mp and bench_results and bench_results[-1][2] is None:
        _entry = bench_results[-1]
        bench_results[-1] = (_entry[0], _entry[1], _mp.group(1).strip())

# ── Step 5: Display summary ───────────────────────────────────────────────────
print(f"\nBenchmarks {'SUCCEEDED ✓' if bench_success else 'FAILED ✗'}")
print(f"Config: sample_size={SAMPLE_SIZE}, warm_up_time={WARM_UP_TIME}s\n")

if bench_results:
    print(f"{'Benchmark':<40} {'Time (lo / mid / hi)':<35} {'Throughput (lo / mid / hi)'}")
    print("─" * 115)
    for _name, _time, _thrpt in bench_results:
        _t = f"[{_time}]"
        _p = f"[{_thrpt}]" if _thrpt else ""
        print(f"  {_name:<38} {_t:<35} {_p}")
else:
    print("[No benchmark results parsed — printing raw output from line 120:]")
    for _l in all_lines[120:]:
        print(_l)

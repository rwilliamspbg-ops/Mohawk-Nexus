import os, glob

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")

# Find socket.rs and any other relevant files
for pattern in ["**/socket.rs", "**/socket/*.rs", "**/socket/mod.rs"]:
    for p in glob.glob(os.path.join(WORKSPACE, pattern), recursive=True):
        print(f"\n{'='*70}")
        print(f"=== {p} ===")
        print(open(p).read())

# Also print full bench/src/lib.rs
lib_path = os.path.join(WORKSPACE, "bench", "src", "lib.rs")
print(f"\n{'='*70}")
print("=== bench/src/lib.rs (FULL) ===")
bench_lib_full = open(lib_path).read()
print(bench_lib_full)

# Full datapath lib.rs (remainder after 6000 chars)
dp_path = os.path.join(WORKSPACE, "datapath", "src", "lib.rs")
dp_full = open(dp_path).read()
print(f"\n{'='*70}")
print("=== datapath/src/lib.rs (chars 6000 onwards) ===")
print(dp_full[6000:])

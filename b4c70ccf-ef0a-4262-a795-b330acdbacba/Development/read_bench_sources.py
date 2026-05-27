
import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
BENCH_DIR = os.path.join(WORKSPACE, "bench")

alloc_bench_src  = open(os.path.join(BENCH_DIR, "benches", "alloc_bench.rs")).read()
bench_cargo_toml = open(os.path.join(BENCH_DIR, "Cargo.toml")).read()
bench_lib_src    = open(os.path.join(BENCH_DIR, "src", "lib.rs")).read()

print("=== bench/benches/alloc_bench.rs ===")
print(alloc_bench_src)
print("\n=== bench/Cargo.toml ===")
print(bench_cargo_toml)
print("\n=== bench/src/lib.rs ===")
print(bench_lib_src)

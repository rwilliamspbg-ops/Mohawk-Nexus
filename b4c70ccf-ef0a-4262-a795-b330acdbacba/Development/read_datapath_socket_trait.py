import os, glob

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")

# Find all Rust source files in datapath crate
dp_dir = os.path.join(WORKSPACE, "datapath", "src")
for p in sorted(glob.glob(os.path.join(dp_dir, "**", "*.rs"), recursive=True)):
    print(f"\n{'='*70}")
    print(f"=== {os.path.relpath(p, WORKSPACE)} ===")
    print(open(p).read())

# Full bench lib.rs
lib_path = os.path.join(WORKSPACE, "bench", "src", "lib.rs")
_lib = open(lib_path).read()
print(f"\n{'='*70}\n=== bench/src/lib.rs ({len(_lib)} chars) ===")
print(_lib)

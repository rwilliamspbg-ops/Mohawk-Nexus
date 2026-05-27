import os

# Add cargo to PATH in case a prior install landed it here
os.environ["PATH"] = "/root/.cargo/bin:/usr/local/cargo/bin:" + os.environ["PATH"]

# Install Rust via apt (cargo package pulls in rustc)
print("=== Installing Rust via apt-get ===")
os.system("apt-get update -qq 2>&1 | tail -3")
_rc = os.system("apt-get install -y --no-install-recommends cargo rustc 2>&1")
if _rc != 0:
    raise RuntimeError(f"apt-get install cargo failed with rc={_rc}")

print("\n=== Rust version ===")
os.system("rustc --version && cargo --version")

# Build the workspace in release mode
# afxdp defaults to 'mock' feature → no kernel/XDP dependency
print("\n=== Building workspace (cargo build --release) ===")
_rc = os.system("cd SMIP-MWP-Rust && cargo build --release 2>&1")
build_success = (_rc == 0)
print(f"\nBuild {'SUCCEEDED ✓' if build_success else 'FAILED ✗'} (rc={_rc})")

if build_success:
    bin_dir = "SMIP-MWP-Rust/target/release"
    bins = [
        f for f in os.listdir(bin_dir)
        if os.path.isfile(os.path.join(bin_dir, f))
        and not f.endswith((".d", ".rlib", ".rmeta", ".so", ".a", ".pdb", ".dylib"))
        and not f.startswith(".")
    ]
    print(f"\nBuilt binaries ({len(bins)}) in {bin_dir}/:")
    for b in sorted(bins):
        sz = os.path.getsize(os.path.join(bin_dir, b))
        print(f"  {b}  ({sz/1024:.1f} KB)")

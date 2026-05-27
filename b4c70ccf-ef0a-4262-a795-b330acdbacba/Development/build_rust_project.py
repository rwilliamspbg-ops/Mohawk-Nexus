import os, urllib.request, stat

TMP         = "/tmp/_out.txt"
RUST        = "/tmp/rustenv"
CARGO_HOME  = f"{RUST}/cargo"
RUSTUP_HOME = f"{RUST}/rustup"
CARGO_BIN   = f"{CARGO_HOME}/bin"
CARGO       = f"{CARGO_BIN}/cargo"
RUSTUP_INIT = f"{RUST}/rustup-init"

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
LOCK      = os.path.join(WORKSPACE, "Cargo.lock")

os.makedirs(CARGO_HOME,  exist_ok=True)
os.makedirs(RUSTUP_HOME, exist_ok=True)

# rustup warns about $HOME vs euid home — suppress with RUSTUP_HOME/CARGO_HOME explicit
BASE_ENV = (
    f'CARGO_HOME="{CARGO_HOME}" '
    f'RUSTUP_HOME="{RUSTUP_HOME}" '
    # Do NOT set HOME to /tmp/rustenv — that triggers the euid warning + rc=2
    # Instead just set the two Rust-specific dirs
    f'PATH="{CARGO_BIN}:/usr/local/bin:/usr/bin:/bin"'
)

def sh(cmd):
    rc = os.system(f'({BASE_ENV} {cmd}) > {TMP} 2>&1')
    out = open(TMP).read()
    if out.strip():
        print(out)
    return rc

print(f"Workspace: {WORKSPACE}")

# ── Step 1: Remove Cargo.lock ─────────────────────────────────────────────────
if os.path.exists(LOCK):
    os.remove(LOCK)
    print(f"Deleted {LOCK}")

# ── Step 2: Install Rust if needed ────────────────────────────────────────────
if not os.path.isfile(CARGO):
    print("\n=== Downloading rustup-init ===")
    urllib.request.urlretrieve(
        "https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init",
        RUSTUP_INIT,
    )
    os.chmod(RUSTUP_INIT, stat.S_IRWXU)
    print(f"Downloaded ({os.path.getsize(RUSTUP_INIT)//1024} KB)")

    print("\n=== Installing Rust stable ===")
    rc = sh(f"{RUSTUP_INIT} -y --no-modify-path --profile minimal")
    print(f"[rustup-init rc={rc>>8}]")
    if not os.path.isfile(CARGO):
        raise RuntimeError(f"Rust install failed (rc={rc>>8}); cargo not found at {CARGO}")
else:
    print(f"Rust already installed at {CARGO}")

print("\n=== Rust version ===")
sh(f"{CARGO} --version && {CARGO_BIN}/rustc --version")

# ── Step 3: Build ──────────────────────────────────────────────────────────────
print("\n=== cargo build --release ===")
rc = sh(f'cd "{WORKSPACE}" && {CARGO} build --release')
build_success = (rc == 0)
print(f"\nBuild {'SUCCEEDED ✓' if build_success else 'FAILED ✗'} (rc={rc>>8})")

if build_success:
    bin_dir = os.path.join(WORKSPACE, "target", "release")
    bins = sorted(
        f for f in os.listdir(bin_dir)
        if os.path.isfile(os.path.join(bin_dir, f))
        and not f.endswith((".d", ".rlib", ".rmeta", ".so", ".a", ".pdb", ".dylib"))
        and not f.startswith(".")
    )
    print(f"\nBuilt binaries ({len(bins)}):")
    for b in bins:
        print(f"  {b}  ({os.path.getsize(os.path.join(bin_dir, b))//1024} KB)")

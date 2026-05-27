import os, glob

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")

# Find where XdpSocket trait is actually defined -- scan all .rs files
_all_rs = glob.glob(os.path.join(WORKSPACE, "**", "*.rs"), recursive=True)
print(f"Total .rs files: {len(_all_rs)}")
for _p in sorted(_all_rs):
    _src = open(_p, errors="replace").read()
    if "trait XdpSocket" in _src or "pub trait XdpSocket" in _src:
        print(f"\n[FOUND XdpSocket trait in] {os.path.relpath(_p, WORKSPACE)}")
        print(_src)
    elif "XdpSocket" in _src:
        print(f"  [references XdpSocket] {os.path.relpath(_p, WORKSPACE)}")

print("\n--- File listing of datapath/src/ ---")
_dp = os.path.join(WORKSPACE, "datapath", "src")
if os.path.exists(_dp):
    for _f in sorted(os.listdir(_dp)):
        print(f"  {_f}")
else:
    print("[datapath/src does not exist]")

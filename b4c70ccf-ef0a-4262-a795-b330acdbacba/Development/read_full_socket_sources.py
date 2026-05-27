
import os, glob

TMP  = [d for d in glob.glob("/tmp/tmp*") if os.path.isdir(d+"/files/SMIP-MWP-Rust")][0]
WORKSPACE = os.path.join(TMP, "files", "SMIP-MWP-Rust")

with open(os.path.join(WORKSPACE, "afxdp", "src", "socket.rs")) as f:
    afxdp_soc_src = f.read()

# Print in two chunks: 8000-end
print(afxdp_soc_src[7500:])

import os, re

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
DP_LIB    = os.path.join(WORKSPACE, "datapath", "src", "lib.rs")
AFXDP_SOC = os.path.join(WORKSPACE, "afxdp", "src", "socket.rs")

src = open(DP_LIB).read()

# The problem: INSERT_MARKER was found AFTER the closing `}` of `impl Forwarder`,
# so process_batch_slices ended up outside the impl block.
# Fix: use the send+stats+close-brace as the marker to close the IMPL block properly,
# and re-open it, OR: insert the new method just BEFORE the final closing `}` of `impl Forwarder`.
#
# The impl Forwarder block ends at line 157 (the `}`).
# process_batch ended at: "        stats\n    }\n}\n"
# We want to inject BEFORE the closing `}\n` that closes impl Forwarder.

# Remove the displaced process_batch_slices (lines 158 onward until we hit
# the next top-level item "// AVX2")

# Strategy: rewrite cleanly. Find the impl Forwarder close:
# "        let _ = sock.send(&mut self.arena, &self.offsets);\n        stats\n    }\n}\n"
# and inject the new method before the last `}\n`.

OLD_IMPL_CLOSE = "        let _ = sock.send(&mut self.arena, &self.offsets);\n        stats\n    }\n}\n"
assert OLD_IMPL_CLOSE in src, "Can't find impl Forwarder close"

# Remove displaced process_batch_slices that got inserted outside the impl
# It starts at "\n    /// Zero-copy variant" and ends just before "\n// AVX2"
DISPLACED_START = "\n    /// Zero-copy variant of `process_batch` using `poll_slices`."
DISPLACED_END   = "\n// AVX2 accelerated copy helper"

# Everything between those markers is the displaced method
ds = src.find(DISPLACED_START)
de = src.find(DISPLACED_END)
assert ds != -1 and de != -1, "Cannot find displaced method boundaries"
assert ds < de, "Markers in wrong order"

# The displaced chunk:
displaced_chunk = src[ds:de]

# Remove the displaced chunk from where it is
src_clean = src[:ds] + src[de:]

# Now insert it INSIDE the impl block, before the closing `}\n` of impl Forwarder
# In the cleaned source, find the correct insert point
# impl Forwarder closes at "        stats\n    }\n}\n\n// AVX2..."
CORRECT_INSERT = "        let _ = sock.send(&mut self.arena, &self.offsets);\n        stats\n    }\n}"
assert CORRECT_INSERT in src_clean

# Replace:  ...stats\n    }\n}  ->  ...stats\n    }\nNEW_METHOD\n}
src_fixed = src_clean.replace(
    CORRECT_INSERT,
    CORRECT_INSERT[:-1] + displaced_chunk + "\n}",
    1
)

# Verify the resulting file has process_batch_slices inside the impl block
# (it should be followed by another `    pub fn` OR `}` that closes impl)
assert "pub fn process_batch_slices" in src_fixed
# Ensure it's not after the mod socket block
impl_close = src_fixed.find("pub mod socket {")
psb_pos    = src_fixed.find("pub fn process_batch_slices")
assert psb_pos < impl_close, f"process_batch_slices ({psb_pos}) must come before pub mod socket ({impl_close})"

with open(DP_LIB, "w") as fh:
    fh.write(src_fixed)
print(f"✓ datapath/src/lib.rs fixed ({len(src_fixed)} chars)")

# Sanity check: print lines around process_batch_slices
lines = src_fixed.splitlines()
psb_line = next(i for i, l in enumerate(lines) if "pub fn process_batch_slices" in l)
print(f"\n=== Lines {psb_line-2} to {psb_line+4} ===")
for i, l in enumerate(lines[psb_line-2:psb_line+5], start=psb_line-1):
    print(f"  {i:4d}: {l}")

# Check the impl block closes properly right after process_batch_slices ends
impl_close_line = next((i for i, l in enumerate(lines) if i > psb_line and l == "}"), None)
mod_socket_line = next(i for i, l in enumerate(lines) if "pub mod socket {" in l)
print(f"\n  impl Forwarder closes at line {impl_close_line}")
print(f"  pub mod socket at line {mod_socket_line}")
assert impl_close_line < mod_socket_line, "impl block not closed before mod socket"
print("✓ impl block structure is correct")

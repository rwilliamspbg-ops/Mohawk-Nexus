import os

CWD       = os.getcwd()
WORKSPACE = os.path.join(CWD, "SMIP-MWP-Rust")
lib_path  = os.path.join(WORKSPACE, "bench", "src", "lib.rs")
dp_socket = os.path.join(WORKSPACE, "datapath", "src", "socket.rs")

print("=== bench/src/lib.rs ===")
print(repr(open(lib_path).read()))

print("\n=== datapath/src/socket.rs ===")
print(open(dp_socket).read())

import os, sys

# The runtime patches io.open (lazy_load_files.py), which breaks subprocess pipes.
# os.system() streams to fd 1/2 but those are also redirected.
# Try writing directly via /proc/self/fd/1 or use a temp file as a bridge.

# Write output to a temp file and read it back
TMP = "/tmp/_diag_out.txt"

def sh(cmd):
    rc = os.system(f"({cmd}) > {TMP} 2>&1")
    try:
        with open(TMP) as fh:
            out = fh.read()
    except Exception as e:
        out = f"(read error: {e})"
    print(out if out.strip() else "(no output)")
    return rc

print("=== uname ===")
sh("uname -a")

print("=== /etc/os-release ===")
sh("cat /etc/os-release")

print("=== whoami ===")
sh("whoami; id")

print("=== apt-get update ===")
rc = sh("apt-get update")
print(f"[rc={rc>>8}]")

print("=== apt-cache search cargo/rustc ===")
sh("apt-cache search '.' | grep -i 'cargo\\|rustc'")

print("=== curl ===")
sh("curl --version")

print("=== Internet test ===")
sh("curl -s --max-time 5 -o /dev/null -w 'HTTP %{http_code}' https://sh.rustup.rs")

print("=== which tools ===")
sh("which curl wget python3 pip gcc make; echo '---'; ls /usr/bin/curl /usr/bin/wget 2>&1")

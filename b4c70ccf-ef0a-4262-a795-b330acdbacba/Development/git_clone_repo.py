import os

repo_url = "https://github.com/rwilliamspbg-ops/SMIP-MWP-Rust"
repo_name = repo_url.rstrip("/").split("/")[-1]

if os.path.exists(repo_name):
    print(f"Repo already exists at ./{repo_name}, pulling latest changes...")
    _rc = os.system(f"git -C {repo_name} pull")
else:
    print(f"Cloning {repo_url}...")
    _rc = os.system(f"git clone {repo_url}")

if _rc != 0:
    raise RuntimeError(f"git command failed with return code {_rc}")

repo_files = os.listdir(repo_name)
print(f"\nRepository contents ({len(repo_files)} items):")
for f in sorted(repo_files):
    print(f"  {f}")

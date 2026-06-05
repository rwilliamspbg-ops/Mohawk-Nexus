#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"


def sha256_hex(path: Path) -> str:
    # Normalize line endings so generated hashes are stable across OS checkout modes.
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    schema_path = BRIDGE_DIR / "bridge_contract.schema.json"
    example_path = BRIDGE_DIR / "examples" / "control_request.example.json"
    manifest_path = BRIDGE_DIR / "bridge_contract.manifest.json"
    version_path = BRIDGE_DIR / "bridge_contract.version.json"

    version = json.loads(version_path.read_text(encoding="utf-8"))

    manifest = {
        "schema": {
            "path": "bridge/bridge_contract.schema.json",
            "sha256": sha256_hex(schema_path),
        },
        "example": {
            "path": "bridge/examples/control_request.example.json",
            "sha256": sha256_hex(example_path),
        },
        "version_file": {
            "path": "bridge/bridge_contract.version.json",
            "sha256": sha256_hex(version_path),
        },
        "contract": version["contract"],
        "schema_version": version["schema_version"],
        "version": version["manifest_version"],
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"


def sha256_hex(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    schema_path = BRIDGE_DIR / "bridge_contract.schema.json"
    example_path = BRIDGE_DIR / "examples" / "control_request.example.json"
    manifest_path = BRIDGE_DIR / "bridge_contract.manifest.json"

    manifest = {
        "schema": {
            "path": "bridge/bridge_contract.schema.json",
            "sha256": sha256_hex(schema_path),
        },
        "example": {
            "path": "bridge/examples/control_request.example.json",
            "sha256": sha256_hex(example_path),
        },
        "contract": "Mohawk Go-Rust Bridge Contract",
        "version": "bridge_contract.manifest.v1",
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
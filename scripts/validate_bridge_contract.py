#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = BRIDGE_DIR / "bridge_contract.manifest.json"
    schema_path = BRIDGE_DIR / "bridge_contract.schema.json"
    example_path = BRIDGE_DIR / "examples" / "control_request.example.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["contract"] == "Mohawk Go-Rust Bridge Contract"
    assert manifest["version"] == "bridge_contract.manifest.v1"
    assert manifest["schema"]["path"] == "bridge/bridge_contract.schema.json"
    assert manifest["example"]["path"] == "bridge/examples/control_request.example.json"
    assert sha256_hex(schema_path) == manifest["schema"]["sha256"]
    assert sha256_hex(example_path) == manifest["example"]["sha256"]


if __name__ == "__main__":
    main()
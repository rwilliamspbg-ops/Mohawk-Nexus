#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"


def sha256_hex(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest_path = BRIDGE_DIR / "bridge_contract.manifest.json"
    schema_path = BRIDGE_DIR / "bridge_contract.schema.json"
    example_path = BRIDGE_DIR / "examples" / "control_request.example.json"
    version_path = BRIDGE_DIR / "bridge_contract.version.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    example = json.loads(example_path.read_text(encoding="utf-8"))
    version = json.loads(version_path.read_text(encoding="utf-8"))

    assert manifest["contract"] == version["contract"]
    assert manifest["version"] == version["manifest_version"]
    assert manifest["schema_version"] == version["schema_version"]
    assert manifest["schema"]["path"] == "bridge/bridge_contract.schema.json"
    assert manifest["example"]["path"] == "bridge/examples/control_request.example.json"
    assert manifest["version_file"]["path"] == "bridge/bridge_contract.version.json"
    assert sha256_hex(schema_path) == manifest["schema"]["sha256"]
    assert sha256_hex(example_path) == manifest["example"]["sha256"]
    assert sha256_hex(version_path) == manifest["version_file"]["sha256"]

    assert "contract_version" in schema["required"]
    assert schema["properties"]["contract_version"]["const"] == version["schema_version"]
    assert example["contract_version"] == version["schema_version"]


if __name__ == "__main__":
    main()
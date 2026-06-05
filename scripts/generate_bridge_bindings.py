#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"
VERSION_PATH = BRIDGE_DIR / "bridge_contract.version.json"
SCHEMA_PATH = BRIDGE_DIR / "bridge_contract.schema.json"


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_version() -> dict[str, str]:
    payload = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    required = {"contract", "schema_version", "manifest_version"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"missing bridge version fields: {sorted(missing)}")
    return payload


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> None:
    version = load_version()
    schema_hash = sha256_hex(SCHEMA_PATH)

    write_file(
        ROOT / "sdk/go/mohawksdk/bridge_contract.go",
        (
            "package mohawksdk\n\n"
            "const (\n"
            f"\tBridgeContractName = \"{version['contract']}\"\n"
            f"\tBridgeContractSchemaVersion = \"{version['schema_version']}\"\n"
            f"\tBridgeContractManifestVersion = \"{version['manifest_version']}\"\n"
            f"\tBridgeContractSchemaSHA256 = \"{schema_hash}\"\n"
            ")\n"
        ),
    )

    write_file(
        ROOT / "sdk/rust/src/bridge_contract.rs",
        (
            f"pub const BRIDGE_CONTRACT_NAME: &str = \"{version['contract']}\";\n"
            f"pub const BRIDGE_CONTRACT_SCHEMA_VERSION: &str = \"{version['schema_version']}\";\n"
            f"pub const BRIDGE_CONTRACT_MANIFEST_VERSION: &str = \"{version['manifest_version']}\";\n"
            f"pub const BRIDGE_CONTRACT_SCHEMA_SHA256: &str = \"{schema_hash}\";\n"
        ),
    )

    write_file(
        ROOT / "sdk/python/mohawk_sdk/bridge_contract.py",
        (
            f"BRIDGE_CONTRACT_NAME = \"{version['contract']}\"\n"
            f"BRIDGE_CONTRACT_SCHEMA_VERSION = \"{version['schema_version']}\"\n"
            f"BRIDGE_CONTRACT_MANIFEST_VERSION = \"{version['manifest_version']}\"\n"
            f"BRIDGE_CONTRACT_SCHEMA_SHA256 = \"{schema_hash}\"\n"
        ),
    )

    write_file(
        ROOT / "sdk/typescript/src/bridgeContract.js",
        (
            f"const BRIDGE_CONTRACT_NAME = \"{version['contract']}\";\n"
            f"const BRIDGE_CONTRACT_SCHEMA_VERSION = \"{version['schema_version']}\";\n"
            f"const BRIDGE_CONTRACT_MANIFEST_VERSION = \"{version['manifest_version']}\";\n"
            f"const BRIDGE_CONTRACT_SCHEMA_SHA256 = \"{schema_hash}\";\n\n"
            "module.exports = {\n"
            "  BRIDGE_CONTRACT_NAME,\n"
            "  BRIDGE_CONTRACT_SCHEMA_VERSION,\n"
            "  BRIDGE_CONTRACT_MANIFEST_VERSION,\n"
            "  BRIDGE_CONTRACT_SCHEMA_SHA256,\n"
            "};\n"
        ),
    )


if __name__ == "__main__":
    main()

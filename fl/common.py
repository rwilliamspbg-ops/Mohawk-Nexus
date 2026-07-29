import os
import json
from pathlib import Path
from typing import Any, Dict


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def read_config_file(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path)
    try:
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as handle:
            if config_path.suffix in {".json"}:
                data = json.load(handle)
            elif config_path.suffix in {".yaml", ".yml"}:
                import yaml

                data = yaml.safe_load(handle) or {}
            else:
                return {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}

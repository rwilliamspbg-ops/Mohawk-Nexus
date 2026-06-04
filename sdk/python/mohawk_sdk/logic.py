from typing import Dict, Any


def _round6(value: float) -> float:
    return round(float(value), 6)


def swip_scale(value: float) -> float:
    return _round6(float(value) * 1.5)


def fl_apply_update(state: Dict[str, Any], value: float) -> Dict[str, Any]:
    round_num = int(state.get("round", 0))
    updates = [float(v) for v in state.get("updates", [])]
    updates.append(float(value))

    if len(updates) >= 2:
        avg = sum(updates) / len(updates)
        return {
            "round": round_num + 1,
            "global": _round6(avg),
            "updates": [],
        }

    return {
        "round": round_num,
        "updates": [_round6(v) for v in updates],
    }

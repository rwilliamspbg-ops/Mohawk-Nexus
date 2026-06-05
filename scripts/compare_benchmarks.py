#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import median


BENCH_RE = re.compile(r'^(Benchmark\S+).*?([0-9]+\.?[0-9]*)\s+ns/op')


def parse_bench_file(path: Path) -> dict:
    data = {}
    for line in path.read_text().splitlines():
        m = BENCH_RE.match(line.strip())
        if m:
            name = m.group(1)
            ns = float(m.group(2))
            data.setdefault(name, []).append(ns)
    # reduce to median
    return {k: median(v) for k, v in data.items()}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--bench-file", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--threshold-percent", type=float, default=5.0)
    args = p.parse_args()

    bench = parse_bench_file(Path(args.bench_file))
    baseline_path = Path(args.baseline)

    if not baseline_path.exists():
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(bench, indent=2))
        print(f"Baseline created at {baseline_path}, no regression check performed.")
        return

    baseline = json.loads(baseline_path.read_text())
    regressions = []

    for name, value in bench.items():
        base_val = baseline.get(name)
        if base_val is None:
            print(f"New benchmark {name} (no baseline). Baseline value: {value}")
            continue
        diff_pct = ((value - base_val) / base_val) * 100.0
        if diff_pct > args.threshold_percent:
            regressions.append((name, base_val, value, diff_pct))

    if regressions:
        print("Performance regressions detected:")
        for r in regressions:
            print(f" - {r[0]}: baseline={r[1]:.2f} ns/op, current={r[2]:.2f} ns/op, +{r[3]:.2f}%")
        raise SystemExit(2)

    print("No regressions detected.")


if __name__ == "__main__":
    main()

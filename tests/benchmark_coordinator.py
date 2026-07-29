import subprocess
import time
import urllib.request
import json
import os
import shutil

def run_benchmark():
    run_data_dir = "run_data_bench"
    if os.path.exists(run_data_dir):
        shutil.rmtree(run_data_dir)
    os.makedirs(run_data_dir, exist_ok=True)

    env = os.environ.copy()
    env["FL_SERVER_PORT"] = "19000"
    env["FL_METRICS_ENABLED"] = "False"
    env["FL_PROFILING_ENABLED"] = "False"
    env["FL_STATE_DIR"] = run_data_dir

    proc = subprocess.Popen(
        ["python3", "fl/coordinator.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for coordinator to start
    time.sleep(1.0)

    url = "http://127.0.0.1:19000"

    num_requests = 1000
    latencies = []

    print(f"Running {num_requests} POST requests to coordinator...")
    for i in range(num_requests):
        payload = json.dumps({"value": 0.1 * i}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"}
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req) as resp:
                resp.read()
            latencies.append(time.perf_counter() - start)
        except Exception as e:
            print(f"Request {i} failed: {e}")
            break

    proc.terminate()
    proc.wait()

    if os.path.exists(run_data_dir):
        shutil.rmtree(run_data_dir)

    if not latencies:
        print("No latencies recorded.")
        return

    total_time = sum(latencies)
    avg_latency = total_time / len(latencies)
    print(f"Total time for {len(latencies)} requests: {total_time:.4f} seconds")
    print(f"Average latency: {avg_latency * 1000:.2f} ms")

if __name__ == "__main__":
    run_benchmark()

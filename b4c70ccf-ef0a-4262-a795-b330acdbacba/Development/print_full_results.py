import re

# Pull from upstream block's parsed results
for row in final_bench_results:
    name, time_s, thrpt_s = row
    if "datapath_with_refill" in name:
        print(f"{name:<65} | {time_s[:40]:<42} | {thrpt_s or ''}")

#!/usr/bin/env python3
import os, sys

ROUTES_PATH = os.path.join(os.path.dirname(__file__), "api", "routes.py")

OLD = """        prev_bucket_ts = curr_bucket_ts

    return jsonify({"""

NEW = """        prev_bucket_ts = curr_bucket_ts

    # packet_log buckets only cover up to the last closed bucket boundary.
    # Any stats_packets error data beyond that is in the still-open current
    # bucket -- add it to the last bucket so no errors are lost.
    last_bucket_ts = rows[-1]["bucket"] if rows else 0
    trailing_errors = sum(
        dup_by_ts[dts]["rx_errors"]
        for dts in dup_timestamps
        if dts > last_bucket_ts
    )
    if trailing_errors and rx_errors_list:
        rx_errors_list[-1] += trailing_errors

    return jsonify({"""

content = open(ROUTES_PATH).read()

if "trailing_errors" in content:
    print("Fix already applied.")
    sys.exit(0)

if OLD not in content:
    print("ERROR: Pattern not found.")
    sys.exit(1)

content = content.replace(OLD, NEW)
open(ROUTES_PATH, "w").write(content)
print("Done.")

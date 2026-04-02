#!/usr/bin/env python3
"""
patch_rx_errors.py — Fixes RX error counts changing with time range selection.
"""
import os
import sys

MODELS_PATH = os.path.join(os.path.dirname(__file__), "database", "models.py")
MARKER = "_rx_errors_patch_applied"

OLD_ACTIVITY = '''def query_packets_activity_from_stats(hours: int = 24) -> list[dict]:
    """Derive per-interval packet counts from cumulative stats_packets counters."""
    rows = _conn().execute(
        "SELECT ts, direct_tx, flood_tx, direct_rx, flood_rx, recv_errors "
        "FROM stats_packets WHERE ts >= ? ORDER BY ts",
        (_since(hours),),
    ).fetchall()
    result = []
    prev = None
    for r in rows:
        row = dict(r)
        if prev is not None:
            dtx = max(0, (row["direct_tx"] or 0) - (prev["direct_tx"] or 0))
            ftx = max(0, (row["flood_tx"] or 0) - (prev["flood_tx"] or 0))
            drx = max(0, (row["direct_rx"] or 0) - (prev["direct_rx"] or 0))
            frx = max(0, (row["flood_rx"] or 0) - (prev["flood_rx"] or 0))
            re = max(0, (row["recv_errors"] or 0) - (prev["recv_errors"] or 0))
            result.append({
                "bucket": row["ts"],
                "tx_direct": dtx,
                "tx_flood": ftx,
                "rx_direct": drx,
                "rx_flood": frx,
                "rx_errors": re,
                "total": dtx + ftx + drx + frx,
            })
        prev = row
    return result'''

NEW_ACTIVITY = '''def query_packets_activity_from_stats(hours: int = 24) -> list[dict]:
    """Derive per-interval packet counts from cumulative stats_packets counters.

    Counter resets (e.g. after service restart) produce a negative delta.
    When a reset is detected the new counter value is used as the delta so
    errors are never silently discarded across time-range changes.
    """
    rows = _conn().execute(
        "SELECT ts, direct_tx, flood_tx, direct_rx, flood_rx, recv_errors "
        "FROM stats_packets WHERE ts >= ? ORDER BY ts",
        (_since(hours),),
    ).fetchall()
    result = []
    prev = None

    def _delta(cur, prv):
        c = cur or 0
        p = prv or 0
        d = c - p
        return c if d < 0 else d

    for r in rows:
        row = dict(r)
        if prev is not None:
            dtx = _delta(row["direct_tx"],   prev["direct_tx"])
            ftx = _delta(row["flood_tx"],    prev["flood_tx"])
            drx = _delta(row["direct_rx"],   prev["direct_rx"])
            frx = _delta(row["flood_rx"],    prev["flood_rx"])
            re  = _delta(row["recv_errors"], prev["recv_errors"])
            result.append({
                "bucket": row["ts"],
                "tx_direct": dtx,
                "tx_flood":  ftx,
                "rx_direct": drx,
                "rx_flood":  frx,
                "rx_errors": re,
                "total": dtx + ftx + drx + frx,
            })
        prev = row
    return result'''

OLD_DUPS = '''def query_packet_dups(hours: int = 24) -> list[dict]:
    rows = _conn().execute(
        "SELECT ts, direct_dups, flood_dups, recv_errors "
        "FROM stats_packets WHERE ts >= ? ORDER BY ts",
        (_since(hours),),
    ).fetchall()
    result = []
    prev = None
    for r in rows:
        row = dict(r)
        if prev is not None:
            dd = max(0, (row["direct_dups"] or 0) - (prev["direct_dups"] or 0))
            fd = max(0, (row["flood_dups"] or 0) - (prev["flood_dups"] or 0))
            re = max(0, (row["recv_errors"] or 0) - (prev["recv_errors"] or 0))
            result.append({"ts": row["ts"], "dups_direct": dd, "dups_flood": fd, "rx_errors": re})
        prev = row
    return result'''

NEW_DUPS = '''def query_packet_dups(hours: int = 24) -> list[dict]:
    rows = _conn().execute(
        "SELECT ts, direct_dups, flood_dups, recv_errors "
        "FROM stats_packets WHERE ts >= ? ORDER BY ts",
        (_since(hours),),
    ).fetchall()
    result = []
    prev = None

    def _delta(cur, prv):
        c = cur or 0
        p = prv or 0
        d = c - p
        return c if d < 0 else d

    for r in rows:
        row = dict(r)
        if prev is not None:
            dd = _delta(row["direct_dups"], prev["direct_dups"])
            fd = _delta(row["flood_dups"],  prev["flood_dups"])
            re = _delta(row["recv_errors"], prev["recv_errors"])
            result.append({"ts": row["ts"], "dups_direct": dd, "dups_flood": fd, "rx_errors": re})
        prev = row
    return result'''


def main():
    if not os.path.exists(MODELS_PATH):
        print(f"ERROR: models.py not found at {MODELS_PATH}")
        sys.exit(1)

    content = open(MODELS_PATH).read()

    if MARKER in content:
        print("Patch already applied — nothing to do.")
        sys.exit(0)

    changed = False

    if OLD_ACTIVITY in content:
        content = content.replace(OLD_ACTIVITY, NEW_ACTIVITY)
        print("Patched: query_packets_activity_from_stats")
        changed = True
    else:
        print("WARNING: query_packets_activity_from_stats not found — may already be patched.")

    if OLD_DUPS in content:
        content = content.replace(OLD_DUPS, NEW_DUPS)
        print("Patched: query_packet_dups")
        changed = True
    else:
        print("WARNING: query_packet_dups not found — may already be patched.")

    if not changed:
        print("No changes made.")
        sys.exit(0)

    content += f"\n# {MARKER}\n"
    open(MODELS_PATH, "w").write(content)

    print("\nDone. Restart RepeaterWatch to apply:")
    print("  sudo systemctl restart RepeaterWatch")


if __name__ == "__main__":
    main()

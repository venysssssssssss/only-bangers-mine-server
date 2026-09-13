#!/usr/bin/env bash
set -euo pipefail

ROOT=${1:?server root}
SESSION=${2:?tmux session}
OUT=${3:?output directory}
LOG=$ROOT/logs/latest.log
WARMUP=60
DURATION=300
RUNS=$OUT/runs.tsv

mkdir -p "$OUT"

send() { tmux send-keys -t "$SESSION" "$1" C-m; }
say() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$OUT/controller.log"; }

kill_players() {
  for i in $(seq 1 15); do
    send "/player $(printf 'bench%02d' "$i") kill"
  done
}

server_pid() {
  for p in $(pgrep -f 'fabric-server-launch.jar|fabric-server-mc-.*\.jar' || true); do
    [ -r "/proc/$p/cwd" ] || continue
    [ "$(readlink "/proc/$p/cwd")" = "$ROOT" ] && { echo "$p"; return; }
  done
  return 1
}

finish() {
  kill_players >/dev/null 2>&1 || true
  sleep 2
  send stop >/dev/null 2>&1 || true
  say cleanup_requested
}
trap finish EXIT

# ponytail: native Carpet fake players; no protocol dependency. Add real clients only for network-overhead testing.
printf 'run_id\tplayers\trep\tpid\tstart_epoch\tmeasure_start_epoch\tend_epoch\tlog_start\tlog_end\n' > "$RUNS"
: > "$OUT/controller.log"
say benchmark_start
kill_players
sleep 5

for players in ${PLAYERS:-5 10 15}; do
  for rep in 1 2 3; do
    run_id="${players}p-r${rep}"
    run_dir=$OUT/$run_id
    mkdir -p "$run_dir"
    log_start=$(wc -l < "$LOG")
    start_epoch=$(date +%s)
    say "$run_id spawn"

    for i in $(seq 1 "$players"); do
      name=$(printf 'bench%02d' "$i")
      send "/player $name spawn"
      sleep 0.35
    done

    for i in $(seq 1 "$players"); do
      name=$(printf 'bench%02d' "$i")
      x=$(( ((i - 1) % 5 - 2) * 96 ))
      z=$(( ((i - 1) / 5 - 1) * 96 ))
      send "/tp $name $x 100 $z"
    done

    sleep 10
    say "$run_id warmup"
    (
      dirs=(north east south west)
      for step in $(seq 0 17); do
        dir=${dirs[$((step % 4))]}
        for i in $(seq 1 "$players"); do
          name=$(printf 'bench%02d' "$i")
          send "/player $name move stop"
          send "/player $name look $dir"
          send "/player $name move forward"
        done
        sleep 20
      done
    ) &
    route_pid=$!

    sleep "$WARMUP"
    measure_start_epoch=$(date +%s)
    pid=$(server_pid)
    say "$run_id measure pid=$pid"
    send /list
    send "/servercore status"
    pidstat -h -u -p "$pid" 5 61 > "$run_dir/cpu.pidstat" 2>&1 & cpu_pid=$!
    pidstat -h -r -p "$pid" 5 61 > "$run_dir/mem.pidstat" 2>&1 & mem_pid=$!
    vmstat 5 61 > "$run_dir/vmstat.txt" 2>&1 & vm_pid=$!

    (
      for _ in $(seq 1 60); do
        send "/tick query"
        sleep 5
      done
    ) & tick_pid=$!

    sleep "$DURATION"
    end_epoch=$(date +%s)
    kill "$tick_pid" "$route_pid" "$cpu_pid" "$mem_pid" "$vm_pid" 2>/dev/null || true
    wait "$tick_pid" "$route_pid" "$cpu_pid" "$mem_pid" "$vm_pid" 2>/dev/null || true
    send /list
    send "/servercore status"
    sleep 3
    log_end=$(wc -l < "$LOG")
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$run_id" "$players" "$rep" "$pid" "$start_epoch" "$measure_start_epoch" \
      "$end_epoch" "$log_start" "$log_end" >> "$RUNS"
    say "$run_id done"
    kill_players
    sleep 8
  done
done

python3 - "$OUT" "$LOG" <<'PY'
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

out = Path(sys.argv[1])
log_path = Path(sys.argv[2])
lines = log_path.read_text(errors="replace").splitlines()

def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * p / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (pos - lo)

def pidstat_values(path, pid, offset):
    values = []
    if not path.exists():
        return values
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split()
        try:
            index = parts.index(str(pid))
            values.append(float(parts[index + offset]))
        except (ValueError, IndexError):
            pass
    return values

rows = []
with (out / "runs.tsv").open() as stream:
    for row in csv.DictReader(stream, delimiter="\t"):
        pid = int(row["pid"])
        players = int(row["players"])
        lo = max(0, int(row["log_start"]) - 1)
        hi = min(len(lines), int(row["log_end"]))
        segment = lines[lo:hi]
        names = [f"bench{i:02d}" for i in range(1, players + 1)]
        joined = sum(1 for line in segment if any(f"{name} joined the game" in line for name in names))
        disconnects = sum(1 for line in segment if "lost connection:" in line and any(name in line for name in names))
        keepup = sum("Can't keep up!" in line for line in segment)
        errors = sum("[ERROR]" in line for line in segment)
        ticks = []
        for index, line in enumerate(segment):
            if "Average time per tick:" not in line:
                continue
            block = line + (" " + segment[index + 1] if index + 1 < len(segment) else "")
            match = re.search(
                r"Average time per tick:\s*([\d.]+)ms.*?"
                r"P50:\s*([\d.]+)ms P95:\s*([\d.]+)ms P99:\s*([\d.]+)ms",
                block,
            )
            if match:
                ticks.append(tuple(float(value) for value in match.groups()))
        cpu = pidstat_values(out / row["run_id"] / "cpu.pidstat", pid, 5)
        rss = pidstat_values(out / row["run_id"] / "mem.pidstat", pid, 4)
        rows.append({
            "run_id": row["run_id"],
            "players": players,
            "rep": int(row["rep"]),
            "joined": joined,
            "disconnects": disconnects,
            "tick_samples": len(ticks),
            "mspt_avg": round(statistics.mean(item[0] for item in ticks), 3) if ticks else None,
            "mspt_p95_avg": round(statistics.mean(item[2] for item in ticks), 3) if ticks else None,
            "mspt_p99_max": round(max(item[3] for item in ticks), 3) if ticks else None,
            "cpu_p95": round(percentile(cpu, 95), 3) if cpu else None,
            "rss_max_kb": round(max(rss), 1) if rss else None,
            "keepup_warnings": keepup,
            "error_lines": errors,
        })

(out / "summary.json").write_text(json.dumps({"runs": rows}, indent=2) + "\n")
fields = list(rows[0]) if rows else []
with (out / "summary.tsv").open("w") as stream:
    stream.write("\t".join(fields) + "\n")
    for row in rows:
        stream.write("\t".join("" if row[field] is None else str(row[field]) for field in fields) + "\n")
with (out / "summary.md").open("w") as stream:
    stream.write("# Minecraft benchmark\n\n")
    stream.write("| run | players | joined | disconnects | ticks | avg MSPT | avg P95 MSPT | max P99 MSPT | CPU P95 | RSS max KB | keep-up | errors |\n")
    stream.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in rows:
        stream.write("| {run_id} | {players} | {joined} | {disconnects} | {tick_samples} | {mspt_avg} | {mspt_p95_avg} | {mspt_p99_max} | {cpu_p95} | {rss_max_kb} | {keepup_warnings} | {error_lines} |\n".format(**row))
PY

say benchmark_complete

#!/bin/bash
set -euo pipefail

# expected format: YYYY-mm-dd
rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

cd "$CAERRA_WORK_DIR"

for task in prepare infer archive; do
    log="$CAERRA_LOGS/${task}_$rundate.log"

    case $task in
    prepare) scripts/prepare.sh --date "$rundate" >>"$log" 2>&1 ;;
    infer) scripts/parallel_infer.sh "$rundate" >>"$log" 2>&1 ;;
    archive) scripts/mars.sh "$rundate" >>"$log" 2>&1 ;;
    *) echo "Invalid task: $task" >&2 && exit 1 ;;
    esac

    rc=$?
    if ((rc != 0)); then
        echo "Task '$task' failed, here's the last 20 lines from $log" >&2
        tail -n 20 "$log" >&2
        exit 1
    fi
done

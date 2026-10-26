#!/bin/bash
set -euo pipefail

# expected format: YYYY-mm-dd
rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

# Runs a given command saving its output to a log file,
run() {
    local task=$1
    local cmd=$2
    local log="$CAERRA_LOGS/${task}_$rundate.log"

    if ! eval "$cmd" >"$log" 2>&1; then
        echo "Task '$task' failed, check the log file: $log" >&2
        exit 1
    fi
}

run "prepare" \
    "ssh ac-login \"cd $CAERRA_WORK_DIR; scripts/prepare.sh $rundate\""

run "infer" \
    "ssh ag-login \"cd $CAERRA_WORK_DIR; scripts/parallel_infer.sh $rundate\""

run "archive" \
    "ssh ac-login \"cd $CAERRA_WORK_DIR; scripts/mars.sh $rundate\""

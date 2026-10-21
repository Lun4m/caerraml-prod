#!/bin/bash
set -euo pipefail

# expected format: YYYY-mm-dd
rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

# Runs a given command saving to the output log and err files,
# while also printing to screen the error when the command fails
# Usuful because cron sends the stdout to email if a cron job fails.
run() {
    local out=$CAERRA_LOGS/$1_$rundate
    local cmd=$2
    local log="$out.log"
    local err="$out.err"

    if ! eval "$cmd" >"$log" 2>"$err"; then
        cat "$err"
        exit 1
    fi
}

echo "$(date -Iseconds): Preparaing inputs on cluster AC"
run "prepare" \
    "ssh ac-login \"cd $CAERRA_WORK_DIR; scripts/prepare.sh $rundate\""

echo "$(date -Iseconds): Running inference on cluster AG"
run "infer" \
    "ssh ag-login \"cd $CAERRA_WORK_DIR; scripts/parallel_infer.sh $rundate\""

echo "$(date -Iseconds): Finished production run"

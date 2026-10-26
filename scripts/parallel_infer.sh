#!/bin/bash
set -e

rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

run() {
    local domain=$1 && shift
    sbatch "$@" \
        --output="$CAERRA_LOGS/${domain}_${rundate}_%j.out" \
        scripts/infer.sh \
        "$rundate" \
        "$domain"
    return $?
}

run cerra
run carra-east
# Wait for the longest job before terminating
if ! run carra-west --wait; then
    echo "Inference runs failed. Check domain log files for $rundate" >&2
    exit 1
fi

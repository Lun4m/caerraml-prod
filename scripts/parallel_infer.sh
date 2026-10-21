#!/bin/bash
set -e

rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

submit_run() {
    local domain=$1
    sbatch --output="$CAERRA_LOGS/${domain}_%j.out" \
        scripts/infer.sh \
        "$rundate" \
        "$domain"
}

submit_run cerra
submit_run carra-east
submit_run carra-west

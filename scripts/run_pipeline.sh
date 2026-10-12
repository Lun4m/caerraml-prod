#!/bin/bash
# expected format: YYYY-mm-dd
rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

set -euo pipefail

echo "$(date -Iseconds): Preparaing inputs on cluster AC for $rundate"
ssh ac-login "cd \$CAERRA_WORK_DIR; scripts/prepare.sh $rundate" >>"$CAERRA_LOGS/prepare_$rundate.log" 2>&1

echo "$(date -Iseconds): Running inference on cluster AG for $rundate"
ssh ag-login "cd \$CAERRA_WORK_DIR; scripts/parallel_inference.sh $rundate" >>"$CAERRA_LOGS/inference_$rundate.log" 2>&1

echo "$(date -Iseconds): Archiving to MARS on cluster AC for $rundate"
ssh ac-login "cd \$CAERRA_WORK_DIR; scripts/mars.sh $rundate" >>"$CAERRA_LOGS/archive_$rundate.log" 2>&1

echo "$(date -Iseconds): Finished production run for $rundate"

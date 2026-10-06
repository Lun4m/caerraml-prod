#!/bin/bash
set -e

rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

sbatch --output="$CAERRA_LOGS/cerra_%j.out" scripts/infer.sh "$rundate" cerra
sbatch --output="$CAERRA_LOGS/carra-east_%j.out" scripts/infer.sh "$rundate" carra-east

# Wait for the longest job before terminating
sbatch --output="$CAERRA_LOGS/carra-west_%j.out" --wait scripts/infer.sh "$rundate" carra-west

echo "Inference step completed successfully"

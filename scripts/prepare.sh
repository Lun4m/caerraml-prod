#!/bin/bash
# TODO: does this require SLURM?
set -e

rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}

module purge
module load prgenv/gnu
module load ecmwf-toolbox
module load python3/3.12.11
module load uv

cd packages/prepare
uv run --frozen caerra-prep --date "$rundate"

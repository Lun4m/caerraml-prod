#!/bin/bash
#SBATCH --job-name=inference
#SBATCH --output=logs/%x_%j.out
#SBATCH --qos=ng
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-gpu=8
#SBATCH --time=01:40:00
#SBATCH --hint=nomultithread

set -e

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load ecmwf-toolbox/2026.04.0.0
module load python3/3.12.11
module load uv/0.13.4

rundate=${1:-$(date -I -d "$CAERRA_PROD_DELAY days ago")}
domain=${2:-"cerra,carra-east,carra-west"}

# shellcheck disable=SC2086
uv run --frozen caerra-infer --date $rundate --domains $domain

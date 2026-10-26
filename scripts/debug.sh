#!/bin/bash
#SBATCH --job-name=debug
#SBATCH --output=logs/%x.out
#SBATCH --qos=dg
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --hint=nomultithread

set -e

rundate=$1
domain=${2:-cerra}
member=${3:-0}

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load ecmwf-toolbox/2026.04.0.0
module load python3/3.12.11
module load uv/0.13.4

uv run --frozen caerra-infer \
    --domains "$domain" \
    --members "$member" \
    --date "$rundate"

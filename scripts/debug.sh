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
domain=$2

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load ecmwf-toolbox/2026.04.0.0
module load python3/3.12.11
module load uv

uv run --frozen caerra-infer \
    --domain "$domain" \
    --member 0 \
    --date "$rundate"

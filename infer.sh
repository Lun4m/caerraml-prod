#!/bin/bash
#SBATCH --job-name=caerra-tu-ml
#SBATCH --output=logs/%x.out
#SBATCH --qos=ng
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --hint=nomultithread

set -e
date=$1

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load cuda/13.0
module load ecmwf-toolbox/2026.04.0.0
module load python3/3.12.11
module load uv

uv run --frozen caerra-tu-ml "$date"

#!/bin/bash
#SBATCH --job-name=inference
#SBATCH --output=logs/%x.out
##SBATCH --qos=ng
#SBATCH --qos=dg
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --hint=nomultithread

set -e
date=$1

module purge
module load uv
module load cuda/13.0
module load ecmwf-toolbox
module load python3/3.12.11

uv run --frozen caerra_tu_ml prepare "$date"
uv run --frozen caerra_tu_ml run "$date"

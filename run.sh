#!/bin/bash
#SBATCH --job-name=inference
#SBATCH --output=logs/%x.out
##SBATCH --qos=ng
#SBATCH --qos=dg
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-tasks=8
#SBATCH --time=00:30:00
#SBATCH --hint=nomultithread

module purge
module load uv
module load cuda/13.0
module load ecmwf-toolbox
module load python3/3.12.11

date=$1

uv run caerra_ml_tu prepare "$date"
uv run caerra_ml_tu run "$date"

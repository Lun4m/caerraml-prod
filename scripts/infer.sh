#!/bin/bash
#SBATCH --job-name=caerra-tu-ml
#SBATCH --output=logs/%x_%j.out
#SBATCH --qos=ng
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --hint=nomultithread

set -e

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load ecmwf-toolbox/2026.04.0.0
module load python3/3.12.11
module load uv

if [ -z "${1+present}" ]; then
    date_arg=""
else
    date_arg="--date $1"
fi

# shellcheck disable=SC2086
uv run --frozen caerra-infer $date_arg

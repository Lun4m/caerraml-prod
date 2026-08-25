#!/bin/bash
# TODO: does this require SLURM
set -e
date=$1

module purge
module load prgenv/gnu
module load gcc/11.5.0
module load ecmwf-toolbox
module load python3/3.12.11
module load uv

cd packages/prepare
uv run --frozen caerra_prep "$date"

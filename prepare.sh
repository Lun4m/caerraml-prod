#!/bin/bash
# TODO: does this require SLURM
# NOTE: run inside tmux
set -e
date=$1

module purge
module load prgenv/gnu
module load ecmwf-toolbox
module load python3/3.12.11
module load uv

root=$(pwd)
cd packages/prepare
uv run --frozen caerra-prep "$date" 2>&1 | tee "$root/logs/prepare.out"

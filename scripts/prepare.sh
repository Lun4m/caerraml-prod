#!/bin/bash
# TODO: does this require SLURM?
set -e

module purge
module load prgenv/gnu
module load ecmwf-toolbox
module load python3/3.12.11
module load uv/0.13.4

cd packages/caerra-utils
uv run --frozen caerra-prep "$@"

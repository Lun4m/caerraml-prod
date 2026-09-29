#!/bin/bash
# TODO: does this require SLURM
# NOTE: run inside tmux
set -e

if [ -z "${1+present}" ]; then
    date_arg=""
else
    date_arg="--date $1"
fi

module purge
module load prgenv/gnu
module load ecmwf-toolbox
module load python3/3.12.11
module load uv

cd packages/prepare
# shellcheck disable=SC2086
uv run --frozen caerra-prep $date_arg

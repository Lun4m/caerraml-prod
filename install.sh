#!/bin/bash
set -e

cluster=$1

module load uv
module load python3/3.12.11

if [[ "${UV_CACHE_DIR@a}" != *x* ]]; then
    echo "Exporting environment variables in ~/.bashrc"

    cat >>"${HOME}"/.bashrc <<EOF
export UV_CACHE_DIR=$PERM/.cache/uv
export CAERRA_MASKS_PATH=$HOME/masks
export CAERRA_CKPTS_PATH=$HOME/checkpoints
export CAERRA_FORCINGS_PATH=$HOME/forcings
export CAERRA_TEMPLATES_PATH=$HOME/templates
export CAERRA_DATASETS_PATH=$SCRATCH/datasets
export CAERRA_OUTPUTS_PATH=$SCRATCH/outputs
EOF

    source "${HOME}/.bashrc"
fi

case $cluster in
AC)
    # Only need to prepare datasets on AC
    cd packages/prepare
    uv sync --frozen
    ;;
AG)
    module load cuda/13.0
    uv sync --frozen
    ;;
*)
    echo "Provide the name of the cluster: AC or AG"
    ;;
esac

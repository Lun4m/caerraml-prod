#!/bin/bash

cat >>~/.bashrc <<EOF
export UV_CACHE_DIR=$PERM/.cache/uv
export DATASETS_PATH=$SCRATCH/datasets
EOF

source "${HOME}/.bashrc"

# Set output path for era5t dataset
era5t_path="$DATASETS_PATH/era5t.zarr"
sed -i -e "s/\(dataset:\s\).*/\1$era5t_path" recipes/regrid.yaml

module load uv
module load cuda/12.8
module load python3/3.12.11

uv sync --frozen

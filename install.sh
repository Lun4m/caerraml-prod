#!/bin/bash
module load uv
module load cuda/12.8
module load python3/3.12.11

cat >>"${HOME}/.bashrc" <<EOF
export UV_CACHE_DIR=$PERM/.cache/uv
EOF

source "${HOME}/.bashrc"

# Set output path for era5t dataset
era5t_path="$SCRATCH/datasets/era5t.zarr"
sed -i -e "s/\(dataset:\s\).*/\1$era5t_path" recipes/regrid.yaml

uv sync --frozen

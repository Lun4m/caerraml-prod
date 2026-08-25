#!/bin/bash

set -e

module load uv
module load cuda/13.0
module load python3/3.12.11

if [[ "${UV_CACHE_DIR@a}" != *x* ]]; then
    echo "Setting UV_CACHE_DIR in ~/.bashrc"
    echo "export UV_CACHE_DIR=$PERM/.cache/uv" >>"${HOME}"/.bashrc
    source "${HOME}/.bashrc"
fi

echo "Setting ERA5T dataset path in recipes/regrid.yaml"
era5t_path="$SCRATCH/datasets/era5t.zarr"
sed -e "s|\(dataset:\s\).*|\1$era5t_path|" recipes/regrid_template.yaml >recipes/regrid.yaml

uv sync --frozen

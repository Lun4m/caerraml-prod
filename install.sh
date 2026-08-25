#!/bin/bash
set -e

cluster=$1

module load uv
module load python3/3.12.11

if [[ "${UV_CACHE_DIR@a}" != *x* ]]; then
    echo "Setting UV_CACHE_DIR in ~/.bashrc"
    echo "export UV_CACHE_DIR=$PERM/.cache/uv" >>"${HOME}"/.bashrc
    source "${HOME}/.bashrc"
fi

case $cluster in
AC)
    echo "Setting ERA5T dataset path in recipes/regrid.yaml"
    base_dir="packages/prepare/recipes"
    out_path="$SCRATCH/datasets/era5t.zarr"
    sed -e "s|\(dataset:\s\).*|\1$out_path|" $base_dir/regrid_template.yaml >$base_dir/regrid.yaml

    # Only need to prepare on AC
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

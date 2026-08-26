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

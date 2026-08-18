#!/bin/bash
#SBATCH --job-name=inference
#SBATCH --output=logs/%x.out
#SBATCH --qos=ng
#SBATCH --gpus=1
#SBATCH --time=00:30:00

module purge
module load uv
module load eccodes
module load cuda/12.6

# Runtime tweaks
export HYDRA_FULL_ERROR=1

uv run scripts/infer.py

# seed=$1
# member=$2
# output=$3
# region=$4

# export ANEMOI_BASE_SEED=...
export PERTURB_NUM=0
export OUT_GRIB="$HPCPERM/outputs/test.grib"

# TODO: could export directly in .bashrc
export UV_CACHE_DIR=

regions=("carra-east" "carra-west" "cerra")

for region in "${regions[@]}"; do
    uv run --frozen \
        anemoi-inference run config.yaml \
        --defaults defaults/post_processors.yaml \
        --defaults defaults/"$region".yaml \
        --defaults defaults/typed_variables.yaml
done

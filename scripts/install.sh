#!/usr/bin/env bash

set -euo pipefail

# Function that writes an rc file with CAERRA specific env vars
write_rc() {
    rcfile=$1
    echo "Exporting environment variables to $rcfile"

    path_to_script=$(dirname "$0")
    work_dir=$(realpath "$path_to_script"/..)

    cat >"$rcfile" <<EOF
# Centralize uv cache
export UV_CACHE_DIR=\$PERM/.cache/uv

export CAERRA_PROD_DELAY=7 # days
export CAERRA_MASKS_PATH=\$HOME/masks
export CAERRA_CKPTS_PATH=\$HOME/checkpoints
export CAERRA_FORCINGS_PATH=\$HOME/forcings
export CAERRA_TEMPLATES_PATH=\$HOME/templates
export CAERRA_DATASETS_PATH=\$SCRATCH/datasets
export CAERRA_OUTPUTS_PATH=\$SCRATCH/outputs
export CAERRA_LOGS=\$SCRATCH/logs
export CAERRA_WORK_DIR=$work_dir
EOF
}

module load uv
module load python3/3.12.11

flag="--force"
if [ -z "$1" ]; then
    overwrite=false
elif [ "$1" == $flag ]; then
    overwrite=true
else
    echo "Invalid argument: $1"
    echo "Usage: $0 ($flag)"
    exit 1
fi

rcfile="\$HOME/.caerrarc"
bashrc="$HOME/.bashrc"

if grep $rcfile "$bashrc" >/dev/null; then
    case $overwrite in
    true) echo "Ovewriting $rcfile" && write_rc $rcfile ;;
    false) echo "$rcfile already exist, pass '$flag' if you want to recreate it" ;;
    esac
else
    echo "Writing config file to $rcfile"
    write_rc $rcfile
    echo ". $rcfile" >>"$bashrc"
fi

source "$bashrc"
mkdir -p "$CAERRA_LOGS"

# HACK: reads cluster name directly from $HOSTNAME,
# will crash if these change in the future
case ${HOSTNAME:0:2} in
ac)
    echo "Syncing python packages on AC cluster"
    # Only need to prepare datasets on AC
    cd packages/prepare
    uv sync --frozen
    ;;
ag)
    echo "Syncing python packages on AG cluster"
    module load cuda/13.0
    uv sync --frozen
    ;;
*)
    echo "Unknown cluster '$HOSTNAME', expected first two characters to be 'ac' or 'ag'"
    exit 1
    ;;
esac

echo "Installation completed"

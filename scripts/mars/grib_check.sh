#!/usr/bin/bash
# Usage grib_check.sh <output_dir>
# Runs grib-check (CRRA convention) on all split GRIB files,
# exits nonzero if any check fails, so nothing bad is archived to MARS.

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 output_dir" >&2
    exit 1
fi

split_dir=$1/split

if [[ ! -d $split_dir ]]; then
    echo "Directory $split_dir does not exist!" >&2
    exit 1
fi

module load python3/3.12.11
module load uv/0.13.4

# grib-check is installed in the caerra-grib environment
cd "$CAERRA_WORK_DIR/packages/caerra-grib"

shopt -s nullglob
grib_files=("$split_dir"/*.grib2)

if [ ${#grib_files[@]} -eq 0 ]; then
    echo "No GRIB files found in $split_dir!" >&2
    exit 1
fi

failed_files=()
for file in "${grib_files[@]}"; do
    echo "Checking $file"
    rc=0
    report=$(uv run --frozen grib-check --failed-only -C crra "$file" 2>&1) || rc=$?

    if ((rc != 0)); then
        echo "$report"
        echo "Error: grib-check exited with code $rc on '$file'." >&2
        failed_files+=("$file")
    elif grep -q FAIL <<<"$report"; then
        echo "$report"
        failed_files+=("$file")
    fi
done

if [ ${#failed_files[@]} -ne 0 ]; then
    echo "grib-check reported failures for the following files:" >&2
    printf '%s\n' "${failed_files[@]}" >&2
    exit 1
fi

echo "grib-check passed for all ${#grib_files[@]} files"

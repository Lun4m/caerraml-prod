#!/usr/bin/env bash
# Usage MARS_wrapper.sh yyyy-mm-dd  # Archive CAERRAML data for this day

module load ecmwf-toolbox/new

# TODO: make function to send mail to MAILADDR whenever there is exit 1 below
# MAILADDR=manuel.carrer@met.no # ,mail2@dmi.dk
# sendmail=0

set -euo pipefail

# 1. Check if an argument was provided
if [ $# -ge 2 ]; then
    echo "Error: too many arguments." >&2
    echo "Usage: $0 (YYYY-MM-DD, defaults to 8 days ago)" >&2
    exit 1
fi

if [ -z "${1+present}" ]; then
    input_date=$(date -I -d "8 days ago")
else
    input_date="$1"
fi

# 2. Check strict string format
if [[ ! "$input_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Input '$input_date' must be in YYYY-MM-DD format." >&2
    exit 1
fi

# 3. Check calendar validity using GNU date
if ! date -d "$input_date" >/dev/null 2>&1; then
    echo "Error: Input '$input_date' is not a valid calendar date." >&2
    exit 1
fi

# 4. Run scripts
output_dir=$CAERRA_OUTPUTS_PATH/$input_date

if [[ ! -d $output_dir ]]; then
    echo "Directory $output_dir does not exist!"
    exit 1
fi

# ===== Separate an,fc,hl files ============
echo "$CAERRA_WORK_DIR/mars/split_output.sh" "$output_dir"
time "$CAERRA_WORK_DIR/mars/split_output.sh" "$output_dir" || exit 1

# TODO:
# ===== Run grib-check ============
# If we want, to run
# grib-check -C crra /path/to/file.grib2 | grep FAIL # If nonzero, exit

# TODO:
# ===== Sanitycheck values ========
# $CAERRA_WORK_DIR/monitoring/check_data_range.py

# ===== Archive to MARS =============
echo "$CAERRA_WORK_DIR/mars/archive.sh" "$output_dir"
time "$CAERRA_WORK_DIR/mars/archive.sh" "$output_dir" || exit 1

# TODO:
# ==== Check archived data =========
# Grab example from /perm/c3s2361b/caerraml_wrapper/mars_templates
# Fetch from MARS
# run quicklook.py on it

echo "All finished!"

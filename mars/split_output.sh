#!/usr/bin/env bash
# Usage split_output.sh <output_dir>
# output_dir is location of inference output
# One day execution all members an domains should take 2-3 minutes.

if [ $# -ne 1 ]; then
    echo "Usage: $0 output_dir" >&2
    exit 1
fi

gribs_path="$1" # Format: .../path/yyyy-mm-dd

if [[ ! -d $gribs_path ]]; then
    echo "Directory $gribs_path does not exist!"
    exit 1
fi

# Output data split in an,fc,hl goes here
output_dir=$gribs_path/split
mkdir -p "$output_dir"

for domain in carra-east carra-west cerra; do
    for input_file in "$gribs_path/$domain"*; do
        base_name="${input_file##*/}"

        if [[ ! -f $gribs_path/$base_name ]]; then
            echo "Input file $gribs_path/$base_name does not exist!"
            exit 1
        fi

        # Create a temporary rules file
        rules_file=$(mktemp)

        # Ensure the temporary file is deleted when the script exits
        trap 'rm -f "$rules_file"' EXIT

        # Write rules with dynamic output paths, crop .grib2 from base_name
        cat <<EOF >"$rules_file"
if (levtype is "hl") {
    if (type is "an") {
        write "${output_dir}/${base_name:0:-6}_hl_an.grib2";
    }
}

if (levtype is "sfc") {
    if (type is "an") {
        write "${output_dir}/${base_name:0:-6}_sfc_an.grib2";
    }

    if (type is "fc" && time != 2100) {
        write "${output_dir}/${base_name:0:-6}_sfc_fc.grib2";
    }

    if (type is "fc" && time == 2100) {
        write "${output_dir}/${base_name:0:-6}_sfc_fc_prev.grib2";
    }
}
EOF

        # Run grib_filter
        if ! grib_filter "$rules_file" "$input_file"; then
            echo "Error: grib_filter failed on file '$input_file'." >&2
            exit 1
        fi
    done
done

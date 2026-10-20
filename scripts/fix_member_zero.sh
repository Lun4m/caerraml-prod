#!/bin/bash

input_dir=$1 # format: .../path/YYYY-mm-dd/split

while IFS='' read -r -d '' filename; do
    temp="${filename}.tmp"

    case $filename in
    *an*) n=0 ;;
    *sfc_fc*) n=8 ;;
    *)
        echo "Unrecognized filename $filename: missing expted substring ('sfc_fc' or 'an')" >&2
        exit 1
        ;;
    esac

    if grib_set -s productDefinitionTemplateNumber="$n" "$filename" "$temp"; then
        mv -- "$temp" "$filename"
    else
        rm -f -- "$temp"
        echo "grib_set failed: $filename" >&2
    fi
done < <(find "$input_dir" -type f -name "*00*" -print0)

# TODO: change also ensemble number for all?
# for filename in "$input_dir"/*; do
#     temp="${filename}.tmp"
#
#     setopt="numberOfForecastsInEnsemble=10"
#
#     case $filename in
#     *00*an*) setopt="$setopt,productDefinitionTemplateNumber=0" ;;
#     *00*sfc_fc*) setopt="$setopt,productDefinitionTemplateNumber=8" ;;
#     esac
#
#     if grib_set -s "$setopt" "$filename" "$temp"; then
#         mv -- "$temp" "$filename"
#     else
#         rm -f -- "$temp"
#         echo "grib_set failed: $filename" >&2
#     fi
# done

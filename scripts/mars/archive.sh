#!/usr/bin/env bash
# Usage MARS_archive.sh <output_dir>
# output_dir is location of inference output

if [ $# -ne 1 ]; then
    echo "Usage: $0 output_dir" >&2
    exit 1
fi

module load ecmwf-toolbox/new

output_dir="$1" # Format: .../path/yyyy-mm-dd

# Output data split in an,fc,hl is expected to be here
output_dir_split=$output_dir/split

# Check that necessary directories exist
if [[ ! -d $output_dir_split ]]; then
    echo "Directory $output_dir_split does not exist!"
    exit 1
fi

list_dir=$output_dir/mars_templates
mkdir -p "$list_dir"

# Common MARS parameters across domains
database=marsscratch # CHANGE TO marser WHEN GOING PROD
class=rr
stream=enda
expver=prod

rundate=$(basename "$output_dir")
prev_date=$(date -I -d "$rundate - 1 day")

# For each domain, generate MARS request, then archive it
for domain in carra-east carra-west cerra; do
    for member in {00..10}; do
        list_file=$list_dir/${domain}_${member}.mars

        # Set domain specific parameters
        if [[ $domain == "cerra" ]]; then
            fcparams="201/202/169/175/228228/49" # wind gust only in cerra
            fcexpect1=6                          # Expect for fc params 21 run previous day
            fcexpect2=42                         # Expect for fc params current day
            origin="se-al-ai-ec"
        else
            fcparams="201/202/169/175/228228"
            fcexpect1=5
            fcexpect2=35
            [ "$domain" = "carra-east" ] && origin="no-ar-ai-ce"
            [ "$domain" = "carra-west" ] && origin="no-ar-ai-cw"
        fi

        sfc_fc_prev_file="${output_dir_split}/${domain}_m${member}_sfc_fc_prev.grib2"
        sfc_fc_file="${output_dir_split}/${domain}_m${member}_sfc_fc.grib2"
        sfc_an_file="${output_dir_split}/${domain}_m${member}_sfc_an.grib2"
        hl_an_file="${output_dir_split}/${domain}_m${member}_hl_an.grib2"

        # Ensure that all files exist before proceeding, or abort.
        for myfile in $sfc_fc_prev_file $sfc_fc_file $sfc_an_file $hl_an_file; do
            if [[ ! -f $myfile ]]; then
                echo "File $myfile is missing. Aborting."
                exit 1
            fi
        done

        cat <<EOF >"$list_file"
archive,
  source="${sfc_fc_prev_file}",
  database=${database},
  class=${class},
  origin=${origin},
  expver=${expver},
  stream=${stream},
  date=${prev_date},
  levtype=sfc,
  number=${member},
  param=${fcparams},
  step=3,
  time=21,
  type=fc,
  expect=${fcexpect1}
archive,
  source="${sfc_fc_file}",
  database=${database},
  class=${class},
  origin=${origin},
  expver=${expver},
  stream=${stream},
  date=${rundate},
  levtype=sfc,
  number=${member},
  param=${fcparams},
  step=3,
  time=00/03/06/09/12/15/18,
  type=fc,
  expect=${fcexpect2}
archive,
  source="${sfc_an_file}",
  database=${database},
  class=${class},
  origin=${origin},
  expver=${expver},
  stream=${stream},
  date=${rundate},
  levtype=sfc,
  number=${member},
  param=167/260242/207/260260/151/134/228164/260057,
  step=0,
  time=00/03/06/09/12/15/18/21,
  type=an,
  expect=64
archive,
  source="${hl_an_file}",
  database=${database},
  class=${class},
  origin=${origin},
  expver=${expver},
  stream=${stream},
  date=${rundate},
  levtype=hl,
  levelist=100,
  number=${member},
  param=10/3031,
  step=0,
  time=00/03/06/09/12/15/18/21,
  type=an,
  expect=16
EOF
        echo "Archiving ${domain} (origin=$origin, member=${member})"
        mars -n "$list_file" || exit 1
    done
done

#!/bin/bash

NAME=${0##*/}

print_help() {
    echo "Usage: $NAME (opts) TARGET_DIRECTORY" >&2
    echo
    echo "Positional arguments"
    echo "    TARGET_DIRECTORY            Directory containing daily inference files for all domains and members"
    echo "                                Expects the path to end with a 'YYYY-mm-dd' subdirectory"
    echo
    echo "Optional arguments"
    echo "    --domain/-d DOMAIN          Domain to archive. Default: all domains. Choices: cerra, carra-east, carra-west"
    echo "    --member/-m MEMBER          Member to archive (as a single two digit number with leading zero, for example 00, 01). Default: all members."
    exit 1
}

getopt -T &>/dev/null && exit_code=$? || exit_code=$?
if ((exit_code != 4)); then
    echo "This script requires GNU getopt" >&2
    exit 1
fi

opts=$(getopt --name "$NAME" --option hd:m: --longoptions help,domain:,member: -- "$@") || print_help
eval set -- "$opts"

declare input_domain input_member

while (($#)); do
    case $1 in
    --help | -h) print_help ;;
    --domain | -d)
        input_domain=$2
        shift 2
        ;;
    --member | -m)
        input_member=$2
        shift 2
        ;;
    --)
        shift
        break
        ;;
    *)
        print_help
        ;;
    esac
done

case $# in
1) output_dir=$1 ;;
0)
    echo "Missing required argument: TARGET_DIRECTORY" >&2
    print_help
    ;;
*)
    echo "Wrong required argument: $*" >&2
    print_help
    ;;
esac

module load ecmwf-toolbox/new

# Output data split in an,fc,hl is expected to be here
output_dir_split=$output_dir/split

# Check that necessary directories exist
if [[ ! -d $output_dir_split ]]; then
    echo "Directory $output_dir_split does not exist!" >&2
    exit 1
fi

list_dir=$output_dir/mars_templates
mkdir -p "$list_dir"

# Common MARS parameters across domains
database=marsscratch # CHANGE TO marser WHEN GOING PROD
class=rr
expver=prod

rundate=$(basename "$output_dir")
prev_date=$(date -I -d "$rundate - 1 day")

# For each domain, generate MARS request, then archive it
for domain in carra-east carra-west cerra; do
    # Filter by user input if provided
    if [[ ! -z $input_domain && $domain != "$input_domain" ]]; then
        continue
    fi

    for member in {00..10}; do
        # Filter by user input if provided
        if [[ ! -z $input_member && $member != "$input_member" ]]; then
            continue
        fi

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

        if [[ $member == "00" ]]; then
            stream=oper
        else
            stream=enda
        fi

        sfc_fc_prev_file="${output_dir_split}/${domain}_m${member}_sfc_fc_prev.grib2"
        sfc_fc_file="${output_dir_split}/${domain}_m${member}_sfc_fc.grib2"
        sfc_an_file="${output_dir_split}/${domain}_m${member}_sfc_an.grib2"
        hl_an_file="${output_dir_split}/${domain}_m${member}_hl_an.grib2"

        # Ensure that all files exist before proceeding, or abort.
        for myfile in $sfc_fc_prev_file $sfc_fc_file $sfc_an_file $hl_an_file; do
            if [[ ! -f $myfile ]]; then
                echo "File $myfile is missing. Aborting." >&2
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

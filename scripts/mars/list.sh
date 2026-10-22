#!/bin/bash -e
#SBATCH --job-name=manifest
#SBATCH --time=1-00:00:00

if (($# != 1)); then
    echo "USAGE: list.sh RUNDATE" >&2
    echo "RUNDATE follows the mars date format" >&2
    exit 1
fi

# Strip hyphens
rundate=${1//-/}

list_dir="$HOME"

db=marsscratch
class=rr
expver=prod
hl_params="10/3031"
fc_params="201/202/169/175/228228"
an_params="167/260242/207/260260/151/134/228164/260057"

for domain in carra-east carra-west cerra; do
    list_file=$list_dir/${domain}.mars

    # Set domain specific parameters
    case $domain in
    cerra)
        origin="se-al-ai-ec"
        # wind gust only in cerra
        fc_params="$fc_params/49"
        ;;
    carra-east) origin="no-ar-ai-ce" ;;
    carra-west) origin="no-ar-ai-cw" ;;
    esac

    params=$an_params/$hl_params/$fc_params

    # TODO: need to separate leveltype, stream, and paramtype for best performance?
    cat <<EOF >"$list_file"
list,
  database=${db},
  class=${class},
  origin=${origin},
  expver=${expver},
  stream=oper/enda,
  date=${rundate},
  levtype=sfc/hl,
  number=1/to/10,
  param=${params},
  step=3,
  time=00/03/06/09/12/15/18/21,
  type=an/fc,
  target="caerraml-${domain}-manifest.txt",
  output=tree
EOF

    echo "Listing ${domain} (origin=$origin})"
    mars -n "$list_file" || exit 1
    rm -f "$list_file"
done
exit

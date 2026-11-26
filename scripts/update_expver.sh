domain=$1

for f in ./"${domain}"*; do
    temp=${f}.tmp
    if grib_set -s "crraLocalVersion=2,experimentVersionNumber=test" "$f" "$temp"; then
        mv "$temp" "$f"
        echo "Updated $f"
    else
        rm -f -- "$temp"
        echo "grib_set failed: $f" >&2
    fi
done

#!/bin/bash
# usage: fetch_nist.sh OUTDIR SYMBOLS_FILE
OUT=$1; SYMS=$2
Q="low_w=200&upp_w=1000&unit=1&de=0&format=2&line_out=0&remove_js=on&en_unit=1&output=0&page_size=15&show_obs_wl=1&show_calc_wl=1&order_out=0&show_av=2&tsb_value=0&A_out=0&intens_out=on&allowed_out=1&forbid_out=1&conf_out=on&term_out=on&enrg_out=on&J_out=on&submit=Retrieve+Data"
z=0
while read s; do
  z=$((z+1)); [ $z -gt 99 ] && break
  for ion in I II; do
    fn=$(printf "%s/%03d_%s_%s.csv" "$OUT" $z "$s" $ion)
    [ -s "$fn" ] && continue
    for attempt in 1 2 3; do
      code=$(curl -s --max-time 120 -o "$fn" -w "%{http_code}" "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra=${s}+${ion}&${Q}")
      if [ "$code" = "200" ]; then echo "$z $s $ion $(wc -c < "$fn")"; break; else echo "ERR $z $s $ion $code"; rm -f "$fn"; sleep 5; fi
    done
    sleep 1
  done
done < "$SYMS"
echo DONE

#!/bin/bash
OUT=$1
for z in $(seq 1 118); do
  for h in "Estimated+Crustal+Abundance" "Estimated+Oceanic+Abundance"; do
    tag=$(echo $h | cut -d+ -f2)
    fn="$OUT/${z}_${tag}.json"
    [ -s "$fn" ] && continue
    code=$(curl -s --max-time 60 -o "$fn" -w "%{http_code}" "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/element/${z}/JSON?heading=${h}")
    echo "$z $tag $code"
    [ "$code" != "200" ] && rm -f "$fn"
    sleep 0.35
  done
done
echo DONE

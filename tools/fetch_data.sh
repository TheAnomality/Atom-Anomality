#!/bin/bash
# Download the raw open data used by the site into a working directory, then
# build the compact JSON files in data/.
#
#   tools/fetch_data.sh /path/to/raw
#
# Sources: PubChem PUG REST/View (NCBI), NIST Atomic Spectra Database,
# IAEA LiveChart of Nuclides API. Be polite: the scripts pause between requests.
set -euo pipefail
RAW=${1:?usage: fetch_data.sh RAW_DIR}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$RAW/nist" "$RAW/pubchem_abund"

echo "PubChem periodic table"
curl -sS --fail -o "$RAW/pubchem_pt.json" "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"

echo "NIST ground states and ionisation energies"
curl -sS --fail -o "$RAW/nist_ie.csv" "https://physics.nist.gov/cgi-bin/ASD/ie.pl?spectra=H-Og+I&units=1&format=2&order=0&at_num_out=on&sp_name_out=on&ion_charge_out=on&el_name_out=on&seq_out=on&shells_out=on&conf_out=on&level_out=on&ion_conf_out=on&e_out=0&unc_out=on&biblio=on&remove_js=on&submit=Retrieve+Data"

echo "IAEA nuclide ground states"
curl -sS --fail -o "$RAW/iaea_ground.csv" "https://nds.iaea.org/relnsd/v1/data?fields=ground_states&nuclides=all"

python3 -c "
import json; rows=json.load(open('$RAW/pubchem_pt.json'))['Table']['Row']
open('$RAW/symbols.txt','w').write('\n'.join(r['Cell'][1] for r in rows)+'\n')"

echo "NIST spectral lines (elements 1-99, neutral and singly ionised; takes several minutes)"
"$HERE/fetch_nist.sh" "$RAW/nist" "$RAW/symbols.txt"

echo "PubChem crustal and oceanic abundances"
"$HERE/fetch_abund.sh" "$RAW/pubchem_abund"

echo "Building data/*.json"
python3 "$HERE/build_data.py" "$RAW" "$HERE/../data"

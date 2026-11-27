#!/usr/bin/env python3
"""Build the compact JSON data files used by the site from raw open-data downloads.

Inputs (tools/fetch_data.sh downloads them and then runs this script):
  RAW/pubchem_pt.json            PubChem periodic table (PUG REST)
  RAW/nist_ie.csv                NIST ASD ground states & ionization energies
  RAW/iaea_ground.csv            IAEA LiveChart of Nuclides, ground states
  RAW/pubchem_abund/*.json       PubChem PUG View crustal/oceanic abundance
  RAW/nist/*.csv                 NIST ASD lines, 200-1000 nm, neutral + singly ionized

Outputs: data/elements.json, data/nuclides.json, data/spectra.json
"""
import csv, glob, json, math, os, re, sys

RAW = sys.argv[1]
OUT = sys.argv[2]

def nist_clean(v):
    v = v.strip()
    if v.startswith('='):
        v = v[1:]
    return v.strip('"')

# ---------------------------------------------------------------- elements
pt = json.load(open(os.path.join(RAW, 'pubchem_pt.json')))['Table']
cols = pt['Columns']['Column']
pub = [dict(zip(cols, r['Cell'])) for r in pt['Row']]

ie_rows = {}
txt = open(os.path.join(RAW, 'nist_ie.csv'), encoding='latin-1').read()
for row in csv.reader([l for l in txt.splitlines() if l.startswith('"') or l.startswith('At.')]):
    if row[0].startswith('At.'):
        hdr = row
        continue
    r = dict(zip(hdr, [nist_clean(c) for c in row]))
    ie_rows[int(r['At. num'])] = r

def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

def layout(z):
    """Return (period, group or None, block, x, y) using the IUPAC-recommended
    arrangement with Lu and Lr in group 3 and La-Yb / Ac-No in the f-block."""
    periods = [(1, 2), (3, 10), (11, 18), (19, 36), (37, 54), (55, 86), (87, 118)]
    for p, (a, b) in enumerate(periods, start=1):
        if a <= z <= b:
            period, i = p, z - a
            break
    if period == 1:
        g = 1 if z == 1 else 18
        return period, g, 's', g, 1
    if period in (2, 3):
        g = [1, 2, 13, 14, 15, 16, 17, 18][i]
        return period, g, ('s' if g <= 2 else 'p'), g, period
    if period in (4, 5):
        g = i + 1
        blk = 's' if g <= 2 else ('d' if g <= 12 else 'p')
        return period, g, blk, g, period
    # periods 6, 7 (32 elements)
    if i < 2:
        return period, i + 1, 's', i + 1, period
    if i < 16:  # f-block: La..Yb / Ac..No
        return period, None, 'f', 3 + (i - 2), period + 3
    g = i - 13  # i=16 -> group 3 (Lu/Lr)
    blk = 'd' if g <= 12 else 'p'
    return period, g, blk, g, period

SUP = {'S': 'S', 'P': 'P', 'D': 'D', 'F': 'F'}
L_LETTERS = 'spdfghi'

NOBLE = {'He': '1s2', 'Ne': '1s2 2s2 2p6', 'Ar': '1s2 2s2 2p6 3s2 3p6',
         'Kr': '1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6',
         'Xe': '1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6 4d10 5s2 5p6',
         'Rn': '1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6 4d10 5s2 5p6 4f14 5d10 6s2 6p6'}
# NIST also abbreviates with closed-subshell cores that are not noble gases
CORES = dict(NOBLE,
             Cd='1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6 4d10 5s2',
             Hg='1s2 2s2 2p6 3s2 3p6 3d10 4s2 4p6 4d10 5s2 5p6 4f14 5d10 6s2')
NOBLE_Z = [('Rn', 86), ('Xe', 54), ('Kr', 36), ('Ar', 18), ('Ne', 10), ('He', 2)]

def parse_config(s):
    """'[Ar].3d5.4s' or '[Rn]7s2 7p6 5f14 6d10' -> (core, [(n,l,count),...])"""
    s = s.replace('(predicted)', '').replace('(calculated)', '').strip()
    core = None
    m = re.match(r'\[(\w+)\]', s)
    if m:
        core = m.group(1)
        s = s[m.end():]
    parts = re.findall(r'(\d)([spdfg])(\d*)', s)
    subs = [(int(n), L_LETTERS.index(l), int(c) if c else 1) for n, l, c in parts]
    return core, subs

def full_occupancy(core, subs):
    occ = {}
    if core:
        for n, l, c in parse_config(CORES[core])[1]:
            occ[(n, l)] = c
    for n, l, c in subs:
        occ[(n, l)] = c
    return occ

def term_pretty(t):
    # NIST: '2S<1/2>', '3P*<0>', '1S0', '<5/2>'
    if not t:
        return ''
    return t

elements = []
for e in pub:
    z = int(e['AtomicNumber'])
    period, group, block, x, y = layout(z)
    nist = ie_rows.get(z)
    if nist and nist.get('Ground Shells (a)'):
        core, subs = parse_config(nist['Ground Shells (a)'])
        cfg_src = 'NIST'
        predicted = False
    else:
        core, subs = parse_config(e['ElectronConfiguration'])
        cfg_src = 'PubChem'
        predicted = 'predicted' in e['ElectronConfiguration'] or 'calculated' in e['ElectronConfiguration']
    occ = full_occupancy(core, subs)
    # re-express with the largest noble-gas core that is fully contained (and smaller than Z)
    core = None
    for gas, zc in NOBLE_Z:
        if zc >= z:
            continue
        core_occ = {(n, l): c for n, l, c in parse_config(NOBLE[gas])[1]}
        if all(occ.get(k, 0) == v for k, v in core_occ.items()):
            core = gas
            break
    core_occ = {(n, l): c for n, l, c in parse_config(NOBLE[core])[1]} if core else {}
    subs = sorted([(n, l, c) for (n, l), c in occ.items() if c and core_occ.get((n, l), 0) != c],
                  key=lambda t: (t[0], t[1]))
    shells = {}
    for (n, l), c in occ.items():
        shells[n] = shells.get(n, 0) + c
    shell_list = [shells.get(n, 0) for n in range(1, max(shells) + 1)]
    assert sum(shell_list) == z, (z, shell_list, core, subs)
    ie = num(nist['Ionization Energy (eV)']) if nist else num(e['IonizationEnergy'])
    ie_note = ''
    if nist:
        pre = nist.get('Prefix', '')
        ie_note = {'(': 'theoretical', '[': 'semi-empirical'}.get(pre, '')
    year = e['YearDiscovered']
    state = e['StandardState'].lower().replace('expected to be a ', '')
    elements.append({
        'z': z, 'sym': e['Symbol'], 'name': e['Name'],
        'weight': e['AtomicWeight'],
        'period': period, 'group': group, 'block': block, 'x': x, 'y': y,
        'cat': e['GroupBlock'],
        'core': core, 'valence': [[n, l, c] for n, l, c in subs],
        'shells': shell_list,
        'cfgSrc': cfg_src, 'cfgPredicted': predicted,
        'term': (nist or {}).get('Ground Level', ''),
        'en': num(e['Electronegativity']),
        'radius': num(e['AtomicRadius']),
        'ie': ie, 'ieNote': ie_note,
        'ea': num(e['ElectronAffinity']),
        'ox': e['OxidationStates'],
        'state': state, 'statePredicted': e['StandardState'].startswith('Expected'),
        'mp': num(e['MeltingPoint']), 'bp': num(e['BoilingPoint']),
        'density': num(e['Density']),
        'year': year,
        'cpk': e['CPKHexColor'] or None,
    })

# abundance
for el in elements:
    z = el['z']
    for tag, key in (('Crustal', 'crust'), ('Oceanic', 'ocean')):
        fn = os.path.join(RAW, 'pubchem_abund', f'{z}_{tag}.json')
        val = None
        if os.path.exists(fn):
            d = json.load(open(fn))
            def walk(s):
                for sec in s.get('Section', []):
                    if 'Information' in sec:
                        return sec['Information']
                    r = walk(sec)
                    if r:
                        return r
            info = walk(d.get('Record', {})) or []
            for i in info:
                for m in i['Value'].get('StringWithMarkup', []):
                    mm = re.match(r'([\d.]+)(?:×10(-?\d+))?\s+milligrams per', m.get('String', ''))
                    if mm:
                        val = float(mm.group(1)) * (10 ** int(mm.group(2)) if mm.group(2) else 1)
        el[key] = val

# ---------------------------------------------------------------- nuclides
nuc_rows = list(csv.DictReader(open(os.path.join(RAW, 'iaea_ground.csv'), encoding='latin-1')))
nuclides = []
for r in nuc_rows:
    z, n = int(r['z']), int(r['n'])
    if z == 0 and n != 1:
        continue  # keep only the free neutron from the Z=0 row
    if r['half_life'] == 'STABLE':
        hl = -1
    else:
        hl = num(r['half_life_sec'])
    modes = []
    for k in ('1', '2', '3'):
        m = r[f'decay_{k}']
        if m:
            p = r[f'decay_{k}_%']
            modes.append([m, num(p.replace('?', '')) if p else None])
    hl_txt = ''
    if r['half_life'] not in ('STABLE', ''):
        op = {'GT': '>', 'LT': '<', 'GE': '≥', 'AP': '≈'}.get(r['operator_hl'], '')
        hl_txt = f"{op}{r['half_life']} {r['unit_hl']}".strip()
    nuclides.append([
        z, n, hl, modes,
        num(r['binding']),                 # binding energy per nucleon, keV
        num(r['atomic_mass']),             # atomic mass, micro-u
        num(r['abundance']),               # natural abundance, %
        r['jp'] or '',
        int(r['discovery']) if r['discovery'].isdigit() else None,
        num(r['radius']),                  # rms charge radius, fm
        hl_txt,
        1 if r['me_systematics'] == 'Y' else 0,
    ])

# longest-lived isotope per element (for [A] notation)
by_z = {}
for row in nuclides:
    by_z.setdefault(row[0], []).append(row)
for el in elements:
    iso = by_z.get(el['z'], [])
    stable = [r for r in iso if r[2] == -1]
    el['stableIsotopes'] = len(stable)
    if not stable:
        known = [r for r in iso if r[2] is not None and r[2] > 0]
        if known:
            best = max(known, key=lambda r: r[2])
            el['longestLived'] = best[0] + best[1]
            el['longestHalfLife'] = best[2]

# ---------------------------------------------------------------- spectra
def parse_int(s):
    m = re.search(r'\d+(?:\.\d+)?', s or '')
    return float(m.group(0)) if m else None

spectra = {}
for fn in sorted(glob.glob(os.path.join(RAW, 'nist', '*.csv'))):
    base = os.path.basename(fn)[:-4]
    zs, sym, ion = base.split('_')
    txt = open(fn, encoding='latin-1').read()
    if not txt.startswith('obs_wl'):
        continue
    rows = list(csv.reader(txt.splitlines()))
    lines = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        obs, ritz, inten = (nist_clean(c) for c in row[:3])
        I = parse_int(inten)
        if I is None or I <= 0:
            continue
        wl = num(obs) or num(ritz.strip('[]()'))
        if wl is None or wl < 200 or wl > 1000:
            continue
        lines.append((wl, I))
    if not lines:
        continue
    # merge components listed at the same wavelength (keep the strongest)
    merged = {}
    for wl, I in lines:
        k = round(wl, 3)
        merged[k] = max(merged.get(k, 0), I)
    lines = sorted(merged.items())
    total = len(lines)
    # keep the strongest lines in each region so the visible band stays well represented
    quota = {'I': (120, 200, 80), 'II': (60, 120, 40)}[ion]
    regions = [(200, 380), (380, 750), (750, 1000.0001)]
    kept = []
    for (lo, hi), q in zip(regions, quota):
        part = [t for t in lines if lo <= t[0] < hi]
        part.sort(key=lambda t: -t[1])
        kept += part[:q]
    kept.sort()
    def sig3(x):
        return float(f'{x:.3g}')
    spectra.setdefault(sym, {})[ion] = {
        'n': total,
        'l': [[wl, sig3(I)] for wl, I in kept],
    }

meta = {
    'generated': '2026-11-27',
    'sources': {
        'elements': 'PubChem Periodic Table (NCBI, public domain) https://pubchem.ncbi.nlm.nih.gov/periodic-table/',
        'configurations': 'NIST Atomic Spectra Database, Ground States and Ionization Energies https://physics.nist.gov/PhysRefData/ASD/ionEnergy.html',
        'abundance': 'PubChem element pages (Jefferson Lab / CRC Handbook values)',
        'nuclides': 'IAEA Nuclear Data Section, LiveChart of Nuclides API https://nds.iaea.org/relnsd/v1/data',
        'spectra': 'NIST Atomic Spectra Database, Lines (Kramida, Ralchenko, Reader & NIST ASD Team) https://physics.nist.gov/asd',
    },
}

os.makedirs(OUT, exist_ok=True)
def dump(name, obj):
    with open(os.path.join(OUT, name), 'w') as f:
        json.dump(obj, f, separators=(',', ':'), ensure_ascii=False)
    print(name, os.path.getsize(os.path.join(OUT, name)))

dump('elements.json', {'meta': meta, 'elements': elements})
dump('nuclides.json', {'meta': meta,
                       'fields': ['z', 'n', 'halfLifeSec', 'decay', 'bindingPerA_keV', 'mass_uu',
                                  'abundance', 'jp', 'discovery', 'radius_fm', 'halfLifeText', 'estimated'],
                       'rows': nuclides})
dump('spectra.json', {'meta': meta, 'spectra': spectra})

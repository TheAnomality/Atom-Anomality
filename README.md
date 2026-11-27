# Atom

An interactive guide to the atom: how small atoms are, how we found out what is inside them, why electrons sit on energy ladders, the true shapes of orbitals, how electron filling builds the periodic table, what holds a nucleus together, and what a chemical bond really is.

Almost every figure is a small simulation. The physics runs in your browser, and the data comes from measurements by NIST, the IAEA and PubChem.

## What's inside

**Chapters**

| Page | Chapter | Interactive figures |
| --- | --- | --- |
| `scale.html` | 1. Smaller than small | Zoom from an ant to a quark at true scale; proton vs. electron mass; how empty an atom is; where the proton's mass comes from |
| `discovery.html` | 2. How we found out | Five models of the atom; Rutherford's gold-foil experiment (Thomson vs. nuclear atom); a scanning tunnelling microscope imaging a quantum corral |
| `quantum.html` | 3. Quantum leaps | Single-electron double slit; de Broglie standing waves; why atoms have the size they do; hydrogen energy levels and spectrum; NIST element spectra; solar Fraunhofer lines; two-state superposition and selection rules |
| `orbitals.html` | 4. Orbitals | 3D hydrogen orbital explorer (cloud, 90% isosurface, slice); node cross-sections; radial distributions; catalogue of all orbitals up to n = 4 |
| `periodic.html` | 5. Building the table | Aufbau filling with the measured NIST configurations; Slater effective nuclear charge; periodic trends |
| `nucleus.html` | 6. The nucleus | Nuclear vs. electric force; chart of all ~3,400 nuclides; binding-energy curve with mass-defect calculator; decay simulator; the uranium-238 decay chain |
| `bonding.html` | 7. Atoms together | H₂ bonding/antibonding electron density and Morse curve; bond polarity; the NaCl crystal and the energy accounting of an ionic bond |

**Tools**

- `table.html`: periodic table with property heatmaps, state at any temperature, a trend chart, and a full profile for every element (configuration, isotopes, spectrum, live Wikipedia and PubChem descriptions). Deep links work, e.g. `table.html#Fe`.
- `nuclides.html`: chart of nuclides with zoom, search (`U-238`), half-lives, decay modes and decay chains.
- `spectra.html`: emission and absorption spectra of 98 elements, comparisons, line lists and a mystery-spectrum game.
- `build.html`: build an atom from protons, neutrons and electrons, checked against the IAEA database of known nuclei.

## How it is built

A static site with no build step: plain HTML, CSS and JavaScript modules. Figures load lazily as you scroll and pause when off screen.

- `assets/css/`: `site.css` (design system), `figures.css`, `home.css`, `table.css`
- `assets/js/site.js`: navigation, theme, reading progress, lazy figure loading
- `assets/js/lib/`: shared code. `hydrogen.js` holds the exact hydrogen wavefunctions (generalised Laguerre polynomials and real spherical harmonics), sampling and isosurface extraction. `color.js` maps wavelengths to colours using the CIE 1931 colour-matching functions.
- `assets/js/figures/`: one module per interactive figure
- `assets/js/workers/orbital-worker.js`: orbital sampling off the main thread
- `assets/vendor/`: three.js r170 (MIT licence) and its OrbitControls
- `data/`: compact JSON built from the open data sources below

### Run it locally

Module scripts need to be served over HTTP, so open the site through a local server rather than as a file:

```bash
python3 -m http.server 8000
```

Then visit http://localhost:8000.

### Shared header and footer

Each page carries its own copy of the header and footer between `<!-- header:start -->` / `<!-- footer:start -->` markers. Edit `tools/partials/*.html`, then run:

```bash
python3 tools/sync_partials.py
```

### Rebuilding the data

```bash
tools/fetch_data.sh /tmp/atom-raw
```

This downloads the raw data (a few minutes, with pauses between requests) and regenerates `data/elements.json`, `data/nuclides.json` and `data/spectra.json`.

### Deployment

`.github/workflows/static.yml` publishes the repository to GitHub Pages on every push to `main`.

## Data sources

| Data | Source | Terms |
| --- | --- | --- |
| Element properties, crustal and oceanic abundance | [PubChem](https://pubchem.ncbi.nlm.nih.gov/periodic-table/) (NCBI) | NCBI data is generally in the public domain |
| Ground-state configurations, ionisation energies, spectral lines | [NIST Atomic Spectra Database](https://physics.nist.gov/asd) (Kramida, Ralchenko, Reader and NIST ASD Team) | US government work |
| Half-lives, decay modes, masses, abundances, charge radii | [IAEA LiveChart of Nuclides](https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html) API (NUBASE2020, AME2020) | Free to use with attribution |
| Element summaries and images, fetched live | [Wikipedia REST API](https://www.mediawiki.org/wiki/API:REST_API) | CC BY-SA 4.0, credited where shown |
| Element history and uses, fetched live | [PubChem PUG View](https://pubchem.ncbi.nlm.nih.gov/docs/pug-view) (from CIAAW, Jefferson Lab and others) | Credited to each original source where shown |
| Physical constants | [CODATA 2018](https://physics.nist.gov/cuu/Constants/) | |

Literature references are listed at the end of each chapter.

## Simplifications

These are deliberate and are stated on the pages where they appear:

- Multi-electron atoms use measured configurations. Effective nuclear charge uses Slater's 1930 rules, an approximation.
- The H₂ curve is a Morse potential fitted to spectroscopic constants. The antibonding curve is Sato's approximate "anti-Morse" form.
- The nuclear force plot uses a Malfliet–Tjon model potential, which has the right range and shape but is not a full nucleon–nucleon force.
- The solar spectrum is synthetic: a blackbody continuum with the principal Fraunhofer lines at their measured wavelengths.
- NIST relative line intensities depend on the light source and are comparable only within one spectrum.
- Shell (ring) diagrams are labelled as bookkeeping pictures, not the real shapes of electrons.

#!/usr/bin/env python3
"""Copy the shared header/footer (tools/partials/*.html) into every page.

Pages mark the regions with <!-- header:start --> ... <!-- header:end --> and
<!-- footer:start --> ... <!-- footer:end -->. Links to the current page get
aria-current="page". Run from the repository root: python3 tools/sync_partials.py
"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parts = {name: open(os.path.join(ROOT, 'tools', 'partials', f'{name}.html')).read().strip()
         for name in ('header', 'footer')}

for page in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    fname = os.path.basename(page)
    html = open(page).read()
    for name, body in parts.items():
        cur = re.sub(r'(<a [^>]*href="%s")' % re.escape(fname), r'\1 aria-current="page"', body)
        pat = re.compile(r'(<!-- %s:start -->)(.*?)(<!-- %s:end -->)' % (name, name), re.S)
        html, n = pat.subn(lambda m: m.group(1) + '\n' + cur + '\n' + m.group(3), html)
        if n == 0:
            print(f'warning: no {name} markers in {fname}')
    open(page, 'w').write(html)
    print('synced', fname)

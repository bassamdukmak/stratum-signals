"""Rebuild index.html: capture Supabase rows and substitute them into template.html.
Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python build/build.py"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capture import capture, KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACEHOLDER = 'var SNAPSHOT = __SNAPSHOT_JSON__;'

template = open(os.path.join(ROOT, 'template.html'), encoding='utf-8').read()
assert template.count(PLACEHOLDER) == 1, 'template placeholder missing or duplicated'

snap = capture(template)
line = 'var SNAPSHOT = ' + json.dumps(snap, separators=(',', ':'), ensure_ascii=False) + ';'
page = template.replace(PLACEHOLDER, line)
assert KEY not in page and 'eyJ' not in page, 'key leaked into page'

open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(page)
print({k: len(v) for k, v in snap['tables'].items()}, 'bars', len(snap['bars']), snap['versions'], snap['today'])

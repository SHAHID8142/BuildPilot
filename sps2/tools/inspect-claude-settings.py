#!/usr/bin/env python3
"""Read-only inspection of .claude/settings.json.

Prints KEY NAMES and presence only. It never prints, logs, hashes or
transmits any credential value, and it performs no provider-side check.
"""
import json
import os
import subprocess
import sys

REPO = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main'
PATH = '.claude/settings.json'
os.chdir(REPO)


def keys(d, pre=''):
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out += keys(v, pre + k + '.')
        else:
            out.append((pre + k, bool(str(v).strip())))
    return out


def show(label, data):
    if data is None:
        print('  %s: (absent)' % label)
        return
    for name, present in keys(data):
        print('  %-46s %s' % (name,
                              '<present, VALUE WITHHELD>' if present
                              else '<empty>'))


print('=== working tree copy ===')
print('  exists on disk:', os.path.isfile(PATH))
wt = None
if os.path.isfile(PATH):
    wt = json.load(open(PATH))
show('working tree keys', wt)

print()
print('=== committed copy at HEAD ===')
try:
    blob = subprocess.run(['git', 'show', 'HEAD:' + PATH],
                          capture_output=True, text=True, check=True).stdout
    head = json.loads(blob)
    show('HEAD keys', head)
except Exception as e:
    head = None
    print('  could not read:', type(e).__name__)

print()
print('=== structural comparison (no values) ===')
if wt is not None and head is not None:
    wk, hk = dict(keys(wt)), dict(keys(head))
    print('  keys only in HEAD  :', sorted(set(hk) - set(wk)) or 'none')
    print('  keys only in tree  :', sorted(set(wk) - set(hk)) or 'none')
    for k in sorted(set(wk) & set(hk)):
        if wk[k] != hk[k]:
            print('  differs in presence: %s (HEAD=%s tree=%s)'
                  % (k, hk[k], wk[k]))
    print('  (no credential value was read, printed or transmitted)')
sys.exit(0)
#!/usr/bin/env python3
"""Identify which commits hold a credential in .claude/settings.json.

Prints commit ids, short SHAs and KEY NAMES only. No credential value is
printed, hashed, logged or transmitted, and no provider-side check is made.
"""
import json
import os
import re
import subprocess

REPO = '/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main'
PATH = '.claude/settings.json'
TOKEN_KEYS = ('ANTHROPIC_AUTH_TOKEN', 'OPENROUTER_KEY')
os.chdir(REPO)

commits = subprocess.run(['git', 'rev-list', '--all'],
                         capture_output=True, text=True,
                         check=True).stdout.split()

held, env_only = [], []
for c in commits:
    try:
        raw = subprocess.run(['git', 'show', '%s:%s' % (c, PATH)],
                             capture_output=True, text=True,
                             check=True).stdout
        d = json.loads(raw)
    except Exception:
        continue
    env = d.get('env') or {}
    keys = sorted(k for k in env if k in TOKEN_KEYS)
    if keys:
        held.append((c, keys))
    elif env:
        env_only.append((c, sorted(env.keys())))

short = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                       capture_output=True, text=True).stdout.strip()


def sha(c):
    return c[:7] + (' (HEAD)' if c == subprocess.run(
        ['git', 'rev-parse', 'HEAD'], capture_output=True,
        text=True).stdout.strip() else '')


print('commits examined:', len(commits))
print()
print('=== commits whose .claude/settings.json holds a CREDENTIAL KEY ===')
if not held:
    print('  none')
for c, keys in held:
    print('  %s  keys=%s' % (sha(c), keys))
print()
print('=== commits whose .claude/settings.json has env but NO credential key ===')
for c, keys in env_only:
    print('  %s  env keys=%s' % (sha(c), keys))
print()
print('=== is the forensic checkpoint a7767cf credential-bearing? ===')
cp = 'a7767cf5f761cab4aa633c1cbc7604f83e4d14f8'
print('  ', 'YES' if any(c == cp for c, _ in held) else 'no')
print()
print('  (no credential value was printed, hashed or transmitted)')
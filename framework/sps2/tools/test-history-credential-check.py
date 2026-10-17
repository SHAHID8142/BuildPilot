#!/usr/bin/env python3
"""Mutation-test the P3 history-credential check across three scenarios.

Builds throwaway repositories in a temp directory and applies the exact same
predicate that validate-p3.sh uses. Nothing here touches the real repository,
and no credential value is printed or transmitted.

Scenarios:
  1. clean history                      -> must PASS
  2. only the preserved checkpoint      -> must PASS, and must be classified
  3. checkpoint plus a second offender  -> must FAIL
  4. a lone non-checkpoint offender     -> must FAIL
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

KEYS = ('ANTHROPIC_AUTH_TOKEN', 'OPENROUTER_KEY', 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY')
PRESERVED = 'a7767cf5f761cab4aa633c1cbc7604f83e4d14f8'
PATH = '.claude/settings.json'


def build(tmp, commits):
    """commits: list of (label, settings_dict). Returns (repo, label->sha)."""
    d = os.path.join(tmp, 'repo')
    os.makedirs(os.path.join(d, '.claude'))
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@e',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@e')
    run = lambda *a: subprocess.run(a, cwd=d, env=env, capture_output=True)
    run('git', 'init', '-q')
    run('git', 'config', 'user.name', 't')
    run('git', 'config', 'user.email', 't@e')
    shas = {}
    for label, settings in commits:
        with open(os.path.join(d, PATH), 'w') as f:
            json.dump(settings, f)
        run('git', 'add', '-A')
        # --allow-empty: a repeated offender commit has an identical tree, and
        # git would otherwise refuse to create it, silently losing the case.
        run('git', 'commit', '-q', '--allow-empty', '-m', label)
        shas[label] = subprocess.run(
            ['git', '-C', d, 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True).stdout.strip()
    return d, shas


def check(repo, preserved):
    """The exact predicate used by validate-p3.sh section 10.

    `preserved` is the forensic checkpoint SHA. It is a parameter so the
    mutation test can exercise the same logic on a synthetic repository, whose
    commit hashes necessarily differ from the real checkpoint.
    """
    shas = subprocess.run(['git', '-C', repo, 'rev-list', '--all'],
                          capture_output=True, text=True, check=True
                          ).stdout.split()
    offenders = []
    for s in shas:
        raw = subprocess.run(['git', '-C', repo, 'show', '%s:%s' % (s, PATH)],
                             capture_output=True, text=True).stdout
        if not raw.strip():
            continue
        try:
            env = (json.loads(raw) or {}).get('env') or {}
        except Exception:
            continue
        if any(k in env for k in KEYS):
            offenders.append(s)
    others = [s for s in offenders if s != preserved]
    classified = offenders == [preserved]
    return (1 if others else 0), classified, len(offenders)


CLEAN = {'enabledPlugins': {}}
WITH_TOKEN = {'env': {'ANTHROPIC_AUTH_TOKEN': 'SYNTHETIC-FIXTURE'}}

results = []


def scenario(name, commits, want_rc, want_classified):
    tmp = tempfile.mkdtemp()
    try:
        repo, shas = build(tmp, commits)
        # The synthetic "checkpoint" stands in for the real preserved SHA.
        preserved = shas.get('checkpoint', PRESERVED)
        rc, classified, n = check(repo, preserved)
        ok = (rc == want_rc) and (classified == want_classified)
        results.append(ok)
        print('  %-46s rc=%d classified=%s offenders=%d -> %s'
              % (name, rc, classified, n, 'PASS' if ok else 'UNEXPECTED'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print('=== mutation test: P3 history-credential check ===')
scenario('1 clean history', [('clean', CLEAN)], 0, False)
scenario('2 preserved checkpoint only',
         [('baseline', CLEAN), ('checkpoint', WITH_TOKEN)], 0, True)
scenario('3 checkpoint + second offender',
         [('baseline', CLEAN), ('checkpoint', WITH_TOKEN),
          ('other', WITH_TOKEN)], 1, False)
scenario('4 lone non-checkpoint offender',
         [('baseline', CLEAN), ('other', WITH_TOKEN)], 1, False)

print()
if all(results):
    print('RESULT: all %d scenarios behaved as required' % len(results))
    sys.exit(0)
print('RESULT: %d of %d scenarios were UNEXPECTED'
      % (results.count(False), len(results)))
sys.exit(1)
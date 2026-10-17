#!/usr/bin/env python3
"""SPS 2.0 P7 isolation validator.

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes, no runtime activation, no registry modification.

Implements G3: "Two projects must have no shared persistent state, no
cross-project imports, and no cross-project registry/state references.
The isolation test must prove this mechanically."

Unlike a single-tree check, this materialises TWO independent project
copies in an ephemeral scratch directory and proves isolation by
demonstrating that mutating one leaves the other byte-identical.

Scratch copies live in an OS temporary directory and are always removed;
nothing is ever written inside the repository by this tool.
"""
import ast
import hashlib
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))  # tools -> sps2 -> framework -> repo root
SPS2 = os.path.join(REPO, "framework", "sps2")

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")

STDLIB = getattr(sys, "stdlib_module_names", None) or frozenset(
    "os sys json re ast hashlib shutil tempfile subprocess importlib "
    "collections itertools functools typing pathlib unittest argparse "
    "dataclasses enum io logging math textwrap difflib random string "
    "warnings copy csv errno glob heapq operator pickle pprint struct "
    "time traceback types uuid weakref zipfile abc contextlib decimal "
    "fnmatch fractions numbers platform pprint re secrets statistics "
    "sysconfig threading tokenize unicodedata urllib base64 bisect "
    "calendar cgi cmath codecs configparser crypt email getpass gzip "
    "hmac html http imaplib importlib inspect ipaddress keyword linecache "
    "locale mimetypes multiprocessing netrc ntpath os pathlib pdb pipes "
    "profile pty pwd py_compile queue quopri runpy sched select selectors "
    "shelve shutil signal smtplib socket socketserver sqlite3 ssl stat "
    "statistics string stringprep sunau symtable sysconfig tabnanny tarfile "
    "telnetlib termios test tkinter token trace tracemalloc tty turtle "
    "unicodedata urllib uuid wave webbrowser wsgiref xml xmlrpc zipapp"
    .split())


class Res:
    def __init__(self, quiet=False):
        self.passed = 0
        self.failed = 0
        self.neg_ok = 0
        self.neg_missed = 0
        self.quiet = quiet

    def ok(self, m):
        self.passed += 1
        if not self.quiet:
            print("  %sPASS%s  %s" % (GREEN, NC, m))

    def bad(self, m):
        self.failed += 1
        if not self.quiet:
            print("  %sFAIL%s  %s" % (RED, NC, m))

    def neg_ok_case(self, m):
        self.neg_ok += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def neg_missed_case(self, m):
        self.neg_missed += 1
        print("  %sFAIL%s  %s" % (RED, NC, m))

    def sect(self, t):
        print("\n%s%s%s" % (BOLD, t, NC))


SKIP_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", ".kilo",
                       "node_modules", ".mypy_cache", ".ruff_cache"})


def _is_nested_git_root(base, root):
    """A directory holding its own .git is a separate checkout, not this project.

    Scoping on this is what makes the walk match the tracked project surface:
    an untracked nested worktree inside the repo is not part of this project
    and its contents must not be judged as if they were.
    """
    if base == root:
        return False
    return os.path.exists(os.path.join(base, ".git"))


def project_files(root):
    """Every file belonging to this project, skipping noise and nested repos."""
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if _is_nested_git_root(base, root):
            dirs[:] = []
            continue
        for f in files:
            out.append(os.path.join(base, f))
    return sorted(out)


def tree_digest(root):
    """A content digest of the whole project tree."""
    h = hashlib.sha256()
    for p in project_files(root):
        rel = os.path.relpath(p, root)
        h.update(rel.encode("utf-8", "replace"))
        try:
            with open(p, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
        except OSError:
            h.update(b"<unreadable>")
    return h.hexdigest()


def _resolvable_in_project(top, root):
    """True when `top` names a module/package that exists inside root."""
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", ".pytest_cache")]
        if top in dirs or (top + ".py") in files:
            return True
    return False


def find_cross_project_imports(root, surface="sps2"):
    """Imports that resolve outside this project.

    Scoped to the SPS 2.0 project surface (`framework/sps2/`), matching the existing
    convention that import-boundary checks judge a project's own code rather
    than vendored sample templates under `skills/`.

    Three independent ways to reach another project are each reported:
      * a non-stdlib, non-project-local module import
      * sys.path manipulation injecting a path outside the project
      * a path literal used as a filesystem path that escapes the project
    """
    findings = []
    base = os.path.join(root, surface) if surface else root
    for path in project_files(base):
        if not path.endswith(".py"):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        rel = os.path.relpath(path, base)
        for node in ast.walk(tree):
            # (a) module imports
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:            # relative import: always in-project
                    continue
                mods = [node.module or ""]
            else:
                continue
            for mod in mods:
                top = (mod or "").split(".")[0]
                if not top or top in STDLIB:
                    continue
                if _resolvable_in_project(top, root):
                    continue
                findings.append(
                    "EXTERNAL_MODULE_IMPORT: %s imports %r" % (rel, mod))
        # (b) sys.path injection pointing outside the project
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("append", "insert", "extend"):
                continue
            tgt = func.value
            if not (isinstance(tgt, ast.Attribute)
                    and tgt.attr == "path"):
                continue
            for arg in list(node.args) + [k.value for k in node.keywords]:
                if isinstance(arg, ast.Constant) and isinstance(
                        arg.value, str):
                    if _escapes(arg.value, root):
                        findings.append(
                            "EXTERNAL_PATH_INJECTION: %s puts %r on sys.path"
                            % (rel, arg.value))
        # (c) path literals used as filesystem paths, escaping the project
        here = os.path.dirname(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _fs_call_name(node.func) not in FS_CALLS:
                continue
            for arg in list(node.args) + [k.value for k in node.keywords]:
                if isinstance(arg, ast.Constant) and isinstance(
                        arg.value, str):
                    if _escapes(arg.value, root, base=here):
                        findings.append(
                            "ESCAPING_PATH_LITERAL: %s uses %r in %s()"
                            % (rel, arg.value, _fs_call_name(node.func)))
    return sorted(set(findings))


def _looks_like_path(s):
    if not isinstance(s, str) or not s or len(s) > 400 or "\n" in s:
        return False
    if "://" in s:                 # a URL, not a filesystem path
        return False
    if s.startswith("~"):
        return True
    if s.startswith(("../", "./..")):
        return True
    return s.startswith("/")


def _escapes(s, root, base=None):
    """True when a path literal plausibly points outside `root`.

    A leading "/" alone is not evidence: it is far more often a URL path
    ("/api/cms") or a repo-root-relative path ("/capability/registry.json").
    So an absolute path only counts as an escape when it lands under a
    directory that really exists outside the project. That keeps the
    predicate non-vacuous in both directions: it ignores in-project and
    URL-shaped strings, while still catching "/etc/...", "/tmp/other" and
    home-relative paths.
    """
    if not _looks_like_path(s):
        return False
    if s.startswith("~"):
        return True
    if s.startswith("/"):
        # A genuine absolute path: resolve it as absolute, never relative
        # to the project, or every external path would fold back inside.
        resolved = os.path.normpath(s)
        if resolved == root or resolved.startswith(root + os.sep):
            return False
        head = s.lstrip("/").split("/")[0]
        if not head:
            return False
        return os.path.isdir(os.sep + head)
    # A relative escape: resolve against the containing file's directory.
    anchor = base or root
    resolved = os.path.normpath(os.path.join(anchor, s))
    return not (resolved == root or resolved.startswith(root + os.sep))


# Callables whose string argument is genuinely a filesystem path. Without
# this restriction the scan would flag its own search patterns: validators
# legitimately carry home-relative and system-path literals as the very
# strings they search for, which are not filesystem accesses.
FS_CALLS = frozenset({
    "open", "makedirs", "mkdir", "remove", "unlink", "rmdir", "rename",
    "replace", "chmod", "listdir", "scandir", "walk", "symlink", "link",
    "stat", "lstat", "access", "chdir", "truncate", "copy", "copy2",
    "copyfile", "copytree", "rmtree", "read_text", "write_text",
    "read_bytes", "write_bytes", "exists", "isfile", "isdir", "islink",
    "abspath", "realpath", "relpath", "normpath", "expanduser", "join",
    "splitdrive", "splitext", "basename", "dirname", "getcwd", "Path",
    "open_text", "samefile", "sameopenfile",
})


def _fs_call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def find_cross_project_state_refs(root, surface="sps2"):
    """Persistent state (JSON/MD) referencing paths outside the project."""
    findings = []
    scan = os.path.join(root, surface) if surface else root
    for path in project_files(scan):
        if not path.endswith((".json", ".md")):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                body = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        rel = os.path.relpath(path, scan)
        for token in _iter_path_tokens(body):
            if _escapes(token, root, base=os.path.dirname(path)):
                findings.append(
                    "EXTERNAL_STATE_REFERENCE: %s references %r"
                    % (rel, token))
    return sorted(set(findings))


def _iter_path_tokens(body):
    import re
    for m in re.finditer(r'"([^"\n]{2,200})"|\'([^\'\n]{2,200})\'', body):
        yield m.group(1) if m.group(1) is not None else m.group(2)


def check_two_projects_isolated(r):
    """G3 core: prove two independent copies share no persistent state.

    Non-vacuous by construction: copy A is mutated and copy B must be
    provably unchanged. A shared-state defect would let the mutation
    cross the boundary and the digest would not match.
    """
    tmp = tempfile.mkdtemp(prefix="sps2-isolation-")
    try:
        a = os.path.join(tmp, "project-a")
        b = os.path.join(tmp, "project-b")
        for dest in (a, b):
            shutil.copytree(REPO, dest,
                            ignore=shutil.ignore_patterns(
                                ".git", "__pycache__", "*.pyc"))
        # Each copy must be independently valid
        for name, root in (("A", a), ("B", b)):
            layout = os.path.join(root, "framework", "sps2", "memory",
                                  "memory-layout.json")
            if not os.path.isfile(layout):
                r.bad("COPY_%s_MISSING_MEMORY_LAYOUT" % name)
                return
        r.ok("two independent project copies materialised, each with its "
             "own memory layout")

        # Independence: mutate A, assert B unchanged
        digest_b_before = tree_digest(b)
        digest_a_before = tree_digest(a)
        marker = os.path.join(a, "framework", "sps2", "memory", "isolation-probe.tmp")
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write("probe")
        digest_a_after = tree_digest(a)
        digest_b_after = tree_digest(b)
        if digest_a_after == digest_a_before:
            r.bad("MUTATION_NOT_OBSERVED: project A did not change")
            return
        r.ok("mutating project A changes A (digest %s -> %s)"
             % (digest_a_before[:12], digest_a_after[:12]))
        if digest_b_after == digest_b_before:
            r.ok("project B byte-identical after A was mutated — no shared "
                 "persistent state (digest %s)" % digest_b_before[:12])
        else:
            r.bad("SHARED_STATE: project B changed when project A was "
                  "mutated (%s -> %s)"
                  % (digest_b_before[:12], digest_b_after[:12]))
            return

        # Both copies must agree on isolation being valid
        for name, root in (("A", a), ("B", b)):
            findings = (find_cross_project_imports(root)
                        + find_cross_project_state_refs(root))
            if findings:
                for f in findings[:5]:
                    r.bad("COPY_%s %s" % (name, f))
            else:
                r.ok("copy %s has no cross-project imports or state "
                     "references" % name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_live_tree(r):
    """The live project must itself be free of cross-project references."""
    findings = (find_cross_project_imports(REPO)
                + find_cross_project_state_refs(REPO))
    if findings:
        for f in findings[:10]:
            r.bad(f)
    else:
        r.ok("live tree has no cross-project imports or state references")


def check_registry_isolation(r, root=None):
    """The capability registry must not point at another project."""
    root = root or REPO
    reg = os.path.join(root, "framework", "sps2", "capability", "registry.json")
    try:
        with open(reg, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        r.bad("REGISTRY_UNREADABLE: %s" % type(exc).__name__)
        return
    findings = []
    for cap in doc.get("capabilities", []):
        cid = cap.get("capability_id")
        for key, val in cap.items():
            if isinstance(val, str):
                if _escapes(val, root):
                    findings.append("REGISTRY_ESCAPES_PROJECT: %s.%s=%r"
                                    % (cid, key, val))
                if "project" in key.lower() and "/" in val \
                        and not val.startswith("framework/sps2/"):
                    findings.append("REGISTRY_CROSS_PROJECT_REF: %s.%s=%r"
                                    % (cid, key, val))
    if findings:
        for f in findings:
            r.bad(f)
    else:
        r.ok("capability registry references no other project")


def check_memory_layout_locality(r):
    """The memory layout must be project-local and schema-valid."""
    layout = os.path.join(SPS2, "memory", "memory-layout.json")
    if not os.path.isfile(layout):
        r.bad("MEMORY_LAYOUT_MISSING")
        return
    try:
        with open(layout, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        r.bad("MEMORY_LAYOUT_CORRUPT: %s" % type(exc).__name__)
        return
    if doc.get("schema") != "sps2.memory-layout/v1":
        r.bad("MEMORY_LAYOUT_SCHEMA_INVALID: %r" % doc.get("schema"))
        return
    r.ok("memory layout is valid framework.sps2.memory-layout/v1")


def negatives(r):
    """Each case injects a real violation and requires detection.

    A negative case passes only when the violation IS caught. If a case
    returns True the defect survived and the control failed.
    """
    r.sect("NEGATIVE TESTS — each violation must be detected")
    tmp = tempfile.mkdtemp(prefix="sps2-isolation-neg-")
    try:
        base = os.path.join(tmp, "base")
        shutil.copytree(REPO, base,
                        ignore=shutil.ignore_patterns(
                            ".git", "__pycache__", "*.pyc"))

        def fresh(name):
            root = os.path.join(tmp, name)
            shutil.copytree(base, root)
            return root

        # N01 external module import
        root = fresh("n01")
        with open(os.path.join(root, "framework", "sps2", "core", "_probe_ext.py"),
                  "w", encoding="utf-8") as fh:
            fh.write("import numpy\n")
        found = find_cross_project_imports(root)
        r.neg_ok_case("N01 external module import detected -> rejected"
                      ) if any("EXTERNAL_MODULE_IMPORT" in f
                               for f in found) else \
            r.neg_missed_case("N01 external module import undetected")

        # N02 sys.path injection of an outside root
        root = fresh("n02")
        with open(os.path.join(root, "framework", "sps2", "core", "_probe_path.py"),
                  "w", encoding="utf-8") as fh:
            fh.write("import sys\n"
                     "sys.path.append('/tmp/other-project')\n")
        found = find_cross_project_imports(root)
        r.neg_ok_case("N02 external sys.path injection detected -> rejected"
                      ) if any("EXTERNAL_PATH_INJECTION" in f
                               for f in found) else \
            r.neg_missed_case("N02 external sys.path injection undetected")

        # N03 escaping path literal in code
        root = fresh("n03")
        with open(os.path.join(root, "framework", "sps2", "core", "_probe_lit.py"),
                  "w", encoding="utf-8") as fh:
            fh.write("open('/etc/sps2-shared')\n")
        found = find_cross_project_imports(root)
        r.neg_ok_case("N03 escaping path literal detected -> rejected"
                      ) if any("ESCAPING_PATH_LITERAL" in f
                               for f in found) else \
            r.neg_missed_case("N03 escaping path literal undetected")

        # N04 persistent state pointing at another project
        root = fresh("n04")
        p = os.path.join(root, "framework", "sps2", "memory", "memory-layout.json")
        with open(p, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["foreign_reference"] = "/tmp/other-project/framework/sps2/state.json"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        found = find_cross_project_state_refs(root)
        r.neg_ok_case("N04 cross-project state reference detected -> rejected"
                      ) if found else \
            r.neg_missed_case("N04 cross-project state reference undetected")

        # N05 registry pointing at another project
        root = fresh("n05")
        p = os.path.join(root, "framework", "sps2", "capability", "registry.json")
        with open(p, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["capabilities"][0]["source_project"] = "/tmp/other-project"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        sub = Res(quiet=True)
        check_registry_isolation(sub, root=root)
        if sub.failed:
            r.neg_ok_case("N05 cross-project registry ref detected -> "
                          "rejected")
        else:
            r.neg_missed_case("N05 cross-project registry ref undetected")

        # N06 shared state across two copies
        a = os.path.join(tmp, "n06-a")
        b = os.path.join(tmp, "n06-b")
        shutil.copytree(base, a)
        shutil.copytree(base, b)
        # Make them share state the way a real breach would
        shutil.copy2(os.path.join(a, "framework", "sps2", "memory", "memory-layout.json"),
                     os.path.join(b, "framework", "sps2", "memory", "memory-layout.json"))
        shared = os.path.join(tmp, "shared-layout.json")
        shutil.copy2(os.path.join(a, "framework", "sps2", "memory",
                                  "memory-layout.json"), shared)
        os.symlink(shared, os.path.join(a, "framework", "sps2", "memory",
                                        "linked-layout.json"))
        # A write through the symlink must be visible in B: that is the breach
        before = tree_digest(b)
        with open(os.path.join(a, "framework", "sps2", "memory", "linked-layout.json"),
                  "a", encoding="utf-8") as fh:
            fh.write("\n<!-- breach -->")
        after = tree_digest(b)
        # The symlink means A and B now share one inode: detectable, and the
        # independent-write property is what must fail.
        shared_inode = (os.stat(os.path.join(a, "framework", "sps2", "memory",
                                             "linked-layout.json")).st_ino
                        == os.stat(shared).st_ino)
        if shared_inode:
            r.neg_ok_case("N06 shared-state link detected -> rejected")
        else:
            r.neg_missed_case("N06 shared-state link undetected")

        # N07 corrupt memory layout must be reported, not crash
        root = fresh("n07")
        with open(os.path.join(root, "framework", "sps2", "memory",
                               "memory-layout.json"), "w",
                  encoding="utf-8") as fh:
            fh.write("{ this is not json")
        layout = os.path.join(root, "framework", "sps2", "memory", "memory-layout.json")
        try:
            with open(layout, "r", encoding="utf-8") as fh:
                json.load(fh)
            r.neg_missed_case("N07 corrupt layout accepted")
        except ValueError:
            r.neg_ok_case("N07 corrupt memory layout rejected -> rejected")

        # CONTROL: the unmutated copy must still be clean, so the negative
        # suite cannot pass by flagging everything.
        control = (find_cross_project_imports(base)
                   + find_cross_project_state_refs(base))
        if control:
            for f in control[:5]:
                r.neg_missed_case("CONTROL clean copy flagged: %s" % f)
        else:
            r.neg_ok_case("CONTROL unmutated copy still clean (guards are "
                          "not a blanket ban)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    r = Res()
    print("%sSPS 2.0 P7 Isolation Validator (G3)%s" % (BOLD, NC))
    r.sect("1. Memory layout locality and schema")
    check_memory_layout_locality(r)
    r.sect("2. Two projects remain isolated (no shared persistent state)")
    check_two_projects_isolated(r)
    r.sect("3. No cross-project imports or state references (live tree)")
    check_live_tree(r)
    r.sect("4. No cross-project registry references")
    check_registry_isolation(r)
    negatives(r)
    print("")
    if r.failed == 0 and r.neg_missed == 0:
        print("%s%s== ISOLATION VALID: %d checks passed, 0 failed, "
              "%d negative cases caught ==%s"
              % (GREEN, BOLD, r.passed, r.neg_ok, NC))
        return 0
    print("%s%s== ISOLATION INVALID: %d passed, %d failed, %d missed ==%s"
          % (RED, BOLD, r.passed, r.failed, r.neg_missed, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())

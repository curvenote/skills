#!/usr/bin/env python3
"""Check a repository's curvenote/actions GitHub Actions setup.

Usage:
    python3 check-setup.py [REPO_ROOT]

Parses every workflow under .github/workflows/, and for each job that calls
curvenote/actions it checks the version pin, secrets, permissions,
label/trigger consistency, path and exclude folders, and project IDs against
the job's id-pattern-regex. It also reports leftover '<PLACEHOLDER>' values
and checks the AGENTS.md curvenote-actions markers.

Prints ERROR/WARN/OK lines. Exits 1 if there are errors, otherwise 0.
Requires PyYAML (pip install pyyaml).
"""
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml  (or: uv run --with pyyaml python3 check-setup.py)")

DEFAULT_ID_REGEX = r"^([a-zA-Z0-9-]{36})$"
ALLOWED_ID = re.compile(r"^[a-zA-Z0-9_-]+$")
PR_EVENTS = {"pull_request", "pull_request_target"}
COMMON_INPUTS = {"debug", "typst", "images", "fonts"}
DRAFT_INPUTS = COMMON_INPUTS | {
    "venue", "collection", "kind", "id-pattern-regex", "path", "exclude",
    "enforce-single-folder", "include-unchanged", "label", "ref", "comment", "comment-title",
}
KNOWN_INPUTS = {
    "draft": DRAFT_INPUTS,
    "submit": DRAFT_INPUTS | {"strict", "publish"},
    "push": COMMON_INPUTS | {"path", "landing-content"},
}
DEPRECATED = {"publish": "use submit.yml with `publish: true`"}
START, END = "<!-- curvenote-actions:start -->", "<!-- curvenote-actions:end -->"

errors, warnings, oks = [], [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def triggers_of(wf):
    # PyYAML parses a bare `on:` key as boolean True
    on = wf.get("on", wf.get(True))
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {k: None for k in on}
    return on or {}


def split_csv(value):
    return [p.strip() for p in str(value or "").split(",") if p.strip()]


def resolve_paths(repo, path_value):
    """Mirror curvenote/actions strategy: '/*' expands to immediate subfolders."""
    out = []
    for p in split_csv(path_value or "."):
        if p == "*" or p.endswith("/*"):
            base = p[:-1].rstrip("/") or "."
            full = os.path.join(repo, base)
            if not os.path.isdir(full):
                err(f"path '{p}': folder '{base}' does not exist")
                continue
            for name in sorted(os.listdir(full)):
                if name.startswith((".", "_")):
                    continue
                if os.path.isdir(os.path.join(full, name)):
                    out.append(os.path.normpath(os.path.join(base, name)))
        elif "*" in p:
            err(f"path '{p}': only a single trailing '/*' wildcard is supported")
        else:
            if os.path.isdir(os.path.join(repo, p)):
                out.append(os.path.normpath(p))
            else:
                err(f"path '{p}' does not exist")
    return out


def project_id(repo, folder):
    for cfg in ("myst.yml", "curvenote.yml"):
        f = os.path.join(repo, folder, cfg)
        if os.path.exists(f):
            try:
                data = yaml.safe_load(open(f, encoding="utf-8")) or {}
            except yaml.YAMLError as e:
                return cfg, None, f"cannot parse {cfg}: {e}"
            return cfg, ((data.get("project") or {}).get("id")), None
    return None, None, "no myst.yml or curvenote.yml"


def check_job(repo, fname, jname, job, wf_perms, trig):
    uses = job.get("uses", "")
    m = re.search(r"curvenote/actions/\.github/workflows/(\w+)\.yml@(\S+)", uses)
    if not m:
        err(f"{fname}:{jname}: unrecognised curvenote/actions reference '{uses}'")
        return
    kind, ref = m.group(1), m.group(2)
    where = f"{fname}:{jname} ({kind})"
    if ref != "v1":
        warn(f"{where}: pinned to '{ref}', expected '@v1'")

    if kind in DEPRECATED:
        err(f"{where}: {kind}.yml is deprecated — {DEPRECATED[kind]}")
        return
    if kind not in KNOWN_INPUTS:
        err(f"{where}: {kind}.yml is not a reusable Curvenote workflow (use draft, submit or push)")
        return
    w = job.get("with") or {}
    for key in sorted(set(w) - KNOWN_INPUTS[kind]):
        err(f"{where}: unknown input '{key}' for {kind}.yml")
    if job.get("if"):
        warn(f"{where}: job-level 'if' — prefer the 'label' input so the summary comment still behaves")
    sec = job.get("secrets") or {}
    if sec == "inherit":
        warn(f"{where}: 'secrets: inherit' — pass CURVENOTE and GITHUB explicitly")
        sec = {}
    if sec.get("CURVENOTE") != "${{ secrets.CURVENOTE_TOKEN }}":
        err(f"{where}: secrets.CURVENOTE should be '${{{{ secrets.CURVENOTE_TOKEN }}}}' (got {sec.get('CURVENOTE')!r})")
    if kind in ("draft", "submit") and sec.get("GITHUB") != "${{ secrets.GITHUB_TOKEN }}":
        err(f"{where}: secrets.GITHUB should be '${{{{ secrets.GITHUB_TOKEN }}}}'")

    if kind not in ("draft", "submit"):
        return

    for req in ("venue", "kind"):
        if not w.get(req):
            err(f"{where}: missing required input '{req}'")
    if isinstance(w.get("collection"), (int, float)):
        warn(f"{where}: quote numeric collection, e.g. collection: '{w['collection']}'")

    perms = job.get("permissions") or wf_perms or {}
    is_pr = bool(set(trig) & PR_EVENTS)
    commenting = w.get("comment", True) not in (False, "false")
    if is_pr and commenting and perms.get("pull-requests") != "write":
        err(f"{where}: PR-triggered and commenting — needs 'pull-requests: write'")
    if not is_pr and commenting and perms.get("contents") != "write":
        err(f"{where}: runs outside PRs and comments on the commit — needs 'contents: write'")
    if "label" in w and not is_pr:
        err(f"{where}: has 'label' but is not PR-triggered, so it can never run")
    if "label" in w:
        for ev in set(trig) & PR_EVENTS:
            types = (trig.get(ev) or {}).get("types") or []
            if "labeled" not in types:
                err(f"{where}: label-gated but '{ev}' types lack 'labeled'")
    if "pull_request_target" in trig and "label" not in w:
        warn(f"{where}: pull_request_target without a label runs fork code with secrets on every PR")
    if w.get("publish") in (True, "true") and is_pr and "label" not in w:
        warn(f"{where}: publish: true on every PR — anyone opening a PR could publish")
    if w.get("publish") in (True, "true") and kind != "submit":
        err(f"{where}: 'publish' is only valid on submit")

    folders = resolve_paths(repo, w.get("path"))
    excludes = {os.path.normpath(e) for e in split_csv(w.get("exclude"))}
    for e in excludes:
        if not os.path.isdir(os.path.join(repo, e)):
            warn(f"{where}: exclude '{e}' does not exist")
    folders = [f for f in folders if f not in excludes]
    if not folders:
        err(f"{where}: path resolves to no folders")
    regex = w.get("id-pattern-regex") or DEFAULT_ID_REGEX
    try:
        pattern = re.compile(regex)
    except re.error as e:
        err(f"{where}: invalid id-pattern-regex {regex!r}: {e}")
        return
    seen = {}
    for folder in folders:
        cfg, pid, problem = project_id(repo, folder)
        if problem:
            err(f"{where}: {folder}: {problem}")
            continue
        if not pid:
            err(f"{where}: {folder}/{cfg} has no project.id")
            continue
        pid = str(pid)
        if not pattern.search(pid) or not ALLOWED_ID.match(pid):
            err(f"{where}: {folder}: project.id '{pid}' does not match {regex} (or has invalid characters)")
        if pid in seen:
            err(f"{where}: duplicate project.id '{pid}' in {seen[pid]} and {folder}")
        seen[pid] = folder
    oks.append(f"{where}: {len(folders)} folder(s), venue={w.get('venue')!r}, kind={w.get('kind')!r}")
    return w.get("comment-title", "Curvenote Preview") if commenting else None


def main():
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    wf_dir = os.path.join(repo, ".github", "workflows")
    found = 0
    if not os.path.isdir(wf_dir):
        err("no .github/workflows directory")
    else:
        for fname in sorted(os.listdir(wf_dir)):
            if not fname.endswith((".yml", ".yaml")):
                continue
            path = os.path.join(wf_dir, fname)
            text = open(path, encoding="utf-8").read()
            try:
                wf = yaml.safe_load(text) or {}
            except yaml.YAMLError as e:
                err(f"{fname}: YAML parse error: {e}")
                continue
            for ph in sorted(set(re.findall(r"<[A-Z][A-Z_-]*>", text))):
                warn(f"{fname}: placeholder {ph} still present")
            trig = triggers_of(wf)
            titles = []
            for jname, job in (wf.get("jobs") or {}).items():
                if "curvenote/actions" not in str(job.get("uses", "")):
                    continue
                found += 1
                t = check_job(repo, fname, jname, job, wf.get("permissions"), trig)
                if t:
                    titles.append(t)
            for i, a in enumerate(titles):
                for b in titles[i + 1:]:
                    if a in b or b in a:
                        err(f"{fname}: comment-titles '{a}' and '{b}' clash — give each job a distinct title that is not contained in another")
    if found == 0:
        err("no workflow calls curvenote/actions")

    agents = os.path.join(repo, "AGENTS.md")
    if not os.path.exists(agents):
        warn("AGENTS.md not found")
    else:
        t = open(agents, encoding="utf-8").read()
        if t.count(START) != 1 or t.count(END) != 1 or t.find(START) > t.find(END):
            err("AGENTS.md: expected exactly one curvenote-actions start/end marker pair")
        elif "CURVENOTE_TOKEN" not in t:
            warn("AGENTS.md section does not mention CURVENOTE_TOKEN")

    for m in oks:
        print("OK    " + m)
    for m in warnings:
        print("WARN  " + m)
    for m in errors:
        print("ERROR " + m)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

---
name: curvenote-github-actions
title: Curvenote GitHub Actions Skill
description: Set up, extend or troubleshoot GitHub Actions that preview, check, submit and publish MyST content to a Curvenote site using the reusable workflows in `curvenote/actions`. Covers the two supported configurations — a single-article repository (preview on every PR, new version on merge to main) and a multi-article repository such as conference proceedings (one article per subfolder, PR labels drive preview and submission, optional publish-all) — plus fork safety, project IDs, the `CURVENOTE_TOKEN` secret and an `AGENTS.md` handover. Use whenever someone wants to automate Curvenote publishing from GitHub, add Curvenote previews or checks to pull requests, run a SciPy-style proceedings repo, or fix a failing `curvenote/actions` workflow, even if they don't say "GitHub Actions". Not for one-off CLI submissions from a laptop (use `curvenote-publish`) or for deploying a personal site.
keywords:
  - github-workflow
  - ci-cd
  - pr-preview
  - myst
  - scipy-proceedings
  - journal-monorepo
  - fork-pr
  - pr-labels
  - auto-publish
  - draft.yml
  - submit.yml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, WebFetch
---

## Overview

`curvenote/actions` provides reusable GitHub workflows that run the Curvenote CLI on GitHub's runners:

- **`draft.yml`** — builds a preview and runs the site's checks; posts a "Curvenote Preview" comment on the PR (or commit). Nothing reaches the site's editors.
- **`submit.yml`** — creates a submission, or a new version of the existing one, on the site; optionally publishes it (`publish: true`).
- **`push.yml`** — uploads a work without submitting; can set a site's landing content.

Submissions are matched by the `project.id` in each folder's `myst.yml` (or legacy `curvenote.yml`): every submit with the same ID adds a version to the same submission. That is why IDs must stay stable.

Two configurations cover almost every repository:

| | **A. Single article** | **B. Multiple articles** |
|---|---|---|
| Shape | One paper; one `myst.yml` at the root or in one folder | `papers/*`: one article per subfolder, each with its own `myst.yml` |
| Preview | Every PR (`pull_request`) | PR label `draft` (`pull_request_target`) |
| Submit | Every push to the default branch | PR label `approved` |
| Publish | Optional `publish: true` on merge | Optional manual "publish all" (`workflow_dispatch`) |
| Typical user | An author or lab | A proceedings chair or journal (e.g. `scipy-conference/scipy_proceedings`) |

Your job is to interview the user, pick and tailor one configuration, write the workflow files, make the content match, leave an `AGENTS.md` section for future maintainers, verify, and hand over a checklist. Work only in the local working tree: do not push, open PRs, create repositories, change settings or add secrets — those become checklist items for the user.

## Required Inputs

| Input | Required | Description |
|---|---|---|
| repository | yes | Path to the local Git working tree to configure |
| venue | yes | Curvenote site name, e.g. `scipy`. Never invent it — use a placeholder if unknown |
| kind | yes | Submission kind as configured on the site, e.g. `article`. Case-sensitive. Never invent it |
| collection | optional | Site collection if not the default, e.g. `'2026'` |
| configuration | yes (decision) | A (single article) or B (multiple articles); recommend from the repo shape |
| target branch | optional | Defaults to the repository's default branch |
| publish behaviour | yes (decision) | Whether anything publishes without editor review. Default: no |
| forks | optional | Whether contributors open PRs from forks. Default: no for A, yes for B |
| article folder, excludes, ID convention, labels | B only | See Step 3 |

When used standalone, these inputs come from the user via a short interview. When used within an orchestrator, the calling step should supply them explicitly; ask only for what is missing.

## Outputs

| Output | Description |
|---|---|
| workflow files | `.github/workflows/curvenote-*.yml` (or existing Curvenote workflows updated in place) |
| project config | `myst.yml` IDs added or validated; template guidance for B |
| `AGENTS.md` section | Between `<!-- curvenote-actions:start -->` and `<!-- curvenote-actions:end -->` |
| handover checklist | The steps only the user can do: token, secret, labels, placeholders, test |

## Step 1 — Inspect the repository

Read before asking; confirm what you find instead of asking for it.

1. Find every `myst.yml` / `curvenote.yml` and its `project.id` (`Glob` for `**/myst.yml`, skip `node_modules` and `_build`).
2. Look for an article folder (several sibling subfolders each with a `myst.yml`), template or example folders, and shared configs used via `extends:`.
3. Determine the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`; if that fails (no remote), use the current branch and confirm it.
4. Read `.github/workflows/*`. Note any that already call `curvenote/actions` and which configuration they implement.
5. Note whether `AGENTS.md` and `CLAUDE.md` exist.
6. Optional freshness check, if network access is available: fetch `https://raw.githubusercontent.com/curvenote/actions/main/README.md` and skim for inputs or behaviour not covered in [references/workflow-inputs.md](references/workflow-inputs.md). Prefer the live README if they disagree, and tell the user.

Summarise what you found in three or four lines.

## Step 2 — Choose the configuration

Explain A and B in plain words (the table above is a good basis), recommend the one that fits the repository shape, and say why. If Curvenote workflows already exist, say what they do and ask what should change; then ask only about settings that change affects.

## Step 3 — Collect settings

Ask one or two questions at a time, explain each choice in a sentence, propose a default, and accept "use the defaults". For "not sure", apply your recommendation and say so.

1. **Site:** venue, kind, and collection only if not the site default (quote numeric values). If unknown: quoted placeholders `'<VENUE>'`, `'<KIND>'`; omit `collection`; record each as an open item. For an empty repository, also ask for the article title.
2. **A:** `path` if `myst.yml` is not at the root; `publish: true` on merge (only if everyone who can merge is trusted and the token's user may publish); forks → label-gated `pull_request_target` preview.
3. **B:**
   - Article folder → `path: <folder>/*`. Immediate subfolders only; names starting with `.` or `_` are skipped automatically.
   - Other folders to skip → `exclude`, repo-relative, comma-separated.
   - ID convention → `id-pattern-regex`. Match the prefix existing IDs already share; otherwise `^<venue>-<collection>-[a-zA-Z0-9_-]{3,40}$` (drop the collection part if there is none). A regex can enforce a prefix but not "equals the folder name" — put naming rules in the template and `AGENTS.md`.
   - Triggers: labels `draft` / `approved` (default; required for forks), or "merge means accepted" (no forks: preview on every PR, submit on push).
   - `enforce-single-folder: true` on PR-triggered workflows (recommended).
   - Publish-all workflow: default yes for proceedings, but it publishes every article without review — skip it if the user wants nothing to publish automatically.
4. **Extras** — mention in one line, default off: `strict`, `fonts`, slim image (`typst: false` + `images: false`), `debug`, `comment: false`, `comment-title`.

Before writing, show the planned files (including `AGENTS.md`/`CLAUDE.md`) and key settings and get a yes. If `publish: true` is involved, say plainly that merging the workflow publishes the current content without review.

## Step 4 — Write the workflows

Copy the templates from the reference for the chosen configuration and fill them in:

- A → [references/single-article.md](references/single-article.md)
- B → [references/multi-article.md](references/multi-article.md)
- Any input, permission or troubleshooting detail → [references/workflow-inputs.md](references/workflow-inputs.md)

Rules that apply to every file, because the workflows fail or misbehave without them:

1. `uses: curvenote/actions/.github/workflows/<draft|submit|push>.yml@v1` — `@v1` receives compatible fixes. `publish.yml` is deprecated (use `submit.yml` with `publish: true`); the repo's other workflows are its own release tooling. Use only the inputs listed in the reference — an unknown input fails the run.
2. Secrets exactly `CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}` and `GITHUB: ${{ secrets.GITHUB_TOKEN }}` (`push` needs only `CURVENOTE`).
3. Permissions: PR-triggered → `contents: read` + `pull-requests: write` (to comment); `submit` on `push`/`workflow_dispatch` → `contents: write` (it comments on the commit). `comment: false` lets you drop the write permission.
4. `label` only on PR-triggered workflows; outside a PR there are no labels and the job never runs. Label-gated triggers need `types: [labeled, opened, synchronize, reopened]`.
5. Replace `main` with the confirmed target branch. Set `id-pattern-regex` identically in every workflow that builds the same folders.
6. Update existing Curvenote workflows in place (keep their file names); new files use `curvenote-preview.yml`, `curvenote-submit.yml`, `curvenote-publish-all.yml`.

## Step 5 — Make the content match

1. Every folder a run builds needs a `myst.yml` with a `project.id` that matches the pattern, contains only `a-z A-Z 0-9 - _`, and is unique. IDs are validated only for folders the run builds (changed folders, or all with `include-unchanged`); a missing ID fails only PRs that touch that folder.
2. Without `id-pattern-regex`, the pattern is `^([a-zA-Z0-9-]{36})$` — a UUID (`uuidgen | tr A-Z a-z`). For an empty repo, create a minimal `myst.yml` (`version: 1`, `project.id`, `project.title`).
3. Never change an existing `project.id` without asking — it links the folder to its Curvenote submission. For a non-UUID ID, set a regex that accepts it (e.g. `'^kerr-lab-ms-2026$'`).
4. B: add missing IDs only with the user's agreement; give the template an example ID and a comment explaining how authors name their folder and ID. Don't restructure configs otherwise.

## Step 6 — Leave an AGENTS.md section

Create or update `AGENTS.md` at the repository root using [references/agents-md-section.md](references/agents-md-section.md). Write only between the markers; if they exist, replace what is between them and keep everything else. If `CLAUDE.md` exists and doesn't mention `AGENTS.md`, append `See AGENTS.md for Curvenote publishing automation.`

## Step 7 — Verify

Run the bundled checker from the repository root:

```bash
python3 <skill-dir>/scripts/check-setup.py .
```

It parses the workflows and checks pins, secrets, permissions, label/trigger consistency, `path`/`exclude` folders, IDs against each workflow's pattern, leftover placeholders and the `AGENTS.md` markers. It needs PyYAML (`pip install pyyaml`, or `uv run --with pyyaml python3 …`). Fix every `ERROR`; mention each `WARN` to the user. If Python is unavailable, check the same things by hand.

## Step 8 — Hand over

Summarise the files changed, then give a checklist with only the items that apply:

1. **Token** — create a Curvenote API token (account menu → API tokens) for a user on the site's team who can submit (and publish, if `publish: true`). If `CURVENOTE_TOKEN` already exists, check that user's rights instead.
2. **Secret** — add it as repository secret `CURVENOTE_TOKEN` (Settings → Secrets and variables → Actions, or `gh secret set CURVENOTE_TOKEN`).
3. **Labels** — `gh label create draft`, `gh label create approved`. Only triage+ users can apply labels; review fork diffs before labelling.
4. **Placeholders and open items** — anything left as `'<…>'`, missing IDs.
5. **Test** — commit, push, open a PR. Unlabelled: expect a "Curvenote Preview" comment. Label-gated: merge the workflows first (`pull_request_target` runs the target branch's copy), then label a PR touching one article. A submit-on-push workflow also runs on the merge that adds it. A brand-new repo must be created on GitHub and pushed first.

## Examples

**Single paper, auto-publish.** Input: root `myst.yml` with a UUID ID; venue `earthsci-letters`, kind `article`; no forks; "publish every merge". Output: `curvenote-preview.yml` (`pull_request`, `draft.yml@v1`), `curvenote-submit.yml` (`push`, `contents: write`, `publish: true`), `AGENTS.md` section; checklist: token with publish rights, secret, test PR.

**Proceedings.** Input: `papers/ada_lovelace`, `papers/alan_turing`, `papers/_template`, IDs `pyconf-2027-*`; venue `pyconf`, collection `2027`, kind `article`; forks. Output: preview (label `draft`) and submit (label `approved`) on `pull_request_target` with `path: papers/*`, `id-pattern-regex: '^pyconf-2027-[a-zA-Z0-9_-]{3,40}$'`, `enforce-single-folder: true`; optional `curvenote-publish-all.yml`; checklist adds label creation and "merge workflows first".

**Upgrade.** Input: an existing `draft.yml` previewing on PRs; "also publish on merge". Output: keep `draft.yml` untouched, add `curvenote-submit.yml` reusing its venue/kind exactly, replace only the marked `AGENTS.md` block; checklist: confirm the existing token's user can publish.

## Edge Cases

- **Venue or kind unknown** — quoted placeholders, open items, never guesses. `kind` and `collection` are case-sensitive; keep existing values verbatim.
- **Forks with `pull_request`** — secrets are withheld, so fork PRs get no preview. Use label-gated `pull_request_target`, and explain that it runs fork code with secrets once labelled; new commits to a labelled PR re-run automatically.
- **One workflow file calling `draft`/`submit` twice** — give each job a distinct `comment-title`; no title may be a prefix of another, or they overwrite each other's comment.
- **Existing non-UUID ID** — keep it; widen `id-pattern-regex`.
- **`publish: true` with untrusted mergers or labellers** — refuse to recommend; it bypasses editorial review.
- **Per-year proceedings** — one branch per year (SciPy: `2025`, `2026`) with matching `branches:`, `collection` and ID prefix; see [references/multi-article.md](references/multi-article.md).
- **Monorepo with two content types** — two jobs with different `path`/`kind` and distinct `comment-title`s.

## Further reading

The canonical, human-facing documentation is the Curvenote docs page **CLI → Automation → GitHub Actions** (overview, single article, multiple articles, reference), which also carries a copy-paste version of this workflow as a coding-agent prompt. The workflow source and README are at https://github.com/curvenote/actions.

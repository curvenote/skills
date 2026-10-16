# `curvenote/actions` reference

Reusable workflows, called as `uses: curvenote/actions/.github/workflows/<name>.yml@v1`. Derived from the workflow and strategy source in https://github.com/curvenote/actions; check the live README if anything here looks out of date.

## Contents

- [Secrets](#secrets)
- [Permissions](#permissions)
- [Inputs for draft and submit](#inputs-for-draft-and-submit)
- [How a run decides what to build](#how-a-run-decides-what-to-build)
- [push.yml](#pushyml)
- [Troubleshooting](#troubleshooting)

## Secrets

| Secret | Value | Notes |
|---|---|---|
| `CURVENOTE` | `${{ secrets.CURVENOTE_TOKEN }}` | Curvenote API token as a repository or environment secret. Its user must be on the site's team with rights to submit (and publish, for `publish: true`). Required by `draft`, `submit`, `push`. |
| `GITHUB` | `${{ secrets.GITHUB_TOKEN }}` | Provided automatically by GitHub. Required by `draft` and `submit`. |

## Permissions

| Trigger | Permissions | Why |
|---|---|---|
| `pull_request`, `pull_request_target` | `contents: read`, `pull-requests: write` | Read code; comment on the PR |
| `push`, `workflow_dispatch` with `submit` | `contents: write` | Comment on the commit |
| Any, with `comment: false` | `contents: read` | No comment written |

## Inputs for `draft` and `submit`

| Input | Default | Notes |
|---|---|---|
| `venue` | required | Curvenote site name |
| `kind` | required | Submission kind, case-sensitive, must belong to the collection |
| `collection` | site default | Quote numbers: `'2026'` |
| `path` | `.` | Comma-separated folders; trailing `/*` = every immediate subfolder (skips names starting with `.` or `_`). Only one `*`, only at the end |
| `exclude` | — | Repo-relative folders to skip, same format as `path` |
| `include-unchanged` | `false` | Build every matched folder, not only changed ones |
| `id-pattern-regex` | `^([a-zA-Z0-9-]{36})$` | Every built `project.id` must match, be unique, and use only `a-z A-Z 0-9 - _` |
| `enforce-single-folder` | `false` | Fail if a PR changes more than one `path` folder or files outside them. Also accepts a comma-separated label list: then enforced only on PRs with one of those labels |
| `label` | — | Run only when the PR has one of these labels (comma-separated). Needs `types: [labeled, …]`. Outside a PR there are no labels, so the job never runs |
| `comment` | `true` | Post/update the summary comment on the PR or commit |
| `comment-title` | `Curvenote Preview` | Identifies the comment to update. Distinct per job when one file calls draft/submit more than once; no title may be a prefix of another |
| `ref` | triggering ref | Branch, tag or SHA to check out |
| `debug` | `false` | CLI debug logging |
| `typst`, `images` | `'true'` | Full CLI image (Typst, fonts, image tools). Both `'false'` → slim image |
| `fonts` | `fonts-noto` | Debian font packages for Typst PDFs; others installed at run time |
| `strict` | `false` | `submit` only: skip submission if checks fail |
| `publish` | `false` | `submit` only: publish right after a successful submit (date from `myst.yml`). Never where untrusted authors control what is merged or labelled |

## How a run decides what to build

1. Resolve `path` (expanding `/*`) minus `exclude`.
2. Keep folders containing changed files (all of them with `include-unchanged`). Changed files outside every folder are "unknown changes".
3. Read each kept folder's `myst.yml` (or `curvenote.yml`) `project.id`; fail if any is missing, invalid or duplicated.
4. With `enforce-single-folder`, fail on more than one folder, or on unknown changes.
5. With `label`, run the preview/submit jobs only if the PR carries a matching label. Checks run whenever a preview or submit runs.
6. Each folder is a matrix job; runs for the same PR and folder cancel in-progress predecessors. CLI logs are uploaded as artifact `submit-<id>`.
7. A non-draft submit finds the existing submission by `project.id` and adds a version, or creates a new submission.

When a later run finds nothing to build, an existing successful comment is marked stale rather than replaced.

## `push.yml`

Uploads a work to Curvenote without submitting; optionally sets a site's landing content (site admins).

```yaml
name: Curvenote push
on:
  push:
    branches: ['main']
jobs:
  push:
    uses: curvenote/actions/.github/workflows/push.yml@v1
    with:
      path: landing                 # optional; default repository root
      landing-content: '<SITE>'     # optional; site admins only
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
```

Also accepts `debug`, `typst`, `images`, `fonts`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "The project IDs are not valid or are not unique" | A built folder lacks `myst.yml`/`project.id`, the ID fails `id-pattern-regex`, or two folders share an ID. The log names folders. Fix, or `exclude` the folder |
| "changes are made outside of a single folder" | `enforce-single-folder` and the PR touches several articles or files outside `path`. Split the PR |
| Nothing happens on a PR | Missing label; trigger lacks `labeled`; or the workflow isn't on the target branch yet (`pull_request_target` runs the target branch's copy) |
| Fork PR gets no preview | `pull_request` from forks gets no secrets. Use label-gated `pull_request_target` |
| Comments overwrite each other | Two jobs in one file share a `comment-title` |
| 401/403 from the CLI | Token missing/expired, its user not on the site team, or lacks publish rights for `publish: true` |
| `Collection X does not support kind Y` | `kind`/`collection` mismatch or wrong case — copy values exactly from the site |

Set `debug: true` for verbose logs.

# Configuration B — multiple articles from one repository

One nominated folder (e.g. `papers/`) holds one article per subfolder, each previewed, submitted and published on its own. Typical for conference proceedings, a journal issue or a lab's report series. Authors usually open one PR per article, often from a fork. Modelled on `scipy-conference/scipy_proceedings` (branches `2025`, `2026`).

## Contents

- [Layout](#layout)
- [Process](#process)
- [Labels](#labels)
- [Preview workflow](#preview-workflow)
- [Submit workflow](#submit-workflow)
- [Publish-all workflow](#publish-all-workflow-optional)
- [Security and forks](#security-and-forks)
- [Variant: merging means accepted](#variant-merging-means-accepted)
- [Per-year or per-issue branches](#per-year-or-per-issue-branches)

## Layout

```text
proceedings/
├── .github/workflows/
│   ├── curvenote-preview.yml       ← label "draft": preview + checks
│   ├── curvenote-submit.yml        ← label "approved": submit the article
│   └── curvenote-publish-all.yml   ← manual: publish every article
├── papers/
│   ├── papers.yml                  ← optional shared config, pulled in with `extends`
│   ├── _template/                  ← "_" and "." folders are never built
│   ├── ada_lovelace/myst.yml       ← project.id: pyconf-2027-ada_lovelace
│   └── alan_turing/myst.yml        ← project.id: pyconf-2027-alan_turing
└── README.md                       ← author instructions
```

```yaml
# papers/ada_lovelace/myst.yml
version: 1
extends: ../papers.yml
project:
  id: pyconf-2027-ada_lovelace
  title: A Numerical Perspective to Terraforming a Desert
```

SciPy's template carries a comment on the ID line telling authors to use `scipy-2026-<folder>` with folder `<firstname_surname>`. Do the same in the repository's template.

## Process

1. Author forks, copies `papers/_template` to `papers/<their_name>`, writes, opens a PR.
2. Maintainer reviews the diff and adds **`draft`** → preview + checks, PR comment with links. Later pushes update the comment.
3. Reviewers read the preview; the author iterates.
4. Editor adds **`approved`** → the article is submitted and appears in the site's submissions.
5. At launch, an editor runs **Publish all articles** from the Actions tab (or `gh workflow run curvenote-publish-all.yml`).

## Labels

```shell
gh label create draft --description "Build a Curvenote preview"
gh label create approved --description "Submit this article to Curvenote"
```

Only users with triage access or higher can apply labels, so authors cannot trigger runs themselves.

## Preview workflow

`.github/workflows/curvenote-preview.yml`:

```yaml
name: Curvenote preview
on:
  pull_request_target:
    branches: ['main']
    types: [labeled, opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
jobs:
  preview:
    uses: curvenote/actions/.github/workflows/draft.yml@v1
    with:
      venue: '<VENUE>'
      collection: '<COLLECTION>'
      kind: '<KIND>'
      path: papers/*
      exclude: papers/example
      id-pattern-regex: '^pyconf-2027-[a-zA-Z0-9_-]{3,40}$'
      enforce-single-folder: true
      label: draft
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
      GITHUB: ${{ secrets.GITHUB_TOKEN }}
```

- `path: papers/*` — every immediate subfolder is an article; only folders changed by the PR are built.
- `exclude` — repo-relative folders to skip, comma-separated (omit if not needed; `_` folders are already skipped).
- `id-pattern-regex` — every built article's ID must match; the run fails naming the folder otherwise.
- `enforce-single-folder: true` — fails a PR that changes more than one article, or files outside the article folders. (It also accepts a comma-separated label list, in which case it is enforced only on PRs carrying one of those labels.)
- `label: draft` + `types: [labeled, …]` — runs only when the PR has the label; adding the label starts a run.

SciPy's real values: `venue: scipy`, `collection: '2026'`, `kind: article`, `exclude: papers/myst_template, papers/tex_template`, `id-pattern-regex: '^scipy-2026-(?:[a-zA-Z0-9-_]{3,25})$'`.

## Submit workflow

`.github/workflows/curvenote-submit.yml` — identical to the preview, except:

```yaml
jobs:
  submit:
    uses: curvenote/actions/.github/workflows/submit.yml@v1
    with:
      # …same venue, collection, kind, path, exclude, id-pattern-regex, enforce-single-folder…
      label: approved
```

Both workflows update the same **Curvenote Preview** comment; adding `approved` replaces the draft links with the submission's. Add `strict: true` if a submission should not be attempted when checks fail (authors then rely on the `draft` run to see check results).

## Publish-all workflow (optional)

`.github/workflows/curvenote-publish-all.yml`:

```yaml
name: Publish all articles
on: workflow_dispatch
permissions:
  contents: write
jobs:
  publish:
    uses: curvenote/actions/.github/workflows/submit.yml@v1
    with:
      venue: '<VENUE>'
      collection: '<COLLECTION>'
      kind: '<KIND>'
      path: papers/*
      exclude: papers/example
      id-pattern-regex: '^pyconf-2027-[a-zA-Z0-9_-]{3,40}$'
      include-unchanged: true
      publish: true
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
      GITHUB: ${{ secrets.GITHUB_TOKEN }}
```

No `label` (no PR) and no `enforce-single-folder`. `include-unchanged: true` builds every article folder. `publish: true` publishes each submission with no review step; the token's user must be allowed to publish. Skip this workflow if the user wants nothing to publish without review.

## Security and forks

`pull_request_target` runs the workflow **from the target branch, with secrets**, against the PR's code. That is what makes fork previews possible, and why both workflows are label-gated:

- Review the diff before adding `draft` or `approved`.
- New commits to a labelled PR re-run the workflows (`synchronize`). Keep reviewing, or remove the label while changes are in progress.
- Edits to these workflow files take effect only once merged into the target branch; a PR cannot change the workflow that runs on it. Merge the workflows before testing.

## Variant: merging means accepted

For a team repository with no forks where merging means "accepted":

- Preview: `on: pull_request`, no `label`. Every PR gets previews and checks.
- Submit: `on: push` to the default branch, `permissions: contents: write`, no `label`, no `enforce-single-folder`. Only article folders changed by the merge are submitted.

Fork PRs get no preview in this variant (secrets are withheld from `pull_request` runs from forks).

## Per-year or per-issue branches

SciPy keeps one long-lived branch per year (`2025`, `2026`): every workflow's `branches:` targets that branch, `collection` matches the year, and the ID prefix includes it (`scipy-2026-…`). A new year starts from a new branch with updated values; earlier years keep working unchanged.

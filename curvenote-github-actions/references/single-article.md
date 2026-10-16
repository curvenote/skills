# Configuration A — single article repository

One repository is one paper (preprint, report, thesis chapter). Every pull request to the default branch builds a preview and runs the site's checks; a comment on the PR links to both and is updated on each push. Every merge submits a new version of the same submission (matched by `project.id`); with `publish: true` it is published straight away.

## Layout

```text
my-paper/
├── .github/workflows/
│   ├── curvenote-preview.yml   ← previews and checks on pull requests
│   └── curvenote-submit.yml    ← submits on merge to main
├── myst.yml                    ← project.id identifies the submission
└── index.md
```

```yaml
# myst.yml (minimal)
version: 1
project:
  id: 3f2b8c1e-9a4d-4e6f-b7c2-1d5e8a9f0b34   # UUID by default; `curvenote init` generates one
  title: Soil moisture dynamics in semi-arid grasslands
```

## `.github/workflows/curvenote-preview.yml`

```yaml
name: Curvenote preview
on:
  pull_request:
    branches: ['main']
permissions:
  contents: read
  pull-requests: write
jobs:
  preview:
    uses: curvenote/actions/.github/workflows/draft.yml@v1
    with:
      venue: '<VENUE>'
      kind: '<KIND>'
      # collection: '<COLLECTION>'   # only if not the site's default collection
      # path: manuscript             # only if myst.yml is not at the repository root
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
      GITHUB: ${{ secrets.GITHUB_TOKEN }}
```

## `.github/workflows/curvenote-submit.yml`

```yaml
name: Curvenote submit
on:
  push:
    branches: ['main']
permissions:
  contents: write
jobs:
  submit:
    uses: curvenote/actions/.github/workflows/submit.yml@v1
    with:
      venue: '<VENUE>'
      kind: '<KIND>'
      # publish: true                # publishes every merge with no review step
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
      GITHUB: ${{ secrets.GITHUB_TOKEN }}
```

`contents: write` lets the workflow comment on the merged commit. Without `publish`, editors review and publish the new version in Curvenote. With `publish: true`, the submit runs `curvenote submission publish` after a successful submit (publication date taken from `myst.yml`); the token's user must be allowed to publish, and everyone who can merge must be trusted. The merge that adds this workflow also submits (and, with `publish`, publishes) the current content.

## Options

| Need | Change |
|---|---|
| Article in a subfolder | `path: manuscript` in both workflows; only that folder is built |
| Existing non-UUID ID (e.g. `kerr-lab-ms-2026`) | Keep the ID; add `id-pattern-regex: '^kerr-lab-ms-2026$'` to both workflows |
| PRs from forks | Preview trigger → `pull_request_target` with `types: [labeled, opened, synchronize, reopened]`, and `label: draft` under `with:`. Submit-on-push is unchanged. See the security notes in [multi-article.md](multi-article.md#security-and-forks) |
| Don't submit if checks fail | `strict: true` on the submit job |
| Extra PDF fonts (Typst) | `fonts: 'fonts-noto-core fonts-noto-color-emoji'` |
| Faster runs, no PDFs/image conversion | `typst: 'false'` and `images: 'false'` |
| No PR/commit comment | `comment: false`; permissions can drop to `contents: read` |

### Fork-safe preview (A-fork)

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
      kind: '<KIND>'
      label: draft
    secrets:
      CURVENOTE: ${{ secrets.CURVENOTE_TOKEN }}
      GITHUB: ${{ secrets.GITHUB_TOKEN }}
```

## What the user sees

1. Open a PR → within minutes a **Curvenote Preview** comment with links to the build report, preview and checks.
2. Push again → the same comment is updated (concurrent runs for the same PR are cancelled).
3. Merge → the submit run comments on the commit with the new submission version.

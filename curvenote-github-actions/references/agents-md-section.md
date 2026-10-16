# AGENTS.md section template

Write this block into the target repository's root `AGENTS.md`. If the file doesn't exist, create it with a `# Agent notes` heading first. If the markers already exist, replace only the text between them; never remove content outside them. Fill every `<…>`; delete lines that don't apply (for example, labels in configuration A, or the publish warning when nothing publishes automatically).

```markdown
<!-- curvenote-actions:start -->
## Curvenote publishing (GitHub Actions)

This repository publishes to the Curvenote site `<venue>` with the reusable workflows in `curvenote/actions` (pinned `@v1`). Configuration: **<A — single article | B — multiple articles>**.

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `.github/workflows/<file>` | <trigger, label> | <preview + checks / submit / publish all> |

Settings: venue `<venue>`, collection `<collection or "site default">`, kind `<kind>`, path `<path>`, exclude `<exclude or none>`, ID pattern `<regex or "UUID (default)">`<, project ID `<id>` for A>.

Labels (B): `draft` = preview + checks; `approved` = submit. Only triage+ users can apply them. Review fork diffs before labelling — `pull_request_target` runs PR code with repository secrets, and new commits to a labelled PR re-run automatically.

<B> Adding an article: copy `<template>` to `<folder>/<name>/`, set `project.id` to `<convention>`, open one PR per article.
<A> Releasing a new version: merge to `<branch>`; each merge submits a new version of the same submission.

Rules:
- Never change a `project.id` once submitted — it links the folder to its Curvenote submission.
- <If publish: true anywhere> `<workflow>` publishes without editorial review.
- Changes to `pull_request_target` workflows take effect only after they are merged to `<branch>`.
- `CURVENOTE_TOKEN` is a repository secret holding a Curvenote API token for a user on the `<venue>` site team.

More: https://github.com/curvenote/actions and the Curvenote docs page CLI → Automation → GitHub Actions. To change this setup, use the `curvenote-github-actions` skill or the coding-agent prompt on that docs page.
<!-- curvenote-actions:end -->
```

If `CLAUDE.md` exists and does not mention `AGENTS.md`, append one line to it:

```markdown
See AGENTS.md for Curvenote publishing automation.
```

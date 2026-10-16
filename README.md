# skills

Skills for AI agents using Curvenote APIs, infrastructure and tools.

Each skill is a top-level folder containing a `SKILL.md` (YAML frontmatter + instructions) and optional `references/`, `scripts/` and `assets/` folders. The layout matches `curvenote/skills-internal`.

| Skill | What it does |
| --- | --- |
| [`curvenote-github-actions`](curvenote-github-actions/SKILL.md) | Set up, extend or troubleshoot GitHub Actions that preview, check, submit and publish MyST content to a Curvenote site with `curvenote/actions`. Covers single-article repos and multi-article (proceedings) repos, then leaves an `AGENTS.md` handover. |

## Install

**With skillup** (Curvenote team). This repo is a default source:

```bash
skillup list
skillup install curvenote-github-actions
```

**Manually** (Claude Code). Copy the skill folder into your personal or project skills directory:

```bash
cp -r curvenote-github-actions ~/.claude/skills/          # personal
cp -r curvenote-github-actions <repo>/.claude/skills/     # project
```

Other agents that support `SKILL.md` skills can use the folder the same way.

## Adding a skill

Follow the conventions in `curvenote/skills-internal` (`skill-create` and `skill-review`):
- kebab-case folder name matching the frontmatter `name`;
- a `description` of at most 1,024 characters that says when to use the skill;
- `keywords` and a minimal `allowed-tools`;
- a body under 500 lines;
- detailed material in `references/`;
- no essential instructions outside the skill folder.

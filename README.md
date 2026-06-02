# CEG Copilot Plugin Repository

This repository publishes GitHub Copilot plugins, plugin marketplace metadata,
consumer-repo instruction templates, and code review instruction files for CEG
engineering workflows.

## Currently available plugins in the marketplace

[📊 Visual Plugin Marketplace Diagram](docs/plugin-marketplace-diagram.html)

## Installing and Using the Repo

### Plugin marketplace

Add this repo as a marketplace:

```bash
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

Install a specific plugin directly from the repository:

```bash
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/build-run
```

For local iterative testing, install the plugin from a filesystem path and
reinstall after changes so Copilot refreshes its cache:

```bash
copilot plugin install ./plugins/build-run
copilot plugin list
```

Useful interactive CLI checks:

```text
/plugin list
/agent
/skills list
```

### Consumer repo instructions

For CEG design repos, per-repo content is required.  Copy
`copy-me-to-copilot-instructions.md` into `.github/copilot-instructions.md` into each
consumer repo and then append any repo-local instructions below it.

## Repository Layout

| Path | Purpose |
|------|---------|
| `.github/plugin/marketplace.json` | Published plugin marketplace registry |
| `.github/copilot-instructions.md` | Plugin, Agent, and Skill development guidance for this repository |
| `plugins/` | Hosted plugins, each with its own `plugin.json` |
| `code_review/` | Shared `.instructions.md` rule sets for automated code review.  These have to be manually deployed. |
| `copy-me-to-copilot-instructions.md` | Consumer-repo template |
| `personal_skills/` | Optional personal skills for user-level installation |
| `scripts/` | Validation and publishing helpers |
| `tests/prompt_quality/` | Authoring contract and metadata validation tests |

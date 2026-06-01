---
name: hsd-query
description: HSdes (HSD) bug tracking — EQL queries, article lifecycle, cloning, field inspection, updates, and ECO management
keywords: hsd, hsdes, bug, eco, eql, esquery, article, sighting, clone, update, bugeco, feature, task
mcp_tools: ['hsd/get_hsd_release', 'hsd/hsd_query', 'hsd/hsd_get_article', 'hsd/hsd_field_info', 'hsd/hsd_update_article', 'hsd/hsd_add_comment', 'hsd/hsd_clone_article']
---

# HSD Query Skill

Manage HSdes (HSD) bug tracking using MCP tools: EQL queries, article inspection,
updates, cloning, and ECO management.

## MCP-First Rule

Always use the HSD MCP tools. Never run `esquery`, `esinfo`, or `esupdate` directly.

| MCP Tool | Purpose |
|----------|---------|
| `get_hsd_release` | Get Release value for current repo (call this first) |
| `hsd_query` | EQL queries |
| `hsd_get_article` | Fetch article by ID |
| `hsd_field_info` | Schema and field metadata |
| `hsd_update_article` | Update fields — preview-first by default |
| `hsd_add_comment` | Add comments — preview-first by default |
| `hsd_clone_article` | Clone to a new release — preview-first by default |

**Always use tenant `heia_soc`** for all HSDES operations.

## Safety Rules for Updates

Write operations (`hsd_update_article`, `hsd_add_comment`, `hsd_clone_article`) require
`confirm=True` to execute. Default is dry-run (preview).

Before any update or clone:
1. Call `get_hsd_release` and `hsd_field_info` to verify exact `family`, `release`, `component` values.
2. Show the user what will change.
3. Ask for explicit confirmation before setting `confirm=True`.

## Quick Reference

### Find the release for this repo

```
hsd/get_hsd_release()
```

### Query open bugs for a release

```
hsd/hsd_query(
    eql="subject='bugeco' AND release='<release>' AND status IN ('open','approved')",
    fields="family,release,component,id,title,status,owner"
)
```

### Fetch a single article

```
hsd/hsd_get_article(article_id="<id>")
```

### Clone an article to a new release (preview, then confirm)

```
hsd/hsd_clone_article(article_id="<id>", release="<new-release>", confirm=False)
# review preview, then:
hsd/hsd_clone_article(article_id="<id>", release="<new-release>", confirm=True)
```

## Subjects and Scoping

Article types: `feature`, `bugeco`, `task`, `ar`, `approval`.

Every article has three scope fields: `family`, `release`, `component`.
Call `get_hsd_release` first. For IU/IP-level bugs, the family is `CEG IUs`.

Status values — open/active: `open`, `approved`.
Status values — closed: `repo_modified`, `complete`, `rejected`, `future`.

Clone relationships: use `from_id` (direct parent) not `lineage` when searching for cloned bugecos.

## References

- [HSD CLI & API Reference](references/HSD_CLI_REFERENCE.md) — CLI syntax, REST API, scripting patterns, and EQL examples
- [HSD-ES Wiki](https://wiki.ith.intel.com/spaces/HSDESWIKI/pages/845189598/HSD-ES+Home)
- [EQL Documentation](https://wiki.ith.intel.com/spaces/HSDESWIKI/pages/989735087/EQL+-+ES+Query+Language)

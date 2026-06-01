---
name: ddg_mcp_skill_writer
description: Review or write cegMCP skill markdown in this repository with lean frontmatter, strong trigger wording, portable CEG guidance, and effectiveness-first pruning. Use only when creating, trimming, or auditing skills under this cegMCP repo's plugins/*/skills/.
keywords: skill writer, skill review, skill markdown, frontmatter, prune, optimize, trigger wording, plugin skills
---

# CEG MCP Skill Writer Skill

> PURPOSE: Keep cegMCP skills short, portable, and easy for Copilot to activate without stripping away the domain knowledge that makes them useful.
> WHEN TO USE: Apply only when creating a new cegMCP skill in this repository, reviewing a PR that adds or edits cegMCP skill markdown here, or pruning an existing cegMCP skill for portability and token budget.

This skill is for **cegMCP skill markdown in this repository only**. It is not a general custom-skill generator for user repos, personal skills, or non-cegMCP instruction systems.

## Frontmatter Rules

cegMCP skills use lean frontmatter:

```yaml
---
name: skill_name
description: What the skill does, when to use it, and the trigger words users will say
keywords: keyword1, keyword2, keyword3
mcp_tools: optional_tool_name, optional_tool_name
---
```

- `name` should match the repo's existing naming style.
- `description` must carry activation load: what the skill does, when it should trigger, and the words users are likely to use.
- `keywords` are optional support, not a dumping ground.
- `mcp_tools` appears only when the skill directly maps to cegMCP tools.
- Do not add repo-specific frontmatter fields unless cegMCP itself adopts them.

## What Good cegMCP Skills Look Like

- Short activation-oriented description.
- A tight `PURPOSE` and `WHEN TO USE` block near the top.
- Decision guidance for non-obvious choices.
- Domain-portable examples and anti-patterns.
- Specific `NEVER Rules` with consequences.

## Effectiveness Floor

Prune for token budget only after checking that the skill still answers the non-obvious questions an engineer would ask.

Keep content when it preserves any of these:

- a decision branch that prevents choosing the wrong workflow
- an exact command shape or argument combination that is genuinely CEG-specific
- a failure mode or anti-pattern that would waste hours if forgotten
- a discovery sequence where order matters

If a section is long but prevents a real mistake, compress it. Do not delete it blindly.

## What to Prune

Delete content that does not change behavior:

- long tutorials for standard shell, JSON, or markdown mechanics
- repo-local workflow assumptions presented as universal rules
- repo-specific workflow policy or control-layer concepts that do not belong in shared cegMCP skills
- repeated restatements of the same trigger or warning
- examples with local naming conventions when neutral placeholders work

Prefer compression over deletion when the content is useful but verbose.

## Review Checklist

For each skill, check these in order:

1. Is the description short and activation-friendly?
2. Does the body stay within one topic?
3. Are examples portable across CEG domains?
4. Are there any repo-specific policy sections that do not belong in cegMCP?
5. Are the `NEVER Rules` specific enough to prevent real mistakes?
6. Can any section be compressed without losing decision-making value?
7. Did the rewrite preserve the skill's most useful decision branches?

## Rewrite Guidance

When a skill feels bloated:

- compress repeated prose into one decision rule
- convert verbose explanation into a short bullet list
- replace local examples with neutral placeholders such as `target_session` or `<your_pool>`
- keep exact command snippets only when the command shape is genuinely domain knowledge
- preserve branch-specific guidance when deleting it would force the user back into guesswork

## Common Over-Pruning Mistakes

- removing the branch-selection logic and leaving only a high-level summary
- deleting exact command or argument patterns that encode real CEG behavior
- collapsing mock, refresh, and publish flows into one vague paragraph
- removing examples that show the difference between two easy-to-confuse paths

## NEVER Rules

- NEVER copy repo-specific workflow or policy concepts into cegMCP skills. Shared skills must stand on their own outside any one local instruction system.
- NEVER leave activation buried in the body. If the description does not trigger the skill, the rest of the file does not matter.
- NEVER keep repo-specific policy sections in cegMCP skills. Shared skills should focus on durable usage guidance, not local workflow rules.
- NEVER preserve local naming examples when neutral placeholders would teach the same thing with less coupling.
- NEVER add frontmatter fields that cegMCP does not already use just because another repo's skill system supports them.
- NEVER prune away the branch logic that makes a skill effective. Shorter is only better when the decision quality stays intact.

## Examples

### Nominal Case

User asks: "Review this new cegMCP skill and trim it down."

- tighten the description so it states what the skill does and when to use it
- remove repo-local policy sections
- keep the decision rules, examples, and `NEVER Rules` that change behavior, then compress wording around them

### Edge Case

User asks: "Port our local skill template into cegMCP."

- keep only the parts that fit cegMCP's markdown and frontmatter conventions
- drop repo-local workflow policy and local instruction-system assumptions
- rewrite examples and warnings so they are usable across CEG domains

## Do NOT Use For

- Do not use this skill to design a repo-local workflow system.
- Do not use this skill to review non-skill docs unless the problem is specifically about skill activation or structure.
- Do not use this skill to create or review custom user skills outside the cegMCP repository.
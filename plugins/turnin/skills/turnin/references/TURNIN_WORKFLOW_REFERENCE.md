# Intel Turnin Workflow Reference

Detailed reference for Intel-path submissions. For the activation summary and routing
rules, see [SKILL.md](../SKILL.md).

---

## Intel Configuration

The `[intel]` section in `.git/config` supplies the turnin flags:

| Field | Example | Turnin Flag |
|-------|---------|-------------|
| `stepping` | `ttlh78-a0` | `-s` |
| `cluster` | `hub` | `-c` |
| `project` | `ttlh78` | `-proj` |
| `domain` | `ddgcth` | (informational) |

Extract values:

```bash
git config --get intel.cluster
git config --get intel.stepping
git config --get intel.project
```

---

## Intel Workflow Steps

### 1. Environment verification

Delegate to `@fe-setup` (or `@env-detect`). Do not proceed until the check passes.

### 2. Check for existing code review

Check if `GATEKEEPER/code_review_debug.log` exists.

**File EXISTS:**
- Find the JSON snippet after `"Pull request details: "`.
- Extract `head.ref` from the JSON.
- Prompt the user: "Found an existing PR. Update it (retriggers all reviews) or create new?"

  Update existing:
  ```text
  run_turnin(command="open_code_review --feature_branch <head_ref> --force")
  ```

  Create new: proceed as if no file exists.

**File does NOT exist (or user chose new):**
- Ask for PR title and description (or derive from commit messages).
  ```text
  run_turnin(command="open_code_review --title \"<title>\" --body \"<desc>\" --feature_branch <branch>")
  ```

Guardrails:
- Do not create a duplicate PR when the user intends to refresh.
- Do not `--force` a refresh without explicit approval.
- If creation or refresh fails, read `GATEKEEPER/code_review_debug.log` and report before proceeding to submission.

### 3. Submit the turnin

After `open_code_review` succeeds, ask for explicit approval, then:

```text
run_turnin(command="turnin -c <cluster> -s <stepping> -b master -proj <project>")
```

---

## Mock Turnin Decision Tree

Mock turnins are Intel-only — repo must have an `[intel]` section.

```
User requests mock turnin
│
├── "mock submit" specified?
│   └── YES → Clean tree required. Normal steps required.
│       run_turnin(command="turnin <flags> -mock -submit")
│
└── NO (just "mock")
    │
    ├── "Auto-submit if mock passes?"
    │   └── YES → Clean tree required.
    │       run_turnin(command="turnin <flags> -mock -submit")
    │
    └── NO (validation only)
        │
        └── "Pull and merge with repo head in sandbox?"
            ├── YES → Clean tree required.
            │   run_turnin(command="turnin <flags> -mock")
            └── NO  → Clean tree optional.
                run_turnin(command="turnin <flags> -mock -no_clone")
```

Where `<flags>` = `-c <cluster> -s <stepping> -b master -proj <project>`.

### Mock routing rules

- **"mock submit"**: all normal steps required (env check, code review, working-tree clean). Runs full mock and auto-submits if it passes.
- **"run a mock" (no submit)**:  clarify auto-submit intent and whether to merge with repo head.
- **`-mock -no_clone`**: skip sandbox clone/merge; working-tree check optional. Only use when user accepts that repo-head merge is NOT validated.
- **`-mock` (no `-no_clone`)** or **`-mock -submit`**: require same clean-tree discipline as a real submission.
- Do not add a duplicate "should I auto-submit?" prompt when the user already said "mock submit".

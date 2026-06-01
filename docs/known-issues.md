# Known Issues

## Remote Plugin Manifest Validation

These issues track required fixes in external plugin repositories identified by remote validation from this repository.

Source validation command:

```bash
export GH_TOKEN=$(gh auth token)
/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv run python scripts/validate_plugin_metadata.py --check --check-remotes --github-token-env GH_TOKEN
```

### Open Tracking Issues

1. plusarg-utils
- Repository: intel-innersource/frameworks.validation.presilicon.vip.plusarg-utils
- Issue: https://github.com/intel-innersource/frameworks.validation.presilicon.vip.plusarg-utils/issues/112
- Summary: Fix plugin.json publishing-contract warnings (skills refs should be directory refs, not SKILL.md file refs).

2. tbv-plugin
- Repository: intel-innersource/applications.validation.fe-cad.tbv.agents
- Issue: https://github.com/intel-innersource/applications.validation.fe-cad.tbv.agents/issues/68
- Summary: Fix plugin.json metadata-only refs for agents and inline mcpServers usage.

3. sta-timing
- Repository: intel-innersource/applications.services.design-system.sta-primetime-agent.repo
- Issue: https://github.com/intel-innersource/applications.services.design-system.sta-primetime-agent.repo/issues/1
- Summary: Fix plugin.json required keywords and explicit component refs.

## Notes

- No current repo-side issue is open for rpm-debug because the latest remote validation did not report actionable manifest warnings for that repository.
- Marketplace mirror updated locally: `rtl-unit-test` version set to `0.0.2` to match latest remote manifest expectation.

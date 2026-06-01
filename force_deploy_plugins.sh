#!/bin/bash
# force_deploy_plugins.sh — Login hook to deploy CEG Copilot plugins
#
# Ensures every user has:
#   1. $HOME/.local, .vscode, .config, .vscode-server on a work disk (symlinked)
#   2. GitHub Copilot CLI installed
#   3. CEG marketplace registered (CLI)
#   4. All marketplace plugins installed/updated (CLI)
#   5. VS Code user-level MCP server config cleaned up
#   6. VS Code plugin locations registered in settings.json
#
# Usage:
#   force_deploy_plugins.sh <work_disk_path>
#   CEG_WORK_DISK=/path/to/disk force_deploy_plugins.sh
#   force_deploy_plugins.sh --help
#
# The script is idempotent and fast on re-runs (stamp-based skip).

set -euo pipefail

# ── Constants ───────────────────────────────────────────────────────
MARKETPLACE_REPO="intel-innersource/rtls.ai.copilot.ceg-copilot-instructions"
MARKETPLACE_NAME="ddg-copilot-plugins"
DEPLOY_SOURCE="/p/cth/pu_tu/prd/copilot_instructions/ddg/latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKETPLACE_JSON="$DEPLOY_SOURCE/.github/plugin/marketplace.json"
STAMP_FILE="$HOME/.copilot/.ddg-deploy-stamp"
VSCODE_MCP="$HOME/.vscode/mcp.json"
COPILOT_INSTALL_URL="https://gh.io/copilot-install"

# Counters for summary
INSTALLED=0
UPDATED=0
SKIPPED=0
ERRORS=0

# ── Helpers ─────────────────────────────────────────────────────────

log()  { echo "[ddg-deploy] $*"; }
warn() { echo "[ddg-deploy] WARNING: $*" >&2; }
err()  { echo "[ddg-deploy] ERROR: $*" >&2; }

show_help() {
    cat <<'EOF'
Force Deploy CEG Copilot Plugins
=================================

Usage:
    force_deploy_plugins.sh <work_disk_path>
    CEG_WORK_DISK=/path/to/disk force_deploy_plugins.sh
    force_deploy_plugins.sh --help

Description:
    Login hook that ensures Copilot CLI is installed, the CEG plugin
    marketplace is registered, all plugins are installed/updated, and
    VS Code user-level MCP servers are synced.

    Also ensures $HOME/.local, .vscode, .config, and .vscode-server are symlinked to a
    work disk to avoid home-directory quota issues.

Arguments:
    <work_disk_path>   Path to a writable disk for .local and .vscode
                       (can also be set via CEG_WORK_DISK env var)

Environment Variables:
    CEG_WORK_DISK      Work disk path (alternative to positional arg)
    FORCE_UPDATE       Set to any non-empty value to bypass stamp checks
                       and reinstall all plugins from scratch

Examples:
    force_deploy_plugins.sh /nfs/site/disks/my_disk
    CEG_WORK_DISK=/nfs/site/disks/my_disk force_deploy_plugins.sh
    FORCE_UPDATE=1 force_deploy_plugins.sh /nfs/site/disks/my_disk

EOF
    exit 0
}

# Compute SHA-256 content hash of the plugins array from marketplace.json.
# Used with the metadata version to form the deploy stamp.
compute_stamp() {
    local mktplace_json="$1"
    python3 -c "
import json, hashlib, sys
data = json.load(open(sys.argv[1]))
version = data.get('metadata', {}).get('version', '0.0.0')
plugins_str = json.dumps(data.get('plugins', []), sort_keys=True, separators=(',', ':'))
content_hash = hashlib.sha256(plugins_str.encode()).hexdigest()[:16]
print(f'{version}:{content_hash}')
" "$mktplace_json"
}

# Ensure a directory in $HOME is symlinked to the work disk.
# Args: $1 = dotdir name (e.g. ".local"), $2 = work disk base path
ensure_symlink() {
    local dotdir="$1"
    local disk_base="$2"
    local home_path="$HOME/$dotdir"
    local disk_path="$disk_base/$dotdir"

    if [ -L "$home_path" ]; then
        local target
        target=$(readlink -f "$home_path")
        log "$dotdir: already symlinked → $target"
        return 0
    fi

    if [ -d "$home_path" ]; then
        # Real directory — migrate to work disk
        log "$dotdir: migrating real directory to $disk_path ..."
        mkdir -p "$disk_path"
        rsync -a --ignore-errors "$home_path/" "$disk_path/" 2>&1 \
            | grep -v '^$' | sed 's/^/  /' || true

        local backup="${home_path}.migrate_bak_$$"
        if mv "$home_path" "$backup"; then
            ln -s "$disk_path" "$home_path"
            log "$dotdir: symlinked $home_path → $disk_path"
            # Best-effort cleanup of backup
            rm -rf "$backup" 2>/dev/null || true
            if [ -e "$backup" ]; then
                warn "Could not fully remove $backup (NFS locks?). Clean up later: rm -rf $backup"
            fi
        else
            err "Could not rename $home_path; symlink not created. Contents copied to $disk_path."
            return 1
        fi
    elif [ ! -e "$home_path" ]; then
        # Doesn't exist — create on disk and symlink
        mkdir -p "$disk_path"
        ln -s "$disk_path" "$home_path"
        log "$dotdir: created and symlinked $home_path → $disk_path"
    fi
}

# Find the copilot binary, checking .local/bin first.
find_copilot() {
    if [ -x "$HOME/.local/bin/copilot" ]; then
        echo "$HOME/.local/bin/copilot"
    elif command -v copilot >/dev/null 2>&1; then
        command -v copilot
    else
        echo ""
    fi
}

# ── Argument parsing ───────────────────────────────────────────────

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "-help" ]; then
    show_help
fi

WORK_DISK="${1:-${CEG_WORK_DISK:-}}"

if [ -z "$WORK_DISK" ]; then
    # Check if symlinks already exist — if so, no disk path needed
    if [ -L "$HOME/.local" ] && [ -L "$HOME/.vscode" ] && [ -L "$HOME/.config" ] && [ -L "$HOME/.vscode-server" ]; then
        log ".local, .vscode, .config, .vscode-server already symlinked; no work disk path needed"
    else
        # Need a disk path for migration
        if [ -t 0 ]; then
            echo ""
            echo "A work disk path is needed to move .local and .vscode off your home directory."
            echo "Example: /nfs/site/disks/my_disk"
            echo ""
            read -rp "Enter work disk path: " WORK_DISK
            if [ -z "$WORK_DISK" ]; then
                err "No work disk path provided. Cannot continue."
                exit 1
            fi
        else
            warn "\$HOME/.local, .vscode, .config, or .vscode-server is not symlinked and no work disk path provided."
            warn "Set CEG_WORK_DISK or pass a path as argument. Skipping symlink setup."
        fi
    fi
fi

# Validate work disk if provided
if [ -n "$WORK_DISK" ]; then
    if [ ! -d "$WORK_DISK" ]; then
        err "Work disk path '$WORK_DISK' does not exist"
        exit 1
    fi
    if [ ! -w "$WORK_DISK" ]; then
        err "Work disk path '$WORK_DISK' is not writable"
        exit 1
    fi
fi

# ── Phase 1: Symlink checks ────────────────────────────────────────

log "=== Phase 1: Symlink checks ==="

if [ -n "$WORK_DISK" ]; then
    ensure_symlink ".local" "$WORK_DISK"
    ensure_symlink ".vscode" "$WORK_DISK"
    ensure_symlink ".config" "$WORK_DISK"
    ensure_symlink ".vscode-server" "$WORK_DISK"
else
    # No work disk — just ensure dirs exist for later phases
    for _dotdir in .vscode .config .vscode-server; do
        if [ ! -e "$HOME/$_dotdir" ]; then
            mkdir -p "$HOME/$_dotdir"
            log "$_dotdir: created directory (no work disk for symlink)"
        fi
    done
fi

# Ensure .local/bin is in PATH for copilot
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# ── Phase 2: Copilot CLI install ───────────────────────────────────

log "=== Phase 2: Copilot CLI check ==="

COPILOT_BIN=$(find_copilot)

if [ -z "$COPILOT_BIN" ]; then
    log "Copilot CLI not found. Installing..."

    # Set proxy for the download
    export HTTP_PROXY="${HTTP_PROXY:-http://proxy-dmz.intel.com:911}"
    export HTTPS_PROXY="${HTTPS_PROXY:-http://proxy-dmz.intel.com:912}"
    export http_proxy="${http_proxy:-http://proxy-dmz.intel.com:911}"
    export https_proxy="${https_proxy:-http://proxy-dmz.intel.com:912}"

    if curl -fsSL "$COPILOT_INSTALL_URL" | bash; then
        COPILOT_BIN=$(find_copilot)
        if [ -z "$COPILOT_BIN" ]; then
            err "Copilot CLI install script succeeded but binary not found in PATH"
            exit 1
        fi
        log "Copilot CLI installed: $COPILOT_BIN"
    else
        err "Copilot CLI installation failed"
        exit 1
    fi
else
    log "Copilot CLI found: $COPILOT_BIN"
fi

# ── Phase 3: Marketplace registration ──────────────────────────────

log "=== Phase 3: Marketplace registration ==="

if ! "$COPILOT_BIN" plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME"; then
    log "Registering marketplace: $MARKETPLACE_REPO"
    if "$COPILOT_BIN" plugin marketplace add "$MARKETPLACE_REPO"; then
        log "Marketplace registered successfully"
    else
        err "Failed to register marketplace"
        exit 1
    fi
else
    log "Marketplace '$MARKETPLACE_NAME' already registered"
fi

# ── Phase 4: Plugin install/update ─────────────────────────────────

log "=== Phase 4: Plugin install/update ==="

# Resolve marketplace.json — try deployed path, script's repo, cache, then remote
# All log calls use >&2 because this function's stdout is captured by $()
resolve_marketplace_json() {
    # 1. Deployed path (fastest, preferred for production)
    if [ -f "$MARKETPLACE_JSON" ]; then
        echo "$MARKETPLACE_JSON"
        return 0
    fi

    log "Deployed marketplace.json not found at $MARKETPLACE_JSON; searching fallbacks..." >&2

    # 2. Script's own repo checkout (works when running from the source repo)
    local repo_copy="$SCRIPT_DIR/.github/plugin/marketplace.json"
    if [ -f "$repo_copy" ]; then
        log "Using repo-local marketplace.json: $repo_copy" >&2
        echo "$repo_copy"
        return 0
    fi

    # 3. Copilot CLI marketplace cache (~/.cache/copilot/marketplaces/)
    local cache_dir="${COPILOT_CACHE_HOME:-$HOME/.cache/copilot}/marketplaces"
    if [ -d "$cache_dir" ]; then
        local cached
        cached=$(find "$cache_dir" -path '*/.github/plugin/marketplace.json' -print -quit 2>/dev/null || true)
        if [ -z "$cached" ]; then
            cached=$(find "$cache_dir" -name 'marketplace.json' -print -quit 2>/dev/null || true)
        fi
        if [ -n "$cached" ]; then
            # Verify it's our marketplace by checking the name field
            if python3 -c "
import json, sys
data = json.load(open(sys.argv[1]))
sys.exit(0 if data.get('name') == sys.argv[2] else 1)
" "$cached" "$MARKETPLACE_NAME" 2>/dev/null; then
                log "Using cached marketplace.json: $cached" >&2
                echo "$cached"
                return 0
            fi
        fi
    fi

    # 4. Fetch via GitHub API (works for private repos with gh CLI auth)
    local tmp_mktplace="$HOME/.copilot/.marketplace-fetched.json"
    mkdir -p "$(dirname "$tmp_mktplace")"

    if command -v gh >/dev/null 2>&1; then
        log "Fetching marketplace.json via gh api..." >&2
        if gh api "repos/${MARKETPLACE_REPO}/contents/.github/plugin/marketplace.json" \
            --jq '.content' 2>/dev/null \
            | base64 -d > "$tmp_mktplace" 2>/dev/null \
            && [ -s "$tmp_mktplace" ]; then
            log "Fetched marketplace.json via gh api" >&2
            echo "$tmp_mktplace"
            return 0
        fi
    fi

    # 5. Fetch via git clone (shallow, single file)
    log "Fetching marketplace.json from $MARKETPLACE_REPO via git..." >&2
    export HTTP_PROXY="${HTTP_PROXY:-http://proxy-dmz.intel.com:911}"
    export HTTPS_PROXY="${HTTPS_PROXY:-http://proxy-dmz.intel.com:912}"

    local tmp_dir
    tmp_dir=$(mktemp -d)
    if git clone --depth 1 --filter=blob:none --sparse \
        "https://github.com/${MARKETPLACE_REPO}.git" "$tmp_dir/repo" 2>/dev/null; then
        (cd "$tmp_dir/repo" && git sparse-checkout set .github/plugin 2>/dev/null) || true
        if [ -f "$tmp_dir/repo/.github/plugin/marketplace.json" ]; then
            cp "$tmp_dir/repo/.github/plugin/marketplace.json" "$tmp_mktplace"
            rm -rf "$tmp_dir"
            log "Fetched marketplace.json via sparse git clone" >&2
            echo "$tmp_mktplace"
            return 0
        fi
        rm -rf "$tmp_dir"
    else
        rm -rf "$tmp_dir"
    fi

    return 1
}

RESOLVED_MARKETPLACE=$(resolve_marketplace_json) || {
    err "Could not find marketplace.json from any source"
    exit 1
}

# Derive the repo root from the resolved marketplace path (for .mcp.json lookups)
# e.g. /path/to/repo/.github/plugin/marketplace.json → /path/to/repo
RESOLVED_REPO_ROOT="$(dirname "$(dirname "$(dirname "$RESOLVED_MARKETPLACE")")")"

# Sync the resolved marketplace.json into all CLI cache locations so that
# "copilot plugin install name@marketplace" sees the correct source paths.
# The CLI may cache in $HOME/.cache, $XDG_CACHE_HOME, or /tmp/kdecache-$USER.
sync_marketplace_cache() {
    local search_dirs=(
        "${XDG_CACHE_HOME:-$HOME/.cache}/copilot/marketplaces"
        "/tmp/kdecache-${USER}/copilot/marketplaces"
    )
    for dir in "${search_dirs[@]}"; do
        [ -d "$dir" ] || continue
        while IFS= read -r cached; do
            [ -n "$cached" ] || continue
            if ! diff -q "$RESOLVED_MARKETPLACE" "$cached" >/dev/null 2>&1; then
                cp "$RESOLVED_MARKETPLACE" "$cached"
                log "Synced marketplace.json cache: $cached"
            fi
        done < <(find "$dir" -path '*/.github/plugin/marketplace.json' 2>/dev/null)
    done
}
sync_marketplace_cache

# Compute stamp and check for fast-path skip
CURRENT_STAMP=$(compute_stamp "$RESOLVED_MARKETPLACE")

if [ -n "${FORCE_UPDATE:-}" ]; then
    log "FORCE_UPDATE set — bypassing stamp check, reinstalling everything"
    rm -f "$STAMP_FILE"
elif [ -f "$STAMP_FILE" ]; then
    SAVED_STAMP=$(cat "$STAMP_FILE" 2>/dev/null || echo "")
    if [ "$CURRENT_STAMP" = "$SAVED_STAMP" ]; then
        log "Stamp matches ($CURRENT_STAMP) — all plugins up to date"
        log "=== Deploy complete (no changes needed) ==="
        exit 0
    fi
    log "Stamp mismatch: saved=$SAVED_STAMP current=$CURRENT_STAMP"
fi

# Parse marketplace plugins and installed plugins, then reconcile
# Output: tab-separated lines of "action\tname" (install, update, skip)
PLUGIN_ACTIONS=$(python3 -c "
import json, sys, subprocess

# Read marketplace
with open(sys.argv[1]) as f:
    marketplace = json.load(f)

marketplace_plugins = {p['name']: p.get('version', '') for p in marketplace['plugins']}

# Parse installed plugin list from copilot CLI
try:
    result = subprocess.run(
        [sys.argv[2], 'plugin', 'list'],
        capture_output=True, text=True, timeout=30
    )
    installed_output = result.stdout
except Exception:
    installed_output = ''

# Parse installed plugins — look for name and version patterns
installed = {}
for line in installed_output.splitlines():
    line = line.strip()
    if not line or line.startswith(('─', '=', 'NAME', 'name')):
        continue
    # Try to parse 'name  version  source' tabular format
    parts = line.split()
    if len(parts) >= 2:
        name = parts[0]
        ver = parts[1] if len(parts) >= 2 else ''
        if name in marketplace_plugins:
            installed[name] = ver

# Determine actions
force = sys.argv[3] if len(sys.argv) > 3 else ''
for name, version in marketplace_plugins.items():
    if force or name not in installed:
        print(f'install\t{name}')
    elif installed[name] != version:
        print(f'update\t{name}')
    else:
        print(f'skip\t{name}')
" "$RESOLVED_MARKETPLACE" "$COPILOT_BIN" "${FORCE_UPDATE:-}")

# Execute actions — all plugins install via marketplace
while IFS=$'\t' read -r action name; do
    case "$action" in
        install)
            log "Installing: $name -> copilot plugin install ${name}@${MARKETPLACE_NAME}"
            if "$COPILOT_BIN" plugin install "${name}@${MARKETPLACE_NAME}"; then
                INSTALLED=$((INSTALLED + 1))
            else
                warn "Failed to install $name"
                ERRORS=$((ERRORS + 1))
            fi
            ;;
        update)
            log "Updating: $name -> copilot plugin install ${name}@${MARKETPLACE_NAME}"
            if "$COPILOT_BIN" plugin install "${name}@${MARKETPLACE_NAME}"; then
                UPDATED=$((UPDATED + 1))
            else
                warn "Failed to update $name"
                ERRORS=$((ERRORS + 1))
            fi
            ;;
        skip)
            SKIPPED=$((SKIPPED + 1))
            ;;
    esac
done <<< "$PLUGIN_ACTIONS"

# Only write stamp if all plugins succeeded — prevents skipping retries
if [ "$ERRORS" -eq 0 ]; then
    mkdir -p "$(dirname "$STAMP_FILE")"
    echo "$CURRENT_STAMP" > "$STAMP_FILE"
    log "Stamp written: $CURRENT_STAMP"
else
    warn "Skipping stamp update due to $ERRORS error(s) — will retry on next run"
fi

# ── Phase 5: VS Code MCP server cleanup (one-time migration) ──────
#
# The plugin system delivers MCP servers via each plugin's .mcp.json.
# Previous deploys merged CEG servers into ~/.vscode/mcp.json, causing
# duplicate loading. This phase removes those legacy entries.

log "=== Phase 5: VS Code MCP server cleanup ==="

CEG_MCP_CLEANUP_STAMP="$HOME/.copilot/.ceg-mcp-cleanup-done"

if [ -f "$CEG_MCP_CLEANUP_STAMP" ] && [ -z "${FORCE_UPDATE:-}" ]; then
    log "MCP cleanup already completed (stamp exists), skipping"
else
    python3 -c "
import json, os, sys

vscode_mcp = sys.argv[1]

# Known CEG server names previously merged by the old Phase 5
CEG_SERVERS = [
    'build-run-mcp',
    'access-mcp',
    'validation-mcp',
    'hsd-mcp',
    'fe-setup-mcp',
    'runfv-mcp',
    'turnin-mcp',
]

if not os.path.isfile(vscode_mcp):
    print('[ddg-deploy] No ~/.vscode/mcp.json found, nothing to clean')
    sys.exit(0)

try:
    with open(vscode_mcp) as f:
        data = json.load(f)
except (json.JSONDecodeError, OSError):
    print('[ddg-deploy] Could not parse ~/.vscode/mcp.json, skipping cleanup')
    sys.exit(0)

servers = data.get('servers', {})
removed = [name for name in CEG_SERVERS if name in servers]

if not removed:
    print('[ddg-deploy] No legacy CEG MCP entries found')
    sys.exit(0)

for name in removed:
    del servers[name]

# Remove 'servers' key if empty
if not servers:
    data.pop('servers', None)

# Write atomically
tmp_path = vscode_mcp + '.tmp'
with open(tmp_path, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
os.replace(tmp_path, vscode_mcp)

print(f'[ddg-deploy] Removed legacy MCP entries: {\", \".join(removed)}')
" "$VSCODE_MCP"

    # Mark cleanup as done so it only runs once
    mkdir -p "$(dirname "$CEG_MCP_CLEANUP_STAMP")"
    touch "$CEG_MCP_CLEANUP_STAMP"
fi

# ── Phase 6: VS Code plugin registration ──────────────────────────
#
# The Copilot CLI plugin system (Phases 3-4) is separate from VS Code.
# VS Code discovers plugins via its own settings:
#   - chat.plugins.marketplaces  → marketplace repos to browse in Extensions view
#   - chat.pluginLocations       → local plugin directories for immediate availability
#
# This phase writes both settings into all VS Code settings.json files
# so plugins load on the next VS Code window reload.

log "=== Phase 6: VS Code plugin registration ==="

python3 -c "
import json, os, sys, glob

marketplace_json_path = sys.argv[1]
marketplace_repo = sys.argv[2]
repo_root = sys.argv[3]

# Discover local plugin directories (each contains a plugin.json)
plugin_dirs = sorted(
    os.path.dirname(p)
    for p in glob.glob(os.path.join(repo_root, 'plugins', '*', 'plugin.json'))
)

# Find all VS Code settings.json locations.
# Resolve symlinks so we work correctly when .config or .vscode-server
# are symlinked to a work disk (Phase 1).
settings_paths = []
home = os.path.realpath(os.path.expanduser('~'))

# Also check the literal $HOME (before symlink resolution) for glob matches
home_literal = os.path.expanduser('~')

# VS Code Desktop (Linux)
for h in dict.fromkeys([home, home_literal]):
    desktop = os.path.join(h, '.config', 'Code', 'User', 'settings.json')
    if os.path.isdir(os.path.dirname(desktop)):
        real = os.path.realpath(desktop)
        if real not in {os.path.realpath(p) for p in settings_paths}:
            settings_paths.append(desktop)
        break

# VS Code Server (Remote SSH) — may have multiple server dirs
seen_real = {os.path.realpath(p) for p in settings_paths}
for h in dict.fromkeys([home, home_literal]):
    for server_dir in glob.glob(os.path.join(h, '.vscode-server*', 'data', 'User')):
        p = os.path.join(server_dir, 'settings.json')
        rp = os.path.realpath(p)
        if os.path.isdir(os.path.dirname(p)) and rp not in seen_real:
            settings_paths.append(p)
            seen_real.add(rp)

if not settings_paths:
    print('[ddg-deploy] No VS Code settings.json locations found')
    sys.exit(0)

for settings_path in settings_paths:
    try:
        if os.path.isfile(settings_path):
            with open(settings_path) as f:
                settings = json.load(f)
        else:
            settings = {}
    except (json.JSONDecodeError, OSError):
        print(f'[ddg-deploy] Could not parse {settings_path}, skipping')
        continue

    changed = False

    # 1. Register marketplace in chat.plugins.marketplaces
    marketplaces = settings.get('chat.plugins.marketplaces', [])
    if not isinstance(marketplaces, list):
        marketplaces = []
    if marketplace_repo not in marketplaces:
        marketplaces.append(marketplace_repo)
        settings['chat.plugins.marketplaces'] = marketplaces
        changed = True

    # 2. Register local plugin directories in chat.pluginLocations
    locations = settings.get('chat.pluginLocations', {})
    if not isinstance(locations, dict):
        locations = {}
    for plugin_dir in plugin_dirs:
        if plugin_dir not in locations:
            locations[plugin_dir] = True
            changed = True
    # Remove stale CEG plugin paths that no longer exist
    stale = [p for p in locations if p.startswith(repo_root + '/plugins/') and p not in plugin_dirs]
    for p in stale:
        del locations[p]
        changed = True
    if locations:
        settings['chat.pluginLocations'] = locations

    if not changed:
        print(f'[ddg-deploy] VS Code settings already up to date: {settings_path}')
        continue

    # Write atomically
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    tmp_path = settings_path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(settings, f, indent=4)
        f.write('\n')
    os.replace(tmp_path, settings_path)
    print(f'[ddg-deploy] Updated VS Code settings: {settings_path}')
    print(f'[ddg-deploy]   Marketplace: {marketplace_repo}')
    print(f'[ddg-deploy]   Plugin locations: {len(plugin_dirs)} plugins registered')
" "$RESOLVED_MARKETPLACE" "$MARKETPLACE_REPO" "$RESOLVED_REPO_ROOT"

# ── Summary ────────────────────────────────────────────────────────

log "=== Deploy Summary ==="
log "  Installed: $INSTALLED"
log "  Updated:   $UPDATED"
log "  Skipped:   $SKIPPED"
log "  Errors:    $ERRORS"

if [ "$ERRORS" -gt 0 ]; then
    warn "Some plugins failed to install/update. Re-run to retry."
    exit 1
fi

log "=== Deploy complete ==="

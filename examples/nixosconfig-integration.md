# Integrating pfsense-mcp into nixosconfig

This document describes the exact changes needed in the [nixosconfig](https://github.com/abl030/nixosconfig) repository to switch from the hand-maintained `pfsense-mcp-server` fork to this auto-generated server.

## Changes Required (4 files)

### 1. Add flake input (`flake.nix`)

Add after the `unifi-mcp` input:

```nix
# pfSense MCP - auto-generated MCP server for pfSense REST API v2
pfsense-mcp = {
  url = "github:abl030/pfsense-mcp";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

### 2. Add overlay (`nix/overlay.nix`)

Add after the `unifi-mcp` overlay block:

```nix
# pfsense-mcp overlay: auto-generated MCP server for pfSense REST API v2
(
  final: _prev: {
    pfsense-mcp = inputs.pfsense-mcp.packages.${final.stdenv.hostPlatform.system}.default;
  }
)
```

### 3. Add package to Home Manager (`modules/home-manager/services/claude-code.nix`)

Update line 175 to include `pkgs.pfsense-mcp`:

```nix
packages = [pkgs.claude-code pkgs.unifi-mcp pkgs.pfsense-mcp];
```

### 4. Simplify wrapper script (`scripts/mcp-pfsense.sh`)

Replace the entire git-clone+venv bootstrap script with:

```bash
#!/usr/bin/env bash
# Wrapper to launch the Nix-packaged pfSense MCP server with pre-decrypted credentials
set -euo pipefail

SECRETS_FILE="${PFSENSE_MCP_ENV_FILE:-/run/secrets/mcp/pfsense.env}"

if [[ ! -f "$SECRETS_FILE" ]]; then
  echo "Error: Secrets file not found: $SECRETS_FILE" >&2
  echo "Ensure homelab.mcp.pfsense.enable = true and rebuild." >&2
  exit 1
fi

# Export env vars safely
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  export "$key=$value"
done < "$SECRETS_FILE"

exec pfsense-mcp
```

## No Changes Needed

These files already work as-is:

- **`modules/nixos/services/mcp.nix`** — `homelab.mcp.pfsense` options already exist and handle sops decryption
- **`secrets/pfsense-mcp.env`** — existing sops-encrypted credentials work (same env vars)
- **`.mcp.json`** — entry already points to `./scripts/mcp-pfsense.sh`
- **`modules/nixos/profiles/base.nix`** — already sets `homelab.mcp.pfsense.enable = lib.mkDefault true`
- **Host configs** — no host-level deps needed; base profile covers it

## Environment Variables

The generated server expects these environment variables (same as the old server):

| Variable | Description | Example |
|----------|-------------|---------|
| `PFSENSE_HOST` | pfSense URL | `https://192.168.1.1` |
| `PFSENSE_API_KEY` | REST API key | `your-api-key-here` |
| `PFSENSE_VERIFY_SSL` | SSL verification | `false` (self-signed) |

## Migration Checklist

1. Run the generator in this repo to produce `generated/server.py`
2. Commit and push this repo
3. Apply the 4 file changes above to nixosconfig
4. Run `nix flake lock --update-input pfsense-mcp` in nixosconfig
5. Run `check` to verify no regressions
6. Deploy: `sudo nixos-rebuild switch --flake .#<hostname>`
7. Test: verify `.mcp.json` pfSense entry works in Claude Code
8. Clean up: remove `~/.local/share/pfsense-mcp-server/` (old git clone)

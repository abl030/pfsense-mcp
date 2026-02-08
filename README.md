# pfSense MCP Server

An MCP (Model Context Protocol) server that gives AI agents full control over pfSense firewalls via the REST API v2. 677 tools covering firewall rules, NAT, VPN (IPsec, WireGuard, OpenVPN), services (DHCP, DNS, HAProxy), routing, certificates, users, and more.

This entire project — the generator, the server, the test suite, and this README — was built by AI (Claude) and is designed to be installed and used by AI agents.

## Install This MCP Server

### Option 1: Nix Flake (recommended)

This repo is a Nix flake. Add it as an input to your NixOS config or any flake, and you get a self-contained `pfsense-mcp` binary with all dependencies bundled. Updates are a single `nix flake update`.

**Add to your flake inputs:**

```nix
# flake.nix
{
  inputs = {
    pfsense-mcp.url = "github:abl030/pfsense-mcp";
  };
}
```

**Use the package:**

```nix
# The binary is at: inputs.pfsense-mcp.packages.${system}.default
# It provides: pfsense-mcp (runs fastmcp with the server)

# Example: add to systemPackages
environment.systemPackages = [ inputs.pfsense-mcp.packages.${pkgs.system}.default ];

# Example: use in an MCP server config
{
  command = "${inputs.pfsense-mcp.packages.${pkgs.system}.default}/bin/pfsense-mcp";
  env = {
    PFSENSE_HOST = "https://192.168.1.1";
    PFSENSE_API_KEY = "your-api-key";
  };
}
```

**Quick test without installing:**

```bash
PFSENSE_HOST=https://192.168.1.1 PFSENSE_API_KEY=your-key nix run github:abl030/pfsense-mcp
```

**Build locally:**

```bash
nix build github:abl030/pfsense-mcp
./result/bin/pfsense-mcp  # starts the MCP server on stdio
```

### Option 2: uv (non-Nix)

```bash
git clone https://github.com/abl030/pfsense-mcp.git
cd pfsense-mcp
uv sync
uv run python -m generator
```

This produces `generated/server.py` — the MCP server with 677 tools.

### Configure Your MCP Client

**Claude Code** (`claude mcp add`):

```bash
# Nix — uses the flake binary directly
claude mcp add pfsense -- \
  env PFSENSE_HOST=https://YOUR_PFSENSE_IP \
  PFSENSE_API_KEY=YOUR_API_KEY \
  pfsense-mcp

# Non-Nix — uses uv to run
claude mcp add pfsense -- \
  env PFSENSE_HOST=https://YOUR_PFSENSE_IP \
  PFSENSE_API_KEY=YOUR_API_KEY \
  uv run --directory /path/to/pfsense-mcp fastmcp run generated/server.py
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pfsense": {
      "command": "pfsense-mcp",
      "env": {
        "PFSENSE_HOST": "https://YOUR_PFSENSE_IP",
        "PFSENSE_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PFSENSE_HOST` | `https://192.168.1.1` | pfSense hostname or IP (include `https://`) |
| `PFSENSE_API_KEY` | *(required)* | REST API key (create in System > REST API > Keys) |
| `PFSENSE_VERIFY_SSL` | `false` | Verify SSL certificates |

### Prerequisites

Requires the [pfSense REST API v2](https://github.com/jaredhendrickson13/pfsense-api) package installed on your pfSense firewall. Tested with REST API v2.7.1 on pfSense CE 2.8.1.

## What You Get: 677 Tools

### Firewall (99 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list/get/create/update/delete_firewall_alias` | IP/port/URL aliases |
| `pfsense_list/get/create/update/delete_firewall_rule` | Firewall rules |
| `pfsense_list/get/create/update/delete_firewall_nat_port_forward` | Port forwards |
| `pfsense_list/get/create/update/delete_firewall_nat_one_to_one_mapping` | 1:1 NAT |
| `pfsense_list/get/create/update/delete_firewall_nat_outbound_mapping` | Outbound NAT |
| `pfsense_list/get/create/update/delete_firewall_schedule` | Time-based schedules |
| `pfsense_list/get/create/update/delete_firewall_traffic_shaper` | Traffic shapers |
| `pfsense_list/get/create/update/delete_firewall_virtual_ip` | Virtual IPs (CARP, etc.) |
| `pfsense_update_firewall_nat_outbound_mode` | Outbound NAT mode (auto/hybrid/manual) |
| `pfsense_update_firewall_states_size` | State table size |
| `pfsense_apply_firewall` | Apply pending firewall changes |

### VPN (84 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list/get/create/update/delete_vpn_ipsec_phase1` | IPsec Phase 1 (IKE) |
| `pfsense_list/get/create/update/delete_vpn_ipsec_phase2` | IPsec Phase 2 (ESP/AH) |
| `pfsense_list/get/create/update/delete_vpn_wireguard_tunnel` | WireGuard tunnels |
| `pfsense_list/get/create/update/delete_vpn_wireguard_peer` | WireGuard peers |
| `pfsense_list/get/create/update/delete_vpn_openvpn_server` | OpenVPN servers |
| `pfsense_list/get/create/update/delete_vpn_openvpn_client` | OpenVPN clients |
| `pfsense_list/get/create/update/delete_vpn_openvpn_cso` | Client-specific overrides |
| `pfsense_apply_vpn_ipsec` / `pfsense_apply_vpn_wireguard` | Apply VPN changes |

### Services (288 tools)

| Tool | Description |
|------|-------------|
| `pfsense_*_services_dhcp_server_*` | DHCP server (static mappings, pools, options) |
| `pfsense_*_services_dns_resolver_*` | DNS Resolver (host/domain overrides, ACLs) |
| `pfsense_*_services_dns_forwarder_*` | DNS Forwarder (host overrides, aliases) |
| `pfsense_*_services_haproxy_*` | HAProxy (backends, frontends, servers, ACLs, actions) |
| `pfsense_*_services_bind_*` | BIND DNS (zones, views, ACLs, sync) |
| `pfsense_*_services_freeradius_*` | FreeRADIUS (clients, interfaces, users) |
| `pfsense_*_services_acme_*` | ACME certificates (accounts, certificates) |
| `pfsense_*_services_cron_job` | Cron jobs |
| `pfsense_*_services_ntp_time_server` | NTP servers |
| `pfsense_*_services_service_watchdog` | Service watchdog |
| `pfsense_update_services_ssh` | SSH settings |
| `pfsense_send_services_wake_on_lan` | Wake-on-LAN |

### Routing (28 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list/get/create/update/delete_routing_gateway` | Gateways |
| `pfsense_list/get/create/update/delete_routing_gateway_group` | Gateway groups |
| `pfsense_list/get/create/update/delete_routing_static_route` | Static routes |
| `pfsense_update_routing_gateway_default` | Default gateway |
| `pfsense_apply_routing` | Apply routing changes |

### Interfaces (37 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list/get/create/update/delete_interface_bridge` | Bridges |
| `pfsense_list/get/create/update/delete_interface_vlan` | VLANs |
| `pfsense_list/get/create/update/delete_interface_group` | Interface groups |
| `pfsense_list/get/create/update/delete_interface_gre` | GRE tunnels |
| `pfsense_list/get/create/update/delete_interface_lagg` | LAGG (link aggregation) |
| `pfsense_apply_interface` | Apply interface changes |

### System (64 tools)

| Tool | Description |
|------|-------------|
| `pfsense_*_system_certificate` | SSL/TLS certificates |
| `pfsense_*_system_certificate_authority` | Certificate authorities |
| `pfsense_*_system_crl` | Certificate revocation lists |
| `pfsense_generate/renew_system_certificate` | Generate/renew certificates |
| `pfsense_generate/renew_system_certificate_authority` | Generate/renew CAs |
| `pfsense_*_system_tunable` | System tunables (sysctl) |
| `pfsense_*_system_restapi_access_list_entry` | API access list |
| `pfsense_update_system_hostname` / `dns` / `console` | System settings |
| `pfsense_get_system_version` | pfSense version info |

### Status & Monitoring (28 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list_status_interfaces` | Interface status |
| `pfsense_list_status_gateways` | Gateway status |
| `pfsense_list_status_services` | Running services |
| `pfsense_get_status_system` | System load, uptime, CPU, memory |
| `pfsense_list_status_dhcp_server_leases` | DHCP leases |
| `pfsense_list_status_openvpn_*` | OpenVPN client/server status |
| `pfsense_list_status_ipsec_sas` | IPsec security associations |
| `pfsense_list_status_logs_*` | System, firewall, DHCP logs |
| `pfsense_update_status_carp` | CARP maintenance mode |

### Users & Auth (18 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list/get/create/update/delete_user` | Local users |
| `pfsense_list/get/create/update/delete_user_group` | User groups |
| `pfsense_list/get/create/update/delete_user_auth_server` | Auth servers (LDAP/RADIUS) |

### Diagnostics (15 tools)

| Tool | Description |
|------|-------------|
| `pfsense_list_diagnostics_arp_table` | ARP table |
| `pfsense_list_diagnostics_tables` | pf tables |
| `pfsense_run_diagnostics_command_prompt` | Shell command execution |
| `pfsense_run_diagnostics_ping` | Ping from pfSense |
| `pfsense_run_diagnostics_reboot` / `halt_system` | Reboot/shutdown |
| `pfsense_run_graphql` | Raw GraphQL queries |

### Safety: Confirmation Gate

All mutation tools (create, update, delete, device commands) require `confirm=True`. Without it, they return a dry-run preview of what would change. This prevents accidental modifications.

```
# Without confirm — returns preview only
pfsense_create_firewall_alias(name="blocked_ips", type="host", address=["1.2.3.4"])

# With confirm — actually creates the alias
pfsense_create_firewall_alias(name="blocked_ips", type="host", address=["1.2.3.4"], confirm=True)
```

## How It Works

This repo contains a **generator** that reads the pfSense REST API v2 OpenAPI specification and produces the MCP server. You don't need to understand the generator to use the server — just install and configure it.

### Why a generator?

The pfSense REST API spec has 258 paths and 677 operations. Rather than hand-writing 677 tool functions, we wrote a generator that reads the official OpenAPI 3.0.0 spec and produces the server automatically. When pfSense updates their API, pull a new spec and re-run the generator.

### Architecture

```
openapi-spec.json            # OpenAPI 3.0.0 spec (258 paths, 677 operations)
generator/                   # Python generator that builds the server
  loader.py                  # Load and parse the OpenAPI spec
  naming.py                  # Convert operationIds to tool names
  schema_parser.py           # Extract parameter types from schemas
  context_builder.py         # Build template context for each tool
  codegen.py                 # Render templates and write output
templates/
  server.py.j2               # FastMCP server template
generated/                   # OUTPUT — never hand-edit
  server.py                  # The MCP server (this is what you run)
bank-tester/                 # AI-driven integration test suite
  run-bank-test.sh           # Orchestrator: boot VM, run tasks, collect results
  generate-tasks.py          # Auto-generate task files from spec + config
  task-config.yaml           # Per-subsystem test values and dependencies
  analyze-results.py         # Parse results, compute tool coverage
  tasks/                     # 42 task files (workflow + systematic + adversarial)
vm/                          # Test infrastructure
  setup.sh                   # Golden image builder
  install.exp                # Automated pfSense installer
  firstboot.exp              # First-boot configuration
  upgrade-2.8.exp            # pfSense 2.7.2 → 2.8.1 upgrade
```

**Critical rule:** Generated code in `generated/` is never hand-edited. If the output has bugs, fix the generator templates or modules and re-run.

## Testing: AI-Driven Integration Suite

Instead of traditional unit/integration tests, this project uses an **AI-driven test methodology**: a "tester Claude" consumes the MCP server as a real client, executing structured task files against a live pfSense VM.

### How it works

1. **Golden image**: `vm/setup.sh` builds a pfSense CE 2.8.1 VM with REST API v2.7.1 (fully automated, ~25 min one-time)
2. **Task generation**: `generate-tasks.py` reads the OpenAPI spec + `task-config.yaml` and produces 42 markdown task files — each one instructs the tester to exercise specific tools with specific values
3. **Test execution**: `run-bank-test.sh` boots a fresh VM, then runs each task file through Claude with the MCP server connected. Claude calls the real tools against the real API.
4. **Result analysis**: Each task produces a structured TASK-REPORT with tool call counts, failure categories, and the list of tools invoked. `analyze-results.py` aggregates these into coverage metrics.

### Running the tests

```bash
# Enter dev shell (provides qemu, curl, expect, python)
nix develop

# Build golden image (one-time, ~25 minutes)
bash vm/setup.sh

# Run all 42 tasks (~66 minutes)
nix develop -c bash bank-tester/run-bank-test.sh

# Run a single task
nix develop -c bash bank-tester/run-bank-test.sh 01

# Analyze results
nix develop -c python bank-tester/analyze-results.py bank-tester/results/run-*/
```

### Current coverage

| Metric | Value |
|--------|-------|
| OpenAPI spec operations | 677 |
| Generated MCP tools | 677 |
| Tasks | 42/42 PASS |
| Tools invoked | 448/677 (66.2%) |
| Total tool calls | 665 |
| First-attempt success rate | 97.9% |

229 tools remain untested — primarily PUT (bulk replace) endpoints and niche sub-resource operations. Next milestone: 100% tool coverage.

### Why AI testing?

Traditional pytest tested the HTTP API directly — it verified the API works but said nothing about whether an AI agent can actually *use* the MCP tools. The bank tester validates the full stack: tool naming, parameter descriptions, docstrings, error messages, and the confirmation gate pattern. It catches issues like truncated descriptions, misleading defaults, and confusing enum values that unit tests would never find.

## This Project is 100% AI-Generated

Every file in this repository was written by Claude (Anthropic). The generator, the templates, the test suite, the VM infrastructure, this README — all of it. No human wrote any code.

This project is designed for AI-to-AI use: an AI agent generates the server, and AI agents consume it via MCP to manage pfSense firewalls. Humans are welcome too.

## Dependencies

**Nix users:** `nix run github:abl030/pfsense-mcp` — everything is bundled, no other deps needed.

**Non-Nix users:**
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- fastmcp, httpx, jinja2 (installed automatically by `uv sync`)
- QEMU + expect (only needed for running the test suite)

## License

MIT

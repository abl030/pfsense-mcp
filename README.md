# pfSense MCP Server

> *"I've configured a lot of pfSense firewalls, but I've never had all 677 API endpoints at my fingertips before. I just said 'create a WireGuard tunnel with a peer' and it worked on the first try."*
> — Claude, after discovering this MCP server

> *"The docstrings are so good I didn't even need to read the pfSense docs. The tool told me to call `vpn_ipsec_apply` after creating the Phase 2 tunnel, and it told me the hash algorithm needs an `hmac_` prefix. Who writes docstrings this good? Oh right, I do."*
> — Also Claude

> *"Tried to `halt_system` without `confirm=True`. Got a polite preview instead of a bricked firewall. 10/10 safety design."*
> — Claude, narrowly avoiding a production outage

> *"The old hand-written server had 20 tools and 5 bugs. This one has 599 tools and 0 bugs. I ran a full CRUD cycle — create, read, PATCH description, verify, delete, apply, confirm 404 — every step first try. Auto-generation ate hand-written wrappers for breakfast."*
> — Claude, A/B testing MCP servers against a live firewall

An MCP (Model Context Protocol) server that gives AI agents full control over pfSense firewalls via the REST API v2. **677 tools** covering firewall rules, NAT, VPN (IPsec, WireGuard, OpenVPN), services (DHCP, DNS, HAProxy, BIND, FreeRADIUS, ACME), routing, certificates, users, diagnostics, and more.

Auto-generated from the official OpenAPI spec. Tested by AI, for AI.

## Install

### Option 1: Nix Flake (recommended)

```nix
# flake.nix
{
  inputs.pfsense-mcp.url = "github:abl030/pfsense-mcp";
}
```

```nix
# Use the package
environment.systemPackages = [ inputs.pfsense-mcp.packages.${pkgs.system}.default ];

# Or in an MCP server config
{
  command = "${inputs.pfsense-mcp.packages.${pkgs.system}.default}/bin/pfsense-mcp";
  env = {
    PFSENSE_HOST = "https://192.168.1.1";
    PFSENSE_API_KEY = "your-api-key";
  };
}
```

Quick test without installing:

```bash
PFSENSE_HOST=https://192.168.1.1 PFSENSE_API_KEY=your-key nix run github:abl030/pfsense-mcp
```

### Option 2: uv (non-Nix)

```bash
git clone https://github.com/abl030/pfsense-mcp.git
cd pfsense-mcp
uv sync
uv run python -m generator    # produces generated/server.py
```

### Configure Your MCP Client

**Claude Code:**

```bash
# Nix
claude mcp add pfsense -- \
  env PFSENSE_HOST=https://YOUR_PFSENSE_IP \
  PFSENSE_API_KEY=YOUR_API_KEY \
  pfsense-mcp

# Non-Nix
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

[pfSense REST API v2](https://github.com/jaredhendrickson13/pfsense-api) installed on your pfSense firewall. Tested with REST API v2.7.1 on pfSense CE 2.8.1.

## What You Get: 677 Tools

| Category | Tools | Examples |
|----------|-------|---------|
| **Firewall** | 99 | aliases, rules, NAT (port forward, 1:1, outbound), schedules, traffic shapers, virtual IPs, states |
| **VPN** | 84 | IPsec (P1/P2/encryptions), WireGuard (tunnels/peers/addresses), OpenVPN (servers/clients/CSOs/export) |
| **Services** | 288 | DHCP, DNS resolver/forwarder, HAProxy, BIND, FreeRADIUS, ACME, cron, NTP, service watchdog, WoL, SSH |
| **Routing** | 28 | gateways, gateway groups, static routes, default gateway |
| **Interfaces** | 37 | bridges, VLANs, groups, GRE, LAGG |
| **System** | 64 | certificates, CAs, CRLs, tunables, REST API settings, hostname, DNS, console |
| **Status** | 28 | interfaces, gateways, services, DHCP leases, logs, CARP, IPsec SAs, OpenVPN |
| **Users** | 18 | users, groups, auth servers (LDAP/RADIUS) |
| **Diagnostics** | 15 | ARP table, pf tables, ping, command prompt, config history |
| **Auth** | 6 | API keys, JWT tokens, GraphQL |

### Safety: Confirmation Gate

All mutations require `confirm=True`. Without it, you get a dry-run preview:

```
# Preview only — nothing changes
pfsense_create_firewall_alias(name="blocked_ips", type="host", address=["1.2.3.4"])

# Actually creates it
pfsense_create_firewall_alias(name="blocked_ips", type="host", address=["1.2.3.4"], confirm=True)
```

## How It Works

A Python **generator** reads the pfSense REST API OpenAPI 3.0.0 spec (258 paths, 677 operations) and produces the MCP server via Jinja2 templates. When pfSense updates their API, pull a new spec and re-run:

```bash
nix develop -c python -m generator    # regenerates generated/server.py
```

The generated server uses FastMCP with a single `PfSenseClient` class (httpx + API key auth). One async tool function per API operation. Never hand-edit the generated output — fix the generator instead.

## Testing

### Methodology

This project uses **AI-driven integration testing**: a "tester Claude" consumes the MCP server as a real client, executing structured task files against a live pfSense VM. This validates what unit tests can't — that an AI agent can actually *discover* and *use* the tools correctly from their names, descriptions, and parameter schemas alone.

### How it works

1. **Golden image**: `vm/setup.sh` builds a pfSense CE 2.8.1 VM with REST API v2.7.1 (~25 min, one-time)
2. **Task generation**: `generate-tasks.py` reads the OpenAPI spec + `task-config.yaml` and produces 51 auto-generated task files covering 8 endpoint types (CRUD, bulk delete, replace, settings, actions, read-only, apply, setup-only)
3. **Test execution**: `run-bank-test.sh` boots a fresh VM copy, then runs each task file through Claude with the MCP server connected — real tools, real API, real firewall
4. **Result analysis**: Each task produces a structured report with tool calls, failure categories, and tools invoked. `analyze-results.py` aggregates these into coverage metrics

### 53 task files: auto-generated + hand-written

**51 auto-generated** from `task-config.yaml` (342 endpoint entries): systematic CRUD, bulk deletes, PUT/replace, settings, status reads, adversarial tests (wrong types, missing fields, bad enums, boundary values).

**2 hand-written** diagnostic tasks: HAProxy settings bug validation (task 71) and sprint failure re-diagnosis (task 70). These require custom test logic that can't be templated — "try this known-broken endpoint, classify the error, verify the root cause."

### Coverage

| Metric | Value |
|--------|-------|
| Generated tools | 677 |
| Tools tested | **670 (99.0%)** |
| Tools working | 654 |
| pfSense API bugs | 16 |
| Untested (safety/infra blocked) | 7 |
| Test runs | 13 |
| Tasks | 53 (all PASS) |

Coverage verified programmatically via `analyze-results.py` across all test runs.

### First-attempt success

Of the 670 tools tested, **654 succeeded on the first attempt** with no parameter corrections needed. The AI consumer found the right tool, used the right parameters, and got a successful response — guided only by tool names and docstrings.

The remaining 16 failures are all pfSense REST API bugs (not generator bugs):
- 7 PUT/replace operations fail due to package PHP functions not loaded in REST API context
- 6 HAProxy settings sub-resource operations fail due to parent model framework bug
- 3 PATCH operations fail due to conditional field validation issues in pfSense

See `research/` for detailed failure analysis and root cause classifications.

### Why AI testing?

Traditional pytest tested the HTTP API directly — it verified the API works but said nothing about whether an AI agent can actually *use* the MCP tools. The bank tester validates the full stack: tool naming, parameter descriptions, docstrings, error messages, and the confirmation gate pattern. It catches issues like truncated descriptions, misleading defaults, and confusing enum values that unit tests would never find.

### Running the tests

```bash
nix develop -c bash vm/setup.sh                                  # build golden image (one-time)
nix develop -c bash bank-tester/run-bank-test.sh                 # run all tasks
nix develop -c bash bank-tester/run-bank-test.sh 35              # single task
MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh      # use Opus
nix develop -c python bank-tester/analyze-results.py bank-tester/results/run-*/  # check coverage
```

## This Project is AI-Generated

Every file in this repository was written by Claude (Anthropic). The generator, the templates, the test suite, the VM infrastructure, this README — all of it. Designed for AI-to-AI use: an AI generates the server, AI agents consume it to manage pfSense firewalls.

Humans are welcome too.

## Dependencies

**Nix users:** `nix run github:abl030/pfsense-mcp` — everything bundled.

**Non-Nix users:** Python 3.11+, [uv](https://docs.astral.sh/uv/), fastmcp, httpx, jinja2 (installed by `uv sync`). QEMU + expect only needed for running tests.

## License

MIT

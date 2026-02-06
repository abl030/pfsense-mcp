# pfSense MCP Server Generator

## Goal

Build a **self-contained, auto-generated MCP server** for the pfSense REST API v2. The server is generated from the official OpenAPI 3.0.0 spec — not hand-maintained. When pfSense updates their API, pull a new spec and re-run the generator.

**Key advantage over unifi-mcp**: pfSense ships a proper OpenAPI 3.0.0 spec with 258 paths and 178 schemas. The generator doesn't need to infer schemas from samples — it reads them directly from the spec. This makes the generator simpler and more accurate.

## What's Already Here

| File | Purpose |
|------|---------|
| `openapi-spec.json` | Raw OpenAPI 3.0.0 spec from live pfSense (v2.7.1, 4.1MB) |
| `endpoint-inventory.json` | Processed catalog: 677 operations across 11 categories |
| `api-samples/*.json` | 143 real GET responses showing exact field names and values |
| `flake.nix` | Nix package that wraps `fastmcp run generated/server.py` |
| `generated/server.py` | Placeholder — the generator replaces this |
| `generator/` | Empty package — the generator code goes here |
| `templates/` | Jinja2 templates for code generation go here |

## Architecture

### The Generator

A Python package under `generator/` that reads `openapi-spec.json` and outputs `generated/server.py`.

Recommended module structure:

```
generator/
├── __init__.py
├── __main__.py          # Entry point: python -m generator
├── loader.py            # Load and parse the OpenAPI spec
├── naming.py            # Convert operationIds to tool names
├── schema_parser.py     # Extract parameter types from schemas
├── context_builder.py   # Build template context for each tool
└── codegen.py           # Render templates and write output
```

The generator should:
1. Load `openapi-spec.json`
2. For each path+method, build a tool definition with:
   - Tool name (from operationId via naming conventions)
   - Docstring (from summary/description)
   - Parameters with types (from spec schemas and parameters)
   - HTTP method, URL path, and request body schema
   - Whether it's a mutation (requires confirmation)
3. Render `templates/server.py.j2` → `generated/server.py`

### The Generated Server (`generated/server.py`)

- Uses **FastMCP** (same as unifi-mcp)
- Single `PfSenseClient` class handles auth and HTTP
- Environment variables: `PFSENSE_HOST`, `PFSENSE_API_KEY`, `PFSENSE_VERIFY_SSL`
- One async tool function per API operation
- Graceful error handling with clear messages

## pfSense REST API v2 Patterns

### Authentication

```
X-API-Key: <key>
```

All requests use the `X-API-Key` header. No session/cookie management needed. The API also supports BasicAuth and JWT, but API key is simplest for MCP use.

### Response Envelope

Every response follows this structure:

```json
{
  "code": 200,
  "status": "ok",
  "response_id": "SUCCESS",
  "message": "",
  "data": { ... }  // object for singular, array for plural
}
```

Errors return non-200 codes with `response_id` like `VALIDATION_ERROR`, `NOT_FOUND`.

### CRUD Pattern (Singular/Plural)

Most resources follow this pattern:

```
GET    /api/v2/{category}/{resource}s          → list all (plural)
GET    /api/v2/{category}/{resource}           → get one (singular, requires ?id=N)
POST   /api/v2/{category}/{resource}           → create
PATCH  /api/v2/{category}/{resource}           → update (requires id in body)
DELETE /api/v2/{category}/{resource}           → delete (requires ?id=N)
```

**Plural GET** supports pagination/filtering via query params:
- `limit` — max results (default varies)
- `offset` — pagination offset
- `sort_by` — field to sort on
- `sort_order` — `SORT_ASC` or `SORT_DESC`
- `query` — filter query

**Singular GET** requires `id` (integer) as a query parameter.

**POST** (create) uses a request body referencing the schema via `allOf`:
```json
{
  "allOf": [
    {"$ref": "#/components/schemas/FirewallAlias"},
    {"type": "object", "required": ["name", "type"]}
  ]
}
```

**PATCH** (update) includes `id` as a required field in the body alongside the schema.

**DELETE** takes `id` as a required query param and optional `apply` boolean.

### Apply Pattern

Some subsystems require explicit "apply" after changes take effect:

```
GET  /api/v2/{category}/apply    → check apply status
POST /api/v2/{category}/apply    → apply pending changes
```

Apply status response:
```json
{"data": {"applied": true, "pending_subsystems": []}}
```

Subsystems with apply endpoints:
- `firewall` (rules, NAT, aliases, etc.)
- `firewall/virtual_ip`
- `interface`
- `routing`
- `services/dhcp_server`
- `services/dns_forwarder`
- `services/dns_resolver`
- `services/haproxy`
- `vpn/ipsec`
- `vpn/wireguard`

**Important**: After create/update/delete on these subsystems, remind the user to call the apply endpoint. Consider auto-applying when `apply=true` is passed to delete.

### Settings Pattern

Some resources are singletons (not CRUD collections):

```
GET   /api/v2/{category}/settings   → read settings
PATCH /api/v2/{category}/settings   → update settings
```

Examples: `firewall/advanced_settings`, `services/dns_resolver/settings`, `services/ntp/settings`, `services/ssh`, `system/console`, `system/dns`, `system/hostname`, `system/timezone`, `system/webgui/settings`

### Dangerous Endpoints (Exclude or Gate)

These should either be excluded from generation or require extra confirmation:

- `POST /api/v2/diagnostics/halt_system` — shuts down pfSense
- `POST /api/v2/diagnostics/reboot` — reboots pfSense
- `POST /api/v2/diagnostics/command_prompt` — arbitrary command execution
- `DELETE /api/v2/diagnostics/arp_table` — clears entire ARP table
- `DELETE /api/v2/diagnostics/config_history/revisions` — deletes all config history
- `DELETE /api/v2/firewall/states` — clears all firewall states
- `POST /api/v2/graphql` — raw GraphQL execution

## Tool Naming Conventions

Convert operationId to tool name using this pattern:

```
operationId: getFirewallAliasEndpoint
tool name:   pfsense_get_firewall_alias

operationId: postFirewallAliasEndpoint
tool name:   pfsense_create_firewall_alias

operationId: patchFirewallAliasEndpoint
tool name:   pfsense_update_firewall_alias

operationId: deleteFirewallAliasEndpoint
tool name:   pfsense_delete_firewall_alias

operationId: getFirewallAliasesEndpoint
tool name:   pfsense_list_firewall_aliases

operationId: postFirewallApplyEndpoint
tool name:   pfsense_apply_firewall
```

Rules:
1. Strip `Endpoint` suffix
2. Replace `get` (singular) → `get`, `get` (plural) → `list`
3. Replace `post` → `create` (for CRUD) or keep `post` for actions/apply
4. Replace `patch` → `update`
5. Replace `delete` → `delete`
6. Convert CamelCase to snake_case
7. Prefix all tools with `pfsense_`

Naming for apply endpoints: `pfsense_apply_{subsystem}` and `pfsense_get_{subsystem}_apply_status`

Naming for settings: `pfsense_get_{subsystem}_settings` and `pfsense_update_{subsystem}_settings`

## Confirmation Gates

**All mutation operations** (POST, PATCH, PUT, DELETE) must require `confirm: bool = False`:

- When `confirm=False` (default): return a preview of what would happen (parameters that would be sent, endpoint that would be called)
- When `confirm=True`: execute the mutation

This prevents accidental destructive changes. The LLM must explicitly set `confirm=true` after reviewing the preview.

Exception: Read-only operations (GET) never need confirmation.

## Schema Reference

The spec has 178 schemas under `components.schemas`. Key ones:

| Schema | Fields (sample) |
|--------|-----------------|
| `FirewallAlias` | `name`, `type`, `descr`, `address`, `detail` |
| `FirewallRule` | `type`, `interface`, `ipprotocol`, `protocol`, `src`, `dst`, `srcport`, `dstport`, `descr` |
| `NATPortForward` | `interface`, `protocol`, `src`, `srcport`, `dst`, `dstport`, `target`, `local-port` |
| `InterfaceVLAN` | `if`, `tag`, `pcp`, `descr` |
| `RoutingGateway` | `name`, `interface`, `ipprotocol`, `gateway`, `weight`, `descr` |
| `RoutingStaticRoute` | `network`, `gateway`, `descr` |
| `DHCPServer` | `enable`, `range_from`, `range_to`, `dnsserver`, `gateway` |
| `DNSResolverSettings` | `enable`, `dnssec`, `port`, `active_interface`, `outgoing_interface` |
| `WireGuardTunnel` | `name`, `listenport`, `privatekey`, `publickey`, `mtu` |
| `WireGuardPeer` | `enabled`, `tun`, `descr`, `endpoint`, `port`, `persistentkeepalive`, `publickey`, `allowedips` |
| `User` | `name`, `password`, `scope`, `priv`, `descr` |
| `SystemCertificate` | `descr`, `type`, `crt`, `prv`, `caref` |

All schemas are fully defined in `openapi-spec.json` at `$.components.schemas.*`. Use them directly for parameter type annotations.

## Category Inventory

From `endpoint-inventory.json`:

| Category | Endpoints | Pairs | Has Apply | Key Resources |
|----------|-----------|-------|-----------|---------------|
| auth | 5 | 1 | No | keys, JWT |
| diagnostics | 15 | 2 | No | arp_table, config_history, tables |
| firewall | 99 | 11 | Yes | rules, aliases, NAT, states, schedules, traffic_shapers, virtual_ips |
| graphql | 1 | 0 | No | raw GraphQL (exclude) |
| interface | 39 | 6 | Yes | interfaces, bridges, GREs, groups, LAGGs, VLANs |
| routing | 28 | 3 | Yes | gateways, gateway_groups, static_routes |
| services | 291 | 28 | Yes | DHCP, DNS, HAProxy, NTP, ACME, BIND, cron, FreeRADIUS, SSH |
| status | 28 | 4 | No | CARP, DHCP leases, gateway status, interfaces, logs, OpenVPN, services, system |
| system | 67 | 4 | No | CAs, certificates, CRLs, console, DNS, hostname, packages, REST API, timezone, tunables, webgui |
| user | 20 | 3 | No | users, groups, auth_servers |
| vpn | 84 | 10 | Yes | IPsec (phases 1&2), OpenVPN (clients/servers/CSOs), WireGuard (tunnels/peers) |

**Total: 677 operations → generates ~350-400 unique tools** (after deduplication of GET singular/plural → get/list).

## Known Quirks and Edge Cases

1. **Singular GET returns 400 without `id`**: Singular endpoints (`/firewall/alias`) require `?id=N`. The 400 response is normal when called without `id` — it's not a broken endpoint.

2. **DELETE `apply` parameter**: Some DELETE endpoints accept `?apply=true` to auto-apply changes. The generator should expose this as an optional parameter.

3. **Nested resources**: Some resources are deeply nested:
   - `/services/haproxy/backend/acl` — an ACL within a backend within HAProxy
   - `/services/bind/access_list/entry` — an entry within an access list within BIND
   The tool name should flatten these: `pfsense_create_haproxy_backend_acl`

4. **PUT vs PATCH**: The API uses `PUT` for bulk replacement and `PATCH` for partial update. Most tools should use PATCH. PUT is for bulk operations on plural endpoints.

5. **Status endpoints are read-only**: Everything under `/status/` is GET-only. No confirmation needed.

6. **Log endpoints return large payloads**: `/status/logs/*` can return megabytes. The tools should accept `limit` parameters.

7. **CARP status update**: `PATCH /status/carp` can enable/disable CARP — this is a mutation disguised as a status endpoint.

## Testing

### Manual Testing Against Live pfSense

```bash
# Enter dev shell
nix develop

# Set credentials
export PFSENSE_HOST=https://192.168.1.1
export PFSENSE_API_KEY=your-key
export PFSENSE_VERIFY_SSL=false

# Run the server
fastmcp run generated/server.py

# Or test directly with curl
curl -sk "${PFSENSE_HOST}/api/v2/firewall/aliases" -H "X-API-Key: ${PFSENSE_API_KEY}"
```

### Sample-Based Tests

The `api-samples/` directory contains real responses that can be used for offline testing:
- Verify the generated server parses response envelopes correctly
- Verify tool parameter types match the spec
- Verify naming conventions are applied consistently

## Nix Packaging

The `flake.nix` produces a single package:

```nix
packages.x86_64-linux.default = writeShellApplication {
  name = "pfsense-mcp";
  runtimeInputs = [ pythonEnv ];  # python3 with fastmcp + httpx
  text = ''exec fastmcp run ${./generated/server.py}'';
};
```

After generating `server.py`, the package "just works":
```bash
nix build  # produces ./result/bin/pfsense-mcp
PFSENSE_HOST=... PFSENSE_API_KEY=... ./result/bin/pfsense-mcp
```

## Critical Rule: Never Touch Generated Code

**NEVER manually edit `generated/server.py`**. If the generated code has bugs, fix the generator or templates so re-running produces correct output. Hand-patching defeats the entire purpose.

## Getting Started

1. Read `endpoint-inventory.json` to understand the full API surface
2. Read a few `api-samples/*.json` files to understand response shapes
3. Read `openapi-spec.json` schema definitions for parameter types
4. Build the generator under `generator/`
5. Create `templates/server.py.j2` for the Jinja2 template
6. Generate `generated/server.py`
7. Test with `nix develop` → `fastmcp run generated/server.py`
8. Verify with `nix build` → run the package

## Integration

See `examples/nixosconfig-integration.md` for how this server gets deployed into the homelab fleet via NixOS.

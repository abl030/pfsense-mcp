# Definitive Error Table — Opus 4.6 Target

All known first-attempt errors when using Claude Opus 4.6 as the MCP consumer.
Sonnet-only issues (MCP client serialization bug #22) are excluded.

## Summary

| Category | Count | Fixable by us? | Fix location |
|----------|-------|---------------|-------------|
| OpenAPI spec / conditional required | 7 | YES | Generator (`schema_parser.py`) |
| pfSense API bugs | 3 | NO | pfSense upstream |
| Expected behavior / auth | 2 | YES | Generator (mark unsupported) |
| Expected behavior / discoverability | 2 | YES | Generator (improve docstrings) |
| Parameter format | 1 | YES | Generator (docstring examples) |
| **Total** | **15** | **12 fixable** | |

## Every Error, With Fix Status

### Fixable in Generator (12 errors)

| # | Tool | Error | Root Cause | Fix | Effort |
|---|------|-------|-----------|-----|--------|
| 1 | `update_services_dns_resolver_settings` | `sslcertref` required unconditionally | Spec marks conditional field as required | Detect "only available when enablessl" in description, downgrade to optional | Low |
| 2 | `create_services_ha_proxy_frontend_action` | 16 fields required regardless of action type | Polymorphic schema flattened, all variants marked required | Detect "only available when action is" pattern, downgrade to optional | Medium |
| 3 | `create_system_certificate_authority_generate` | `caref`, `ecname` required for self-signed RSA | Spec marks key-type/hierarchy-specific fields required | Detect "only available when" for `ecname` (ECDSA) and `caref` (intermediate) | Low |
| 4 | `create_user_auth_server` | RADIUS fields required for LDAP server | Polymorphic LDAP+RADIUS schema flattened | Detect "only available when type is" pattern | Medium |
| 5 | `create_vpni_psec_phase1` | `caref`, `certref`, `mode`, `myid_data`, `peerid_data` required with PSK | Polymorphic auth-method schema | Detect "only available when authentication_method is" | Medium |
| 6 | `create_vpni_psec_phase1` | Encryption array item format unclear | Docstring doesn't show flat field name format | Add example to encryption param description: `[{"encryption_algorithm_name": "aes", "encryption_algorithm_keylen": 256, ...}]` | Low |
| 7 | `create_vpni_psec_phase2` | `natlocalid_address`, `natlocalid_netbits` required without NAT | Spec marks NAT fields required unconditionally | Detect "only available when" for NAT/BINAT fields | Low |
| 8 | `create_services_free_radius_user` | `motp_pin`, `motp_secret` required with MOTP disabled | Spec marks MOTP fields required unconditionally | Detect "only available when motp_enable" pattern | Low |
| 9 | `create_auth_key` | 401 — requires BasicAuth | MCP server only supports API key auth | Add docstring warning: "This endpoint requires BasicAuth and cannot be used via API key authentication." Or exclude from generation. | Low |
| 10 | `post_auth_jwt` | 401 — requires BasicAuth | MCP server only supports API key auth | Same as above | Low |
| 11 | `get_diagnostics_table` | Guessed wrong PF table name | Docstring doesn't list common table names | Add to description: "Common tables: virusprot, bogons, snort2c, LAN_NETWORK, WAN_NETWORK" | Low |
| 12 | `get_system_package` | Used package name string instead of integer index | Docstring doesn't clarify ID format | Add to description: "id is an integer array index (0, 1, 2, ...), not a package name" | Low |

### NOT Fixable — pfSense API Bugs (3 errors)

| # | Tool | Error | Bug Description | Workaround |
|---|------|-------|----------------|------------|
| 13 | `update_firewall_traffic_shaper_limiter_queue` | 500: `ecn` references non-existent `sched` field | Limiter queue model inherits `ecn` condition from parent limiter, but `sched` field only exists on parent | Update `name` field instead of `aqm`; avoid PATCHing `aqm`/`ecn` on limiter queues |
| 14 | `update_services_free_radius_user` | PATCH requires `password` even when unchanged | API validates ALL required fields on PATCH, not just submitted ones | Always re-send `password` when PATCHing any FreeRADIUS user field |
| 15 | `replace_user_groups` | `FIELD_MUST_BE_UNIQUE` on idempotent replace | PUT validates uniqueness before clearing existing items | Cannot safely PUT replace user groups with existing data |

## Generator Fix Strategy

### Phase A: Conditional Required Field Detection (errors 1-8)

The generator already detects `"only available when"` in field descriptions (CLAUDE.md finding #17) and sets those fields' defaults to `None`. This needs expansion:

**Current detection** (in `schema_parser.py`):
- Pattern: `"only available when"`
- Action: Set default to `None` instead of spec default

**Expanded detection needed**:
- `"only available when"` (existing)
- `"only needed for"` / `"only needed when"`
- `"required when"` / `"required if"`
- `"only used with"` / `"only used when"`
- `"only applies when"` / `"only applies to"`
- `"only relevant when"` / `"only relevant for"`

**Additional action needed**: For fields matching these patterns that are marked `required` in the spec, downgrade them to optional (remove from the function's required parameter list, set default to `None` or `""`).

This is the highest-impact fix: eliminates 8 of 15 errors with a single pattern-matching change.

### Phase B: Docstring Improvements (errors 6, 11, 12)

Add concrete examples and format clarifications to specific tool parameter descriptions:
- IPsec encryption array: show example JSON structure
- Diagnostics table: list common PF table names
- System package: clarify integer index vs package name

### Phase C: BasicAuth Endpoint Marking (errors 9, 10)

Either:
1. Add prominent docstring warning that these tools require BasicAuth
2. Or exclude them from generation entirely (they can never work via MCP API key auth)

Option 1 is better — keeps tools discoverable but sets clear expectations.

## Impact After Fixes

| Scenario | First-attempt errors | Self-correction needed |
|----------|---------------------|----------------------|
| Before fixes (run-080902) | 5 | 2 self-correct, 3 permanent |
| After Phase A only (run-083300) | 5 | 2 self-correct, 3 permanent |
| **After Phase A+B+C (run-084301)** | **3** | **0 self-correct, 3 permanent** |
| Theoretical minimum | 3 | 0 (all 3 are pfSense bugs) |

**Achieved theoretical minimum.** The 3 permanent pfSense API bugs cannot be fixed without upstream changes.

### Verified Results (run-20260209-084301)

Opus 4.6 independently confirmed: `generator_bug: 0, claude_code_bug: 0, openapi_spec_issue: 0`.

All 12 generator-fixable errors eliminated:
- 8 conditional required field downgrades (Phase A)
- 2 BasicAuth endpoint warnings (Phase C)
- 2 docstring improvements (Phase B: PF table names, IPsec hash enums)
- 1 HAProxy ACL guidance (Phase B)
- 1 package ID format clarification (Phase B)

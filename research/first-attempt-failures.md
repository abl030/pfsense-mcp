# Bank Tester First-Attempt Failures — Complete Analysis

**Source runs**: `run-20260208-222134` (23 tasks) + `run-20260209-062124` (26 tasks, 5 overlap)
**Model**: Claude Sonnet 4.5

After fixing all task-config bugs (8 failures eliminated), the remaining failures are:

**Total first-attempt failures**: 54 across 14 tasks
**Self-correction rate**: 46/54 (85.2%)

**NOTE (Sonnet-specific analysis)**: This document captures Sonnet 4.5 failures. 37 of 54 are the MCP client serialization bug (#22), which is **Sonnet-only** — Opus 4.6 does not reproduce it. For the Opus-specific error table (15 errors → 3 after generator fixes), see `research/error-table-opus.md`.

**Generator fixes applied**: The conditional required field problems documented below (10 failures, 18.5%) have been **fixed** in the generator — `schema_parser.py` now detects `"only available when"` in field descriptions and downgrades those fields from required to optional. The docstring improvements (enum prefix, PF table names, package ID format) have also been applied via `context_builder.py` parameter hints. See `research/error-table-opus.md` for verified results.

---

## Failure Taxonomy

| Category | Count | Root Cause Layer | Self-Corrects? |
|----------|-------|-----------------|----------------|
| MCP client serialization bug | 37 | Claude Code MCP client | No |
| Conditional required fields | 10 | OpenAPI spec / generator | Yes (empty strings) |
| Missing prerequisite / dependency | 4 | Test design / auth limitation | Partially |
| Missing enum prefix | 1 | Docstring quality | Yes |
| Wrong parameter value guess | 1 | Tester guessed wrong | Yes |
| Integer vs string ID confusion | 1 | Docstring quality | Yes |
| pfSense API bug | 1 | pfSense | Yes (different field) |

Adversarial tasks (40, 44) intentionally provoke errors — counted separately at the end.

---

## Every Remaining Failure, By Task

### Task 13 — Traffic Shaper Limiter Queue (Both runs)

**Tool**: `pfsense_update_firewall_traffic_shaper_limiter_queue`
**Category**: pfSense API bug
**Self-corrected**: Yes

```
Error: Field `ecn` contains a condition for field `sched` from Model
       `TrafficShaperLimiterQueue`, but that Model has no such field.
Input: aqm="codel" (changing from "droptail")
Fix:   Updated `name` field instead
```

**What the tester said**: "This is a pfSense API bug — the limiter queue model has conditional field validation referencing a non-existent `sched` field (which only exists on the parent limiter, not the queue)."

**Analysis**: The `sched` field exists on `TrafficShaperLimiter` (parent) but not `TrafficShaperLimiterQueue` (child). PATCHing `aqm` triggers ECN condition checks which crash on the missing field. Unfixable — pfSense bug. The tester sidesteps by updating `name` instead.

---

### Task 18 — DNS Resolver Settings (Run 1 only)

**Tool**: `pfsense_update_services_dns_resolver_settings`
**Category**: Conditional required field
**Self-corrected**: Yes

```
Error: sslcertref: Missing required argument
Fix:   sslcertref=""
```

**What the tester said**: "The tool marks sslcertref as required, but it's actually a conditional field (only needed when enablessl is true)."

**Analysis**: `sslcertref` is only meaningful when `enablessl=true`. The spec marks it unconditionally required. In run 2, the tester knew to pass empty string from the start (0 failures).

---

### Task 23 — HAProxy Frontend (Both runs)

**Failure 1**: `pfsense_create_services_ha_proxy_frontend_action` — Conditional required fields
**Self-corrected**: Yes

```
Error: 11 missing required arguments: backend, customaction, deny_status, find,
       fmt, path, realm, reason, replace, rule, status
Fix:   Added empty strings for all 11 conditional fields
```

**What the tester said**: "The OpenAPI spec marks conditional fields as always-required, even though they're only needed for specific action types. For http-request_lua, only lua_function should be required."

**Analysis**: **Polymorphic schema problem**. HAProxy actions have ~15 types, each needing different fields. The spec marks ALL fields as required regardless of type. The generator can't express "required when action=X". Tester handles it gracefully.

**Failure 2**: `pfsense_get_services_ha_proxy_frontend_certificate` — Missing dependency
**Self-corrected**: No (by design)

```
Error: Created with null ssl_certificate → 404 on GET (not persisted)
Fix:   Accepted as expected limitation
```

**Analysis**: HAProxy frontend cert needs a valid SSL cert reference to persist. Without one, the object vanishes. Would need a CA→cert→HAProxy cert chain to test properly. The tool itself works — it's a missing test dependency.

---

### Task 27 — FreeRADIUS User (Run 2 only)

**Tool**: `pfsense_update_services_free_radius_user`
**Category**: Conditional required field
**Self-corrected**: Yes

```
Error: Field `password` is required.
Input: (only sent descr update)
Fix:   Also sent password="TestPass123"
```

**What the tester said**: "The update endpoint requires the password field even when only updating the description. Password is required when motp_enable is false."

**Analysis**: PATCH-specific variant of conditional-required. Password is "required" because `motp_enable=false`. Our generator defaults non-required PATCH fields to `None`, so password gets omitted. The API rejects.

---

### Task 29 — System PKI (Run 2 only)

**Tool**: `pfsense_create_system_certificate_authority_generate`
**Category**: Conditional required fields
**Self-corrected**: Yes

```
Error: caref: Missing required argument; ecname: Missing required argument
Fix:   caref="", ecname=""
```

**What the tester said**: "Tool schema marks caref and ecname as required, but they are only needed conditionally (caref for intermediate CAs, ecname for ECDSA keys)."

**Analysis**: For a self-signed RSA CA, neither `caref` nor `ecname` is needed. But the spec says they're required. Tester passes empty strings.

---

### Task 31 — User Auth Server (Run 2 only)

**Tool**: `pfsense_create_user_auth_server`
**Category**: Conditional required fields (polymorphic)
**Self-corrected**: Yes

```
Error: Missing ldap_bindpw, radius_nasip_attribute, radius_secret
Input: type_="ldap" (but RADIUS fields still required)
Fix:   Empty strings for all three
```

**What the tester said**: "Tool schema marks conditional RADIUS fields as always-required even when type='ldap'."

**Analysis**: Same polymorphic problem as HAProxy actions. Auth server schema unions LDAP + RADIUS fields, marks all required. Creating an LDAP server shouldn't need RADIUS fields.

---

### Task 32 — VPN IPsec (Run 2 only, 3 failures)

**Failure 1**: `pfsense_create_vpn_ipsec_phase1` — Conditional required fields
**Self-corrected**: Yes

```
Error: Missing caref, certref, encryption, mode, myid_data, peerid_data
Input: authentication_method="pre_shared_key" (cert fields not needed)
Fix:   Empty strings for cert/ID fields, mode="main", encryption=[{...}]
```

**Analysis**: IPsec Phase 1 is heavily polymorphic. With PSK auth, `caref`/`certref` aren't needed. With `myid_type=myaddress`, `myid_data` isn't needed. Spec marks all required. The `encryption` array needing >=1 entry is a legitimate requirement.

**Failure 2**: `pfsense_create_vpn_ipsec_phase2` — Conditional required fields
**Self-corrected**: Yes

```
Error: Missing natlocalid_address, natlocalid_netbits
Fix:   natlocalid_address="", natlocalid_netbits=0
```

**Analysis**: NAT fields only needed for NAT/BINAT traversal. Docstring says "Leave as null if NAT/BINAT is not needed." Schema says required. Same pattern.

**Failure 3**: `pfsense_create_vpn_ipsec_phase2` — Missing enum prefix
**Self-corrected**: Yes

```
Error: hash_algorithm_option must be one of [hmac_sha1, hmac_sha256, ...]
Input: ["sha256"]
Fix:   ["hmac_sha256"]
```

**Analysis**: Tester guessed `sha256` but the enum requires the `hmac_` prefix. Error message is excellent — lists all valid values — so tester self-corrects immediately. Parameter description could include examples.

---

### Task 33 — VPN OpenVPN (Run 2 only)

**Tool**: `pfsense_create_vpn_open_vpn_server`
**Category**: Missing dependency (stale CA reference)
**Self-corrected**: Yes

```
Error: caref could not locate Certificate Authority with refid `698913fd0b038`
Fix:   Created new CA and cert with full DN fields
```

**What the tester said**: "The CA referenced by an existing certificate was no longer present in the system."

**Analysis**: A previous task cleaned up its CA but left a certificate referencing it. The tester creates fresh CA+cert. Test isolation issue — earlier tasks' cleanup left orphan references.

---

### Task 36 — Auth and GraphQL (Run 2 only, 2 failures)

**Tools**: `pfsense_create_auth_key` + `pfsense_post_auth_jwt`
**Category**: Authentication method limitation
**Self-corrected**: No (by design)

```
Error: 401 AUTH_AUTHENTICATION_FAILED
Cause: These endpoints require BasicAuth, MCP server uses API key auth
```

**What the tester said**: "Tool requires BasicAuth (admin:pfsense) but MCP server uses API key auth. Known limitation."

**Analysis**: By design. Auth key creation and JWT endpoints only accept BasicAuth. These 2 tools are permanently untestable via MCP unless we add BasicAuth support.

---

### Task 37 — Diagnostics (Run 2 only, 2 failures)

**Failure 1**: `pfsense_get_diagnostics_table` — Wrong parameter value guess
**Self-corrected**: Yes

```
Error: 404 - Object with ID `sshlockout` does not exist
Fix:   id="virusprot" (valid PF table)
```

**Analysis**: Tester guessed a PF table name that doesn't exist. pfSense has `virusprot`, `bogons`, `LAN_NETWORK`, `WAN_NETWORK` but not `sshlockout`. Docstring could list common table names.

**Failure 2**: `pfsense_get_system_package` — Type confusion (string vs int ID)
**Self-corrected**: Yes

```
Error: 404 - Object with ID `pfSense-pkg-acme` does not exist
Fix:   id=0 (integer index)
```

**Analysis**: Package endpoint uses integer array indices, not package name strings. Unlike most GET endpoints which accept meaningful IDs. Docstring should clarify "id is an integer index, not a package name."

---

### Task 39 — PUT Replace (Run 2 only, 37 failures — MCP CLIENT BUG)

**All 37 failures are identical:**

```
Error: Input should be a valid list [type=list_type, input_value='[]', input_type=str]
Tools: All 37 replace_* tools except replace_firewall_aliases
Cause: Claude Code MCP client passes list parameter as string
```

**What the tester said**: "All 38 PUT endpoints have IDENTICAL generated code and schemas. Yet only pfsense_replace_firewall_aliases works. The MCP client is passing the items parameter as a STRING instead of parsing it as JSON/list."

**Analysis**: **MCP Research finding #22**. All 38 replace tools have byte-identical function signatures, return types, and tool schemas. The only difference is the tool name. One works (`replace_firewall_aliases`), 37 don't. This is a Claude Code MCP client bug — non-deterministic serialization of `list[dict[str, Any]]` parameters. Possibly related to tool registration order or an internal cache. Not fixable on our side.

**Impact**: Blocks 37/38 PUT/replace operations.

---

## Adversarial Tasks (Intentional Failures)

### Task 40 — Wrong Types

| Test | Input | Result | Error Quality |
|------|-------|--------|--------------|
| Integer→string (name) | `12345` | Coerced, rejected: "entirely numerical" | CLEAR |
| String→boolean (disabled) | `"yes"` | Coerced to `true` — no error | Lenient |
| String→list (dnsserver) | `"8.8.8.8"` | Pydantic: "should be a valid list" | CLEAR |
| Boolean→string (username) | `true` | Coerced to `"true"` — no error | Lenient |
| List→string (gateway) | `["10.0.2.1"]` | Coerced to `"[10.0.2.1]"`, rejected: "not valid IPv4" | CLEAR |

Python/Pydantic is lenient with scalar coercions (bool↔str, int↔str) but strict with structural types (str→list). Error quality is consistently clear.

### Task 44 — Boundary Values

| Test | Input | Result | Error Quality |
|------|-------|--------|--------------|
| Empty name | `""` | FIELD_EMPTY_NOT_ALLOWED | CLEAR |
| 200-char name | `"aaa...aaa"` | "Invalid alias name" (no length info) | UNCLEAR |
| XSS in description | `<script>alert('xss')</script>` | **Stored verbatim** | MISSING |

**Security finding**: Free-text `descr` fields accept unvalidated HTML/JavaScript. Stored XSS vulnerability if the WebGUI renders without `htmlspecialchars()`.

---

## Root Cause Analysis

### Distribution

```
MCP client bug ........ 37 (68.5%) ████████████████████████████████████
Conditional required .. 10 (18.5%) ██████████
Dependencies .......... 4  (7.4%)  ████
Other (enum/guess/bug)  3  (5.6%)  ███
```

### The Conditional Required Field Problem (10 failures, 18.5%)

This is the most interesting systemic issue. The OpenAPI 3.0 spec lacks the ability to express:

> "Field X is required **only when** field Y has value Z"

The spec can only say "required" or "not required". When a field is conditionally required, the spec author must choose:
- Mark it **required** → false positives (our problem: consumers must guess to send empty strings)
- Mark it **not required** → false negatives (consumers omit it when it IS needed → server error)

pfSense chose "mark required" for safety, which is the better default. The consumer failure mode (passing empty strings) is benign — the server accepts them silently.

**Affected patterns**:

| Pattern | Example | Fields |
|---------|---------|--------|
| Auth-method polymorphism | IPsec Phase 1 | `caref`, `certref` (cert auth only) |
| Key-type polymorphism | CA generate | `ecname` (ECDSA only) |
| Feature-flag dependency | DNS resolver | `sslcertref` (when `enablessl=true`) |
| Type polymorphism | Auth server | RADIUS fields (when `type=radius`) |
| Action polymorphism | HAProxy actions | 11 fields (per action type) |
| NAT mode dependency | IPsec Phase 2 | `natlocalid_*` (when NAT enabled) |
| Auth-mode dependency | FreeRADIUS user | `password` (when `motp_enable=false`) |

**Generator fix (IMPLEMENTED)**: The generator now detects `"only available when"` in field descriptions and downgrades matching required fields to optional (`default=None`). This was implemented in `schema_parser.py` and eliminates all 10 conditional-required failures when running with Opus. Verified in `run-20260209-084301` (0 conditional-required failures).

### The MCP Client Bug (37 failures, 68.5%)

One bug in Claude Code's MCP client accounts for over two-thirds of all failures. The evidence is conclusive:

1. All 38 `replace_*` tools have **identical** function signatures: `items: list[dict[str, Any]], confirm: bool = False`
2. All 38 have **identical** JSON Schema in the tool registration
3. One tool (`replace_firewall_aliases`) works perfectly
4. The other 37 fail with: `input_value='[]', input_type=str` — the client passes a **string** `'[]'` instead of a **list** `[]`
5. The generated server code is verified identical across all 38

This is not a spec issue, not a generator issue, not a server issue. It's the MCP client serializing the argument differently for different tool names despite identical schemas.

### Dependencies and Auth (4 failures, 7.4%)

- **BasicAuth endpoints** (2): `create_auth_key` and `post_auth_jwt` need username:password auth. Our MCP server only does API key. Permanently untestable without BasicAuth support.
- **Stale CA reference** (1): OpenVPN server referenced a CA cleaned up by a previous task. Test isolation issue.
- **Missing SSL cert** (1): HAProxy frontend cert needs an existing SSL cert to persist. Missing test setup.

### Minor Issues (3 failures, 5.6%)

- **Enum prefix** (1): `sha256` vs `hmac_sha256` — clear error message, instant self-correction
- **Guessed wrong value** (1): `sshlockout` vs `virusprot` PF table — self-corrects on retry
- **ID type confusion** (1): Package uses integer index, not name string — docstring should clarify

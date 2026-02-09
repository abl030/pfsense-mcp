# Opus 4.6 Independent Failure Diagnosis — Run 20260209-080902

**Model**: Claude Opus 4.6 (`claude-opus-4-6`)
**Task**: 50-failure-pattern-diagnosis (custom diagnostic task)
**Result**: PASS, 37 tool calls, 5 first-attempt failures, ~7 minutes
**Purpose**: Independent root cause analysis of known failure patterns, without hints from our prior analysis

## Raw Opus Output

### Opus Root Cause Classification

| Root Cause Layer | Count | Tools Affected |
|-----------------|-------|----------------|
| openapi_spec_issue | 7 | dns_resolver settings, haproxy frontend action, CA generate, auth server, ipsec phase1, ipsec phase2, freeradius user create |
| pfsense_api_bug | 3 | limiter queue update, freeradius user PATCH, replace_user_groups |
| expected_behavior | 3 | auth key (BasicAuth), JWT (BasicAuth), ID format inconsistency |
| generator_bug | 1 | auth/jwt lacks BasicAuth params |

### Opus Diagnosis per Failure

**1. Limiter queue `aqm→codel` (Part 1)**
- Classification: **pfsense_api_bug**
- Error: `ecn` condition references `sched` field that doesn't exist on queue model
- Opus quote: "pfSense API bug — ecn conditional validator tries to resolve sched on queue model, but sched belongs to parent limiter model. Blocks ALL PATCH operations on limiter queues."

**2. DNS resolver `sslcertref` (Part 2)**
- Classification: **openapi_spec_issue**
- Opus noted `sslcertref` required unconditionally; only needed when `enablessl=true`

**3. HAProxy frontend action (Part 3)**
- Classification: **openapi_spec_issue** + minor API bug
- ALL 16 conditional fields required regardless of action type
- Additional finding: API rejects empty `acl` even for action types that don't need an ACL condition

**4. FreeRADIUS user PATCH (Part 4)**
- Classification: **pfsense_api_bug** (differs from our Sonnet analysis which said "conditional required")
- Opus rationale: "PATCH enforces password as required even when not being changed. Should only validate submitted fields."
- Also found `motp_pin`/`motp_secret` required on CREATE even with MOTP disabled (openapi_spec_issue)

**5. CA generate `ecname`/`caref` (Part 5)**
- Classification: **openapi_spec_issue**
- `caref` only needed for intermediate CAs, `ecname` only for ECDSA, `keylen` only for RSA — all unconditionally required

**6. Auth server LDAP (Part 6)**
- Classification: **openapi_spec_issue**
- RADIUS fields (`radius_secret`, `radius_nasip_attribute`) required when creating LDAP server
- LDAP fields required when creating RADIUS server

**7a. IPsec Phase 1 (Part 7)**
- Classification: **openapi_spec_issue** + **parameter_format**
- Conditional cert fields required with PSK auth
- Opus also hit a different failure mode than Sonnet: encryption array item format (nested vs flat field names)

**7b. IPsec Phase 2 (Part 7)**
- Classification: **openapi_spec_issue**
- `natlocalid_address`/`natlocalid_netbits` required even without NAT/BINAT

**8. Auth key + JWT (Part 8)**
- Classification: **expected_behavior** + **generator_bug**
- Both require BasicAuth, MCP server only supports API key
- Opus suggests: generator should detect BasicAuth-only endpoints and mark tools as unsupported

**9. ID format (Part 9)**
- Classification: **expected_behavior**
- Diagnostics table uses string names, packages use integer indices
- Minor discoverability gap

**10. PUT/Replace (Part 10) — MAJOR FINDING**
- 3 of 4 replace operations **succeeded** (aliases, rules, tunables)
- `replace_user_groups` failed with new error: `FIELD_MUST_BE_UNIQUE` (pfSense API bug)
- **MCP client serialization bug #22 DID NOT REPRODUCE with Opus**

### Opus Systemic Analysis

> "The single most impactful issue is the OpenAPI spec marking ALL conditional/variant-specific fields as unconditionally required. This affects every polymorphic endpoint. The generator faithfully reproduces this, so fixing it requires either spec changes or generator intelligence to detect conditional docstrings and override required lists."

### Opus Impact Ranking

1. openapi_spec_issue — conditional fields as required (~50+ tools affected)
2. pfsense_api_bug — limiter queue PATCH (100% blocking, no workaround)
3. pfsense_api_bug — PUT replace uniqueness validation ordering
4. pfsense_api_bug — FreeRADIUS PATCH requires password
5. generator_bug — BasicAuth endpoints inaccessible (2 tools)
6. expected_behavior — ID format inconsistency

## Comparison: Opus vs Our Sonnet-Based Analysis

| Failure | Our Analysis (Sonnet) | Opus Diagnosis | Agree? |
|---------|----------------------|----------------|--------|
| Limiter queue aqm→codel | pfSense API bug | pfSense API bug | YES |
| DNS resolver sslcertref | OpenAPI spec issue | OpenAPI spec issue | YES |
| HAProxy frontend action fields | OpenAPI spec issue | OpenAPI spec + API bug (acl) | MOSTLY |
| FreeRADIUS PATCH password | Conditional required (spec) | **pfSense API bug** (PATCH semantics) | DIFFERENT |
| FreeRADIUS create motp fields | (not separately observed) | OpenAPI spec issue | NEW |
| CA generate ecname/caref | OpenAPI spec issue | OpenAPI spec issue | YES |
| Auth server LDAP+RADIUS | OpenAPI spec issue | OpenAPI spec issue | YES |
| IPsec Phase 1 | OpenAPI spec + conditional | OpenAPI spec + param format | DIFFERENT FAILURE |
| IPsec Phase 2 natlocalid | OpenAPI spec issue | OpenAPI spec issue | YES |
| IPsec Phase 2 hmac_ prefix | Enum prefix in docstring | (Opus didn't hit this) | N/A |
| Auth key / JWT | Expected (BasicAuth) | Expected + generator gap | MOSTLY |
| Diagnostics table ID | Wrong guess | Expected behavior | YES |
| Package ID format | Type confusion | Expected behavior | YES |
| PUT/replace 37 tools | Claude Code MCP client bug | **DID NOT REPRODUCE** | MAJOR DIFFERENCE |
| PUT replace_user_groups | (not observed) | pfSense API bug (uniqueness) | NEW FINDING |

### Key Differences

1. **MCP client bug #22 is model-specific.** Sonnet: 37/38 replace tools fail. Opus: 0/4 fail. The serialization bug only manifests with Sonnet, not Opus. This eliminates 68.5% of all Sonnet failures.

2. **FreeRADIUS PATCH classification.** We called it "conditional required" (spec layer). Opus calls it "pfSense API bug" (PATCH shouldn't require unchanged fields). Opus's classification is more precise — the API's PATCH implementation is at fault, not just the spec's required annotation.

3. **New finding: replace_user_groups uniqueness.** Opus discovered a pfSense API bug where PUT replace validates uniqueness before clearing existing items. This causes false `FIELD_MUST_BE_UNIQUE` on idempotent replace-with-same-data.

4. **IPsec encryption format.** Opus hit a different failure mode (encryption array item format) than Sonnet (conditional cert fields). Both are real issues but show different models stumble at different points.

## Post-Fix Verification

After implementing generator fixes (conditional required downgrade, BasicAuth detection, docstring improvements), two additional Opus runs were conducted:

- **`run-20260209-083300`** (Phase A only): 5 failures — conditional downgrades worked, but HAProxy ACL and IPsec P2 hash hints had wrong operationId keys, so those 2 weren't fixed yet.
- **`run-20260209-084301`** (all fixes): **3 failures — all pfSense API bugs.** Theoretical minimum achieved.

Opus independently confirmed in run-084301: `generator_bug: 0, claude_code_bug: 0, openapi_spec_issue: 0`. All 12 generator-fixable errors eliminated. See `research/error-table-opus.md` for the complete breakdown.

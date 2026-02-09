# Sprint 2: Sub-Resource CRUD + Actions — Failure Analysis

**Run**: `run-20260209-110651`
**Model**: Claude Opus 4.6
**Tasks**: 51-57 (7 tasks)
**Result**: 7/7 PASS (all exit 0)
**Runtime**: ~22 minutes total
**Net new tools**: +35 (544 → 579/677 = 85.5%)

## Summary

| Task | Tools | 1st-attempt failures | Category |
|------|-------|---------------------|----------|
| 51: HAProxy sub-resource updates | 22 | 2 | Conditional required (1), dependency (1) |
| 52: Gateway group priority CRUD | 12 | 0 | — |
| 53: CRL revoked cert + CRL update | 16 | 1 | pfSense API bug (CRL non-editable) |
| 54: Network interface CRUD | 10 | 1 | Generator bug (PATCH id typing) |
| 55: OpenVPN client export | 15 | 0 | — |
| 56: PKI actions + service restart | 16 | 2 | PEM corruption in tool output |
| 57: Singular deletes | 16 | 2 | BasicAuth required (known) |
| **Total** | **107** | **8** | |

## Every Failure, Classified

### 1. HAProxy Backend Action — `lua_function` required (Task 51)

**Error**: `Field 'lua_function' is required.`
**Classification**: **test_design_bug** (task-config missing required field)
**Analysis**: The `http-request_lua` action type requires `lua_function`, but task-config didn't include it.
**Self-corrected**: Yes — Opus added `lua_function: "test_func"` and retried.
**Fix**: Add `lua_function: test_func` to task 51 create_values for backend action.

### 2. HAProxy Backend Error File — missing file dependency (Task 51)

**Error**: `Field 'errorfile' could not locate 'HA Proxy File' object with 'name' set to 'bt_sys51_file'`
**Classification**: **test_design_bug** (missing setup step)
**Analysis**: The error_file references a HAProxy file by name. The task config has a `setup` block but the generator may not have produced the file creation step correctly. Opus created the file manually and retried.
**Self-corrected**: Yes.
**Fix**: Verify setup block in generated task or add explicit file creation step.

### 3. CRL `descr` not editable (Task 53)

**Error**: `FIELD_VALUE_CHANGED_WHEN_NOT_EDITABLE - Field 'descr' is not editable`
**Classification**: **pfsense_api_bug**
**Analysis**: pfSense marks ALL CRL fields as non-editable for internal CRLs. The PATCH endpoint exists in the spec but the backend rejects all field changes. Opus tried `descr`, `lifetime`, `serial`, `method` — all rejected.
**Self-corrected**: No (permanent failure for `update_system_crl`).
**New pfSense bug #26**: CRL PATCH endpoint exists but rejects all field changes.

### 4. Network Interface PATCH `id` typing (Task 54)

**Error**: `Input should be a valid integer, unable to parse string as an integer [input_value='opt1']`
**Classification**: **generator_bug**
**Analysis**: The PATCH tool types `id` as `integer` only, but the API returns string interface IDs (wan, lan, opt1). The GET and DELETE tools for the same endpoint correctly type `id` as `str | int`. This is a generator inconsistency in `schema_parser.py` — PATCH operations on this endpoint need the same union type.
**Self-corrected**: No (Opus tried integer IDs 2, 3 — none mapped to opt1).
**Fix**: In `schema_parser.py`, ensure PATCH body `id` fields for endpoints that use string IDs get `str | int` typing, same as query params.

### 5. CSR Sign — PEM corruption (Task 56)

**Error**: `500 CERTIFICATE_SIGNING_REQUEST_SIGN_FAILED - Failed to sign the certificate signing request for unknown reason.`
**Classification**: **model_behavior** (PEM serialization in tool output)
**Analysis**: When Opus received the CSR PEM from the creation response, copying it into the sign endpoint's `csr` parameter introduced subtle corruption (likely base64 line break issues). Retrieving the exact PEM via GET fixed it.
**Self-corrected**: Yes (after 2 failures — GETted cert, used exact PEM).
**Fix**: Not easily fixable — PEM handling in LLM tool calls is inherently fragile. Docstring could suggest using GET to retrieve exact PEM rather than copying from creation response.

### 6-7. Auth Key create/delete — BasicAuth (Task 57)

**Error**: `401 AUTH_AUTHENTICATION_FAILED`
**Classification**: **expected_behavior** (known limitation)
**Analysis**: Both `create_auth_key` and `delete_auth_key` require BasicAuth. MCP server uses API key auth. Docstrings correctly warn about this. Opus used `command_prompt` with PHP as workaround.
**Self-corrected**: Yes (via command_prompt workaround).
**Fix**: Already documented. Auth key endpoints are permanently BasicAuth-only.

## Actionable Fixes

| # | Fix | Location | Impact |
|---|-----|----------|--------|
| 1 | Add `lua_function: test_func` to task 51 backend action create_values | task-config.yaml | Eliminates 1 failure |
| 2 | Fix PATCH `id` typing for network/interface endpoint | schema_parser.py | Eliminates 1 failure (generator bug) |
| 3 | Document CRL PATCH as non-functional (pfSense bug #26) | error-table-opus.md | Documentation only |
| 4 | Add PEM retrieval hint to CSR sign docstring | context_builder.py | Reduces PEM corruption failures |

## Coverage Impact

- **Before Sprint 2**: 544/677 (80.4%)
- **After Sprint 2**: **579/677 (85.5%)**
- **Remaining gap**: 98 tools (83 bulk DELETEs, ~8 permanently blocked, ~7 misc)

## Task 36: Auth & GraphQL

**task_id**: 36-auth--graphql

**Objective**: Exercise all tools in the auth subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (3):
- `pfsense_create_auth_key`
- `pfsense_post_auth_jwt`
- `pfsense_create_graph_ql`

**Steps**:
1. **Execute** `pfsense_create_auth_key` with `confirm=True` **Note: requires BasicAuth (admin:pfsense), not API key.** (Requires BasicAuth (admin:pfsense), not API key):
    - `descr`: `bt_sys36_key`
    - `length_bytes`: `16`
2. **Execute** `pfsense_post_auth_jwt` with `confirm=True` **Note: requires BasicAuth (admin:pfsense), not API key.** (Requires BasicAuth (admin:pfsense), not API key):
(no parameters needed)
3. **Execute** `pfsense_create_graph_ql` with `confirm=True` (Returns raw {data: ...} — NOT standard response envelope):
    - `query`: `{ __schema { queryType { name } } }`

**Important notes**:
Auth endpoints need BasicAuth, not API key.
GraphQL returns raw response (not standard envelope).

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 3 tools exercised successfully.

# MCP Server Best Practices

Findings from building a 677-tool MCP server for the pfSense REST API v2 and testing it with an AI consumer (Claude via bank tester). These are hard-won lessons applicable to any MCP server project.

## Tool Schema Constraints

### 1. Return type annotations must cover all response shapes
FastMCP validates tool return values against the function's return type annotation. If your API returns both objects and arrays, the return type must be `dict[str, Any] | list[Any] | str` — not just `dict[str, Any] | str`. A `list` response against a `dict`-only annotation triggers an `Output validation error` that confuses the consumer even though the data was successfully retrieved.

### 2. Sanitize large integers from OpenAPI specs
The Anthropic API rejects tool schemas containing integers that exceed safe serialization limits (e.g., `9223372036854775807` / int64 max). OpenAPI specs commonly use these as sentinel values meaning "no limit". The generator must detect values where `abs(value) >= 2**53` and replace them with `None` defaults. Without this, the entire MCP server fails to register with `tools.N.custom.input_schema: int too big to convert`.

### 3. One bad tool schema poisons the whole server
When the Anthropic API rejects a single tool's schema, ALL tools become unavailable for that request — not just the broken one. This makes schema validation bugs critical-severity, since a single overlooked field can take down a 677-tool server.

## Tool Discoverability

### 4. Consistent naming conventions are highly discoverable
The pattern `pfsense_{verb}_{resource}` (e.g., `create_firewall_rule`, `list_status_gateways`, `apply_firewall`) let the tester find every tool on the first attempt. Verbs: `get` (singular), `list` (plural), `create`, `update`, `delete`, `apply`.

### 5. Apply-pattern reminders in docstrings work
Adding `"Note: Call {apply_tool_name} after this to apply changes."` to mutation tool docstrings meant the tester never forgot to apply. This is more effective than relying on the consumer to know which subsystems need apply.

### 6. Confirmation gates (`confirm=True`) work smoothly
The preview-then-execute pattern for mutations caused zero confusion in testing. The tester naturally used `confirm=True` on first attempt. The preview message showing the HTTP method and path provides useful context.

## Tool Count Challenges

### 7. 677 tools is at the edge of API limits
With this many tools, some API calls intermittently fail due to serialization or token budget constraints. Consider: grouping related tools, lazy-loading tool subsets, or offering a "tool catalog" meta-tool that returns available tools for a subsystem.

## Error Handling

### 8. Distinguish API errors from schema validation errors
When FastMCP's output validation rejects a valid API response, the error message is indistinguishable from an actual API failure. The consumer retried with the same parameters (which will never help for a schema bug). Error messages should clearly indicate whether the failure was in the upstream API vs. local schema validation.

### 9. Sibling tool call error propagation is overly aggressive
When one tool in a parallel batch triggers a validation error, FastMCP cancels all sibling calls with a generic error. For read-only operations, this is unnecessarily conservative — one failed GET shouldn't prevent other independent GETs from executing.

## OpenAPI-to-MCP Generation Lessons

### 10. Undocumented route differences cause silent failures
OpenAPI specs may document routes that behave differently on the real server (e.g., some sub-resource plural endpoints may 404 on older versions). Test generated tools against a live instance to identify discrepancies.

### 11. `readOnly` schema fields must be excluded from request parameters
Including response-only fields as tool parameters confuses the consumer into thinking they're settable.

### 12. Enum values belong in parameter descriptions
When an API field accepts a fixed set of values, listing them in the tool's parameter description eliminates the most common failure category (`missing_enum_values`). Don't rely on the consumer guessing valid values.

### 13. Default values from specs need validation
Not all OpenAPI defaults are safe to use as Python defaults. Sentinel values (int64 max/min), empty objects that should be `None`, and values that depend on server state should all be sanitized during generation.

### 14. Array parameters that are actually sub-resources cause failures
Some APIs expose array fields (e.g., WireGuard `addresses`, `allowedips`) in the create schema, but passing JSON arrays triggers validation errors. The correct pattern is to create the parent without the array, then add items via sub-resource endpoints. Tool docstrings should explicitly note when an array parameter must be managed via sub-resources instead of inline.

### 15. Conditional required fields must be downgraded to optional
OpenAPI 3.0 can't express "required when X=Y", so specs mark conditionally-required fields as always-required. The generator detects `"only available when"` in field descriptions and downgrades matching required fields to optional (`default=None`). The pfSense spec has 696 fields with this pattern. This single change eliminated 8 of 15 first-attempt errors.

### 16. Strip HTML and don't truncate conditional field docs
OpenAPI descriptions often contain `<br>` tags and conditional availability notes. Truncating these hides critical dependency information from the consumer. Strip HTML tags, collapse whitespace, and preserve full descriptions.

### 17. Conditional field defaults cause type mismatches
When a spec sets `default: 128` for a subnet field (valid for IPv6), sending that default for an IPv4 address causes validation failure. Detect conditional fields and set their defaults to `None` so they're only sent when explicitly specified.

### 18. `allOf`/`$ref` in array items must resolve to `dict`, not `str`
When an array's `items` schema uses `allOf` with a `$ref`, the type resolver must recognize this as `list[dict[str, Any]]`, not `list[str]`. Without proper handling, the function falls through to the default `"string"` type.

### 19. PATCH operations must default optional fields to `None`
When an OpenAPI spec defines defaults for optional fields, using those as Python function parameter defaults causes PATCH to overwrite existing server values with spec defaults. This is catastrophic for settings like authentication methods. For PATCH operations, all non-required body fields should default to `None`.

### 20. Sub-resource `parent_id` fields need consistent typing
OpenAPI specs may type `parent_id` as `integer` in request bodies but `oneOf: [integer, string]` in query parameters. Normalizing to `str | int` everywhere prevents type errors when consumers pass string identifiers.

## Testing Methodology

### 21. Settings mutations that change the API endpoint break all subsequent tests
Changing WebGUI port, protocol, or SSL certificate makes the API unreachable from MCP clients. Exclude endpoint-altering settings from automated test sequences, or run them last.

### 22. Claude Code MCP client inconsistently serializes `list` parameters (Sonnet only)
When a tool has `items: list[dict[str, Any]]`, the Sonnet MCP client sometimes passes the JSON array as a string instead of a parsed list. Opus 4.6 does NOT reproduce this bug. The bug is model-specific.

### 23. pfSense PUT replace validates uniqueness before clearing existing items
Idempotent PUT operations fail with uniqueness errors because validation runs before clearing. Not fixable — pfSense API bug.

### 24. Independent Opus diagnosis validates analysis
Having a fresh Opus classify all failures independently achieved 75% full agreement with manual analysis. The diagnostic loop consistently uncovers wrong assumptions.

### 25. Conditional required field downgrade eliminates most errors
Combined with BasicAuth endpoint detection and docstring improvements, this reduces Opus first-attempt failures from 15 to 3 (all unfixable pfSense API bugs).

### 26. Always re-validate assumed-broken endpoints
Old assumptions carried forward without validation waste coverage points. Never mark an endpoint as permanently broken without running it through a diagnostic loop first.

### 27. Diagnostic tasks catch false assumptions
Re-testing all first-attempt failures independently recovered tools that were assumed permanently blocked. The diagnostic loop consistently uncovers wrong assumptions.

# pfsense-mcp

Auto-generated MCP (Model Context Protocol) server for the pfSense REST API v2.

Driven from the pfSense OpenAPI 3.0.0 spec (258 paths, 178 schemas, 677 operations), this project generates a comprehensive FastMCP server with full CRUD coverage for all pfSense resources.

## Architecture

```
openapi-spec.json          # Raw OpenAPI 3.0.0 spec from live pfSense
endpoint-inventory.json    # Processed endpoint catalog
api-samples/               # Real GET response samples for testing
generator/                 # Python generator that builds the server
templates/                 # Jinja2 templates for code generation
generated/server.py        # The generated MCP server (output)
```

## Quick Start

```bash
# Enter dev shell with all dependencies
nix develop

# Run the generator (once implemented)
python3 -m generator

# Run the generated server
PFSENSE_HOST=https://10.0.0.1 \
PFSENSE_API_KEY=your-key \
PFSENSE_VERIFY_SSL=false \
fastmcp run generated/server.py
```

## Nix Package

```bash
# Build the MCP server package
nix build

# Run directly
PFSENSE_HOST=https://10.0.0.1 \
PFSENSE_API_KEY=your-key \
nix run
```

## Integration

See `examples/nixosconfig-integration.md` for how to integrate this into a NixOS flake configuration.

## License

MIT

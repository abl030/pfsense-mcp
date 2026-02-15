"""Entry point for `python -m pfsense_mcp` and the `pfsense-mcp` console script.

Runs the FastMCP server on stdio transport.
"""

from __future__ import annotations

import importlib.resources
import subprocess
import sys


def main() -> None:
    """Run the generated MCP server via fastmcp."""
    # Locate the generated server module
    server_path = importlib.resources.files("pfsense_mcp") / "server.py"
    # Use fastmcp CLI to run it (handles stdio transport setup)
    sys.exit(subprocess.call([sys.executable, "-m", "fastmcp", "run", str(server_path)]))


if __name__ == "__main__":
    main()

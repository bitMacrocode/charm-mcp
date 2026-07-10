#!/usr/bin/env python3
"""CHARM MCP Server — verified OEM automotive data as MCP tools.

Portable single-file MCP server. Works on Mac, Linux, Windows.
Requirements: Python 3.10+, mcp package (pip install mcp).

Talks to the CHARM API at chatwithcharm.com over HTTPS.
No local files, no local imports, no filesystem dependencies.

Env vars:
    CHARM_MCP_API_KEY  API key for authentication (required)
    CHARM_API_URL      Base URL (default: https://chatwithcharm.com)
"""

import os
import sys
import json
import httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("CHARM_API_URL", "https://chatwithcharm.com").rstrip("/")
API_KEY = os.environ.get("CHARM_MCP_API_KEY", "")

if not API_KEY:
    print("Error: CHARM_MCP_API_KEY environment variable is required.", file=sys.stderr)
    print("Get a free key at https://chatwithcharm.com/api/v1/docs", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP(
    "charm",
    instructions=(
        "Verified OEM automotive data for vehicles 1982-2013. "
        "Returns part numbers, torque specs, and service procedures "
        "from factory service manuals."
    ),
)


@mcp.tool()
def charm_lookup(
    query: str,
    year: str | None = None,
    make: str | None = None,
    model: str | None = None,
    system: str | None = None,
) -> str:
    """Look up verified OEM part numbers, torque specifications, and service procedures for vehicles 1982-2013.

    Returns structured data sourced directly from factory service manuals.

    Args:
        query: What you want to know about the vehicle (e.g. "brake caliper part number")
        year: 4-digit year, 1982-2013
        make: Manufacturer name (e.g. "Ford", "Honda", "Chevy Truck")
        model: Model name (e.g. "Taurus X", "Civic", "Silverado")
        system: Vehicle system filter (e.g. "brakes", "engine", "electrical")
    """
    body = {"query": query, "format": "structured"}
    if year:
        body["year"] = year
    if make:
        body["make"] = make
    if model:
        body["model"] = model
    if system:
        body["system"] = system

    try:
        resp = httpx.post(
            f"{API_URL}/api/v1/lookup",
            json=body,
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def charm_list_makes() -> str:
    """List all vehicle manufacturers covered by CHARM (1982-2013)."""
    try:
        resp = httpx.get(f"{API_URL}/api/v1/vehicles", timeout=10)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")

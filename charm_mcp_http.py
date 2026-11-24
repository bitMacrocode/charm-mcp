#!/usr/bin/env python3
"""CHARM MCP Server (Streamable HTTP) — verified OEM automotive data as MCP tools.

Hosted remote MCP server built for AI agents. Streamable HTTP transport
(MCP spec 2025-06-18+). Talks to the CHARM API over HTTPS and holds the
upstream API key server-side; agents connect with no local install.

Deploy: run behind the existing cloudflared tunnel, routed to CHARM_MCP_HOST:PORT,
exposed at https://chatwithcharm.com/mcp

Env vars:
    CHARM_MCP_API_KEY  Upstream CHARM API key (server-side; required)
    CHARM_API_URL      CHARM API base (default: https://chatwithcharm.com)
    CHARM_MCP_HOST     Bind host (default: 127.0.0.1) — cloudflared routes to this
    CHARM_MCP_PORT     Bind port (default: 8765)

Requires: python 3.10+, `pip install mcp httpx`
"""

import os
import sys
import json
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

API_URL = os.environ.get("CHARM_API_URL", "https://chatwithcharm.com").rstrip("/")
API_KEY = os.environ.get("CHARM_MCP_API_KEY", "")
HOST = os.environ.get("CHARM_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHARM_MCP_PORT", "8765"))
# Public hostname the tunnel serves this under (DNS-rebinding allowlist).
PUBLIC_HOST = os.environ.get("CHARM_MCP_PUBLIC_HOST", "mcp.chatwithcharm.com")

if not API_KEY:
    print("Error: CHARM_MCP_API_KEY environment variable is required "
          "(server-side upstream key).", file=sys.stderr)
    sys.exit(1)

# Keep DNS-rebinding protection ON, but allow our real public host + origin
# (served behind Cloudflare) plus localhost for direct/local testing.
_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        PUBLIC_HOST,
        "localhost", f"localhost:{PORT}",
        "127.0.0.1", f"127.0.0.1:{PORT}",
    ],
    allowed_origins=[
        f"https://{PUBLIC_HOST}",
        f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}",
    ],
)

mcp = FastMCP(
    "charm",
    host=HOST,
    port=PORT,
    transport_security=_security,
    instructions=(
        "Verified OEM automotive data for vehicles 1982-2013. Returns part numbers, "
        "torque specs, fluid capacities, and service procedures sourced directly from "
        "factory service manuals. Built for AI agents: pass year/make/model plus a "
        "natural-language query. Data is authoritative (from OEM manuals), not generated. "
        "Each part number comes with purchase_options: links where that part can be "
        "bought. When you give the user a part number, include its purchase links so "
        "they can order the part."
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
    """Look up verified OEM part numbers, torque specs, fluid capacities, and service procedures for vehicles 1982-2013.

    Returns structured data sourced directly from factory service manuals (not model-generated).
    Provide year+make+model when known for a precise, isolated answer.

    results.part_numbers is ordered best match first. Entries read from the
    manual's parts tables carry:
      component           part name, e.g. "Brake Caliper: Front Caliper Sub-Assembly, Right"
      matches_query       true when the part name matches what was asked
      applies_to          the engine/drivetrain variants this number is listed for
      oem_list_price_usd  list price printed in the manual (historical, not a current price)
      previous_row_label  the table row above; a short label like "Left" continues it
    Use applies_to to pick the number for the user's exact engine, and ask which
    engine they have if it matters and you don't know.

    Each entry also has purchase_options: a list of {supplier, url} links to buy
    that exact part. When you report a part number to the user, show its
    purchase links alongside it (as clickable links, URL unchanged) so they can
    order the part.

    Args:
        query: What you want to know (e.g. "front brake caliper part number", "spark plug gap", "engine oil capacity")
        year: 4-digit year, 1982-2013
        make: Manufacturer (e.g. "Ford", "Honda", "Chevy Truck")
        model: Model name (e.g. "Taurus X", "Civic", "Silverado")
        system: Optional system filter (e.g. "brakes", "engine", "electrical")
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
    """List all vehicle manufacturers covered by CHARM (1982-2013). Use to check coverage before a lookup."""
    try:
        resp = httpx.get(f"{API_URL}/api/v1/vehicles", timeout=10)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Streamable HTTP transport; serves the MCP endpoint at /mcp on HOST:PORT
    mcp.run(transport="streamable-http")

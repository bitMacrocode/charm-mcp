# CHARM — OEM Automotive Data for AI Agents (MCP)

**CHARM** is an [MCP](https://modelcontextprotocol.io) server that gives AI agents
**authoritative OEM automotive repair data** — factory service-manual **part numbers,
torque specs, fluid capacities, and procedures** for vehicles **1982–2013**, across 80+ makes.

Answers come straight from OEM factory service manuals, **not** a model's memory — so they're
verifiable and source-attributed, not hallucinated. When a part number is identified, CHARM
also returns links to purchase that exact part.

Built to be called by AI agents — Claude, ChatGPT, Gemini, and beyond.

---

## Connect (hosted — no install)

Remote MCP endpoint (Streamable HTTP):

```
https://mcp.chatwithcharm.com/mcp
```

**Claude Code**
```bash
claude mcp add --transport http charm https://mcp.chatwithcharm.com/mcp
```

**Claude Desktop** — Settings → Connectors → Add custom connector → paste the URL above.

**Config-file clients (Cursor, etc.)**
```json
{
  "mcpServers": {
    "charm": { "type": "http", "url": "https://mcp.chatwithcharm.com/mcp" }
  }
}
```

Then just ask naturally:
> What's the front brake caliper part number for a 2009 Ford Taurus X, and where can I buy it?

> What's the spark plug gap for a 2001 Toyota Camry?

---

## Tools

| Tool | Description |
|------|-------------|
| `charm_lookup(query, year?, make?, model?, system?)` | Verified OEM part numbers, torque specs, fluid capacities, and service procedures. Pass `year`+`make`+`model` for a precise, isolated answer. |
| `charm_list_makes()` | List all covered manufacturers. |

## Coverage

- **Model years 1982–2013** — the DIY-repair sweet spot (out-of-warranty, owner-serviced vehicles).
- **80+ makes.**
- Data sourced directly from **OEM factory service manuals** — authoritative, not generated.

## Self-hosting (optional)

You don't need to self-host to use CHARM — the hosted endpoint above is the easy path.
To run your own instance against the CHARM API, grab a free key at
`https://chatwithcharm.com/api/v1/docs`, then:

```bash
pip install mcp httpx
export CHARM_MCP_API_KEY="your_key_here"
python3 charm_mcp_http.py        # Streamable HTTP (remote)
# or
python3 charm_mcp_server.py      # stdio (local, e.g. Claude Desktop)
```

## License

[MIT](LICENSE) © Bitmacro

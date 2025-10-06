# Jira MCP Connector

YouTube: AaiTech

Welcome — this repo contains an MCP connector for Jira (tools are defined in `server.py`). The steps below show a minimal workflow using the `uv` Python package manager. Keep it simple.
---


## Minimal setup using uv

Follow these minimal steps to create a new `uv`-backed project and add MCP as a dependency. This keeps the flow short and focused.

```cmd
uv init mcp-server-demo
cd mcp-server-demo

:: add MCP (CLI extras) to the project
uv add "mcp[cli]"

:: alternative: use pip to install into your active environment
:: pip install "mcp[cli]"

:: install/run the server module (use uv to run mcp install on server.py)
uv run mcp install server.py
```

That's it — a minimal `uv` workflow for this repo. The project `server.py` in this repository defines the MCP tools; use your preferred method (uv-managed environment or pip) to run and test the MCP server.

---

If you'd like, I can now either:

- add a tiny `__main__` run block to `server.py` so `python server.py` starts the MCP server, or
- create a short example that demonstrates invoking one tool through MCP.

Which would you prefer? 


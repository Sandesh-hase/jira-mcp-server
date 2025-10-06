# Jira MCP Connector

YouTube: AaiTech

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


from __future__ import annotations

from src.agents.mcp.tool_registry import TOOL_REGISTRY


class MCPOrchestrator:
    def __init__(self):
        self.tools = TOOL_REGISTRY

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

    def call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        if tool_name not in self.tools:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        if arguments is None:
            arguments = {}

        return self.tools[tool_name](arguments)


mcp_orchestrator = MCPOrchestrator()
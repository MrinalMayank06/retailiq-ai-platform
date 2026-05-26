from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.agents.mcp.mcp_orchestrator import mcp_orchestrator
from src.api.utils.response_formatter import success_response


class MCPToolRequest(BaseModel):
    tool_name: str = Field(..., examples=["demand_forecast_tool"])
    arguments: dict = Field(default_factory=dict)


router = APIRouter(prefix="/api/mcp", tags=["MCP"])


@router.get("/tools")
def list_mcp_tools():
    return success_response(
        "Available MCP tools fetched successfully",
        {
            "tools": mcp_orchestrator.list_tools()
        },
    )


@router.post("/call-tool")
def call_mcp_tool(request: MCPToolRequest):
    result = mcp_orchestrator.call_tool(
        tool_name=request.tool_name,
        arguments=request.arguments,
    )

    return success_response(
        "MCP tool executed successfully",
        result,
    )

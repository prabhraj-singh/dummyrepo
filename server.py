
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "Dummy MCP Server",
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            "metric-detail-intervention-enter.trycloudflare.com",
            "metric-detail-intervention-enter.trycloudflare.com:*",
            "127.0.0.1:*",
            "localhost:*",
        ],
        allowed_origins=[
            "https://metric-detail-intervention-enter.trycloudflare.com",
        ],
    ),
    
)


@mcp.tool()
def get_server_status() -> dict:
    """Return the status of the dummy MCP server."""
    return {
        "status": "healthy",
        "server": "dummy-mcp-server",
        "message": "MCP tool invoked successfully",
    }


@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two integers and return the result."""
    return {
        "a": a,
        "b": b,
        "result": a + b,
    }

# @mcp.tool()
# def new_method


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
from fastmcp import FastMCP

mcp = FastMCP("Test SSE Server")


@mcp.tool()
def ping() -> str:
    """Simple ping test tool."""
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=5001)

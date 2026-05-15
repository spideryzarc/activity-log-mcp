from .server import mcp


def main() -> None:
    """Main entrypoint for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

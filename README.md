# Activity Log MCP

An MCP (Model Context Protocol) server for activity logging workflows used by autonomous agents.

This project replaces script-based logging automation with MCP tools while preserving behavioral parity for:
- append new entries
- update last entry
- dump entries (optionally filtered by date)
- rotate old entries into monthly archives

## Features

- Parity with the original `log-activity` workflow semantics.
- Local file persistence at `activity-log/activity_log.json`.
- Automatic directory creation for write operations.
- Corrupt JSON backup to `.bak` before recovering.
- Rotation into `activity-log/archive/activity_log_YYYY-MM.json`.

## IDE's MCP Installation

To make the MCP tools available in your IDE, add the following configuration to your MCP servers list. This example uses `uvx` to run the server directly from the GitHub repository, but you can also clone the repo locally and point to that path instead.

### Antigravity IDE

Add to the `~/.gemini/antigravity/mcp_servers.json` (on Linux/macOS) or `%APPDATA%\antigravity\mcp_servers.json` (on Windows):

```json
{
    "mcpServers": {
        "activity-log-mcp": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/spideryzarc/activity-log-mcp",
                "activity-log-mcp"
            ]
        }
    }
}
```

### VS Code
Add to the `~/.config/Code/User/settings.json` (on Linux/macOS) or `%APPDATA%\Code\User\settings.json` (on Windows):

```json
{
    "servers": {
        "activity-log-mcp": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/spideryzarc/activity-log-mcp",
                "activity-log-mcp"
            ],
            "type": "stdio"
        }
    }
}
```

## Exposed MCP Tools

- `log_activity`
- `update_last_activity`
- `dump_activity_log`
- `rotate_activity_log`

## Local Development

1. Install `uv` if needed.
2. Run the server:

```bash
uv run activity-log-mcp
```

3. Run tests:

```bash
uv run pytest
```

## Project Structure

- `pyproject.toml`: package metadata, dependencies, and entrypoint.
- `src/activity_log_mcp/main.py`: server entrypoint.
- `src/activity_log_mcp/server.py`: MCP instance and tool implementations.
- `tests/test_server.py`: pytest coverage for parity behaviors.

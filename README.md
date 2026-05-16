# Activity Log MCP

An MCP (Model Context Protocol) server for activity logging workflows used by autonomous agents.

The primary goal of this MCP is to provide a tool for agents to register changes made in a codebase without spending excessive tokens.
This structured log is useful as a reliable source for generating future reports.

It provides tools to:
- append new entries
- update last entry
- dump entries (optionally filtered by date)
- rotate old entries into monthly archives

## Features

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

## Recommended IDE Rule

To ensure consistency, advise users to create a fixed IDE rule/instruction so agents always log tasks with this MCP.

Example rule:

```text
Whenever you complete a relevant coding, refactoring, or documentation task,
log the activity using the activity-log-mcp MCP.
Include a short description and the list of modified files.
If the task is a continuation of a previous one, update the last entry instead of creating a new one.
```

This reduces context loss, avoids unnecessary token usage to reconstruct history, and improves future report generation.

## Exposed MCP Tools

- `log_activity`
- `update_last_activity`
- `dump_activity_log`
- `rotate_activity_log`

## JSON Log Example

Example `activity-log/activity_log.json` file with two entries:

```json
[
    {
        "date": "2026-05-16T10:12:31",
        "objective": "Initialize local MCP server",
        "result": "Initialized the MCP server locally",
        "changed_files": [
            "src/activity_log_mcp/main.py",
            "src/activity_log_mcp/server.py"
        ],
        "status": "success",
        "notes": ""
    },
    {
        "date": "2026-05-16T10:24:05",
        "objective": "Add test for update_last_activity",
        "result": "Added test for update_last_activity",
        "changed_files": [
            "tests/test_server.py"
        ],
        "status": "success",
        "notes": ""
    }
]
```

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
- `tests/test_server.py`: pytest coverage for logging behaviors.

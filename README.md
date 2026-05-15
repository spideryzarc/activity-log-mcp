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

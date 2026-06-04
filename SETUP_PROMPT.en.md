# Prompt for an AI agent: install and configure the «navisworks-viewpoints» MCP

[Русский](SETUP_PROMPT.md) · **English**

> **How to use:** open your AI agent's chat (Cursor, Claude Code, Codex, Opencode, Kimi, etc.)
> and paste the block below (from `=== START ===` to `=== END ===`). The agent will detect your client,
> write the config, run and verify the server. It only asks for a path if you use the master-file scenario.

---

```text
=== START OF AGENT INSTRUCTION ===

Task: install the "navisworks-viewpoints" MCP server and add it to the config of the CURRENT client
you are running in. Act autonomously, run commands yourself, only ask about the data path.

Repository: https://github.com/mikhalchankasm/navisworks-viewpoints-mcp
Launch: via uvx (Python is pulled in automatically by the uv tool).

STEP 1. Check uv.
  Run: uv --version
  If the command is not found — install uv and ask to restart the terminal/client:
    Windows (PowerShell): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    macOS/Linux:          curl -LsSf https://astral.sh/uv/install.sh | sh

STEP 2. Data path — OPTIONAL.
  For everyday work (open an arbitrary file, sort/check/move viewpoints) env is NOT needed —
  the user passes the file path right in the request. In that case install the server WITHOUT
  an "env" block.
  Only ask me: "Do you use the single master-file scenario (an accumulating 'Общие точки' file)?"
   - If yes — ask for the full master path (e.g. D:\Projects\Viewpoints\Общие точки 16-04-2026.xml)
     and add it to env as NAVISWORKS_MASTER. (Or the exports dir NAVISWORKS_VIEWPOINTS_ROOT
     + the file name NAVISWORKS_MASTER_FILENAME.)
   - If no / not sure — install without env, the path will be passed in each request.
  If I already gave a path in my message — use it, don't ask again.

STEP 3. Detect which client you are and write the server into the right config.
  DO NOT overwrite existing MCP servers — only add the new key "navisworks-viewpoints".
  Escape paths in JSON with double backslashes: "D:\\Projects\\Viewpoints\\Общие точки 16-04-2026.xml".

  • Cursor       → .cursor/mcp.json in the project root (or ~/.cursor/mcp.json for all projects)
  • Claude Code  → .mcp.json in the project root (or run: claude mcp add)
  • Claude Desktop → claude_desktop_config.json (Settings → Developer → Edit Config)
  • Opencode     → opencode.json
  • Codex        → ~/.codex/config.toml
  • Other (stdio) → a similar command/args/env block

  Block for JSON clients (Cursor / Claude Code / Claude Desktop):
  {
    "mcpServers": {
      "navisworks-viewpoints": {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
        "env": { "NAVISWORKS_MASTER": "<PATH_WITH_DOUBLE_BACKSLASHES>" }
      }
    }
  }

  For Opencode the top-level key is "mcp", type "local",
  the command field is "command" (an array), variables go under "environment".

  For Codex (TOML):
    [mcp_servers.navisworks-viewpoints]
    command = "uvx"
    args = ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"]
    [mcp_servers.navisworks-viewpoints.env]
    NAVISWORKS_MASTER = "<PATH>"

STEP 4. Verify the install with a deterministic command (do NOT run the server with no args — it blocks on stdio):
  uvx --from git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp navisworks-viewpoints-mcp --check
  The command prints JSON and should finish without errors (package downloaded, server starts).
  If you use the master scenario — set the same env as in the config and check that master_exists=true.
  If installing without env — the "paths not found" warning is NORMAL (the path is passed in requests).

STEP 5. Tell me to restart/refresh the MCP list in the client and verify that "navisworks-viewpoints"
  is active and these tools are visible: get_config, list_folders, list_views, export_tree,
  sort_viewpoints, dedupe_viewpoints, rename_folder, affix_view_names, split_file, merge_viewpoints,
  move_views, audit_viewpoints, reconcile_by_name, sync_lists, add_to_master.
  If the client supports it — call get_config and show the result.

STEP 6. Report briefly: which config file was changed, what path was written, what --check showed.

=== END OF AGENT INSTRUCTION ===
```

---

## Even shorter (for agents that can read URLs)

If your agent can open links, one line is enough:

```text
Read https://raw.githubusercontent.com/mikhalchankasm/navisworks-viewpoints-mcp/main/SETUP_PROMPT.en.md
and follow it to install the navisworks-viewpoints MCP server for my client.
```

## What the server does

After installing, in chat you can ask (the agent picks the tool itself):

Any file (no master needed, path in the request):
- "show the viewpoint tree as collapsible HTML" → `export_tree`
- "sort the viewpoints in D:\…\export.xml" → `sort_viewpoints`
- "remove duplicate viewpoints" → `dedupe_viewpoints`
- "check the file for duplicate GUIDs/names" → `audit_viewpoints`
- "show the folders and how many viewpoints" → `list_folders` / `list_views`
- "rename a folder" → `rename_folder`
- "add a prefix/suffix to viewpoint names" → `affix_view_names`
- "move viewpoints 92, 95 from folder A to B" → `move_views`
- "extract viewpoints into a separate file" → `split_file`
- "add viewpoints from file1 into a folder of file2" → `merge_viewpoints`

Master scenario (needs a path to the master/dir):
- "add viewpoints from this export into the master" → `add_to_master`
- "sync the resolved/open lists" → `sync_lists`
- "reconcile the exports against the master" → `reconcile_by_name`

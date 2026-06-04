# navisworks-viewpoints-mcp

[Русский](README.md) · **English**

An MCP server for working with Navisworks viewpoint XML (`nw-exchange-12.0`) from any MCP-compatible AI client.

Works with **any viewpoint file**: open and sort viewpoints, check for duplicates, move them between folders, merge two files. Stitching several exports into a single master file and syncing "resolved / open" lists are **separate scenarios** on top of the same logic — not a required mode. No master file is needed by default — almost every tool accepts a file path as an argument.

This is a portable version of logic that used to live as scripts inside the `navisworks-external-viewpoint-manage` project. Now it installs on any machine with one line and connects to Claude, Codex, Kimi, Cursor, Opencode and others.

## One-click install

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=navisworks-viewpoints&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL21pa2hhbGNoYW5rYXNtL25hdmlzd29ya3Mtdmlld3BvaW50cy1tY3AiLCJuYXZpc3dvcmtzLXZpZXdwb2ludHMtbWNwIl0sImVudiI6eyJOQVZJU1dPUktTX01BU1RFUiI6IlJFUExBQ0VfV0lUSF9GVUxMX1BBVEhfVE9fTUFTVEVSLnhtbCJ9fQ==)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-007ACC?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=navisworks-viewpoints&config=%7b%22name%22%3a%22navisworks-viewpoints%22%2c%22command%22%3a%22uvx%22%2c%22args%22%3a%5b%22--from%22%2c%22git%2bhttps%3a%2f%2fgithub.com%2fmikhalchankasm%2fnavisworks-viewpoints-mcp%22%2c%22navisworks-viewpoints-mcp%22%5d%2c%22env%22%3a%7b%22NAVISWORKS_MASTER%22%3a%22REPLACE_WITH_FULL_PATH_TO_MASTER.xml%22%7d%7d)

> After the click your client adds the server automatically. Requires [uv](https://docs.astral.sh/uv/) installed.
> For everyday use (open a file and sort/check viewpoints) you need **nothing else** —
> the file path is passed right in your request. Fill in the `NAVISWORKS_MASTER` field
> (placeholder `REPLACE_WITH_FULL_PATH_TO_MASTER.xml`) only if you use the master-file scenario —
> you can do it later in Settings → MCP, or delete it if you don't use a master.

## ⚡ Quick start via an AI agent

Don't want to configure by hand? Open your agent's chat (Cursor, Claude Code, Codex…) and paste one line:

```text
Read https://raw.githubusercontent.com/mikhalchankasm/navisworks-viewpoints-mcp/main/SETUP_PROMPT.en.md
and follow it to install the navisworks-viewpoints MCP server for my client.
```

The agent detects your client, writes the config (without touching other servers), runs and verifies the server. If your agent can't open links, copy the ready-made prompt from [`SETUP_PROMPT.en.md`](SETUP_PROMPT.en.md). Manual setup is below.

## Tools (MCP)

All tools work with any file (path as an argument); where the path is optional, the master from env is used as a default.

| Tool | What it does | File |
|---|---|---|
| `export_tree` | Save the viewpoint tree to HTML (collapsible) / text to browse without Navisworks | any |
| `sort_viewpoints` | Sort viewpoints in a file, recompute `(N)` (one folder or all) | any |
| `dedupe_viewpoints` | Remove duplicates by name (within a folder) or GUID (globally) | any |
| `audit_viewpoints` | Duplicate GUIDs, name/folder conflicts, counts | any |
| `list_folders` | Folders in a file with view counts | any |
| `list_views` | Viewpoints (name, guid) in a specific folder | any |
| `rename_folder` | Rename a folder (recomputes `(N)`) | any |
| `affix_view_names` | Add a prefix/suffix to viewpoint names (bulk) | any |
| `move_views` | Move viewpoints by name between folders of one file (has `dry_run`) | any |
| `split_file` | Extract viewpoints by name into a new file (copy or move) | any |
| `merge_viewpoints` | Add views from one file into a folder of another (name clash = error) | any |
| `reconcile_by_name` | Reconcile by name: present in exports but missing in the target (and vice versa) | dir + target |
| `get_config` | Show current paths from env (only needed for the master scenario) | — |
| `sync_lists` | **Master scenario**: sync two ID lists (resolved/open) against an exports directory | master + dir |
| `add_to_master` | **Master scenario**: dated copy of the master + add into `ЛКП (…)`, dups silently reported | master |

## Scenarios

The server doesn't impose a single process — it's a set of operations. Typical schemes:

### A. Ad-hoc with a single file (no master needed)
The most common case: open an arbitrary export and tidy it up.
- "Show the viewpoint tree so I can browse without Navisworks" → `export_tree` (collapsible HTML; open the returned file in a browser)
- "Sort the viewpoints in `D:\…\export.xml`" → `sort_viewpoints`
- "Remove duplicate viewpoints" → `dedupe_viewpoints`
- "Check the file for duplicate GUIDs and identical names" → `audit_viewpoints`
- "Show the folders and how many viewpoints each has" → `list_folders` / `list_views`
- "Rename folder `Folder 1` to `Floor 1`" → `rename_folder`
- "Add the prefix `AX-` to all viewpoint names" → `affix_view_names`
- "Move viewpoints 92, 95 from folder A to folder B" → `move_views`
- "Extract viewpoints 100–105 into a separate file" → `split_file`

### B. Merge two files
- "Add all viewpoints from `export.xml` into the `Floor 1` folder of `combined.xml`" → `merge_viewpoints`
  (new GUIDs by default; a name clash stops the merge — for "skip silently" see scenario C).

### C. Stitching into a master file (one scheme, optional)
When you keep a single accumulating "Общие точки" (Common viewpoints) file that exports flow into:
- "Add viewpoints from the export into the master" → `add_to_master` (creates a dated copy, places them
  into `ЛКП (…)`, silently skips existing names and collects them in a report).
- "Sync the resolved/open lists with the exports directory" → `sync_lists`.
- "Reconcile what the master is missing relative to the exports" → `reconcile_by_name`.

For scenario C it's convenient to set the master path in env once (see below) — then you don't
need to pass it on every call. For scenarios A and B just pass the file path in your request.

## Requirements

- [uv](https://docs.astral.sh/uv/) (installs Python itself).
- Git (for installing from the repository).

## Install / run

The launch command is the same for every client — `uvx` pulls the package straight from git and keeps it in an isolated environment:

```bash
uvx --from git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp navisworks-viewpoints-mcp
```

Local development:

```bash
git clone https://github.com/mikhalchankasm/navisworks-viewpoints-mcp
cd navisworks-viewpoints-mcp
uv sync --extra dev
uv run pytest
uv run navisworks-viewpoints-mcp           # run the server over stdio
uv run navisworks-viewpoints-mcp --check   # check that env paths are picked up
uv run navisworks-viewpoints-mcp --version
```

## Data paths

**By default you don't need to configure anything** — pass the file path right in your request
("sort `D:\…\export.xml`"). This covers scenarios A and B.

Environment variables are needed **only for convenience in the master scenario** (C): set them once
in your client config, and the `add_to_master` / `sync_lists` / `reconcile_by_name` tools will use
default paths without specifying them on every call.

| Variable | Purpose |
|---|---|
| `NAVISWORKS_MASTER` | Full path to the master file (highest priority) |
| `NAVISWORKS_VIEWPOINTS_ROOT` | Directory with `.xml` exports |
| `NAVISWORKS_MASTER_FILENAME` | Master file name only (inside ROOT) |

An explicit path in a tool argument (`xml=...`, `master=...`, `root=...`) always wins over env.
If the variables are unset and no path is passed, the tool returns a clear error.

## Connecting clients

In all examples, substitute the real paths to your files. Ready-made files are in [`examples/configs/`](examples/configs).

### Claude Code

`.mcp.json` in the project root (or `claude mcp add`):

```json
{
  "mcpServers": {
    "navisworks-viewpoints": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
      "env": {
        "NAVISWORKS_VIEWPOINTS_ROOT": "D:\\\\Path\\\\To\\\\Viewpoints",
        "NAVISWORKS_MASTER_FILENAME": "Общие точки 16-04-2026.xml"
      }
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json` (Settings → Developer → Edit Config) — same `mcpServers` structure as above.

### Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "navisworks-viewpoints": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
      "env": { "NAVISWORKS_MASTER": "D:\\\\...\\\\Общие точки 16-04-2026.xml" }
    }
  }
}
```

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.navisworks-viewpoints]
command = "uvx"
args = ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"]
env = { NAVISWORKS_MASTER = "D:\\\\...\\\\Общие точки 16-04-2026.xml" }
```

### Opencode

`opencode.json`:

```json
{
  "mcp": {
    "navisworks-viewpoints": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
      "environment": { "NAVISWORKS_MASTER": "D:\\\\...\\\\Общие точки 16-04-2026.xml" }
    }
  }
}
```

### Kimi and other stdio clients

Any client that supports MCP over stdio: `command = uvx`, `args = ["--from", "git+...","navisworks-viewpoints-mcp"]`, environment variables with paths. See [`examples/configs/generic-stdio.md`](examples/configs/generic-stdio.md).

## XML format

- Root `<exchange ... xsi:noNamespaceSchemaLocation="...nw-exchange-12.0.xsd">`.
- `<viewpoints>` → `<viewfolder name="..." guid="...">` and/or flat `<view>`.
- The `(N)` counter in a folder name = number of direct child `<view>` elements; recomputed automatically after edits.
- Writing: UTF-8, XML declaration, `xsi` namespace. The `filename`/`filepath` attributes of `<exchange>` are left untouched.

## License

MIT

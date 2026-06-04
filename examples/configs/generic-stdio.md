# Generic stdio MCP (Kimi и любой другой клиент)

Сервер общается по **stdio**. Любому MCP-клиенту нужно передать три вещи:

- **command:** `uvx`
- **args:** `["--from", "git+https://github.com/<USER>/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"]`
- **env:** пути к данным Navisworks.

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `NAVISWORKS_MASTER` | Полный путь к мастер-файлу (высший приоритет) |
| `NAVISWORKS_VIEWPOINTS_ROOT` | Каталог с `.xml` выгрузками |
| `NAVISWORKS_MASTER_FILENAME` | Только имя файла мастера (внутри ROOT) |

Достаточно либо `NAVISWORKS_MASTER`, либо пары `ROOT` + `FILENAME`.
Для `reconcile_by_name` / `sync_lists` нужен `NAVISWORKS_VIEWPOINTS_ROOT`.

## Универсальный JSON-блок

```json
{
  "command": "uvx",
  "args": ["--from", "git+https://github.com/<USER>/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
  "env": {
    "NAVISWORKS_VIEWPOINTS_ROOT": "D:\\Path\\To\\Точки_обзора",
    "NAVISWORKS_MASTER_FILENAME": "Общие точки 16-04-2026.xml"
  }
}
```

## Альтернатива без uvx (локальный клон)

```json
{
  "command": "uv",
  "args": ["run", "--directory", "D:\\GitHub\\navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
  "env": { "NAVISWORKS_MASTER": "D:\\...\\Общие точки 16-04-2026.xml" }
}
```

## Проверка вручную

```bash
uvx --from git+https://github.com/<USER>/navisworks-viewpoints-mcp navisworks-viewpoints-mcp
```

Сервер запустится и будет ждать MCP-сообщения на stdin (Ctrl+C для выхода).
Для интерактивной отладки: `uv run mcp dev src/navisworks_viewpoints_mcp/server.py`.

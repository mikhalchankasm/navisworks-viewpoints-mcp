# Промт для ИИ-агента: установить и настроить MCP «navisworks-viewpoints»

> **Как пользоваться:** открой чат своего ИИ-агента (Cursor, Claude Code, Codex, Opencode, Kimi и т.п.)
> и вставь блок ниже (от `=== НАЧАЛО ===` до `=== КОНЕЦ ===`). Агент сам определит твой клиент,
> пропишет конфиг, запустит и проверит сервер. Когда спросит — назови путь к мастер-файлу точек обзора.

---

```text
=== НАЧАЛО ИНСТРУКЦИИ ДЛЯ АГЕНТА ===

Задача: установить MCP-сервер "navisworks-viewpoints" и прописать его в конфиг ТЕКУЩЕГО клиента,
из которого ты сейчас работаешь. Действуй автономно, выполняй команды сам, спрашивай только путь к данным.

Репозиторий: https://github.com/mikhalchankasm/navisworks-viewpoints-mcp
Запуск: через uvx (Python подтянется автоматически инструментом uv).

ШАГ 1. Проверь uv.
  Выполни: uv --version
  Если команда не найдена — установи uv и попроси перезапустить терминал/клиент:
    Windows (PowerShell): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    macOS/Linux:          curl -LsSf https://astral.sh/uv/install.sh | sh

ШАГ 2. Путь к данным — ОПЦИОНАЛЬНО.
  Для обычной работы (открыть произвольный файл, отсортировать/проверить/перенести точки)
  env НЕ нужен — путь к файлу пользователь передаёт прямо в запросе. В этом случае ставь
  сервер БЕЗ блока "env".
  Спроси меня только: «Используешь схему с единым мастер-файлом (накопительный "Общие точки")?»
   - Если да — попроси полный путь к мастеру (например D:\Проекты\Точки_обзора\Общие точки 16-04-2026.xml)
     и добавь его в env как NAVISWORKS_MASTER. (Либо каталог выгрузок NAVISWORKS_VIEWPOINTS_ROOT
     + имя файла NAVISWORKS_MASTER_FILENAME.)
   - Если нет / не уверен — ставь без env, путь будем передавать в каждом запросе.
  Если я уже дал путь в сообщении — используй его, не переспрашивай.

ШАГ 3. Определи, какой ты клиент, и впиши сервер в нужный конфиг.
  НЕ затирай уже существующие MCP-серверы — только добавь новый ключ "navisworks-viewpoints".
  Пути в JSON экранируй двойным слэшем: "D:\\Проекты\\Точки_обзора\\Общие точки 16-04-2026.xml".

  • Cursor       → .cursor/mcp.json в корне проекта (или ~/.cursor/mcp.json для всех проектов)
  • Claude Code  → .mcp.json в корне проекта (или команда: claude mcp add)
  • Claude Desktop → claude_desktop_config.json (Settings → Developer → Edit Config)
  • Opencode     → opencode.json
  • Codex        → ~/.codex/config.toml
  • Другое (stdio) → аналогичный блок command/args/env

  Блок для JSON-клиентов (Cursor / Claude Code / Claude Desktop):
  {
    "mcpServers": {
      "navisworks-viewpoints": {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
        "env": { "NAVISWORKS_MASTER": "<ПУТЬ_С_ДВОЙНЫМИ_СЛЭШАМИ>" }
      }
    }
  }

  Для Opencode ключ верхнего уровня называется "mcp", тип "local",
  поле команды — "command" (массив), переменные — "environment".

  Для Codex (TOML):
    [mcp_servers.navisworks-viewpoints]
    command = "uvx"
    args = ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"]
    [mcp_servers.navisworks-viewpoints.env]
    NAVISWORKS_MASTER = "<ПУТЬ>"

ШАГ 4. Проверь установку детерминированной командой (НЕ запускай сервер без аргументов — он висит на stdio):
  uvx --from git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp navisworks-viewpoints-mcp --check
  Команда печатает JSON и должна отработать без ошибок (пакет скачался, сервер запускается).
  Если используешь схему с мастером — подставь те же env, что в конфиге, и проверь, что master_exists=true.
  Если ставишь без env — предупреждение «пути не найдены» это НОРМАЛЬНО (путь будешь передавать в запросах).

ШАГ 5. Скажи мне перезапустить/обновить список MCP в клиенте и проверить, что сервер "navisworks-viewpoints"
  активен и видны инструменты: get_config, list_folders, list_views, merge_viewpoints, move_views,
  audit_viewpoints, reconcile_by_name, sync_lists, add_to_master.
  Если клиент это умеет — вызови get_config и покажи результат.

ШАГ 6. Кратко отчитайся: какой конфиг-файл изменён, какой путь прописан, что показал --check.

=== КОНЕЦ ИНСТРУКЦИИ ДЛЯ АГЕНТА ===
```

---

## Ещё короче (для агентов, умеющих читать URL)

Если твой агент умеет открывать ссылки, хватит одной фразы:

```text
Прочитай https://raw.githubusercontent.com/mikhalchankasm/navisworks-viewpoints-mcp/main/SETUP_PROMPT.md
и выполни инструкцию по установке MCP-сервера navisworks-viewpoints для моего клиента.
Путь к мастер-файлу спроси у меня.
```

## Что делает сервер

После установки в чате можно просить (агент сам выберет инструмент):

Любой файл (мастер не нужен, путь — в запросе):
- «отсортируй точки в D:\…\выгрузка.xml» → `sort_viewpoints`
- «проверь файл на дубли GUID/имён» → `audit_viewpoints`
- «покажи папки и сколько точек» → `list_folders` / `list_views`
- «перенеси точки 92, 95 из папки A в B» → `move_views`
- «добавь точки из файла1 в папку файла2» → `merge_viewpoints`

Схема с мастером (нужен путь к мастеру/каталогу):
- «добавь точки из этой выгрузки в мастер» → `add_to_master`
- «синхронизируй списки решённых/открытых» → `sync_lists`
- «сверь выгрузки с мастером» → `reconcile_by_name`

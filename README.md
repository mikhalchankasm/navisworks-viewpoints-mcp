# navisworks-viewpoints-mcp

MCP-сервер для работы с XML точек обзора Navisworks (`nw-exchange-12.0`): merge выгрузок в мастер-файл, перенос точек между папками, синхронизация списков «решено / не решено», аудит и сверка по именам — всё через любой MCP-совместимый ИИ-клиент.

Это портативная версия логики, которая раньше жила скриптами внутри проекта `navisworks-external-viewpoint-manage`. Теперь её можно поставить на любой машине одной строкой и подключить к Claude, Codex, Kimi, Cursor, Opencode и др.

## Установка в один клик

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=navisworks-viewpoints&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL21pa2hhbGNoYW5rYXNtL25hdmlzd29ya3Mtdmlld3BvaW50cy1tY3AiLCJuYXZpc3dvcmtzLXZpZXdwb2ludHMtbWNwIl0sImVudiI6eyJOQVZJU1dPUktTX01BU1RFUiI6IlJFUExBQ0VfV0lUSF9GVUxMX1BBVEhfVE9fTUFTVEVSLnhtbCJ9fQ==)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-007ACC?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=navisworks-viewpoints&config=%7b%22name%22%3a%22navisworks-viewpoints%22%2c%22command%22%3a%22uvx%22%2c%22args%22%3a%5b%22--from%22%2c%22git%2bhttps%3a%2f%2fgithub.com%2fmikhalchankasm%2fnavisworks-viewpoints-mcp%22%2c%22navisworks-viewpoints-mcp%22%5d%2c%22env%22%3a%7b%22NAVISWORKS_MASTER%22%3a%22REPLACE_WITH_FULL_PATH_TO_MASTER.xml%22%7d%7d)

> После клика клиент добавит сервер автоматически. Затем **впишите путь к мастер-файлу** в поле
> `NAVISWORKS_MASTER` (в Cursor: Settings → MCP → navisworks-viewpoints → Edit; вместо
> `REPLACE_WITH_FULL_PATH_TO_MASTER.xml` — полный путь к вашему `.xml`) и обновите список MCP.
> Требуется установленный [uv](https://docs.astral.sh/uv/). Не хотите вписывать путь руками — используйте вариант через агента ниже.

## ⚡ Быстрый старт через ИИ-агента

Не хотите настраивать руками? Откройте чат своего агента (Cursor, Claude Code, Codex…) и дайте одну фразу:

```text
Прочитай https://raw.githubusercontent.com/mikhalchankasm/navisworks-viewpoints-mcp/main/SETUP_PROMPT.md
и выполни инструкцию по установке MCP-сервера navisworks-viewpoints для моего клиента.
Путь к мастер-файлу спроси у меня.
```

Агент сам определит клиент, пропишет конфиг (не трогая другие серверы), запустит и проверит сервер. Если агент не умеет открывать ссылки — скопируйте готовый промт из [`SETUP_PROMPT.md`](SETUP_PROMPT.md). Ручная настройка — ниже.

## Возможности (инструменты MCP)

| Инструмент | Что делает |
|---|---|
| `get_config` | Показать текущие пути (из переменных окружения) |
| `list_folders` | Папки мастера со счётчиками view |
| `list_views` | Точки (имя, guid) в конкретной папке |
| `merge_viewpoints` | Добавить view из выгрузки в папку (конфликт имени = ошибка) |
| `move_views` | Перенести точки по именам между папками (есть `dry_run`) |
| `audit_viewpoints` | Дубли GUID, конфликты имя/папка, счётчики |
| `reconcile_by_name` | Сверка: что есть в выгрузках, но нет в мастере (и наоборот) |
| `sync_lists` | Синхронизировать два списка ID с каталогом выгрузок |
| `add_to_master` | **Рекомендуемый сценарий**: датированная копия мастера + добавление в `ЛКП (…)`, конфликты молча в отчёт |

## Требования

- [uv](https://docs.astral.sh/uv/) (ставит Python сам).
- Git (для установки из репозитория).

## Установка / запуск

Запуск сервера у всех клиентов одинаковый — команда `uvx` тянет пакет прямо из git и держит его в изолированном окружении:

```bash
uvx --from git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp navisworks-viewpoints-mcp
```

Локальная разработка:

```bash
git clone https://github.com/mikhalchankasm/navisworks-viewpoints-mcp
cd navisworks-viewpoints-mcp
uv sync --extra dev
uv run pytest
uv run navisworks-viewpoints-mcp           # запустить сервер по stdio
uv run navisworks-viewpoints-mcp --check   # проверить, что пути из env подхватились
uv run navisworks-viewpoints-mcp --version
```

## Настройка путей (per-machine)

Пути не зашиты в код — каждый задаёт их через переменные окружения **в блоке конфигурации своего клиента**:

| Переменная | Назначение |
|---|---|
| `NAVISWORKS_MASTER` | Полный путь к мастер-файлу (высший приоритет) |
| `NAVISWORKS_VIEWPOINTS_ROOT` | Каталог с `.xml` выгрузками |
| `NAVISWORKS_MASTER_FILENAME` | Только имя файла мастера (внутри ROOT) |

Любой инструмент также принимает путь явным аргументом (`master=...`, `root=...`), что важнее env.

## Подключение к клиентам

Во всех примерах подставьте реальные пути к вашим файлам. Готовые файлы — в [`examples/configs/`](examples/configs).

### Claude Code

`.mcp.json` в корне проекта (или `claude mcp add`):

```json
{
  "mcpServers": {
    "navisworks-viewpoints": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mikhalchankasm/navisworks-viewpoints-mcp", "navisworks-viewpoints-mcp"],
      "env": {
        "NAVISWORKS_VIEWPOINTS_ROOT": "D:\\\\Path\\\\To\\\\Точки_обзора",
        "NAVISWORKS_MASTER_FILENAME": "Общие точки 16-04-2026.xml"
      }
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json` (Settings → Developer → Edit Config) — та же структура `mcpServers`, что и выше.

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

### Kimi и прочие stdio-клиенты

Любой клиент, поддерживающий MCP по stdio: `command = uvx`, `args = ["--from", "git+...","navisworks-viewpoints-mcp"]`, переменные окружения с путями. См. [`examples/configs/generic-stdio.md`](examples/configs/generic-stdio.md).

## Формат XML

- Корень `<exchange ... xsi:noNamespaceSchemaLocation="...nw-exchange-12.0.xsd">`.
- `<viewpoints>` → `<viewfolder name="..." guid="...">` и/или плоские `<view>`.
- Счётчик `(N)` в имени папки = число прямых дочерних `<view>`; пересчитывается автоматически после правок.
- Запись: UTF-8, XML-декларация, namespace `xsi`. Поля `filename`/`filepath` у `<exchange>` не трогаются.

## Лицензия

MIT

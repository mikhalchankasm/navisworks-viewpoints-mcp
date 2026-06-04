# navisworks-viewpoints-mcp

MCP-сервер для работы с XML точек обзора Navisworks (`nw-exchange-12.0`) из любого MCP-совместимого ИИ-клиента.

Работает с **любым файлом** точек обзора: открыть и отсортировать точки, проверить на дубли, перенести между папками, слить два файла. Сборка нескольких выгрузок в один мастер-файл и синхронизация списков «решено / не решено» — это **отдельные сценарии** поверх той же логики, а не обязательный режим. Мастер-файл нигде не требуется по умолчанию — почти все инструменты принимают путь к файлу аргументом.

Это портативная версия логики, которая раньше жила скриптами внутри проекта `navisworks-external-viewpoint-manage`. Теперь её можно поставить на любой машине одной строкой и подключить к Claude, Codex, Kimi, Cursor, Opencode и др.

## Установка в один клик

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=navisworks-viewpoints&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL21pa2hhbGNoYW5rYXNtL25hdmlzd29ya3Mtdmlld3BvaW50cy1tY3AiLCJuYXZpc3dvcmtzLXZpZXdwb2ludHMtbWNwIl0sImVudiI6eyJOQVZJU1dPUktTX01BU1RFUiI6IlJFUExBQ0VfV0lUSF9GVUxMX1BBVEhfVE9fTUFTVEVSLnhtbCJ9fQ==)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-007ACC?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=navisworks-viewpoints&config=%7b%22name%22%3a%22navisworks-viewpoints%22%2c%22command%22%3a%22uvx%22%2c%22args%22%3a%5b%22--from%22%2c%22git%2bhttps%3a%2f%2fgithub.com%2fmikhalchankasm%2fnavisworks-viewpoints-mcp%22%2c%22navisworks-viewpoints-mcp%22%5d%2c%22env%22%3a%7b%22NAVISWORKS_MASTER%22%3a%22REPLACE_WITH_FULL_PATH_TO_MASTER.xml%22%7d%7d)

> После клика клиент добавит сервер автоматически. Требуется установленный [uv](https://docs.astral.sh/uv/).
> Для обычной работы (открыть файл и отсортировать/проверить точки) больше **ничего настраивать не нужно** —
> путь к файлу передаётся прямо в запросе. Поле `NAVISWORKS_MASTER` (placeholder
> `REPLACE_WITH_FULL_PATH_TO_MASTER.xml`) заполняйте, только если работаете по схеме с мастер-файлом —
> можно сделать это позже в Settings → MCP, либо удалить, если мастер не используете.

## ⚡ Быстрый старт через ИИ-агента

Не хотите настраивать руками? Откройте чат своего агента (Cursor, Claude Code, Codex…) и дайте одну фразу:

```text
Прочитай https://raw.githubusercontent.com/mikhalchankasm/navisworks-viewpoints-mcp/main/SETUP_PROMPT.md
и выполни инструкцию по установке MCP-сервера navisworks-viewpoints для моего клиента.
```

Агент сам определит клиент, пропишет конфиг (не трогая другие серверы), запустит и проверит сервер. Если агент не умеет открывать ссылки — скопируйте готовый промт из [`SETUP_PROMPT.md`](SETUP_PROMPT.md). Ручная настройка — ниже.

## Возможности (инструменты MCP)

Работают с любым файлом (путь — аргументом); там, где путь опционален, как дефолт берётся мастер из env.

| Инструмент | Что делает | Файл |
|---|---|---|
| `sort_viewpoints` | Отсортировать точки в файле, пересчитать `(N)` (одна папка или все) | любой |
| `audit_viewpoints` | Дубли GUID, конфликты имя/папка, счётчики | любой |
| `list_folders` | Папки файла со счётчиками view | любой |
| `list_views` | Точки (имя, guid) в конкретной папке | любой |
| `move_views` | Перенести точки по именам между папками одного файла (есть `dry_run`) | любой |
| `merge_viewpoints` | Добавить view из одного файла в папку другого (конфликт имени = ошибка) | любой |
| `reconcile_by_name` | Сверка по именам: что есть в выгрузках, но нет в целевом файле (и наоборот) | каталог + цель |
| `get_config` | Показать текущие пути из env (нужно только для схемы с мастером) | — |
| `sync_lists` | **Схема «мастер»**: синхронизировать два списка ID (решено/открыто) с каталогом выгрузок | мастер + каталог |
| `add_to_master` | **Схема «мастер»**: датированная копия мастера + добавление в `ЛКП (…)`, дубли молча в отчёт | мастер |

## Сценарии работы

Сервер не навязывает один процесс — это набор операций. Типичные схемы:

### A. Ad-hoc с одним файлом (мастер не нужен)
Самый частый случай: открыли произвольную выгрузку и привели в порядок.
- «Отсортируй точки в `D:\…\выгрузка.xml`» → `sort_viewpoints`
- «Проверь файл на дубли GUID и одинаковые имена» → `audit_viewpoints`
- «Покажи папки и сколько в каждой точек» → `list_folders` / `list_views`
- «Перенеси точки 92, 95 из папки A в папку B» → `move_views`

### B. Слить два файла
- «Добавь все точки из `выгрузка.xml` в папку `Этаж 1` файла `сводный.xml`» → `merge_viewpoints`
  (по умолчанию новые GUID, конфликт имени останавливает — для «пропускать молча» см. схему C).

### C. Сборка в мастер-файл (одна из схем, не обязательная)
Когда есть единый накопительный файл «Общие точки», куда стекаются выгрузки:
- «Добавь точки из выгрузки в мастер» → `add_to_master` (создаёт датированную копию, кладёт в `ЛКП (…)`,
  существующие имена молча пропускает и собирает в отчёт).
- «Синхронизируй списки решённых/открытых с каталогом выгрузок» → `sync_lists`.
- «Сверь, чего в мастере не хватает относительно выгрузок» → `reconcile_by_name`.

Для схемы C удобно один раз прописать путь к мастеру в env (см. ниже) — тогда его не нужно
указывать в каждом вызове. Для схем A и B достаточно передавать путь к файлу прямо в запросе.

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

## Пути к данным

**По умолчанию ничего настраивать не нужно** — передавайте путь к файлу прямо в запросе
(«отсортируй `D:\…\выгрузка.xml`»). Это покрывает схемы A и B.

Переменные окружения нужны **только для удобства схемы «мастер»** (C): задайте их один раз
в конфиге клиента, и инструменты `add_to_master` / `sync_lists` / `reconcile_by_name` будут
брать пути по умолчанию, без указания в каждом вызове.

| Переменная | Назначение |
|---|---|
| `NAVISWORKS_MASTER` | Полный путь к мастер-файлу (высший приоритет) |
| `NAVISWORKS_VIEWPOINTS_ROOT` | Каталог с `.xml` выгрузками |
| `NAVISWORKS_MASTER_FILENAME` | Только имя файла мастера (внутри ROOT) |

Явный путь в аргументе инструмента (`xml=...`, `master=...`, `root=...`) всегда важнее env.
Если переменные не заданы и путь не передан — инструмент вернёт понятную ошибку.

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

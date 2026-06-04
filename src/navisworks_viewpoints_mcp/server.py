"""
MCP-сервер (stdio) над core.py. Подключается к любому MCP-клиенту:
Claude Code/Desktop, Codex, Kimi, Cursor, Opencode.

Пути к мастеру/выгрузкам берутся из аргументов инструментов, а если не переданы —
из переменных окружения (см. config.py).
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from navisworks_viewpoints_mcp import config, core

mcp = FastMCP("navisworks-viewpoints")


@mcp.tool()
def get_config() -> dict:
    """Показать текущую настройку путей (env, разрешённый мастер и каталог выгрузок)."""
    return config.current_config()


@mcp.tool()
def list_folders(xml: str | None = None) -> dict:
    """Список папок (viewfolder) в файле: путь, число прямых view и view в поддереве.

    xml — путь к любому .xml точек обзора. Если не задан, берётся мастер из env
    (NAVISWORKS_MASTER / ROOT+FILENAME) — как удобный дефолт, не требование.
    """
    return core.list_folders(config.require_master(xml))


@mcp.tool()
def list_views(folder: str, xml: str | None = None) -> dict:
    """Прямые <view> (имя, guid) в указанной папке.

    folder — путь папки под <viewpoints>, например 'ЛКП (33)' или 'A/B' (пусто = корень).
    xml — путь к файлу; если не задан, берётся мастер из env.
    """
    return core.list_views(config.require_master(xml), folder)


@mcp.tool()
def sort_viewpoints(xml: str, folder: str | None = None, backup: bool = True) -> dict:
    """Отсортировать точки обзора в файле и пересчитать счётчики (N) у папок.

    Базовый ad-hoc сценарий: «открой файл, отсортируй точки» — мастер не нужен.
    folder — путь папки под <viewpoints>; если не задан, сортируются ВСЕ папки
    (и плоские view в корне). Сортировка по ведущему числу имени, затем по суффиксу
    (1552, 1552.1, 1552_2); нечисловые имена — по алфавиту в конце.
    backup — сделать xml.bak перед записью.
    """
    return core.sort_file(xml, folder, backup=backup)


@mcp.tool()
def dedupe_viewpoints(xml: str, by: str = "name", backup: bool = True) -> dict:
    """Удалить дубли точек обзора в файле (оставляя первый). Мастер не нужен.

    by="name" — дубли по имени в пределах одной папки;
    by="guid" — дубли по GUID глобально по всему файлу.
    Возвращает список удалённых; счётчики (N) пересчитываются. backup — сделать xml.bak.
    """
    return core.dedupe(xml, by=by, backup=backup)


@mcp.tool()
def rename_folder(xml: str, folder: str, new_name: str, backup: bool = True) -> dict:
    """Переименовать папку (viewfolder) в файле; счётчик (N) пересчитывается автоматически.

    folder — путь к существующей папке ('ЛКП (2)' или 'A/B').
    new_name — новое имя (можно без '(N)' — суффикс добавится сам).
    """
    return core.rename_folder(xml, folder, new_name, backup=backup)


@mcp.tool()
def split_file(
    xml: str, names: list[str], out: str,
    folder: str | None = None, move: bool = False, backup: bool = True,
) -> dict:
    """Вытащить точки по именам в новый файл (отдельная выгрузка nw-exchange).

    names — список точных имён. folder — искать только в этой папке; иначе по всему файлу.
    out — путь нового файла. move=False — копировать (исходник не трогать);
    move=True — также удалить из исходника (с backup и пересчётом (N)).
    """
    return core.split_file(xml, names, out, folder=folder, move=move, backup=backup)


@mcp.tool()
def affix_view_names(
    xml: str, prefix: str = "", suffix: str = "",
    folder: str | None = None, names: list[str] | None = None, backup: bool = True,
) -> dict:
    """Массово добавить префикс и/или суффикс к именам точек. Мастер не нужен.

    folder — ограничить одной папкой (иначе весь файл). names — ограничить списком имён.
    Затронутые папки пересортировываются, (N) пересчитывается. Нужно задать prefix и/или suffix.
    """
    return core.affix_view_names(
        xml, prefix, suffix, folder=folder, names=names, backup=backup
    )


@mcp.tool()
def export_tree(
    xml: str, out: str | None = None, fmt: str = "html", include_views: bool = True,
) -> dict:
    """Сохранить дерево точек в файл для просмотра без Navisworks; вернуть путь к файлу.

    fmt='html' — сворачиваемые узлы (<details>) + кнопки «развернуть/свернуть всё»;
    fmt='text' или 'md' — текстовое дерево с отступами. include_views — показывать точки.
    out=None — стабильный перезаписываемый файл во временной папке (<temp>/<имя>.tree.<ext>).
    Счётчики у папок: [прямые/в поддереве]. Открой возвращённый путь в браузере.
    """
    return core.export_tree(xml, out, fmt, include_views=include_views)


@mcp.tool()
def merge_viewpoints(
    base: str, src: str, folder: str, new_guids: bool = True, backup: bool = True
) -> dict:
    """Добавить все <view> из выгрузки src в папку folder файла base.

    Конфликт имени в целевой папке = ошибка (используйте add_to_master для «пропускать молча»).
    new_guids — выдать новые GUID переносимым точкам (по умолчанию да).
    backup — сделать base.bak перед записью.
    """
    return core.merge_views(base, src, folder, new_guids=new_guids, backup=backup)


@mcp.tool()
def move_views(
    xml: str, from_folder: str, to_folder: str, names: list[str],
    backup: bool = True, dry_run: bool = False,
) -> dict:
    """Перенести <view> по точным именам между папками одного файла.

    from_folder / to_folder — пути папок под <viewpoints> (через '/').
    names — список точных имён точек.
    dry_run — только показать, что было бы перенесено.
    """
    return core.move_views(
        xml, from_folder, to_folder, names, backup=backup, dry_run=dry_run
    )


@mcp.tool()
def audit_viewpoints(xml: str) -> dict:
    """Аудит файла: папки со счётчиками, дубли GUID, конфликты имя/папка, всего view."""
    return core.audit(xml)


@mcp.tool()
def reconcile_by_name(root: str | None = None, master: str | None = None) -> dict:
    """Сверка «числовых» имён точек: есть в выгрузках, но нет в мастере (и наоборот).

    root — каталог выгрузок (по умолчанию из env), master — мастер (по умолчанию из env).
    """
    return core.reconcile_by_name(config.require_root(root), config.require_master(master))


@mcp.tool()
def sync_lists(
    resolved_ids: list[str], open_ids: list[str],
    open_only: bool = False, root: str | None = None, master: str | None = None,
) -> dict:
    """Синхронизировать два списка ID (решённые/открытые) с каталогом выгрузок.

    Импортирует недостающие имена и переносит точки в мастере между ЛКП-Решено и ЛКП.
    open_only — работать только со списком open_ids (папка ЛКП), ЛКП-Решено не трогать.
    Перед записью делает .bak мастера. ЛКП-ВН.ОСН не трогается.
    """
    return core.sync_lists(
        resolved_ids, open_ids,
        config.require_root(root), config.require_master(master),
        open_only=open_only,
    )


@mcp.tool()
def add_to_master(
    src: str, today: str, master: str | None = None,
    folder_prefix: str = "ЛКП (", new_guids: bool = True, dated_copy: bool = True,
) -> dict:
    """Добавить точки из src в мастер по дефолтным правилам (рекомендуемый сценарий).

    - dated_copy=True: создаёт копию 'Общие точки {today}.xml' и правит её, мастер не трогает.
    - folder_prefix: целевая папка по префиксу имени (по умолчанию 'ЛКП (' — нерешённые).
    - конфликты имён: молча пропускаются и попадают в отчёт skipped_existing.
    today — дата DD-MM-YYYY (передаёт клиент; нельзя зашивать в сервер).
    master — путь к мастеру; если не задан, берётся из env.
    """
    return core.add_to_master(
        src, today=today, master=config.require_master(master),
        folder_prefix=folder_prefix, new_guids=new_guids, dated_copy=dated_copy,
    )


def main() -> None:
    """Точка входа консольного скрипта navisworks-viewpoints-mcp.

    Без аргументов — запуск MCP-сервера по stdio.
    --check    напечатать текущую настройку путей (JSON) и выйти (для проверки установки).
    --version  напечатать версию и выйти.
    """
    import sys

    argv = sys.argv[1:]
    if "--version" in argv or "-V" in argv:
        from navisworks_viewpoints_mcp import __version__
        print(__version__)
        return
    if "--check" in argv:
        import json
        cfg = config.current_config()
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        ok = bool(cfg["master_exists"] or cfg["root_exists"])
        print("\nOK: пути найдены." if ok
              else "\nВНИМАНИЕ: ни master, ни root не найдены — проверь env в конфиге клиента.")
        return
    mcp.run()


if __name__ == "__main__":
    main()

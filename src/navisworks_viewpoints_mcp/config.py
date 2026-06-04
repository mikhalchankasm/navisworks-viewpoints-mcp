"""
Настройка путей под конкретную машину через переменные окружения.

В отличие от старого scripts/navisworks_paths.py здесь НЕТ зашитого пути —
каждый пользователь задаёт окружение в конфиге своего MCP-клиента:

  NAVISWORKS_MASTER           — полный путь к мастер-файлу (высший приоритет)
  NAVISWORKS_VIEWPOINTS_ROOT  — каталог с .xml выгрузками
  NAVISWORKS_MASTER_FILENAME  — только имя файла мастера (внутри ROOT)

Если ни одна переменная не задана — инструменты требуют явный путь аргументом.
"""
from __future__ import annotations

import os
from pathlib import Path


class ConfigError(RuntimeError):
    """Не удалось определить путь к мастеру или каталогу выгрузок."""


def viewpoints_root() -> Path | None:
    raw = os.environ.get("NAVISWORKS_VIEWPOINTS_ROOT")
    return Path(raw) if raw else None


def master_filename() -> str | None:
    return os.environ.get("NAVISWORKS_MASTER_FILENAME")


def master_path() -> Path | None:
    """Полный путь к мастеру из env, либо None если не настроено."""
    full = os.environ.get("NAVISWORKS_MASTER")
    if full:
        return Path(full)
    root = viewpoints_root()
    name = master_filename()
    if root and name:
        return root / name
    return None


def require_master(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Вернуть путь к мастеру: явный аргумент важнее env. Иначе — ошибка."""
    if explicit:
        return Path(explicit)
    p = master_path()
    if p is None:
        raise ConfigError(
            "Путь к мастеру не задан. Передай аргумент master=... или задай "
            "NAVISWORKS_MASTER (либо NAVISWORKS_VIEWPOINTS_ROOT + NAVISWORKS_MASTER_FILENAME)."
        )
    return p


def require_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Вернуть каталог выгрузок: явный аргумент важнее env. Иначе — ошибка."""
    if explicit:
        return Path(explicit)
    r = viewpoints_root()
    if r is None:
        raise ConfigError(
            "Каталог выгрузок не задан. Передай аргумент root=... или задай "
            "NAVISWORKS_VIEWPOINTS_ROOT."
        )
    return r


def current_config() -> dict:
    """Снимок текущей настройки для инструмента get_config."""
    mp = master_path()
    root = viewpoints_root()
    return {
        "env": {
            "NAVISWORKS_MASTER": os.environ.get("NAVISWORKS_MASTER"),
            "NAVISWORKS_VIEWPOINTS_ROOT": os.environ.get("NAVISWORKS_VIEWPOINTS_ROOT"),
            "NAVISWORKS_MASTER_FILENAME": os.environ.get("NAVISWORKS_MASTER_FILENAME"),
        },
        "resolved_master": str(mp) if mp else None,
        "master_exists": mp.is_file() if mp else False,
        "resolved_root": str(root) if root else None,
        "root_exists": root.is_dir() if root else False,
    }

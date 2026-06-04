"""
Чистая логика работы с XML точек обзора Navisworks (nw-exchange).

Портировано из scripts/*.py исходного репозитория, но:
- без argparse / print / SystemExit — функции возвращают dict-отчёты и бросают ViewpointError;
- списки ID и пути приходят аргументами, ничего не зашито;
- запись XML единообразна: UTF-8, xml_declaration, register_namespace(xsi), ET.indent, пересчёт (N).
"""
from __future__ import annotations

import copy
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

XSI = "http://www.w3.org/2001/XMLSchema-instance"
SERVICE_NAMES = frozenset({"Базовый вид", "Сброс представления модели"})
_NUMERIC_VIEW = re.compile(r"^\d+([._\-].+)?$")


class ViewpointError(RuntimeError):
    """Доменная ошибка при обработке точек обзора."""


# --------------------------------------------------------------------------- #
# Низкоуровневые хелперы
# --------------------------------------------------------------------------- #
def _register_ns() -> None:
    ET.register_namespace("xsi", XSI)


def load_tree(path: Path) -> ET.ElementTree:
    p = Path(path)
    if not p.is_file():
        raise ViewpointError(f"Файл не найден: {p}")
    try:
        return ET.parse(p)
    except ET.ParseError as e:
        raise ViewpointError(f"Не удалось разобрать XML {p}: {e}") from e


def find_viewpoints(root: ET.Element) -> ET.Element | None:
    if root.tag == "viewpoints":
        return root
    return root.find("viewpoints")


def is_nw_exchange(root: ET.Element) -> bool:
    if root.tag != "exchange":
        return False
    sch = root.get(f"{{{XSI}}}noNamespaceSchemaLocation") or ""
    return "nw-exchange" in sch


def iter_views(elem: ET.Element) -> list[ET.Element]:
    """Все <view> в поддереве (рекурсивно, учитывает вложенные viewfolder)."""
    out: list[ET.Element] = []
    if elem.tag == "view":
        out.append(elem)
    for c in elem:
        out.extend(iter_views(c))
    return out


def direct_views(folder: ET.Element) -> list[ET.Element]:
    return [c for c in folder if c.tag == "view"]


def folder_base_label(name: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", name or "").strip()


def refresh_folder_counts(vp: ET.Element) -> None:
    """Пересчитать (N) = число прямых <view> у каждого viewfolder."""
    for f in vp.iter("viewfolder"):
        n = len(direct_views(f))
        base = folder_base_label(f.get("name") or "")
        if base:
            f.set("name", f"{base} ({n})")


def sort_key_view(e: ET.Element) -> tuple:
    """Сортировка по ведущему числу имени, затем по суффиксу (1552, 1552.1, 1552_2)."""
    name = e.get("name") or ""
    m = re.match(r"^(\d+)", name)
    if not m:
        return (2, name.lower())
    a = int(m.group(1))
    rest = name[m.end():]
    if not rest:
        return (0, a, 0, "", 0, "")
    sep = rest[0]
    suf = rest[1:]
    try:
        return (0, a, 1, sep, int(suf), "")
    except ValueError:
        return (0, a, 2, sep, 0, suf.lower())


def reorder_views(folder: ET.Element) -> None:
    views = direct_views(folder)
    views.sort(key=sort_key_view)
    for c in list(folder):
        if c.tag == "view":
            folder.remove(c)
    for v in views:
        folder.append(v)


def belongs_to_id(view_name: str, id_str: str) -> bool:
    """Точка относится к номеру ID: name == ID или name начинается с ID + (. _ -)."""
    n = (view_name or "").strip()
    if n in SERVICE_NAMES:
        return False
    if n == id_str:
        return True
    return (
        n.startswith(id_str + ".")
        or n.startswith(id_str + "_")
        or n.startswith(id_str + "-")
    )


def is_numeric_viewpoint_name(name: str) -> bool:
    n = (name or "").strip()
    if not n or n in SERVICE_NAMES:
        return False
    return bool(_NUMERIC_VIEW.match(n))


def _name_sort_key(n: str) -> tuple:
    m = re.match(r"^(\d+)(?:([._\-])(.+))?$", n)
    if not m:
        return (2, n.lower())
    base = int(m.group(1))
    if m.group(2) is None:
        return (0, base, "", 0, "")
    suf = (m.group(3) or "").lower()
    try:
        return (0, base, m.group(2), int(suf), "")
    except ValueError:
        return (1, base, m.group(2), 0, suf)


def _write_tree(tree: ET.ElementTree, path: Path) -> None:
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _backup(path: Path) -> str | None:
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    return str(bak)


def _resolve_folder(vp: ET.Element, path: str) -> ET.Element:
    """Найти viewfolder по пути 'A/B/C' под viewpoints. Пустой путь -> сам viewpoints."""
    path = (path or "").strip().strip("/")
    if not path:
        return vp
    cur = vp
    for part in path.split("/"):
        nxt = None
        for ch in cur:
            if ch.tag == "viewfolder" and (ch.get("name") or "") == part:
                nxt = ch
                break
        if nxt is None:
            here = cur.get("name") if cur.tag == "viewfolder" else "(viewpoints)"
            raise ViewpointError(
                f"Не найдена папка {part!r} внутри {here!r} (полный путь {path!r})"
            )
        cur = nxt
    return cur


def _find_folder_by_name(vp: ET.Element, folder_name: str) -> ET.Element:
    for child in vp:
        if child.tag == "viewfolder" and child.get("name") == folder_name:
            return child
    names = [c.get("name") for c in vp if c.tag == "viewfolder"]
    raise ViewpointError(f"Нет папки name={folder_name!r}. Есть: {names}")


def _find_folder_by_prefix(vp: ET.Element, prefix: str, *, exclude_prefixes=()) -> ET.Element | None:
    for ch in vp:
        if ch.tag != "viewfolder":
            continue
        nm = ch.get("name") or ""
        if any(nm.startswith(ex) for ex in exclude_prefixes):
            continue
        if nm.startswith(prefix):
            return ch
    return None


# --------------------------------------------------------------------------- #
# Операции (возвращают dict-отчёты)
# --------------------------------------------------------------------------- #
def list_folders(xml: Path) -> dict:
    """Все viewfolder: путь, прямые view, view в поддереве."""
    tree = load_tree(xml)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("Нет <viewpoints>")

    def subtree_count(elem: ET.Element) -> int:
        n = len(direct_views(elem))
        for c in elem:
            if c.tag == "viewfolder":
                n += subtree_count(c)
        return n

    def walk(parent: ET.Element, prefix: str):
        for el in parent:
            if el.tag != "viewfolder":
                continue
            name = el.get("name") or ""
            path = f"{prefix}/{name}" if prefix else name
            yield path, el
            yield from walk(el, path)

    folders = [
        {"path": path, "name": el.get("name"), "direct": len(direct_views(el)),
         "subtree": subtree_count(el)}
        for path, el in walk(vp, "")
    ]
    folders.sort(key=lambda r: r["path"].lower())
    return {"file": str(xml), "folders": folders, "total_views": subtree_count(vp)}


def list_views(xml: Path, folder_path: str) -> dict:
    """Прямые <view> в указанной папке (имя, guid)."""
    tree = load_tree(xml)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("Нет <viewpoints>")
    folder = _resolve_folder(vp, folder_path)
    views = [
        {"name": v.get("name"), "guid": v.get("guid")}
        for v in direct_views(folder)
    ]
    return {"file": str(xml), "folder": folder_path, "count": len(views), "views": views}


def merge_views(
    base: Path, src: Path, folder_name: str, *, new_guids: bool = True, backup: bool = True
) -> dict:
    """Добавить <view> из src в папку folder_name мастера base. Конфликт имени -> ошибка."""
    base, src = Path(base), Path(src)
    bak = _backup(base) if backup else None
    _register_ns()

    tree = load_tree(base)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("base: нет <viewpoints>")
    folder = _find_folder_by_name(vp, folder_name)

    stree = load_tree(src)
    svp = find_viewpoints(stree.getroot())
    if svp is None:
        raise ViewpointError("src: нет <viewpoints>")
    src_views = iter_views(svp)
    if not src_views:
        raise ViewpointError("src: нет элементов <view>")

    existing = {c.get("name") for c in direct_views(folder)}
    added: list[str] = []
    for v in src_views:
        name = v.get("name")
        if name in existing:
            raise ViewpointError(f"В целевой папке уже есть view name={name!r}")
        node = copy.deepcopy(v)
        if new_guids:
            node.set("guid", str(uuid.uuid4()))
        folder.append(node)
        existing.add(name)
        added.append(name)

    reorder_views(folder)
    refresh_folder_counts(vp)
    _write_tree(tree, base)
    return {
        "file": str(base), "folder": folder.get("name"), "added": added,
        "added_count": len(added), "new_guids": new_guids, "backup": bak,
    }


def move_views(
    xml: Path, from_path: str, to_path: str, names: list[str], *,
    backup: bool = True, dry_run: bool = False,
) -> dict:
    """Перенести <view> по точному имени между папками одного файла."""
    xml = Path(xml)
    name_set = {n.strip() for n in names if n.strip()}
    if not name_set:
        raise ViewpointError("Пустой список имён")

    bak = _backup(xml) if (backup and not dry_run) else None
    _register_ns()
    tree = load_tree(xml)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("Нет <viewpoints>")
    src = _resolve_folder(vp, from_path)
    dst = _resolve_folder(vp, to_path)

    existing_dst = {c.get("name") for c in direct_views(dst)}
    moved: list[str] = []
    missing: list[str] = []
    for nm in sorted(name_set, key=_name_sort_key):
        node = next((c for c in direct_views(src) if (c.get("name") or "") == nm), None)
        if node is None:
            missing.append(nm)
            continue
        if nm in existing_dst:
            raise ViewpointError(f"Целевая папка уже содержит view name={nm!r}")
        src.remove(node)
        dst.append(node)
        existing_dst.add(nm)
        moved.append(nm)

    if dry_run:
        return {"file": str(xml), "dry_run": True, "would_move": moved,
                "moved_count": len(moved), "missing": missing, "backup": None}

    reorder_views(dst)
    refresh_folder_counts(vp)
    _write_tree(tree, xml)
    return {"file": str(xml), "dry_run": False, "moved": moved,
            "moved_count": len(moved), "missing": missing,
            "from": from_path, "to": to_path, "backup": bak}


def audit(xml: Path) -> dict:
    """Структура папок, дубли guid, конфликты имя/папка, общее число view."""
    tree = load_tree(xml)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("Нет <viewpoints>")

    folders = list_folders(xml)["folders"]

    by_guid: dict[str, list] = defaultdict(list)
    by_name_folder: dict[tuple, list] = defaultdict(list)

    def collect(folder: ET.Element, folder_path: str) -> None:
        for v in direct_views(folder):
            g = (v.get("guid") or "").strip()
            n = v.get("name") or ""
            by_guid[g].append({"folder": folder_path, "name": n})
            by_name_folder[(folder_path, n)].append(g)
        for el in folder:
            if el.tag == "viewfolder":
                name = el.get("name") or ""
                sub = f"{folder_path}/{name}" if folder_path else name
                collect(el, sub)

    collect(vp, "")

    dup_guids = [
        {"guid": g, "locations": locs}
        for g, locs in sorted(by_guid.items()) if g and len(locs) > 1
    ]
    name_conflicts = [
        {"folder": fp, "name": nm, "guids": guids}
        for (fp, nm), guids in sorted(by_name_folder.items())
        if len(set(guids)) > 1
    ]
    return {
        "file": str(xml), "folders": folders,
        "duplicate_guids": dup_guids, "name_conflicts": name_conflicts,
        "total_views": len(iter_views(vp)),
    }


def reconcile_by_name(root: Path, master: Path) -> dict:
    """Сверка «числовых» имён точек: что есть в выгрузках, но нет в мастере, и наоборот."""
    root, master = Path(root), Path(master)
    if not master.is_file():
        raise ViewpointError(f"Нет мастера: {master}")

    def numeric_names(path: Path) -> tuple[list[str], str | None]:
        try:
            tree = ET.parse(path)
        except ET.ParseError as e:
            return [], f"ParseError: {e}"
        r = tree.getroot()
        if not is_nw_exchange(r):
            return [], "not nw-exchange"
        vp = r.find("viewpoints")
        if vp is None:
            return [], "no viewpoints"
        return [
            (v.get("name") or "").strip()
            for v in iter_views(vp)
            if is_numeric_viewpoint_name(v.get("name") or "")
        ], None

    master_list, err = numeric_names(master)
    if err:
        raise ViewpointError(f"Мастер: {err}")
    master_set = set(master_list)
    master_counts = Counter(master_list)

    export_union: set[str] = set()
    export_by_file: dict[str, set[str]] = {}
    skipped: list[dict] = []
    for f in sorted(root.rglob("*.xml")):
        if f.resolve() == master.resolve():
            continue
        names, e = numeric_names(f)
        if e:
            skipped.append({"file": str(f.relative_to(root)), "reason": e})
            continue
        if not names:
            continue
        s = set(names)
        export_by_file[str(f.relative_to(root))] = s
        export_union |= s

    missing_in_master = sorted(export_union - master_set, key=_name_sort_key)
    only_in_master = sorted(master_set - export_union, key=_name_sort_key)
    dup_in_master = sorted(
        [n for n, c in master_counts.items() if c > 1], key=_name_sort_key
    )
    per_file_missing = {
        rel: sorted(s - master_set, key=_name_sort_key)
        for rel, s in sorted(export_by_file.items())
        if s - master_set
    }
    return {
        "master": str(master), "root": str(root),
        "master_unique_names": len(master_set),
        "master_total_views": len(master_list),
        "master_duplicate_names": dup_in_master,
        "export_unique_names": len(export_union),
        "export_files_with_views": len(export_by_file),
        "missing_in_master": missing_in_master,
        "only_in_master": only_in_master,
        "per_file_missing": per_file_missing,
        "skipped": skipped,
    }


def sync_lists(
    resolved_ids: list[str], open_ids: list[str], root: Path, master: Path, *,
    open_only: bool = False,
) -> dict:
    """
    Синхронизация двух списков ID с каталогом выгрузок:
    импорт недостающих имён + перенос точек в мастере между ЛКП-Решено / ЛКП по принадлежности.
    ЛКП-ВН.ОСН не трогаем. Перед записью — .bak мастера.
    """
    root, master = Path(root), Path(master)
    resolved_set = {str(x).strip() for x in resolved_ids if str(x).strip()}
    open_set = {str(x).strip() for x in open_ids if str(x).strip()}
    if not open_only:
        both = resolved_set & open_set
        if both:
            raise ViewpointError(f"Пересечение списков resolved/open: {sorted(both)}")

    def match_open(name: str) -> str | None:
        return next((oid for oid in open_set if belongs_to_id(name, oid)), None)

    def match_any(name: str) -> tuple[str | None, str | None]:
        for rid in resolved_set:
            if belongs_to_id(name, rid):
                return "resolved", rid
        for oid in open_set:
            if belongs_to_id(name, oid):
                return "open", oid
        return None, None

    # --- скан выгрузок ---
    found_resolved: set[str] = set()
    found_open: set[str] = set()
    to_import: dict[str, tuple[str, ET.Element]] = {}
    to_import_open: dict[str, ET.Element] = {}
    for p in sorted(root.rglob("*.xml")):
        if p.name == master.name:
            continue
        try:
            tree = ET.parse(p)
        except ET.ParseError:
            continue
        r = tree.getroot()
        if not is_nw_exchange(r):
            continue
        vp = r.find("viewpoints")
        if vp is None:
            continue
        for v in iter_views(vp):
            nm = (v.get("name") or "").strip()
            if open_only:
                oid = match_open(nm)
                if oid is None:
                    continue
                found_open.add(oid)
                to_import_open.setdefault(nm, copy.deepcopy(v))
                continue
            br, mid = match_any(nm)
            if br is None:
                continue
            (found_resolved if br == "resolved" else found_open).add(mid)  # type: ignore[arg-type]
            to_import.setdefault(nm, (br, copy.deepcopy(v)))

    missing_resolved = [] if open_only else sorted(resolved_set - found_resolved, key=int)
    missing_open = sorted(open_set - found_open, key=int)

    # --- правка мастера ---
    if not master.is_file():
        raise ViewpointError(f"Нет мастера: {master}")
    bak = _backup(master)
    _register_ns()
    mtree = load_tree(master)
    mvp = find_viewpoints(mtree.getroot())
    if mvp is None:
        raise ViewpointError("Мастер: нет <viewpoints>")

    folder_res = _find_folder_by_prefix(mvp, "ЛКП-Решено")
    folder_exc = _find_folder_by_prefix(mvp, "ЛКП-ВН.ОСН")
    folder_open = _find_folder_by_prefix(mvp, "ЛКП (")
    if folder_open is None or (not open_only and folder_res is None):
        raise ViewpointError("В мастере нет папки 'ЛКП (…)' или 'ЛКП-Решено'")

    def names_in(f: ET.Element) -> set[str]:
        return {c.get("name") for c in direct_views(f)}

    imported = 0
    if open_only:
        for ch in list(mvp):
            if ch.tag != "viewfolder" or ch is folder_exc or ch is folder_open:
                continue
            for V in list(direct_views(ch)):
                nm = (V.get("name") or "").strip()
                if match_open(nm) is None:
                    continue
                ch.remove(V)
                folder_open.append(V)
        nopen = names_in(folder_open)
        for nm, node in sorted(to_import_open.items()):
            if nm in nopen:
                continue
            folder_open.append(node)
            nopen.add(nm)
            imported += 1
        reorder_views(folder_open)
    else:
        for ch in list(mvp):
            if ch.tag != "viewfolder" or ch is folder_exc:
                continue
            for V in list(direct_views(ch)):
                nm = (V.get("name") or "").strip()
                br, _ = match_any(nm)
                if br is None:
                    continue
                target = folder_res if br == "resolved" else folder_open
                if ch is target:
                    continue
                ch.remove(V)
                target.append(V)
        nr = names_in(folder_res)  # type: ignore[arg-type]
        nopen = names_in(folder_open)
        for nm, (br, node) in sorted(to_import.items()):
            target = folder_res if br == "resolved" else folder_open
            here = nr if target is folder_res else nopen
            if nm in here:
                continue
            target.append(node)  # type: ignore[union-attr]
            here.add(nm)
            imported += 1
        reorder_views(folder_res)  # type: ignore[arg-type]
        reorder_views(folder_open)

    refresh_folder_counts(mvp)
    _write_tree(mtree, master)
    return {
        "master": str(master), "mode": "open-only" if open_only else "both",
        "imported": imported, "backup": bak,
        "folder_open": folder_open.get("name"),
        "folder_resolved": folder_res.get("name") if folder_res is not None else None,
        "missing_in_exports_resolved": missing_resolved,
        "missing_in_exports_open": missing_open,
    }


def add_to_master(
    src: Path, *, today: str, master: Path | None = None,
    folder_prefix: str = "ЛКП (", new_guids: bool = True, dated_copy: bool = True,
) -> dict:
    """
    Дефолтный сценарий: добавить точки из src в мастер по правилам скилла.
      - dated_copy: создать копию 'Общие точки {today}.xml' рядом, править её (мастер не трогать);
      - folder_prefix: целевая папка по префиксу имени (по умолчанию ЛКП (…) — нерешённые);
      - конфликты имён: молча пропустить, собрать в отчёт (не ошибка);
      - пересчитать (N).
    `today` — строка даты DD-MM-YYYY (передаёт клиент; зашивать дату нельзя).
    """
    if master is None:
        raise ViewpointError("Не задан master (путь к мастер-файлу).")
    master, src = Path(master), Path(src)
    if not master.is_file():
        raise ViewpointError(f"Нет мастера: {master}")

    if dated_copy:
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", today or ""):
            raise ViewpointError(f"today должен быть в формате DD-MM-YYYY, получено: {today!r}")
        target = master.parent / f"Общие точки {today}.xml"
        shutil.copy2(master, target)
    else:
        target = master

    _register_ns()
    tree = load_tree(target)
    vp = find_viewpoints(tree.getroot())
    if vp is None:
        raise ViewpointError("Мастер: нет <viewpoints>")

    folder = _find_folder_by_prefix(vp, folder_prefix, exclude_prefixes=("ЛКП-",) if folder_prefix == "ЛКП (" else ())
    if folder is None:
        names = [c.get("name") for c in vp if c.tag == "viewfolder"]
        raise ViewpointError(f"Нет папки с префиксом {folder_prefix!r}. Есть: {names}")

    stree = load_tree(src)
    svp = find_viewpoints(stree.getroot())
    if svp is None:
        raise ViewpointError("src: нет <viewpoints>")
    src_views = iter_views(svp)
    if not src_views:
        raise ViewpointError("src: нет элементов <view>")

    # имена, уже присутствующие в ЛЮБОЙ папке мастера
    all_names: dict[str, str] = {}
    def index_all(folder_el: ET.Element, path: str) -> None:
        for v in direct_views(folder_el):
            all_names.setdefault(v.get("name") or "", path)
        for el in folder_el:
            if el.tag == "viewfolder":
                nm = el.get("name") or ""
                index_all(el, f"{path}/{nm}" if path else nm)
    index_all(vp, "")

    added: list[str] = []
    skipped: list[dict] = []
    existing_target = {c.get("name") for c in direct_views(folder)}
    for v in src_views:
        name = v.get("name")
        if name in all_names:
            skipped.append({"name": name, "already_in": all_names[name]})
            continue
        node = copy.deepcopy(v)
        if new_guids:
            node.set("guid", str(uuid.uuid4()))
        folder.append(node)
        existing_target.add(name)
        all_names[name] = folder.get("name") or ""
        added.append(name)

    reorder_views(folder)
    refresh_folder_counts(vp)
    _write_tree(tree, target)
    return {
        "written_file": str(target),
        "dated_copy": dated_copy,
        "master": str(master),
        "folder": folder.get("name"),
        "added": added,
        "added_count": len(added),
        "skipped_existing": skipped,
        "new_guids": new_guids,
    }

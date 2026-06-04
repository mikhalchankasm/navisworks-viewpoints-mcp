import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from navisworks_viewpoints_mcp import core


def _valid(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def _folder_count(path: Path, name_prefix: str) -> int:
    root = _valid(path)
    vp = root.find("viewpoints")
    f = next(c for c in vp if c.tag == "viewfolder" and (c.get("name") or "").startswith(name_prefix))
    return len([v for v in f if v.tag == "view"])


def _folder_name(path: Path, prefix: str) -> str:
    root = _valid(path)
    vp = root.find("viewpoints")
    return next(
        c.get("name") for c in vp
        if c.tag == "viewfolder" and (c.get("name") or "").startswith(prefix)
    )


# --- helpers -------------------------------------------------------------- #
def test_belongs_to_id():
    assert core.belongs_to_id("1552", "1552")
    assert core.belongs_to_id("1552.1", "1552")
    assert core.belongs_to_id("785_2", "785")
    assert not core.belongs_to_id("15520", "1552")
    assert not core.belongs_to_id("Базовый вид", "1")


def test_sort_key_numeric_order():
    names = ["1552.1", "1552", "397", "1552_2"]
    elems = [ET.Element("view", {"name": n}) for n in names]
    elems.sort(key=core.sort_key_view)
    assert [e.get("name") for e in elems] == ["397", "1552", "1552.1", "1552_2"]


# --- sort ----------------------------------------------------------------- #
def test_sort_file_all_folders(tmp_path: Path):
    src = tmp_path / "unsorted.xml"
    src.write_text(
        "<?xml version='1.0' encoding='utf-8'?>"
        '<exchange xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="nw-exchange-12.0.xsd">'
        "<viewpoints><viewfolder name='Папка (0)'>"
        "<view name='1552_2' guid='a'/><view name='397' guid='b'/>"
        "<view name='1552' guid='c'/><view name='1552.1' guid='d'/>"
        "</viewfolder></viewpoints></exchange>",
        encoding="utf-8",
    )
    res = core.sort_file(src)
    root = ET.parse(src).getroot()
    folder = root.find("viewpoints").find("viewfolder")
    names = [v.get("name") for v in folder if v.tag == "view"]
    assert names == ["397", "1552", "1552.1", "1552_2"]
    assert folder.get("name") == "Папка (4)"  # (N) пересчитан
    assert Path(res["backup"]).is_file()


def test_sort_single_folder(master: Path):
    res = core.sort_file(master, folder="ЛКП (2)")
    assert res["sorted"] == [{"folder": "ЛКП (2)", "views": 2}]


# --- dedupe / rename / split --------------------------------------------- #
def _make(tmp_path: Path, body: str, name: str = "f.xml") -> Path:
    p = tmp_path / name
    p.write_text(
        "<?xml version='1.0' encoding='utf-8'?>"
        '<exchange xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="nw-exchange-12.0.xsd">'
        f"<viewpoints>{body}</viewpoints></exchange>",
        encoding="utf-8",
    )
    return p


def test_dedupe_by_name_within_folder(tmp_path: Path):
    src = _make(
        tmp_path,
        "<viewfolder name='A (0)'><view name='1' guid='a'/><view name='1' guid='b'/>"
        "<view name='2' guid='c'/></viewfolder>",
    )
    res = core.dedupe(src, by="name")
    assert res["removed_count"] == 1
    folder = ET.parse(src).getroot().find("viewpoints").find("viewfolder")
    assert [v.get("name") for v in folder] == ["1", "2"]
    assert folder.get("name") == "A (2)"


def test_dedupe_by_guid_global(tmp_path: Path):
    src = _make(
        tmp_path,
        "<viewfolder name='A (0)'><view name='1' guid='dup'/></viewfolder>"
        "<viewfolder name='B (0)'><view name='2' guid='dup'/></viewfolder>",
    )
    res = core.dedupe(src, by="guid")
    assert res["removed_count"] == 1  # второй 'dup' удалён


def test_rename_folder_recounts(master: Path):
    res = core.rename_folder(master, "ЛКП (2)", "Открытые")
    assert res["new_name"] == "Открытые (2)"


def test_split_file_copy(master: Path, tmp_path: Path):
    out = tmp_path / "sub.xml"
    res = core.split_file(master, ["191", "397"], out, move=False)
    assert set(res["extracted"]) == {"191", "397"}
    assert out.is_file()
    new_views = {v.get("name") for v in ET.parse(out).getroot().iter("view")}
    assert new_views == {"191", "397"}
    # исходник не тронут (move=False) — в ЛКП всё ещё 2
    assert _folder_count(master, "ЛКП (") == 2


def test_split_file_move_removes_from_source(master: Path, tmp_path: Path):
    out = tmp_path / "sub.xml"
    res = core.split_file(master, ["397"], out, move=True)
    assert res["moved"] is True
    assert _folder_count(master, "ЛКП (") == 1  # 397 ушёл
    assert Path(res["source_backup"]).is_file()


def test_split_rejects_same_path(master: Path):
    with pytest.raises(core.ViewpointError):
        core.split_file(master, ["191"], master)


# --- list / audit --------------------------------------------------------- #
def test_list_folders(master: Path):
    res = core.list_folders(master)
    names = {f["name"] for f in res["folders"]}
    assert "ЛКП (2)" in names
    assert res["total_views"] == 4


def test_audit_detects_no_dups_on_clean(master: Path):
    res = core.audit(master)
    assert res["duplicate_guids"] == []
    assert res["name_conflicts"] == []
    assert res["total_views"] == 4


# --- merge ---------------------------------------------------------------- #
def test_merge_conflict_on_existing_name(master: Path, export: Path):
    # export.xml содержит view name=191, который уже есть в ЛКП (2)
    with pytest.raises(core.ViewpointError):
        core.merge_views(master, export, "ЛКП (2)")


def test_merge_clean(master: Path, tmp_path: Path):
    # выгрузка без конфликтов
    src = tmp_path / "clean.xml"
    src.write_text(
        "<?xml version='1.0' encoding='utf-8'?>"
        '<exchange xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="nw-exchange-12.0.xsd">'
        "<viewpoints><view name='800' guid='x'/></viewpoints></exchange>",
        encoding="utf-8",
    )
    res = core.merge_views(master, src, "ЛКП (2)", new_guids=True)
    assert res["added"] == ["800"]
    assert _folder_count(master, "ЛКП (") == 3
    assert _folder_name(master, "ЛКП (") == "ЛКП (3)"
    assert Path(res["backup"]).is_file()


# --- move ----------------------------------------------------------------- #
def test_move_view_between_folders(master: Path):
    res = core.move_views(master, "ЛКП (2)", "ЛКП-Решено (1)", ["397"])
    assert res["moved"] == ["397"]
    assert _folder_count(master, "ЛКП (") == 1
    assert _folder_count(master, "ЛКП-Решено") == 2
    assert _folder_name(master, "ЛКП-Решено") == "ЛКП-Решено (2)"


def test_move_dry_run_no_write(master: Path):
    before = master.read_text(encoding="utf-8")
    res = core.move_views(master, "ЛКП (2)", "ЛКП-Решено (1)", ["397"], dry_run=True)
    assert res["would_move"] == ["397"]
    assert master.read_text(encoding="utf-8") == before


def test_move_conflict(master: Path):
    # 191 есть в ЛКП; пытаемся внести дубль в ЛКП-Решено где его нет — ок,
    # а вот перенос несуществующего имени -> missing
    res = core.move_views(master, "ЛКП (2)", "ЛКП-Решено (1)", ["99999"])
    assert res["missing"] == ["99999"]
    assert res["moved"] == []


# --- reconcile ------------------------------------------------------------ #
def test_reconcile_by_name(exports_dir: Path):
    master = exports_dir / "Общие точки 01-01-2026.xml"
    res = core.reconcile_by_name(exports_dir, master)
    # 1552 и 1552.1 есть в выгрузке, но нет в мастере
    assert "1552" in res["missing_in_master"]
    assert "1552.1" in res["missing_in_master"]
    # 397 есть в мастере; в выгрузке нет -> only_in_master
    assert "397" in res["only_in_master"]


# --- sync ----------------------------------------------------------------- #
def test_sync_open_only_imports(exports_dir: Path):
    master = exports_dir / "Общие точки 01-01-2026.xml"
    res = core.sync_lists(
        resolved_ids=[], open_ids=["1552"], root=exports_dir, master=master,
        open_only=True,
    )
    assert res["imported"] >= 1  # 1552 и 1552.1 импортированы в ЛКП
    assert _folder_count(master, "ЛКП (") >= 4
    # валидный XML
    _valid(master)


def test_sync_both_moves_between_folders(exports_dir: Path):
    master = exports_dir / "Общие точки 01-01-2026.xml"
    # объявим 191 как решённый -> должен переехать из ЛКП в ЛКП-Решено
    res = core.sync_lists(
        resolved_ids=["191"], open_ids=["1552"], root=exports_dir, master=master,
    )
    assert res["mode"] == "both"
    # 191 теперь в ЛКП-Решено
    root = _valid(master)
    vp = root.find("viewpoints")
    resolved = next(c for c in vp if (c.get("name") or "").startswith("ЛКП-Решено"))
    assert "191" in {v.get("name") for v in resolved if v.tag == "view"}


def test_sync_rejects_overlapping_lists(exports_dir: Path):
    master = exports_dir / "Общие точки 01-01-2026.xml"
    with pytest.raises(core.ViewpointError):
        core.sync_lists(["1"], ["1"], exports_dir, master)


# --- add_to_master -------------------------------------------------------- #
def test_add_to_master_dated_copy_and_skip(master: Path, export: Path):
    res = core.add_to_master(export, today="04-06-2026", master=master)
    # написан новый датированный файл, мастер не тронут
    assert res["written_file"].endswith("Общие точки 04-06-2026.xml")
    assert Path(res["written_file"]).is_file()
    # 191 уже есть -> в skipped; 1552/1552.1 добавлены в ЛКП
    skipped_names = {s["name"] for s in res["skipped_existing"]}
    assert "191" in skipped_names
    assert set(res["added"]) == {"1552", "1552.1"}
    assert res["folder"].startswith("ЛКП (")
    # исходный мастер не изменился (всё ещё 2 в ЛКП)
    assert _folder_count(master, "ЛКП (") == 2
    # новый файл валиден и содержит 4 в ЛКП
    written = Path(res["written_file"])
    assert _folder_count(written, "ЛКП (") == 4


def test_add_to_master_bad_date(master: Path, export: Path):
    with pytest.raises(core.ViewpointError):
        core.add_to_master(export, today="2026-06-04", master=master)

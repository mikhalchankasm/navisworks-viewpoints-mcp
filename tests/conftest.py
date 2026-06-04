import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def master(tmp_path: Path) -> Path:
    dst = tmp_path / "Общие точки 01-01-2026.xml"
    shutil.copy2(FIXTURES / "master.xml", dst)
    return dst


@pytest.fixture
def export(tmp_path: Path) -> Path:
    dst = tmp_path / "export.xml"
    shutil.copy2(FIXTURES / "export.xml", dst)
    return dst


@pytest.fixture
def exports_dir(tmp_path: Path) -> Path:
    """Каталог с мастером и одной выгрузкой (для reconcile/sync)."""
    root = tmp_path / "vp"
    root.mkdir()
    shutil.copy2(FIXTURES / "master.xml", root / "Общие точки 01-01-2026.xml")
    shutil.copy2(FIXTURES / "export.xml", root / "export.xml")
    return root

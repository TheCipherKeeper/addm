import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("skeleton_sync", Path(__file__).with_name("sync.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = MODULE.SOURCE
TARGETS = MODULE.TARGETS
sync = MODULE.sync


def test_sync_updates_and_checks_all_derivatives(tmp_path: Path) -> None:
    source = tmp_path / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("name: product-pipeline\n", encoding="utf-8")

    assert sync(tmp_path, check=True) == [target.as_posix() for target in TARGETS]
    assert sync(tmp_path) == [target.as_posix() for target in TARGETS]
    assert sync(tmp_path, check=True) == []
    assert all((tmp_path / target).read_bytes() == source.read_bytes() for target in TARGETS)


def test_sync_reports_one_drifted_file(tmp_path: Path) -> None:
    source = tmp_path / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("canonical\n", encoding="utf-8")
    sync(tmp_path)
    drifted = tmp_path / TARGETS[0]
    drifted.write_text("drift\n", encoding="utf-8")

    assert sync(tmp_path, check=True) == [TARGETS[0].as_posix()]

import importlib.util
import json
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location("task_complete", Path(__file__).with_name("complete.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
complete = MODULE.complete
CompletionError = MODULE.CompletionError


BACKLOG = """# Задачи

### TASK-0042. [ ] ready — Экспорт

Целевые репозитории:
- reports
Риск: low
Автономность: auto-test-deploy
Триггеры:
- нет
Цель:
Экспортировать отчёт.
Готово, когда:
- отчёт доступен
Не входит:
- импорт
Откат: вернуть артефакт.
"""


def evidence() -> dict[str, object]:
    return {
        "schema_version": 2,
        "task_id": "TASK-0042",
        "run_id": "run-42",
        "methodology_ref": "v2.0.0",
        "deliveries": [{
            "repository": "reports",
            "pr": "https://github.com/acme/reports/pull/42",
            "commit": "abcdef1",
            "attestation": "https://github.com/acme/reports/actions/runs/42",
            "checks": [{"name": "gate", "status": "passed", "source": "https://github.com/acme/reports/actions/runs/42"}],
            "reviews": [{"name": "review", "status": "passed", "source": "https://github.com/acme/reports/pull/42#pullrequestreview-1", "reviewer": "bot"}],
            "artifact": "sha256:" + "a" * 64,
            "deployment": {"environment": "test", "probes": [
                {"name": "smoke", "status": "passed", "source": "https://github.com/acme/reports/actions/runs/42"}
            ]},
        }],
        "attempts": 1,
        "status": "passed",
        "created_at": "2026-07-14T00:00:00Z",
        "retained_until": "2027-07-14T00:00:00Z",
    }


def test_complete_updates_all_hub_records(tmp_path: Path) -> None:
    (tmp_path / ".methodology.yml").write_text(
        "schema_version: 1\nrepository_type: hub\nmethodology_ref: v2.0.0\nrepository_id: platform\n",
        encoding="utf-8",
    )
    (tmp_path / "BACKLOG.md").write_text(BACKLOG, encoding="utf-8")
    source = tmp_path / "source.json"
    source.write_text(json.dumps(evidence()), encoding="utf-8")

    complete(tmp_path, "TASK-0042", source)

    assert "### TASK-0042. [x] — Экспорт" in (tmp_path / "BACKLOG.md").read_text(encoding="utf-8")
    task = json.loads((tmp_path / ".tasks/TASK-0042.json").read_text(encoding="utf-8"))
    assert task["status"] == "done"
    assert json.loads((tmp_path / ".evidence/TASK-0042.json").read_text(encoding="utf-8")) == evidence()


def test_complete_rejects_failed_probe_before_writing(tmp_path: Path) -> None:
    (tmp_path / ".methodology.yml").write_text(
        "schema_version: 1\nrepository_type: hub\nmethodology_ref: v2.0.0\nrepository_id: platform\n",
        encoding="utf-8",
    )
    (tmp_path / "BACKLOG.md").write_text(BACKLOG, encoding="utf-8")
    invalid = evidence()
    invalid["deliveries"][0]["deployment"]["probes"][0]["status"] = "failed"
    source = tmp_path / "source.json"
    source.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(CompletionError, match="семантические ошибки"):
        complete(tmp_path, "TASK-0042", source)

    assert "[ ] ready" in (tmp_path / "BACKLOG.md").read_text(encoding="utf-8")
    assert not (tmp_path / ".evidence/TASK-0042.json").exists()

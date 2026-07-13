import importlib.util
import json
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("migration_v1_to_v2", Path(__file__).with_name("v1_to_v2.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
migrate = MODULE.migrate


def test_migrate_hub_task_and_evidence(tmp_path: Path) -> None:
    (tmp_path / ".methodology.yml").write_text(
        "schema_version: 1\nrepository_type: hub\nmethodology_ref: v1.2.3\n", encoding="utf-8"
    )
    (tmp_path / "BACKLOG.md").write_text(
        "### TASK-0001. [x] — Готово\n\nЦелевой репозиторий: reports\nРиск: low\n"
        "Автономность: auto-test-deploy\nТриггеры:\n- нет\nЦель:\nx\nГотово, когда:\n- x\n"
        "Не входит:\n- нет\nОткат: назад.\n",
        encoding="utf-8",
    )
    second = (
        "\n### TASK-0002. [ ] ready — Ещё отчёт\n\nЦелевой репозиторий: reports\nРиск: low\n"
        "Автономность: auto-test-deploy\nТриггеры:\n- нет\nЦель:\ny\nГотово, когда:\n- y\n"
        "Не входит:\n- нет\nОткат: назад.\n"
    )
    backlog_path = tmp_path / "BACKLOG.md"
    backlog_path.write_text(backlog_path.read_text(encoding="utf-8") + second, encoding="utf-8")
    tasks = tmp_path / ".tasks"
    tasks.mkdir()
    old_task = {
        "schema_version": 1, "id": "TASK-0001", "status": "done", "target": "reports",
        "risk": "low", "autonomy": "auto-test-deploy", "goal": "x",
        "acceptance_criteria": ["x"], "out_of_scope": ["нет"], "triggers": [], "rollback": "назад."
    }
    (tasks / "TASK-0001.json").write_text(json.dumps(old_task), encoding="utf-8")
    second_task = {**old_task, "id": "TASK-0002", "status": "ready", "goal": "y", "acceptance_criteria": ["y"]}
    (tasks / "TASK-0002.json").write_text(json.dumps(second_task), encoding="utf-8")
    evidence_dir = tmp_path / ".evidence"
    evidence_dir.mkdir()
    old_evidence = {
        "schema_version": 1, "task_id": "TASK-0001", "run_id": "run-1",
        "pr": "https://github.com/acme/reports/pull/1", "commit": "abcdef1",
        "methodology_ref": "v1.2.3",
        "checks": [{"name": "gate", "status": "passed", "source": "run:1"}],
        "reviews": [{"name": "review", "status": "passed", "source": "review:1", "reviewer": "bot"}],
        "attempts": 1, "artifact": "sha256:" + "a" * 64,
        "deployment": {"environment": "test", "probes": [{"name": "smoke", "status": "passed", "source": "run:1"}]},
        "status": "passed", "created_at": "2026-01-01T00:00:00Z", "retained_until": "2027-01-01T00:00:00Z"
    }
    evidence_path = evidence_dir / "TASK-0001.json"
    evidence_path.write_text(json.dumps(old_evidence), encoding="utf-8")
    url = "https://github.com/acme/reports/actions/runs/1"

    migrate(tmp_path, "platform", {"TASK-0001": url})

    task = json.loads((tasks / "TASK-0001.json").read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert task["schema_version"] == 2 and task["targets"] == ["reports"]
    assert json.loads((tasks / "TASK-0002.json").read_text(encoding="utf-8"))["targets"] == ["reports"]
    assert evidence["schema_version"] == 2 and evidence["deliveries"][0]["attestation"] == url
    assert "repository_id: platform" in (tmp_path / ".methodology.yml").read_text(encoding="utf-8")

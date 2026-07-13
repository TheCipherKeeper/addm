"""Согласованно завершить хабовую задачу по агрегированному evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from sync import BacklogError, sync, task_records


POLICY_ROOT = Path(__file__).resolve().parents[2]


class CompletionError(RuntimeError):
    """Задачу нельзя безопасно перевести в завершённое состояние."""


def complete(root: Path, task_id: str, evidence_source: Path) -> None:
    """Проверить evidence и одним изменением обновить evidence, backlog и .tasks."""
    backlog_path = root / "BACKLOG.md"
    backlog = backlog_path.read_text(encoding="utf-8")
    tasks = task_records(backlog)
    task = tasks.get(task_id)
    if task is None:
        raise CompletionError(f"задача не найдена: {task_id}")
    if task["status"] == "done":
        raise CompletionError(f"задача уже завершена: {task_id}")

    try:
        evidence = json.loads(evidence_source.read_text(encoding="utf-8"))
        schema = json.loads((POLICY_ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompletionError(f"не удалось прочитать evidence: {error}") from error
    sys.path.insert(0, str(POLICY_ROOT / "tools" / "verify"))
    from verify import methodology_config, validate_json  # noqa: PLC0415

    errors = validate_json(evidence, schema)
    if errors:
        raise CompletionError("evidence не соответствует схеме: " + "; ".join(errors))
    config, config_errors = methodology_config(root)
    if config_errors or evidence["methodology_ref"] != config.get("methodology_ref"):
        raise CompletionError("methodology_ref evidence не совпадает с .methodology.yml хаба")
    if evidence["task_id"] != task_id or evidence["status"] != "passed":
        raise CompletionError("evidence должен относиться к задаче и иметь статус passed")
    repositories = {delivery["repository"] for delivery in evidence["deliveries"]}
    if len(repositories) != len(evidence["deliveries"]):
        raise CompletionError("каждый целевой репозиторий должен иметь ровно одну поставку")
    if repositories != set(task["targets"]):
        raise CompletionError("поставки evidence не совпадают с целевыми репозиториями задачи")
    from evidence import record_errors  # noqa: PLC0415

    semantic_errors = record_errors(
        root,
        {task_id: task},
        {task_id: evidence},
        config.get("methodology_ref"),
        config.get("repository_type"),
        config.get("repository_id"),
    )
    if semantic_errors:
        raise CompletionError("семантические ошибки evidence: " + "; ".join(semantic_errors))

    heading = re.compile(
        rf"^### {re.escape(task_id)}\. \[ \] (?:ready|needs-input|blocked-external|automation-failed|retry-exhausted) — (.+)$",
        re.MULTILINE,
    )
    updated, count = heading.subn(rf"### {task_id}. [x] — \1", backlog, count=1)
    if count != 1:
        raise CompletionError("не найден открытый канонический заголовок задачи")
    updated = re.sub(
        rf"(^### {re.escape(task_id)}\. \[x\] — .+\r?\n\r?\n)Диагностика:[^\r\n]*\r?\n\r?\n?",
        r"\1",
        updated,
        count=1,
        flags=re.MULTILINE,
    )

    destination = root / ".evidence" / f"{task_id}.json"
    if destination.exists():
        raise CompletionError(f"evidence уже существует: {destination.relative_to(root)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        backlog_path.write_text(updated, encoding="utf-8")
        temporary.replace(destination)
        sync(root)
    except Exception:
        backlog_path.write_text(backlog, encoding="utf-8")
        destination.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
        sync(root)
        raise


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        complete(args.root.resolve(), args.task_id, args.evidence.resolve())
    except (OSError, BacklogError, CompletionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(f"Задача {args.task_id} завершена; BACKLOG, .tasks и .evidence согласованы")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

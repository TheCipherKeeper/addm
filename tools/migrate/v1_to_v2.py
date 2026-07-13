"""Преобразовать хабовые task/evidence schema version 1 в version 2."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


POLICY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(POLICY_ROOT / "tools" / "tasks"))
sys.path.insert(0, str(POLICY_ROOT / "tools" / "verify"))
from sync import sync  # noqa: E402
from verify import validate_json  # noqa: E402


class MigrationError(RuntimeError):
    """Миграция не может быть выполнена без потери проверяемых данных."""


def _sources(items: list[object], ci_url: str) -> None:
    for item in items:
        if isinstance(item, dict) and not str(item.get("source", "")).startswith("https://"):
            item["source"] = ci_url


def migrate(root: Path, repository_id: str, ci_urls: dict[str, str]) -> list[str]:
    """Проверить и применить миграцию; вернуть изменённые относительные пути."""
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", repository_id):
        raise MigrationError("repository_id должен быть устойчивым строчным идентификатором")
    backlog_path = root / "BACKLOG.md"
    config_path = root / ".methodology.yml"
    backlog = backlog_path.read_text(encoding="utf-8")
    config = config_path.read_text(encoding="utf-8")
    task_files = sorted((root / ".tasks").glob("TASK-*.json"))
    old_tasks = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in task_files}
    if not old_tasks or any(task.get("schema_version") != 1 or "target" not in task for task in old_tasks.values()):
        raise MigrationError(".tasks должны содержать только записи version 1 с полем target")

    updated_backlog = backlog
    for task_id, task in old_tasks.items():
        old = f"Целевой репозиторий: {task['target']}"
        new = f"Целевые репозитории:\n- {task['target']}"
        block_match = re.search(
            rf"(?ms)^### {re.escape(task_id)}\..*?(?=^### TASK-|\Z)",
            updated_backlog,
        )
        if block_match is None or block_match.group(0).count(old) != 1:
            raise MigrationError(f"{task_id}: не найдено единственное поле «Целевой репозиторий»")
        block = block_match.group(0).replace(old, new)
        updated_backlog = (
            updated_backlog[:block_match.start()] + block + updated_backlog[block_match.end():]
        )

    if re.search(r"(?m)^repository_id:", config):
        raise MigrationError("repository_id уже присутствует; репозиторий не похож на version 1")
    updated_config = config.rstrip() + f"\nrepository_id: {repository_id}\n"

    evidence_schema = json.loads((POLICY_ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8"))
    transformed: dict[Path, dict[str, object]] = {}
    for path in sorted((root / ".evidence").glob("TASK-*.json")):
        old = json.loads(path.read_text(encoding="utf-8"))
        task_id = str(old.get("task_id", ""))
        if old.get("schema_version") != 1 or task_id not in old_tasks:
            raise MigrationError(f"{path.name}: ожидается связанное evidence version 1")
        if not old.get("reviews"):
            raise MigrationError(f"{task_id}: нельзя мигрировать evidence без независимой проверки")
        ci_url = ci_urls.get(task_id)
        if not ci_url or not re.match(r"^https://[^/]+/.+", ci_url):
            raise MigrationError(f"{task_id}: требуется --ci-url {task_id}=https://...")
        checks = old.pop("checks")
        reviews = old.pop("reviews")
        deployment = old.pop("deployment")
        _sources(checks, ci_url)
        _sources(reviews, ci_url)
        _sources(deployment.get("probes", []), ci_url)
        delivery = {
            "repository": old_tasks[task_id]["target"],
            "pr": old.pop("pr"),
            "commit": old.pop("commit"),
            "attestation": ci_url,
            "checks": checks,
            "reviews": reviews,
            "artifact": old.pop("artifact"),
            "deployment": deployment,
        }
        old["schema_version"] = 2
        old["deliveries"] = [delivery]
        errors = validate_json(old, evidence_schema)
        if errors:
            raise MigrationError(f"{task_id}: преобразованное evidence невалидно: {'; '.join(errors)}")
        transformed[path] = old

    originals = {backlog_path: backlog, config_path: config}
    originals.update({path: path.read_text(encoding="utf-8") for path in transformed})
    try:
        backlog_path.write_text(updated_backlog, encoding="utf-8")
        config_path.write_text(updated_config, encoding="utf-8")
        for path, document in transformed.items():
            path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sync(root)
    except Exception:
        for path, content in originals.items():
            path.write_text(content, encoding="utf-8")
        raise
    return [
        ".methodology.yml",
        "BACKLOG.md",
        *[path.relative_to(root).as_posix() for path in task_files],
        *[path.relative_to(root).as_posix() for path in transformed],
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--ci-url", action="append", default=[], metavar="TASK-NNNN=URL")
    args = parser.parse_args()
    try:
        ci_urls = dict(item.split("=", 1) for item in args.ci_url)
        changed = migrate(args.root.resolve(), args.repository_id, ci_urls)
    except (OSError, ValueError, json.JSONDecodeError, MigrationError) as error:
        print(f"Ошибка миграции: {error}", file=sys.stderr)
        return 1
    print("Миграция выполнена: " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

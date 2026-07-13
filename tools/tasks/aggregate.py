"""Собрать агрегированное evidence из записей поставок продуктового CI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


POLICY_ROOT = Path(__file__).resolve().parents[2]


class AggregationError(RuntimeError):
    """Записи поставок нельзя однозначно объединить."""


def aggregate(
    task_id: str,
    methodology_ref: str,
    run_id: str,
    sources: list[Path],
    output: Path,
    attempts: int = 1,
) -> dict[str, object]:
    deliveries = [json.loads(path.read_text(encoding="utf-8")) for path in sources]
    repositories = {item.get("repository") for item in deliveries if isinstance(item, dict)}
    if not deliveries or len(repositories) != len(deliveries):
        raise AggregationError("требуется ровно одна запись для каждого репозитория")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    document = {
        "schema_version": 2,
        "task_id": task_id,
        "run_id": run_id,
        "methodology_ref": methodology_ref,
        "deliveries": deliveries,
        "attempts": attempts,
        "status": "passed",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "retained_until": (now + timedelta(days=365)).isoformat().replace("+00:00", "Z"),
    }
    sys.path.insert(0, str(POLICY_ROOT / "tools" / "verify"))
    from verify import validate_json  # noqa: PLC0415

    schema = json.loads((POLICY_ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8"))
    errors = validate_json(document, schema)
    if errors:
        raise AggregationError("невалидные записи поставок: " + "; ".join(errors))
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--methodology-ref", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--delivery", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=1)
    args = parser.parse_args()
    try:
        aggregate(
            args.task_id, args.methodology_ref, args.run_id,
            [path.resolve() for path in args.delivery], args.output.resolve(), args.attempts,
        )
    except (OSError, json.JSONDecodeError, AggregationError) as error:
        print(f"Ошибка агрегации: {error}", file=sys.stderr)
        return 1
    print(f"Evidence создан: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

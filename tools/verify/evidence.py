"""Смысловая проверка агрегированных свидетельств выполнения."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def _is_ancestor(root: Path, commit: object) -> bool:
    if not (root / ".git").exists() or not isinstance(commit, str):
        return False
    completed = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def record_errors(
    root: Path,
    tasks: dict[str, dict[str, object]],
    evidence: dict[str, dict[str, object]],
    pinned_ref: object,
    repository_type: object,
    repository_id: object,
) -> list[str]:
    """Проверить связь evidence с задачами, поставками и локальной историей."""
    errors: list[str] = []
    for task_id, record in evidence.items():
        if task_id not in tasks:
            errors.append(f"{task_id}: evidence не связан с машинной задачей")
        if record.get("methodology_ref") != pinned_ref and repository_type != "methodology":
            errors.append(f"{task_id}: methodology_ref не совпадает с .methodology.yml")
        deliveries = record.get("deliveries", [])
        task = tasks.get(task_id, {})
        expected = set(task.get("targets", []))
        actual = {delivery.get("repository") for delivery in deliveries if isinstance(delivery, dict)}
        if len(actual) != len(deliveries):
            errors.append(f"{task_id}: каждый целевой репозиторий должен иметь ровно одну поставку")
        if expected != actual:
            errors.append(
                f"{task_id}: поставки {sorted(actual)} не совпадают с целевыми репозиториями {sorted(expected)}"
            )
        results: list[object] = []
        probes: list[object] = []
        for delivery in deliveries:
            if not isinstance(delivery, dict):
                continue
            repository = delivery.get("repository")
            if repository == repository_id and not _is_ancestor(root, delivery.get("commit")):
                errors.append(
                    f"{task_id}: локальный commit поставки {repository} отсутствует в истории текущего HEAD"
                )
            results.extend(delivery.get("checks", []))
            results.extend(delivery.get("reviews", []))
            if not any(
                review.get("status") == "passed"
                for review in delivery.get("reviews", [])
                if isinstance(review, dict)
            ):
                errors.append(f"{task_id}: поставка {repository} не имеет успешной независимой проверки")
            deployment = delivery.get("deployment", {})
            if isinstance(deployment, dict):
                probes.extend(deployment.get("probes", []))
        try:
            created = datetime.fromisoformat(str(record.get("created_at", "")).replace("Z", "+00:00"))
            retained = datetime.fromisoformat(str(record.get("retained_until", "")).replace("Z", "+00:00"))
            if retained <= created:
                errors.append(f"{task_id}: retained_until должен быть позже created_at")
        except (ValueError, TypeError):
            pass
        if record.get("status") == "passed" and any(
            item.get("status") == "failed" for item in results + probes if isinstance(item, dict)
        ):
            errors.append(f"{task_id}: passed evidence содержит failed результат")
    for task_id, task in tasks.items():
        if task.get("status") == "done":
            if task_id not in evidence:
                errors.append(f"{task_id}: завершённая задача не имеет evidence")
            elif evidence[task_id].get("status") != "passed":
                errors.append(f"{task_id}: завершённая задача требует evidence со статусом passed")
    return errors

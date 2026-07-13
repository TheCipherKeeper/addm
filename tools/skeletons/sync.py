"""Синхронизировать общие производные файлы заготовок."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


POLICY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("skeletons/hub/.github/workflows/verify.yml")
TARGETS = tuple(
    Path(f"skeletons/{kind}/.github/workflows/verify.yml")
    for kind in ("service", "interface", "standalone")
)


class SkeletonSyncError(RuntimeError):
    """Общий файл заготовки невозможно синхронизировать."""


def sync(root: Path, check: bool = False) -> list[str]:
    """Вернуть отличающиеся производные файлы и при необходимости обновить их."""
    source = root / SOURCE
    if not source.is_file():
        raise SkeletonSyncError(f"канонический файл не найден: {SOURCE.as_posix()}")
    content = source.read_bytes()
    differences = [target.as_posix() for target in TARGETS if not (root / target).is_file() or (root / target).read_bytes() != content]
    if differences and not check:
        for target in TARGETS:
            destination = root / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(destination)
    return differences


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=POLICY_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        differences = sync(args.root.resolve(), args.check)
    except (OSError, SkeletonSyncError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    if differences:
        prefix = "Не синхронизированы" if args.check else "Обновлены"
        print(f"{prefix}: {', '.join(differences)}")
        return 1 if args.check else 0
    print("Общие файлы заготовок синхронизированы")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

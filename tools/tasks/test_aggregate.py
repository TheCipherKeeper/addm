import importlib.util
import json
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("task_aggregate", Path(__file__).with_name("aggregate.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
aggregate = MODULE.aggregate


def test_aggregate_builds_schema_v2_evidence(tmp_path: Path) -> None:
    delivery = {
        "repository": "reports",
        "pr": "https://github.com/acme/reports/pull/1",
        "commit": "abcdef1",
        "attestation": "https://github.com/acme/reports/actions/runs/1",
        "checks": [{"name": "gate", "status": "passed", "source": "https://github.com/acme/reports/actions/runs/1"}],
        "reviews": [{"name": "review", "status": "passed", "source": "https://github.com/acme/reports/pull/1", "reviewer": "bot"}],
        "artifact": "sha256:" + "a" * 64,
        "deployment": {"environment": "test", "probes": [
            {"name": "smoke", "status": "passed", "source": "https://github.com/acme/reports/actions/runs/1"}
        ]},
    }
    source = tmp_path / "delivery.json"
    source.write_text(json.dumps(delivery), encoding="utf-8")
    output = tmp_path / "evidence.json"

    document = aggregate("TASK-0001", "v2.0.0", "finish-1", [source], output)

    assert document["schema_version"] == 2
    assert document["deliveries"] == [delivery]
    assert json.loads(output.read_text(encoding="utf-8")) == document

import json
import secrets
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from datalens.data import load_csv, read_dataset
from datalens.storage import Store, scope_id


def test_memory_survives_a_new_process(context):
    _, store, scope, _ = context
    store.remember(scope, "task-1", "What is revenue?", "530", "completed", 0.001)
    code = "from pathlib import Path; from datalens.storage import Store; import sys,json; print(json.dumps(Store(Path(sys.argv[1])).recall(sys.argv[2])))"
    result = subprocess.run([sys.executable, "-c", code, str(store.root), scope], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)[0]["answer"] == "530"


def test_workspace_isolation(context):
    _, store, scope, ident = context
    other = scope_id(secrets.token_hex(32))
    store.remember(scope, "task", "secret question", "answer", "completed", 0)
    assert store.recall(other) == []
    with pytest.raises(ValueError):
        read_dataset(store.workspace(other), ident)


def test_concurrent_daily_budget_is_atomic(tmp_path):
    store = Store(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: store.reserve(0.3, 1.0), range(8)))
    assert sum(x is not None for x in results) == 3


@pytest.mark.parametrize("raw", [b"", b"a,a\n1,2", b"a\n", b"\x00abc", b"a,b\n1,2,3", b"\xff\xff"])
def test_bad_uploads_rejected(raw):
    with pytest.raises(ValueError):
        load_csv(raw)

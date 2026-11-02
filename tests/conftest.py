import secrets
from pathlib import Path

import pytest

from datalens.config import Settings
from datalens.data import upload
from datalens.storage import Store, scope_id


@pytest.fixture
def context(tmp_path):
    store = Store(tmp_path)
    scope = scope_id(secrets.token_hex(32))
    ident = upload(store.workspace(scope), Path("sample_data/sales.csv").read_bytes())
    return Settings(data_dir=tmp_path), store, scope, ident

import csv
import hashlib
import io
import json
import re
from pathlib import Path

import pandas as pd

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50000


def load_csv(raw: bytes) -> pd.DataFrame:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Upload a non-empty CSV of at most 5 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError("Save the CSV with UTF-8 encoding") from e
    if "\x00" in text:
        raise ValueError("Binary files are not supported")
    try:
        header = next(csv.reader(io.StringIO(text)))
        if not header or len(header) > 80 or len(set(header)) != len(header):
            raise ValueError("CSV needs 1–80 unique column names")
        if any(not h.strip() or len(h) > 100 for h in header):
            raise ValueError("Column names must be non-empty and at most 100 characters")
        frame = pd.read_csv(io.StringIO(text), nrows=MAX_ROWS + 1)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as e:
        raise ValueError("Invalid CSV. Use a comma delimiter and a header row") from e
    if frame.empty or len(frame) > MAX_ROWS:
        raise ValueError("CSV must contain 1–50,000 data rows")
    if frame.index.tolist() != list(range(len(frame))):
        raise ValueError("CSV rows have more fields than the header")
    return frame


def upload(workspace: Path, raw: bytes) -> str:
    load_csv(raw)
    ident = hashlib.sha256(raw).hexdigest()[:32]
    folder = workspace / "datasets"
    folder.mkdir(exist_ok=True)
    (folder / f"{ident}.csv").write_bytes(raw)
    return ident


def read_dataset(workspace: Path, ident: str):
    if not re.fullmatch(r"[a-f0-9]{32}", ident):
        raise ValueError("Invalid dataset ID; filesystem paths are not accepted")
    path = workspace / "datasets" / f"{ident}.csv"
    if path.is_symlink() or not path.is_file():
        raise ValueError("Dataset does not exist in this workspace")
    return load_csv(path.read_bytes())


def records(frame, limit=30):
    safe = frame.head(limit).copy()
    for name in safe.select_dtypes(include=["object", "string"]).columns:
        safe[name] = safe[name].map(lambda v: v[:300] if isinstance(v, str) else v)
    return json.loads(safe.to_json(orient="records", force_ascii=False))


def column(frame, name, numeric=False):
    if name not in frame.columns:
        raise ValueError(f"Unknown column {name!r}; available columns: {list(frame.columns)}")
    if numeric and not pd.api.types.is_numeric_dtype(frame[name]):
        raise ValueError(f"{name!r} is not numeric; clean the source CSV before computing")
    if numeric and frame[name].isin([float("inf"), float("-inf")]).any():
        raise ValueError(f"{name!r} contains infinite values; fix the source CSV")

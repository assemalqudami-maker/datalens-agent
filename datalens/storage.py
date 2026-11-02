import hashlib
import json
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path


def scope_id(token: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        raise ValueError("Workspace key must contain 64 hexadecimal characters")
    return hashlib.sha256(token.encode()).hexdigest()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Store:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "memory.sqlite3"
        with self.connect() as c:
            c.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS history (
              id INTEGER PRIMARY KEY, scope TEXT, task TEXT UNIQUE, question TEXT,
              answer TEXT, status TEXT, cost REAL, created TEXT);
            CREATE TABLE IF NOT EXISTS approvals (
              token TEXT PRIMARY KEY, scope TEXT, payload TEXT, expires REAL, used INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ledger (
              id TEXT PRIMARY KEY, day TEXT, amount REAL, state TEXT);
            """)

    def connect(self):
        c = sqlite3.connect(self.db, timeout=20)
        c.row_factory = sqlite3.Row
        return c

    def workspace(self, scope: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", scope):
            raise ValueError("Invalid workspace")
        p = self.root / "workspaces" / scope
        p.mkdir(parents=True, exist_ok=True)
        return p

    def remember(self, scope, task, question, answer, status, cost):
        with self.connect() as c:
            c.execute("INSERT OR REPLACE INTO history(scope,task,question,answer,status,cost,created) "
                      "VALUES(?,?,?,?,?,?,?)", (scope, task, question[:6000], answer[:12000], status,
                                                cost, datetime.now(timezone.utc).isoformat()))

    def recall(self, scope, limit=5):
        with self.connect() as c:
            rows = c.execute("SELECT task,question,answer,status,cost,created FROM history "
                             "WHERE scope=? ORDER BY id DESC LIMIT ?", (scope, limit)).fetchall()
        return [dict(r) for r in rows]

    def grant(self, scope, args):
        token = secrets.token_hex(32)
        with self.connect() as c:
            c.execute("INSERT INTO approvals(token,scope,payload,expires) VALUES(?,?,?,?)",
                      (digest(token), scope, digest(args), time.time() + 600))
        return token

    def consume(self, token, scope, args):
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            result = c.execute("UPDATE approvals SET used=1 WHERE token=? AND scope=? AND payload=? "
                               "AND used=0 AND expires>?",
                               (digest(token), scope, digest(args), time.time()))
            return result.rowcount == 1

    def reserve(self, amount, daily_limit):
        """Atomic, shared daily guard; unresolved calls remain reserved after a crash."""
        day = datetime.now(timezone.utc).date().isoformat()
        ident = secrets.token_hex(16)
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            total = c.execute("SELECT COALESCE(SUM(amount),0) FROM ledger WHERE day=?", (day,)).fetchone()[0]
            if total + amount > daily_limit:
                return None
            c.execute("INSERT INTO ledger VALUES(?,?,?,?)", (ident, day, amount, "reserved"))
        return ident

    def settle(self, ident, amount, state="measured"):
        with self.connect() as c:
            c.execute("UPDATE ledger SET amount=?, state=? WHERE id=?", (amount, state, ident))


class Trace:
    def __init__(self, path: Path, task: str, secret_values=()):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.task = task
        self.secret_values = [s for s in secret_values if s]

    def clean(self, value):
        text = json.dumps(value, ensure_ascii=False, default=str)
        for s in self.secret_values:
            text = text.replace(s, "[REDACTED]")
        text = re.sub(r"AIza[\w-]{25,}", "[REDACTED]", text)
        text = re.sub(r"sk-[\w-]{20,}", "[REDACTED]", text)
        return json.loads(text)

    def event(self, event, **payload):
        row = self.clean({"timestamp": datetime.now(timezone.utc).isoformat(), "task_id": self.task,
                          "event": event, **payload})
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        return row

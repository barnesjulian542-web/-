import json
import sqlite3
import uuid
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskBusyError(RuntimeError):
    pass


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "workbench.sqlite"
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL,
                    customer TEXT NOT NULL, text TEXT NOT NULL, role TEXT NOT NULL,
                    deployment TEXT NOT NULL, version TEXT NOT NULL, mode TEXT NOT NULL,
                    status TEXT NOT NULL, items TEXT NOT NULL DEFAULT '[]',
                    stats TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL, item_id TEXT NOT NULL,
                    title TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                    UNIQUE(task_id, item_id));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                    event TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def add_task(self, fingerprint, customer, text, role, deployment, version, mode):
        task_id = uuid.uuid4().hex[:12]
        with self.connect() as connection:
            connection.execute("INSERT OR IGNORE INTO tasks "
                               "(id,fingerprint,customer,text,role,deployment,version,mode,status,created_at) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?)", (task_id, fingerprint, customer, text,
                               role, deployment, version, mode, "running", now()))
            row = connection.execute("SELECT id FROM tasks WHERE fingerprint=?", (fingerprint,)).fetchone()
        return row["id"], row["id"] == task_id

    def get(self, task_id):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError("任务不存在")
        task = dict(row)
        task["items"] = json.loads(task["items"])
        task["stats"] = json.loads(task["stats"])
        return task

    def update(self, task_id, **values):
        if not set(values) <= {"status", "items", "stats", "error"}:
            raise ValueError("不允许修改的任务字段")
        payload = {k: json.dumps(v, ensure_ascii=False) if k in ("items", "stats") else v
                   for k, v in values.items()}
        with self.connect() as connection:
            connection.execute("UPDATE tasks SET " + ",".join(k + "=?" for k in payload) + " WHERE id=?",
                               (*payload.values(), task_id))

    def event(self, task_id, event, detail):
        with self.connect() as connection:
            connection.execute("INSERT INTO events(task_id,event,detail,created_at) VALUES (?,?,?,?)",
                               (task_id, event, json.dumps(detail, ensure_ascii=False), now()))

    def list_tasks(self, role):
        with self.connect() as connection:
            rows = connection.execute("SELECT id FROM tasks WHERE (?='reviewer' OR role='sales') "
                                      "ORDER BY created_at DESC, rowid DESC", (role,)).fetchall()
        return [self.get(r["id"]) for r in rows]

    def events(self, task_id):
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
        return [dict(r) for r in rows]

    def claim_review(self, task_id):
        with self.connect() as connection:
            changed = connection.execute("UPDATE tasks SET status='reviewing' "
                "WHERE id=? AND status='awaiting_review'", (task_id,)).rowcount
        if changed != 1:
            raise ValueError("该任务已审核或正在处理，不可重复提交审核")

    def ticket(self, task_id, item_id, title):
        ticket_id = "SIM-" + uuid.uuid4().hex[:8].upper()
        with self.connect() as connection:
            cursor = connection.execute("INSERT OR IGNORE INTO tickets VALUES (?,?,?,?,?,?)",
                                        (ticket_id, task_id, item_id, title, "待产品评估", now()))
            row = connection.execute("SELECT * FROM tickets WHERE task_id=? AND item_id=?",
                                     (task_id, item_id)).fetchone()
            if cursor.rowcount:
                connection.execute("INSERT INTO events(task_id,event,detail,created_at) VALUES (?,?,?,?)",
                                   (task_id, "ticket_created", json.dumps(dict(row), ensure_ascii=False), now()))
        return dict(row)

    def list_tickets(self, role):
        with self.connect() as connection:
            rows = connection.execute("SELECT t.* FROM tickets t JOIN tasks x ON x.id=t.task_id "
                "WHERE (?='reviewer' OR x.role='sales') ORDER BY t.created_at DESC", (role,)).fetchall()
        return [dict(r) for r in rows]

    @contextmanager
    def task_lock(self, task_id):
        """进程退出后自动释放的 OS 文件锁，保护审核、恢复和重试。"""
        folder = self.directory / "locks"
        folder.mkdir(exist_ok=True)
        stream = (folder / f"{task_id}.lock").open("a+b")
        locked = False
        try:
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                raise TaskBusyError("任务正在处理，请稍后刷新") from None
            yield
        finally:
            if locked:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            stream.close()

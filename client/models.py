"""客户端 SQLite 数据模型"""
import sqlite3
from client.config import DB_PATH


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cached_face (
    student_id   INTEGER PRIMARY KEY,
    stu_no       TEXT    NOT NULL,
    name         TEXT    NOT NULL,
    encrypted_feature BLOB NOT NULL,
    iv           BLOB    NOT NULL,
    feature_version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pending_record (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    record_json  TEXT    NOT NULL,
    retry_count  INTEGER DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cached_face_version ON cached_face(feature_version);
CREATE INDEX IF NOT EXISTS idx_pending_record_time ON pending_record(created_at);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f"客户端数据库已初始化: {DB_PATH}")

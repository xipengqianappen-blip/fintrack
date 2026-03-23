"""
fintrack/db.py
SQLite 数据库初始化与连接管理
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fintrack.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            type        TEXT NOT NULL CHECK(type IN ('checking','savings','credit','investment')),
            currency    TEXT NOT NULL DEFAULT 'CNY',
            balance     REAL NOT NULL DEFAULT 0.0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            kind    TEXT NOT NULL CHECK(kind IN ('income','expense'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id   INTEGER NOT NULL REFERENCES accounts(id),
            category_id  INTEGER REFERENCES categories(id),
            amount       REAL NOT NULL,
            description  TEXT,
            txn_date     TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            month       TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            UNIQUE(category_id, month)
        );

        CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(txn_date);
        CREATE INDEX IF NOT EXISTS idx_txn_account ON transactions(account_id);
    """)

    # 预置分类
    default_categories = [
        ("餐饮", "expense"), ("交通", "expense"), ("购物", "expense"),
        ("娱乐", "expense"), ("医疗", "expense"), ("房租", "expense"),
        ("工资", "income"),  ("奖金", "income"),  ("理财收益", "income"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO categories (name, kind) VALUES (?, ?)",
        default_categories
    )

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成。")

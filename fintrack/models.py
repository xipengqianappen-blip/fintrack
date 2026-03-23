"""
fintrack/models.py
账户与交易的增删查改操作
"""

from .db import get_connection
from datetime import datetime


# ─────────────────────────────────────────
#  Accounts
# ─────────────────────────────────────────

def create_account(name, acct_type, currency="CNY", initial_balance=0.0):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO accounts (name, type, currency, balance) VALUES (?, ?, ?, ?)",
            (name, acct_type, currency, initial_balance)
        )
        conn.commit()
        print(f"✅ 账户 '{name}' 创建成功，初始余额: {initial_balance} {currency}")
    except Exception as e:
        print(f"❌ 创建账户失败: {e}")
    finally:
        conn.close()


def list_accounts():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM accounts ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_by_name(name):
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_account_balance(account_id, delta, conn=None):
    """对账户余额做增量更新（delta 可为负数）"""
    _close = False
    if conn is None:
        conn = get_connection()
        _close = True
    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (delta, account_id)
    )
    if _close:
        conn.commit()
        conn.close()


# ─────────────────────────────────────────
#  Categories
# ─────────────────────────────────────────

def list_categories(kind=None):
    conn = get_connection()
    if kind:
        rows = conn.execute("SELECT * FROM categories WHERE kind = ?", (kind,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_by_name(name):
    conn = get_connection()
    row = conn.execute("SELECT * FROM categories WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────
#  Transactions
# ─────────────────────────────────────────

def add_transaction(account_name, category_name, amount, description="", txn_date=None):
    """
    添加一笔交易并同步更新账户余额。
    收入分类 -> 余额增加；支出分类 -> 余额减少。
    """
    account = get_account_by_name(account_name)
    if not account:
        print(f"❌ 账户 '{account_name}' 不存在。")
        return

    category = get_category_by_name(category_name)
    if not category:
        print(f"❌ 分类 '{category_name}' 不存在。")
        return

    if txn_date is None:
        txn_date = datetime.now().strftime("%Y-%m-%d")

    # BUG 1: 支出应该用 -amount，但这里对 income/expense 都用了 +amount
    # 导致支出也会增加余额
    delta = amount  # ← 应为: delta = amount if category["kind"] == "income" else -amount

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO transactions (account_id, category_id, amount, description, txn_date)
               VALUES (?, ?, ?, ?, ?)""",
            (account["id"], category["id"], amount, description, txn_date)
        )
        update_account_balance(account["id"], delta, conn=conn)
        conn.commit()
        print(f"✅ 交易记录成功: {category_name} {amount} 元 ({txn_date})")
    except Exception as e:
        conn.rollback()
        print(f"❌ 记录交易失败: {e}")
    finally:
        conn.close()


def list_transactions(account_name=None, month=None, limit=20):
    """查询交易记录，支持按账户和月份过滤"""
    conn = get_connection()
    query = """
        SELECT t.id, a.name AS account, c.name AS category, c.kind,
               t.amount, t.description, t.txn_date
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    params = []
    if account_name:
        query += " AND a.name = ?"
        params.append(account_name)
    if month:
        query += " AND strftime('%Y-%m', t.txn_date) = ?"
        params.append(month)
    query += " ORDER BY t.txn_date DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_transaction(txn_id):
    """删除交易记录并回滚余额变动"""
    conn = get_connection()
    row = conn.execute(
        """SELECT t.*, c.kind FROM transactions t
           JOIN categories c ON t.category_id = c.id
           WHERE t.id = ?""", (txn_id,)
    ).fetchone()

    if not row:
        print(f"⚠️  未找到交易 ID: {txn_id}")
        conn.close()
        return

    row = dict(row)
    # BUG 2: 回滚时 delta 方向写反了，应该是撤销原来的操作
    # 若原交易是收入(+amount)，回滚应 -amount；反之亦然
    # 但这里对两种情况都用了同一个方向，导致回滚使余额雪上加霜
    delta = row["amount"]  # ← 应为: delta = -row["amount"] if row["kind"]=="income" else row["amount"]

    conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    update_account_balance(row["account_id"], delta, conn=conn)
    conn.commit()
    conn.close()
    print(f"🗑️  交易 [{txn_id}] 已删除，余额已回滚。")

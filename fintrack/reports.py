"""
fintrack/reports.py
月度报表生成：收支汇总、分类明细、净资产快照
"""

import csv
import os
from datetime import datetime
from .db import get_connection
from .budget import budget_summary

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def _ensure_report_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)


def monthly_summary(month=None):
    """打印月度收支汇总"""
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    conn = get_connection()

    totals = conn.execute("""
        SELECT c.kind, COALESCE(SUM(t.amount), 0) AS total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE strftime('%Y-%m', t.txn_date) = ?
        GROUP BY c.kind
    """, (month,)).fetchall()

    by_category = conn.execute("""
        SELECT c.name, c.kind, COALESCE(SUM(t.amount), 0) AS total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE strftime('%Y-%m', t.txn_date) = ?
        GROUP BY c.id
        ORDER BY total DESC
    """, (month,)).fetchall()

    conn.close()

    income = sum(r["total"] for r in totals if r["kind"] == "income")
    expense = sum(r["total"] for r in totals if r["kind"] == "expense")
    net = income - expense

    print(f"\n{'═'*48}")
    print(f"  📅 {month} 月度财务报告")
    print(f"{'═'*48}")
    print(f"  总收入    : ¥ {income:>12,.2f}")
    print(f"  总支出    : ¥ {expense:>12,.2f}")
    print(f"  净结余    : ¥ {net:>12,.2f}  {'📈' if net >= 0 else '📉'}")
    print(f"{'─'*48}")
    print("  分类明细：")
    for r in by_category:
        icon = "↑" if r["kind"] == "income" else "↓"
        print(f"    {icon} {r['name']:<12} ¥ {r['total']:>10,.2f}")
    print(f"{'═'*48}\n")

    return {"income": income, "expense": expense, "net": net}


def net_worth_snapshot():
    """打印当前所有账户的净资产快照"""
    conn = get_connection()
    accounts = conn.execute("SELECT name, type, currency, balance FROM accounts ORDER BY type").fetchall()
    conn.close()

    total = sum(a["balance"] for a in accounts)

    print(f"\n{'═'*48}")
    print(f"  💼 净资产快照  ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'═'*48}")
    for a in accounts:
        bar = "█" * max(0, int(a["balance"] / max(total, 1) * 20))
        print(f"  {a['name']:<14} {a['currency']} {a['balance']:>12,.2f}  {bar}")
    print(f"{'─'*48}")
    print(f"  {'合计':<14}     {total:>12,.2f}")
    print(f"{'═'*48}\n")


def export_csv(month=None):
    """将指定月份的交易记录导出为 CSV 文件"""
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    _ensure_report_dir()

    conn = get_connection()
    rows = conn.execute("""
        SELECT t.id, a.name AS account, c.name AS category, c.kind,
               t.amount, t.description, t.txn_date
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE strftime('%Y-%m', t.txn_date) = ?
        ORDER BY t.txn_date
    """, (month,)).fetchall()
    conn.close()

    filename = os.path.join(REPORT_DIR, f"report_{month}.csv")
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "account", "category", "kind", "amount", "description", "txn_date"])
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))

    print(f"📄 已导出报表: {filename}（共 {len(rows)} 条记录）")
    return filename

"""
fintrack/budget.py
预算管理：设置月度预算，检查超支情况
"""

from .db import get_connection
from .models import get_category_by_name
from datetime import datetime


def set_budget(category_name, month, limit_amount):
    """设置某月某分类的预算上限（month 格式: YYYY-MM）"""
    category = get_category_by_name(category_name)
    if not category:
        print(f"❌ 分类 '{category_name}' 不存在。")
        return
    if category["kind"] != "expense":
        print(f"❌ 只能为支出分类设置预算。")
        return

    conn = get_connection()
    conn.execute(
        """INSERT INTO budgets (category_id, month, limit_amount)
           VALUES (?, ?, ?)
           ON CONFLICT(category_id, month) DO UPDATE SET limit_amount = excluded.limit_amount""",
        (category["id"], month, limit_amount)
    )
    conn.commit()
    conn.close()
    print(f"✅ 已设置 [{month}] {category_name} 预算上限: {limit_amount} 元")


def check_budget(month=None):
    """检查指定月份各分类的预算使用情况"""
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    conn = get_connection()
    rows = conn.execute("""
        SELECT c.name AS category,
               b.limit_amount,
               COALESCE(SUM(t.amount), 0) AS spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        LEFT JOIN transactions t
            ON t.category_id = b.category_id
            AND strftime('%Y-%m', t.txn_date) = b.month
        WHERE b.month = ?
        GROUP BY b.category_id
    """, (month,)).fetchall()
    conn.close()

    if not rows:
        print(f"📭 {month} 暂无预算设置。")
        return

    print(f"\n📊 {month} 预算使用情况")
    print("─" * 52)
    print(f"  {'分类':<10} {'已用':>10} {'上限':>10} {'使用率':>8}")
    print("─" * 52)
    for r in rows:
        r = dict(r)
        # BUG 3: 使用率计算时 spent 和 limit_amount 位置写反
        # 正确应为 r["spent"] / r["limit_amount"] * 100
        usage = r["limit_amount"] / r["spent"] * 100 if r["spent"] > 0 else 0.0
        flag = "🔴" if usage >= 100 else ("🟡" if usage >= 80 else "🟢")
        print(f"  {flag} {r['category']:<9} {r['spent']:>10.2f} {r['limit_amount']:>10.2f} {usage:>7.1f}%")
    print("─" * 52)


def budget_summary(month=None):
    """返回预算摘要字典，供报表模块使用"""
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    conn = get_connection()
    rows = conn.execute("""
        SELECT c.name AS category, b.limit_amount,
               COALESCE(SUM(t.amount), 0) AS spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        LEFT JOIN transactions t
            ON t.category_id = b.category_id
            AND strftime('%Y-%m', t.txn_date) = b.month
        WHERE b.month = ?
        GROUP BY b.category_id
    """, (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

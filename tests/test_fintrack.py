"""
tests/test_fintrack.py
单元测试套件 — 覆盖账户、交易、预算、报表核心功能
"""

import os
import sys
import sqlite3
import unittest
import tempfile

# 重定向数据库到临时文件，避免污染真实数据
_tmp_dir = tempfile.mkdtemp()
os.environ["FINTRACK_TEST_DB"] = os.path.join(_tmp_dir, "test.db")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 临时 patch DB_PATH
import fintrack.db as _db_mod
_db_mod.DB_PATH = os.environ["FINTRACK_TEST_DB"]

from fintrack import (
    init_db, create_account, list_accounts, get_account_by_name,
    add_transaction, list_transactions, delete_transaction,
    set_budget, check_budget,
    monthly_summary,
)


class TestAccounts(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_create_and_list_account(self):
        create_account("测试账户", "checking", "CNY", 1000.0)
        accounts = list_accounts()
        names = [a["name"] for a in accounts]
        self.assertIn("测试账户", names)

    def test_initial_balance(self):
        create_account("储蓄账户", "savings", "CNY", 5000.0)
        acct = get_account_by_name("储蓄账户")
        self.assertEqual(acct["balance"], 5000.0)

    def test_duplicate_account_name(self):
        create_account("唯一账户", "checking")
        # 再次创建同名账户不应崩溃
        create_account("唯一账户", "savings")
        accounts = [a for a in list_accounts() if a["name"] == "唯一账户"]
        self.assertEqual(len(accounts), 1)


class TestTransactions(unittest.TestCase):

    def setUp(self):
        init_db()
        create_account("主账户", "checking", "CNY", 10000.0)

    def test_income_increases_balance(self):
        """
        收入交易应增加余额。
        Bug 1 存在时，支出也会增加余额，此测试先通过。
        """
        add_transaction("主账户", "工资", 5000.0, "3月工资", "2025-03-31")
        acct = get_account_by_name("主账户")
        self.assertEqual(acct["balance"], 15000.0)

    def test_expense_decreases_balance(self):
        """
        Bug 1: 支出应减少余额，但当前实现会增加余额。
        修复 Bug 1 后此测试才能通过。
        """
        add_transaction("主账户", "餐饮", 100.0, "午餐", "2025-03-01")
        acct = get_account_by_name("主账户")
        # 期望余额减少到 9900，但 Bug 1 会导致余额变为 10100
        self.assertEqual(acct["balance"], 9900.0,
                         "Bug 1: 支出未减少余额，反而增加了余额")

    def test_list_transactions_filter_by_month(self):
        add_transaction("主账户", "工资", 8000.0, "", "2025-02-28")
        add_transaction("主账户", "餐饮", 200.0, "", "2025-03-05")
        feb = list_transactions(month="2025-02")
        mar = list_transactions(month="2025-03")
        self.assertEqual(len(feb), 1)
        self.assertEqual(len(mar), 1)

    def test_delete_transaction_rollback(self):
        """
        Bug 2: 删除交易时余额回滚方向错误。
        修复后：删除一笔收入记录，余额应回到原始值。
        """
        add_transaction("主账户", "工资", 3000.0, "", "2025-03-15")
        txns = list_transactions("主账户")
        txn_id = txns[0]["id"]

        # 若 Bug 1 已修复，此时余额应为 13000
        before_delete = get_account_by_name("主账户")["balance"]
        delete_transaction(txn_id)
        after_delete = get_account_by_name("主账户")["balance"]

        # 删除收入后余额应减少 3000
        self.assertEqual(after_delete, before_delete - 3000.0,
                         "Bug 2: 删除交易后余额回滚方向错误")


class TestBudget(unittest.TestCase):

    def setUp(self):
        init_db()
        create_account("预算账户", "checking", "CNY", 20000.0)

    def test_set_budget(self):
        # 不应抛出异常
        set_budget("餐饮", "2025-03", 1000.0)

    def test_budget_usage_rate(self):
        """
        Bug 3: 预算使用率计算时 spent 和 limit_amount 位置写反。
        修复后此测试才能准确反映使用率。
        """
        set_budget("餐饮", "2025-03", 1000.0)
        add_transaction("预算账户", "餐饮", 800.0, "", "2025-03-10")

        from fintrack.budget import budget_summary
        rows = budget_summary("2025-03")
        canteen = next((r for r in rows if r["category"] == "餐饮"), None)
        self.assertIsNotNone(canteen)

        # 正确使用率应为 80%，Bug 3 会得到 125%
        usage = canteen["spent"] / canteen["limit_amount"] * 100
        self.assertAlmostEqual(usage, 80.0, places=1,
                               msg="Bug 3: 预算使用率计算错误")


class TestReports(unittest.TestCase):

    def setUp(self):
        init_db()
        create_account("报表账户", "checking", "CNY", 50000.0)
        add_transaction("报表账户", "工资", 12000.0, "", "2025-03-31")
        add_transaction("报表账户", "餐饮", 600.0, "", "2025-03-15")
        add_transaction("报表账户", "交通", 200.0, "", "2025-03-20")

    def test_monthly_summary_returns_data(self):
        result = monthly_summary("2025-03")
        self.assertIn("income", result)
        self.assertIn("expense", result)
        self.assertIn("net", result)
        self.assertEqual(result["income"], 12000.0)

    def test_net_is_income_minus_expense(self):
        result = monthly_summary("2025-03")
        expected_net = result["income"] - result["expense"]
        self.assertAlmostEqual(result["net"], expected_net, places=2)


if __name__ == "__main__":
    print("🧪 运行 FinTrack 测试套件...\n")
    unittest.main(verbosity=2)

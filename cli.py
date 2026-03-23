"""
cli.py — FinTrack 命令行入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fintrack import (
    init_db, create_account, list_accounts,
    add_transaction, list_transactions, delete_transaction,
    list_categories, set_budget, check_budget,
    monthly_summary, net_worth_snapshot, export_csv,
)

HELP = """
╔══════════════════════════════════════════════════════╗
║              FinTrack — 个人财务追踪器               ║
╚══════════════════════════════════════════════════════╝

用法: python cli.py <命令> [参数]

账户管理:
  init                              初始化数据库
  account add <名称> <类型> [货币] [初始余额]
                                    类型: checking / savings / credit / investment
  account list                      查看所有账户

交易管理:
  txn add <账户> <分类> <金额> [描述] [日期YYYY-MM-DD]
  txn list [账户] [月份YYYY-MM]
  txn delete <ID>
  txn categories                    查看所有分类

预算管理:
  budget set <分类> <月份YYYY-MM> <上限金额>
  budget check [月份YYYY-MM]

报表:
  report monthly [月份YYYY-MM]
  report networth
  report export [月份YYYY-MM]
"""


def cmd_account(args):
    if not args:
        print("❌ 缺少子命令: add / list")
        return
    sub = args[0]
    if sub == "add":
        if len(args) < 3:
            print("用法: account add <名称> <类型> [货币] [初始余额]")
            return
        name = args[1]
        acct_type = args[2]
        currency = args[3] if len(args) > 3 else "CNY"
        balance = float(args[4]) if len(args) > 4 else 0.0
        create_account(name, acct_type, currency, balance)
    elif sub == "list":
        accounts = list_accounts()
        if not accounts:
            print("📭 暂无账户。")
            return
        print(f"\n  {'名称':<14} {'类型':<12} {'货币':<6} {'余额':>12}")
        print("  " + "─" * 46)
        for a in accounts:
            print(f"  {a['name']:<14} {a['type']:<12} {a['currency']:<6} {a['balance']:>12,.2f}")
    else:
        print(f"❌ 未知子命令: {sub}")


def cmd_txn(args):
    if not args:
        print("❌ 缺少子命令: add / list / delete / categories")
        return
    sub = args[0]
    if sub == "add":
        if len(args) < 4:
            print("用法: txn add <账户> <分类> <金额> [描述] [日期]")
            return
        account = args[1]
        category = args[2]
        amount = float(args[3])
        description = args[4] if len(args) > 4 else ""
        date = args[5] if len(args) > 5 else None
        add_transaction(account, category, amount, description, date)
    elif sub == "list":
        account = args[1] if len(args) > 1 else None
        month = args[2] if len(args) > 2 else None
        rows = list_transactions(account, month)
        if not rows:
            print("📭 无交易记录。")
            return
        print(f"\n  {'ID':<5} {'日期':<12} {'账户':<12} {'分类':<10} {'金额':>10}  描述")
        print("  " + "─" * 60)
        for r in rows:
            icon = "↑" if r["kind"] == "income" else "↓"
            print(f"  {r['id']:<5} {r['txn_date']:<12} {r['account']:<12} {icon}{r['category']:<9} {r['amount']:>10,.2f}  {r['description']}")
    elif sub == "delete":
        if len(args) < 2:
            print("用法: txn delete <ID>")
            return
        delete_transaction(int(args[1]))
    elif sub == "categories":
        cats = list_categories()
        print("\n  支出分类:")
        for c in cats:
            if c["kind"] == "expense":
                print(f"    · {c['name']}")
        print("  收入分类:")
        for c in cats:
            if c["kind"] == "income":
                print(f"    · {c['name']}")
    else:
        print(f"❌ 未知子命令: {sub}")


def cmd_budget(args):
    if not args:
        print("❌ 缺少子命令: set / check")
        return
    sub = args[0]
    if sub == "set":
        if len(args) < 4:
            print("用法: budget set <分类> <月份YYYY-MM> <上限金额>")
            return
        set_budget(args[1], args[2], float(args[3]))
    elif sub == "check":
        month = args[1] if len(args) > 1 else None
        check_budget(month)
    else:
        print(f"❌ 未知子命令: {sub}")


def cmd_report(args):
    if not args:
        print("❌ 缺少子命令: monthly / networth / export")
        return
    sub = args[0]
    if sub == "monthly":
        month = args[1] if len(args) > 1 else None
        monthly_summary(month)
    elif sub == "networth":
        net_worth_snapshot()
    elif sub == "export":
        month = args[1] if len(args) > 1 else None
        export_csv(month)
    else:
        print(f"❌ 未知子命令: {sub}")


def main():
    if len(sys.argv) < 2:
        print(HELP)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "init":
        init_db()
    elif cmd == "account":
        cmd_account(args)
    elif cmd == "txn":
        cmd_txn(args)
    elif cmd == "budget":
        cmd_budget(args)
    elif cmd == "report":
        cmd_report(args)
    else:
        print(f"❌ 未知命令: {cmd}")
        print(HELP)


if __name__ == "__main__":
    main()

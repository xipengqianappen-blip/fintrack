"""
scripts/import_csv.py
批量从 CSV 文件导入交易记录。

CSV 格式（带表头）:
  account,category,amount,description,date
  工资卡,工资,15000,2月工资,2025-02-28
  工资卡,餐饮,68.5,火锅,2025-02-14
"""

import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fintrack import init_db, add_transaction


def import_from_csv(filepath):
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return

    success, failed = 0, 0

    # BUG 6: 未指定编码，若 CSV 是 UTF-8-BOM 或 GBK 会读取乱码或报错
    # 应加 encoding="utf-8-sig" 或让用户指定编码
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # 从第 2 行开始（第 1 行是表头）
            try:
                account  = row["account"].strip()
                category = row["category"].strip()
                amount   = float(row["amount"].strip())
                desc     = row.get("description", "").strip()
                date     = row.get("date", "").strip() or None
                add_transaction(account, category, amount, desc, date)
                success += 1
            except Exception as e:
                print(f"⚠️  第 {i} 行导入失败: {e}")
                failed += 1

    print(f"\n📥 导入完成 — 成功: {success} 条，失败: {failed} 条。")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/import_csv.py <csv文件路径>")
        sys.exit(1)
    init_db()
    import_from_csv(sys.argv[1])

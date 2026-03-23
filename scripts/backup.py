"""
scripts/backup.py
自动备份脚本：将数据库文件按日期归档到 backups/ 目录，
并清理超过 30 天的旧备份。
"""

import os
import shutil
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fintrack.db")

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")


def backup():
    if not os.path.exists(DB_PATH):
        print("⚠️  数据库文件不存在，跳过备份。")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"fintrack_{timestamp}.db")
    shutil.copy2(DB_PATH, dest)
    size_kb = os.path.getsize(dest) / 1024
    print(f"💾 备份完成: {dest}  ({size_kb:.1f} KB)")
    return dest


def cleanup_old_backups(days=30):
    if not os.path.exists(BACKUP_DIR):
        return
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
        if mtime < cutoff:
            os.remove(fpath)
            removed += 1
    print(f"🧹 已清理 {removed} 个超过 {days} 天的旧备份。")


def run():
    print("🔧 开始自动备份...")
    backup()
    cleanup_old_backups()
    print("✅ 备份任务完成。")


if __name__ == "__main__":
    run()

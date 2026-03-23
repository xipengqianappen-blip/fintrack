# 💰 FinTrack — 个人财务追踪器

FinTrack 是一个基于 Python 命令行的个人财务管理工具，使用 SQLite 作为本地数据库，支持多账户管理、收支记录、月度预算设定、财务报表生成，以及自动化数据备份与批量导入。

---

## 📁 项目结构

```
fintrack/
├── cli.py                  # 命令行统一入口
├── fintrack/
│   ├── __init__.py
│   ├── db.py               # 数据库初始化与连接管理
│   ├── models.py           # 账户、分类、交易 CRUD
│   ├── budget.py           # 预算管理与超支检测
│   └── reports.py          # 月度报表、净资产快照、CSV 导出
├── scripts/
│   ├── backup.py           # 自动备份与旧备份清理
│   ├── import_csv.py       # CSV 批量导入交易记录
│   └── sample_data.csv     # 示例数据
├── tests/
│   └── test_fintrack.py    # 单元测试套件
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 快速开始

**环境要求：** Python 3.8+，无需安装第三方依赖。

```bash
# 克隆仓库
git clone https://github.com/xipengqianappen-blip/fintrack-cli.git
cd fintrack-cli

# 初始化数据库（首次使用必须执行）
python cli.py init
```

---

## 📖 使用说明

### 账户管理

```bash
# 创建账户（类型: checking / savings / credit / investment）
python cli.py account add 工资卡 checking CNY 10000

# 查看所有账户及余额
python cli.py account list
```

### 交易记录

```bash
# 添加一笔收入
python cli.py txn add 工资卡 工资 15000 "3月工资" 2025-03-31

# 添加一笔支出
python cli.py txn add 工资卡 餐饮 68.5 "火锅" 2025-03-14

# 查看交易列表（可按账户和月份过滤）
python cli.py txn list 工资卡 2025-03

# 删除一笔交易（余额自动回滚）
python cli.py txn delete 3

# 查看所有可用分类
python cli.py txn categories
```

### 预算管理

```bash
# 为指定月份的分类设置预算上限
python cli.py budget set 餐饮 2025-03 1000
python cli.py budget set 娱乐 2025-03 500

# 查看当月预算使用情况
python cli.py budget check
python cli.py budget check 2025-03
```

### 报表

```bash
# 月度收支报告
python cli.py report monthly 2025-03

# 当前净资产快照（所有账户汇总）
python cli.py report networth

# 导出指定月份交易明细为 CSV
python cli.py report export 2025-03
```

---

## 🛠️ 自动化脚本

### 数据库备份

```bash
# 手动执行备份（自动清理 30 天前的旧备份）
python scripts/backup.py
```

可配合系统定时任务（cron / 任务计划程序）定期自动运行：

```bash
# Linux / macOS — 每天凌晨 2 点自动备份
0 2 * * * cd /path/to/fintrack-cli && python scripts/backup.py
```

### CSV 批量导入

```bash
# 从 CSV 文件批量导入历史交易记录
python scripts/import_csv.py scripts/sample_data.csv
```

CSV 格式参考 `scripts/sample_data.csv`：

```csv
account,category,amount,description,date
工资卡,工资,15000,3月工资,2025-03-31
工资卡,餐饮,68.5,火锅聚餐,2025-03-14
```

---

## 🧪 运行测试

```bash
python tests/test_fintrack.py
```

---

## 🗄️ 数据库结构

| 表名           | 说明                       |
|----------------|----------------------------|
| `accounts`     | 账户（名称、类型、余额）   |
| `categories`   | 收支分类                   |
| `transactions` | 交易记录（关联账户与分类） |
| `budgets`      | 月度预算上限               |

数据库文件存储于 `data/fintrack.db`，备份文件存储于 `backups/`，导出报表存储于 `reports/`（均已加入 `.gitignore`）。

---

## 📄 License

MIT © [xipengqianappen-blip](https://github.com/xipengqianappen-blip)

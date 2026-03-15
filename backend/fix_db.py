import sqlite3
import os

# 数据库路径
db_path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\backend\data\app.db"

if os.path.exists(db_path):
    print(f"执行数据库修复: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 尝试给 users 表增加 permissions 列
        cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '[]';")
        print("成功为 users 表增加 permissions 列。")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("users 表已存在 permissions 列，无需修改。")
        else:
            print(f"修改 users 表出错: {e}")

    try:
        # 确认 role_templates 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='role_templates';")
        if not cursor.fetchone():
            print("检测到缺失 role_templates 表，正在创建...")
            cursor.execute("""
                CREATE TABLE role_templates (
                    role VARCHAR PRIMARY KEY,
                    permissions TEXT NOT NULL DEFAULT '[]',
                    description VARCHAR
                );
            """)
            print("成功创建 role_templates 表。")
    except Exception as e:
        print(f"创建 role_templates 表出错: {e}")

    conn.commit()
    conn.close()
    print("数据库修复完成。")
else:
    print("未找到数据库文件，无需修复。")

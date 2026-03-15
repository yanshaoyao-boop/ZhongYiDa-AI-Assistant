import json
import os
import sys

import bcrypt

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from database import Base, SessionLocal, engine
from models.user import Branch, Department, RoleTemplate, SystemSetting, User


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def default_role_templates() -> list[dict]:
    return [
        {
            "role": "owner",
            "permissions": ["manage_staff", "edit_notices", "edit_prices", "edit_cases", "edit_settings", "view_logs", "edit_knowledge"],
            "description": "系统最高管理者，拥有全量权限",
        },
        {
            "role": "executive",
            "permissions": ["edit_notices", "edit_prices", "edit_cases", "view_logs", "edit_settings", "edit_knowledge"],
            "description": "公司高管，可查看会话审计并参与经营配置",
        },
        {
            "role": "daily_admin",
            "permissions": ["manage_staff", "edit_notices", "edit_prices", "edit_cases", "edit_settings", "edit_knowledge"],
            "description": "日常管理员，拥有除会话审计外的全部后台权限",
        },
        {
            "role": "staff_admin",
            "permissions": ["manage_staff"],
            "description": "人事管理员，仅限账号与组织维护",
        },
        {
            "role": "employee",
            "permissions": [],
            "description": "普通员工，仅限前台功能使用",
        },
    ]


def init_db():
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        super_admin = db.query(User).filter(User.role.in_(["owner", "super_admin"])).first()
        if not super_admin:
            print("正在初始化基础组织架构...")
            hq_branch = Branch(name="总公司", location="总部大楼")
            db.add(hq_branch)
            db.commit()
            db.refresh(hq_branch)

            sys_dept = Department(name="总经办", branch_id=hq_branch.id)
            db.add(sys_dept)
            db.commit()
            db.refresh(sys_dept)

            print("正在生成默认超级管理员...")
            default_admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="owner",
                branch_id=hq_branch.id,
                department_id=sys_dept.id,
            )
            db.add(default_admin)
            db.commit()

            print("初始化成功！")
            print("默认管理员账号: admin")
            print("默认管理员密码: admin123")
        else:
            print("超级管理员已存在，跳过组织架构初始化。")

        print("正在初始化系统默认设置...")
        default_settings = {
            "ai_temperature": "0.3",
            "ai_search_top_k": "5",
            "ai_welcome_message": "您好，我是小易，您的全能助手。我可以为您提供智能报价、地址排雷、轨迹查询等专业支持。请问今天有什么可以帮您的？",
            "ai_enable_rag": "true",
            "ai_enable_search": "true",
            "ai_max_history": "10",
        }
        for key, value in default_settings.items():
            if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
                db.add(SystemSetting(key=key, value=value))
        db.commit()
        print("系统默认设置初始化完成。")

        print("正在初始化角色权限模板...")
        for template_data in default_role_templates():
            template = db.query(RoleTemplate).filter(RoleTemplate.role == template_data["role"]).first()
            if template is None:
                template = RoleTemplate(role=template_data["role"])
                db.add(template)
            template.permissions = json.dumps(template_data["permissions"])
            template.description = template_data["description"]
        db.commit()
        print("角色权限模板初始化完成。")
    except Exception as error:
        print(f"初始化数据库失败: {error}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    os.makedirs(os.path.join(backend_dir, "data"), exist_ok=True)
    init_db()

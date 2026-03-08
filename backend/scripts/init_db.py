import sys
import os

# 将 backend 根目录放入 sys.path，避免导入时找不到模块
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from database import engine, SessionLocal, Base
from models.user import Branch, Department, User
from models.chat_history import ChatHistory
import bcrypt

def get_password_hash(password: str) -> str:
    # bcrypt requires bytes, and returns bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def init_db():
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已经存在超级管理员
        super_admin = db.query(User).filter(User.role == "super_admin").first()
        if not super_admin:
            print("正在初始化基础组织架构...")
            # 1. 创建公司根节点
            hq_branch = Branch(name="总公司", location="总部大楼")
            db.add(hq_branch)
            db.commit()
            db.refresh(hq_branch)
            
            # 2. 创建核心部门
            sys_dept = Department(name="总经办", branch_id=hq_branch.id)
            db.add(sys_dept)
            db.commit()
            db.refresh(sys_dept)

            print("正在生成默认超级管理员...")
            # 3. 创建超级管理员
            # 生产环境部署后请立即修改此密码
            default_admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="super_admin",
                branch_id=hq_branch.id,
                department_id=sys_dept.id
            )
            db.add(default_admin)
            db.commit()
            
            print("初始化成功！")
            print("默认超级管理员账号: admin")
            print("默认超级管理员密码: admin123")
        else:
            print("超级管理员已存在，跳过架构初始化。")
        
        # 4. 初始化默认设置
        print("正在初始化系统默认设置...")
        from models.user import SystemSetting
        default_settings = {
            "ai_temperature": "0.3",
            "ai_search_top_k": "5",
            "ai_welcome_message": "您好，我是小易，您的全能助手。我可以为您提供【智能报价】、【地址排雷】、【轨迹查询】等专业支持。请问今天有什么可以帮您的？",
            "ai_enable_rag": "true",
            "ai_enable_search": "true",
            "ai_max_history": "10"
        }
        for key, value in default_settings.items():
            if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
                db.add(SystemSetting(key=key, value=value))
        db.commit()
        print("系统默认设置初始化完成。")
        
    except Exception as e:
        print(f"初始化数据库失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # 确保 data 目录存在
    os.makedirs(os.path.join(backend_dir, "data"), exist_ok=True)
    init_db()

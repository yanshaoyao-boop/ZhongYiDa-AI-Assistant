from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)

    # 关系映射
    departments = relationship("Department", back_populates="branch")
    users = relationship("User", back_populates="branch")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)

    # 关系映射
    branch = relationship("Branch", back_populates="departments")
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False) # 登录名
    full_name = Column(String, nullable=True) # 用户姓名
    hashed_password = Column(String, nullable=False)
    # role 取值为: owner, executive, daily_admin, staff_admin, employee
    role = Column(String, nullable=False, default="employee")
    # permissions 存储为 JSON 字符串，例如: ["manage_staff", "edit_notices"]
    permissions = Column(String, nullable=True, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 外键
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # 关系映射
    branch = relationship("Branch", back_populates="users")
    department = relationship("Department", back_populates="users")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class RoleTemplate(Base):
    __tablename__ = "role_templates"
    
    role = Column(String, primary_key=True, index=True) # owner, executive, etc.
    permissions = Column(String, nullable=False, default="[]") # JSON list
    description = Column(String, nullable=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)
    description = Column(String, nullable=True)
    category = Column(String, default="general")

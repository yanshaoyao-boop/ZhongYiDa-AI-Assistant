from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services.auth_service import decode_access_token

DAILY_ADMIN_IMPLICIT_PERMISSIONS = {
    "manage_staff",
    "edit_notices",
    "edit_prices",
    "edit_cases",
    "edit_settings",
    "edit_knowledge",
}

# Token 提取器，指向登录接口地址
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前登录用户的依赖项"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
        
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    """校验是否具有基础管理权限 (老板、高管、日常管理员、普通管理员)"""
    if current_user.role not in ["owner", "executive", "daily_admin", "staff_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理权限"
        )
    return current_user

def get_super_admin(current_user: User = Depends(get_current_user)):
    """校验是否为顶级控制权角色 (老板 或 历史遗留超级管理员)"""
    if current_user.role not in ["owner", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅限老板或超级管理员操作"
        )
    return current_user

def has_permission(perm: str):
    """通用权限检查装饰器/依赖项"""
    def _perm_dependency(current_user: User = Depends(get_current_user)):
        # 老板和超级管理员拥有所有权限
        if current_user.role in ["owner", "super_admin"]:
            return current_user

        if current_user.role == "daily_admin" and perm in DAILY_ADMIN_IMPLICIT_PERMISSIONS:
            return current_user

        import json
        try:
            user_perms = json.loads(current_user.permissions or "[]")
        except:
            user_perms = []
            
        if perm in user_perms:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要功能权限: {perm}"
        )
    return _perm_dependency

def get_staff_admin_user(current_user: User = Depends(get_current_user)):
    """Only users with manage_staff can access staff management."""
    return has_permission("manage_staff")(current_user)

def get_chat_audit_user(current_user: User = Depends(get_current_user)):
    """Only users with view_logs can access chat audit."""
    return has_permission("view_logs")(current_user)

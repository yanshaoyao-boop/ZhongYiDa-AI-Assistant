from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
import json

from database import get_db
from models.user import User as UserModel
from services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_DAYS,
    create_access_token,
    verify_password,
    get_password_hash,
)
from dependencies import get_current_user, User as CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = Form(False),
    db: Session = Depends(get_db)
):
    # 查找用户
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号已被禁用"
        )

    # 准备 Token Payload
    access_token_expires = (
        timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
        if remember_me
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    access_token = create_access_token(
        data={
            "sub": user.username,
            "id": user.id,
            "role": user.role,
            "branch_id": user.branch_id,
            "dept_id": user.department_id,
            "remember_me": remember_me,
        },
        expires_delta=access_token_expires
    )

    try:
        permissions = json.loads(user.permissions or "[]")
    except Exception:
        permissions = []
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_seconds": int(access_token_expires.total_seconds()),
        "user": {
            "username": user.username,
            "full_name": user.full_name or user.username,
            "role": user.role,
            "permissions": permissions,
            "branch": user.branch.name if user.branch else None,
            "department": user.department.name if user.department else None,
            "branch_id": user.branch_id,
            "department_id": user.department_id,
        }
    }


# ====== 用户自助修改密码 ======
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户自助修改密码接口，需校验旧密码"""
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码错误，请重新输入")
    
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码不能少于 6 位")
    
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "密码修改成功"}

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import io

from database import get_db
from models.user import User, Branch, Department
from dependencies import get_super_admin, get_admin_user
from services.auth_service import get_password_hash

router = APIRouter(prefix="/api/staff", tags=["staff"])

# --- Pydantic Schemas ---
class UserBase(BaseModel):
    username: str # 登录名
    full_name: Optional[str] = None # 用户姓名
    role: str
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class BranchBase(BaseModel):
    name: str
    location: Optional[str] = None

class DepartmentCreate(BaseModel):
    name: str
    branch_id: int

# --- API Endpoints ---

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    query = db.query(User)
    # 分公司管理员只能看到自己分公司的员工
    if admin.role == "branch_admin":
        query = query.filter(User.branch_id == admin.branch_id)
    
    users = query.all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "branch": u.branch.name if u.branch else None,
            "department": u.department.name if u.department else None,
            "branch_id": u.branch_id,
            "department_id": u.department_id,
        } for u in users
    ]

@router.post("/users")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    # 唯一性检查
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 权限检查：分公司管理员只能创建自己分公司的普通员工
    if admin.role == "branch_admin":
        if data.role == "super_admin":
            raise HTTPException(status_code=403, detail="无权创建超级管理员")
        if data.branch_id != admin.branch_id:
            raise HTTPException(status_code=403, detail="只能为本分公司创建员工")

    new_user = User(
        username=data.username,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        branch_id=data.branch_id,
        department_id=data.department_id,
        is_active=data.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "创建用户成功", "id": new_user.id}

@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # 权限检查
    if admin.role == "branch_admin" and user.branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="无权修改其他分公司的员工")

    if data.full_name is not None: user.full_name = data.full_name
    if data.role: user.role = data.role
    if data.branch_id is not None: user.branch_id = data.branch_id
    if data.department_id is not None: user.department_id = data.department_id
    if data.is_active is not None: user.is_active = data.is_active
    if data.password:
        user.hashed_password = get_password_hash(data.password)

    db.commit()
    return {"message": "更新成功"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    
    # 不能删自己
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")

    if admin.role == "branch_admin" and user.branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="无权删除其他分公司的员工")

    db.delete(user)
    db.commit()
    return {"message": "删除成功"}

@router.get("/users/export")
def export_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    query = db.query(User)
    if admin.role == "branch_admin":
        query = query.filter(User.branch_id == admin.branch_id)
    
    users = query.all()
    data = []
    for u in users:
        data.append({
            "登录名": u.username,
            "用户名": u.full_name or "",
            "角色": u.role,
            "状态": "启用" if u.is_active else "禁用",
            "分公司": u.branch.name if u.branch else "",
            "部门": u.department.name if u.department else ""
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='员工账号列表')
    
    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="staff_export.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@router.post("/users/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件")
    
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    
    # 必要字段检查
    required_cols = ["登录名", "用户名", "密码", "分公司", "部门"]
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Excel 缺少必要列: {col}")
            
    success_count = 0
    errors = []
    
    for index, row in df.iterrows():
        username = str(row["登录名"]).strip()
        full_name = str(row["用户名"]).strip()
        password = str(row["密码"]).strip()
        branch_name = str(row["分公司"]).strip()
        dept_name = str(row["部门"]).strip()
        role = str(row.get("角色", "user")).strip()
        
        if not username or not password:
            errors.append(f"第 {index+2} 行: 登录名或密码不能为空")
            continue
            
        # 权限与业务检查
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            errors.append(f"第 {index+2} 行: 登录名 {username} 已存在")
            continue
            
        # 匹配分公司
        branch = db.query(Branch).filter(Branch.name == branch_name).first()
        if not branch:
            # 如果是超级管理员，自动创建分公司
            if admin.role == "super_admin":
                branch = Branch(name=branch_name)
                db.add(branch)
                db.flush()
            else:
                errors.append(f"第 {index+2} 行: 分公司 {branch_name} 不存在且您无权创建")
                continue
        
        # 权限二次检查
        if admin.role == "branch_admin" and branch.id != admin.branch_id:
            errors.append(f"第 {index+2} 行: 您无权为 {branch_name} 创建账号")
            continue
            
        # 匹配或创建部门
        dept = db.query(Department).filter(Department.name == dept_name, Department.branch_id == branch.id).first()
        if not dept:
            dept = Department(name=dept_name, branch_id=branch.id)
            db.add(dept)
            db.flush()
            
        new_user = User(
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            branch_id=branch.id,
            department_id=dept.id,
            is_active=True
        )
        db.add(new_user)
        success_count += 1
        
    db.commit()
    return {
        "message": f"成功导入 {success_count} 个账号",
        "errors": errors
    }

# --- 结构管理接口 ---

@router.get("/structure")
def get_structure(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    # 超级管理员看全部，分公司管理员只看自己的分公司
    branch_query = db.query(Branch)
    if admin.role == "branch_admin":
        branch_query = branch_query.filter(Branch.id == admin.branch_id)
    
    branches = branch_query.all()
    result = []
    for b in branches:
        result.append({
            "id": b.id,
            "name": b.name,
            "departments": [{"id": d.id, "name": d.name} for d in b.departments]
        })
    return result

@router.post("/branches")
def create_branch(
    data: BranchBase,
    db: Session = Depends(get_db),
    admin: User = Depends(get_super_admin) # 只有超级管理员能建分公司
):
    new_b = Branch(name=data.name, location=data.location)
    db.add(new_b)
    db.commit()
    return {"id": new_b.id}

@router.post("/departments")
def create_dept(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    # 分公司管理员只能给自己分公司建部门
    if admin.role == "branch_admin" and data.branch_id != admin.branch_id:
         raise HTTPException(status_code=403, detail="只能管理本分公司的部门")
         
    new_d = Department(name=data.name, branch_id=data.branch_id)
    db.add(new_d)
    db.commit()
    return {"id": new_d.id}

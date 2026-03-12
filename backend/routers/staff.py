import io
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_admin_user, get_super_admin
from models.user import Branch, Department, User
from services.auth_service import get_password_hash

router = APIRouter(prefix="/api/staff", tags=["staff"])


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
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


def _ensure_branch_admin_can_assign(admin: User, branch_id: Optional[int], role: str):
    if admin.role != "branch_admin":
        return
    if role == "super_admin":
        raise HTTPException(status_code=403, detail="branch admin cannot assign super_admin role")
    if branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="branch admin can only manage users in the current branch")


def _serialize_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "branch": user.branch.name if user.branch else None,
        "department": user.department.name if user.department else None,
        "branch_id": user.branch_id,
        "department_id": user.department_id,
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    query = db.query(User)
    if admin.role == "branch_admin":
        query = query.filter(User.branch_id == admin.branch_id)
    return [_serialize_user(user) for user in query.all()]


@router.post("/users")
def create_user(data: UserCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username already exists")
    _ensure_branch_admin_can_assign(admin, data.branch_id, data.role)

    new_user = User(
        username=data.username,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        branch_id=data.branch_id,
        department_id=data.department_id,
        is_active=data.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "user created", "id": new_user.id}


@router.get("/users/export")
def export_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    query = db.query(User)
    if admin.role == "branch_admin":
        query = query.filter(User.branch_id == admin.branch_id)

    rows = []
    for user in query.all():
        rows.append(
            {
                "username": user.username,
                "full_name": user.full_name or "",
                "role": user.role,
                "status": "active" if user.is_active else "disabled",
                "branch": user.branch.name if user.branch else "",
                "department": user.department.name if user.department else "",
            }
        )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="staff")
    output.seek(0)
    return StreamingResponse(
        output,
        headers={"Content-Disposition": 'attachment; filename="staff_export.xlsx"'},
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/users/import")
async def import_users(file: UploadFile = File(...), db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="please upload an Excel file")

    dataframe = pd.read_excel(io.BytesIO(await file.read()))
    required_cols = ["username", "full_name", "password", "branch", "department"]
    for col in required_cols:
        if col not in dataframe.columns:
            raise HTTPException(status_code=400, detail=f"missing required column: {col}")

    success_count = 0
    errors = []
    for index, row in dataframe.iterrows():
        username = str(row["username"]).strip()
        full_name = str(row["full_name"]).strip()
        password = str(row["password"]).strip()
        branch_name = str(row["branch"]).strip()
        dept_name = str(row["department"]).strip()
        role = str(row.get("role", "user")).strip() or "user"

        if not username or not password:
            errors.append(f"row {index + 2}: username and password are required")
            continue
        if db.query(User).filter(User.username == username).first():
            errors.append(f"row {index + 2}: username {username} already exists")
            continue

        branch = db.query(Branch).filter(Branch.name == branch_name).first()
        if not branch:
            if admin.role != "super_admin":
                errors.append(f"row {index + 2}: branch {branch_name} does not exist")
                continue
            branch = Branch(name=branch_name)
            db.add(branch)
            db.flush()

        try:
            _ensure_branch_admin_can_assign(admin, branch.id, role)
        except HTTPException as exc:
            errors.append(f"row {index + 2}: {exc.detail}")
            continue

        department = db.query(Department).filter(Department.name == dept_name, Department.branch_id == branch.id).first()
        if not department:
            department = Department(name=dept_name, branch_id=branch.id)
            db.add(department)
            db.flush()

        db.add(
            User(
                username=username,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role=role,
                branch_id=branch.id,
                department_id=department.id,
                is_active=True,
            )
        )
        success_count += 1

    db.commit()
    return {"message": f"imported {success_count} users", "errors": errors}


@router.patch("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    if admin.role == "branch_admin" and user.branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="branch admin cannot edit users in another branch")

    requested_role = data.role or user.role
    requested_branch_id = data.branch_id if data.branch_id is not None else user.branch_id
    _ensure_branch_admin_can_assign(admin, requested_branch_id, requested_role)

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role:
        user.role = data.role
    if data.branch_id is not None:
        user.branch_id = data.branch_id
    if data.department_id is not None:
        user.department_id = data.department_id
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password:
        user.hashed_password = get_password_hash(data.password)

    db.commit()
    return {"message": "user updated"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="cannot delete current account")
    if admin.role == "branch_admin" and user.branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="branch admin cannot delete users in another branch")
    db.delete(user)
    db.commit()
    return {"message": "user deleted"}


@router.get("/structure")
def get_structure(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    query = db.query(Branch)
    if admin.role == "branch_admin":
        query = query.filter(Branch.id == admin.branch_id)
    return [
        {
            "id": branch.id,
            "name": branch.name,
            "departments": [{"id": department.id, "name": department.name} for department in branch.departments],
        }
        for branch in query.all()
    ]


@router.post("/branches")
def create_branch(data: BranchBase, db: Session = Depends(get_db), admin: User = Depends(get_super_admin)):
    branch = Branch(name=data.name, location=data.location)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return {"id": branch.id}


@router.post("/departments")
def create_dept(data: DepartmentCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    if admin.role == "branch_admin" and data.branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="branch admin can only manage departments in the current branch")
    department = Department(name=data.name, branch_id=data.branch_id)
    db.add(department)
    db.commit()
    db.refresh(department)
    return {"id": department.id}

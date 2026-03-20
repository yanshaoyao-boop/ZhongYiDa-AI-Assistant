import io
import json
from typing import Optional
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_staff_admin_user, has_permission
from models.user import Branch, Department, RoleTemplate as RoleTemplateModel, User
from services.auth_service import get_password_hash

router = APIRouter(prefix="/staff", tags=["staff"])

FULL_BRANCH_ACCESS_ROLES = {"owner", "super_admin", "executive", "daily_admin"}
FULL_ORG_MANAGEMENT_ROLES = {"owner", "super_admin", "daily_admin"}
DEFAULT_NEW_USER_PASSWORD = "123456"
DAILY_ADMIN_DEFAULT_PERMISSIONS = [
    "manage_staff",
    "edit_notices",
    "edit_prices",
    "edit_cases",
    "edit_settings",
    "edit_knowledge",
]


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: bool = True
    permissions: Optional[list] = []


class UserCreate(UserBase):
    password: Optional[str] = DEFAULT_NEW_USER_PASSWORD


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    permissions: Optional[list] = None


class PasswordUpdate(BaseModel):
    password: str
    confirm_password: str


class BranchBase(BaseModel):
    name: str
    location: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str
    branch_id: int


class RoleTemplateUpdate(BaseModel):
    role: str
    permissions: list
    description: Optional[str] = None


def _load_permissions(raw_permissions: Optional[str]) -> list[str]:
    try:
        parsed = json.loads(raw_permissions or "[]")
    except Exception:
        parsed = []
    return parsed if isinstance(parsed, list) else []


def _serialize_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "permissions": _load_permissions(user.permissions),
        "branch": user.branch.name if user.branch else None,
        "department": user.department.name if user.department else None,
        "branch_id": user.branch_id,
        "department_id": user.department_id,
    }


def _get_role_label(role: Optional[str]) -> str:
    return {
        "owner": "老板",
        "super_admin": "超级管理员",
        "executive": "高管",
        "daily_admin": "日常管理员",
        "staff_admin": "普通管理员",
        "branch_admin": "分公司管理员",
        "employee": "员工",
    }.get(role or "", role or "")


def _default_role_templates() -> list[dict]:
    return [
        {
            "role": "owner",
            "permissions": [
                "manage_staff",
                "edit_notices",
                "edit_prices",
                "edit_cases",
                "edit_settings",
                "view_logs",
                "edit_knowledge",
            ],
            "description": "系统最高管理者，拥有全量权限",
        },
        {
            "role": "executive",
            "permissions": [
                "edit_notices",
                "edit_prices",
                "edit_cases",
                "view_logs",
                "edit_settings",
                "edit_knowledge",
            ],
            "description": "公司高管，可查看会话审计并参与经营配置",
        },
        {
            "role": "daily_admin",
            "permissions": DAILY_ADMIN_DEFAULT_PERMISSIONS,
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


def _ensure_branch_admin_can_manage(
    admin: User, target_user_role: str, target_branch_id: Optional[int]
):
    if admin.role in FULL_BRANCH_ACCESS_ROLES:
        return

    perms = _load_permissions(admin.permissions)
    if "manage_staff" not in perms:
        raise HTTPException(status_code=403, detail="您没有员工管理的权限")

    if target_branch_id and target_branch_id != admin.branch_id:
        raise HTTPException(status_code=403, detail="您只能管理本分公司的员工")


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_staff_admin_user)):
    query = db.query(User)
    if admin.role not in FULL_BRANCH_ACCESS_ROLES:
        query = query.filter(User.branch_id == admin.branch_id)
    return [_serialize_user(user) for user in query.all()]


@router.post("/users")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username already exists")

    _ensure_branch_admin_can_manage(admin, data.role, data.branch_id)

    new_user = User(
        username=data.username,
        full_name=data.full_name,
        hashed_password=get_password_hash((data.password or "").strip() or DEFAULT_NEW_USER_PASSWORD),
        role=data.role,
        permissions=json.dumps(data.permissions or []),
        branch_id=data.branch_id,
        department_id=data.department_id,
        is_active=data.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "user created", "id": new_user.id}


@router.get("/users/export")
def export_users(db: Session = Depends(get_db), admin: User = Depends(get_staff_admin_user)):
    query = db.query(User)
    if admin.role == "branch_admin":
        query = query.filter(User.branch_id == admin.branch_id)

    rows = []
    for user in query.all():
        rows.append(
            {
                "登录名": user.username,
                "姓名": user.full_name or "",
                "角色": _get_role_label(user.role),
                "状态": "启用" if user.is_active else "禁用",
                "分公司": user.branch.name if user.branch else "",
                "部门": user.department.name if user.department else "",
            }
        )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="员工名单")
    output.seek(0)
    return StreamingResponse(
        output,
        headers={
            "Content-Disposition": (
                f'attachment; filename="staff_export.xlsx"; '
                f"filename*=UTF-8''{quote('员工账号导出.xlsx')}"
            )
        },
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/users/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="please upload an Excel file")

    dataframe = pd.read_excel(io.BytesIO(await file.read()))
    required_cols = ["username", "full_name", "password", "branch", "department"]
    for column in required_cols:
        if column not in dataframe.columns:
            raise HTTPException(status_code=400, detail=f"missing required column: {column}")

    success_count = 0
    errors = []
    for index, row in dataframe.iterrows():
        username = str(row["username"]).strip()
        full_name = str(row["full_name"]).strip()
        password = str(row["password"]).strip()
        branch_name = str(row["branch"]).strip()
        dept_name = str(row["department"]).strip()
        role = str(row.get("role", "employee")).strip() or "employee"

        if not username or not password:
            errors.append(f"row {index + 2}: username and password are required")
            continue
        if db.query(User).filter(User.username == username).first():
            errors.append(f"row {index + 2}: username {username} already exists")
            continue

        branch = db.query(Branch).filter(Branch.name == branch_name).first()
        if not branch:
            if admin.role not in FULL_ORG_MANAGEMENT_ROLES:
                errors.append(f"row {index + 2}: branch {branch_name} does not exist")
                continue
            branch = Branch(name=branch_name)
            db.add(branch)
            db.flush()

        try:
            _ensure_branch_admin_can_manage(admin, role, branch.id)
        except HTTPException as exc:
            errors.append(f"row {index + 2}: {exc.detail}")
            continue

        department = (
            db.query(Department)
            .filter(Department.name == dept_name, Department.branch_id == branch.id)
            .first()
        )
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
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    target_branch = data.branch_id if data.branch_id is not None else user.branch_id
    _ensure_branch_admin_can_manage(admin, data.role or user.role, target_branch)

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
    if data.permissions is not None:
        user.permissions = json.dumps(data.permissions)

    db.commit()
    return {"message": "user updated"}


@router.patch("/users/{user_id}/password")
def update_user_password(
    user_id: int,
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    if not data.password.strip():
        raise HTTPException(status_code=400, detail="password cannot be empty")
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="password confirmation does not match")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    _ensure_branch_admin_can_manage(admin, user.role, user.branch_id)
    user.hashed_password = get_password_hash(data.password)
    db.commit()
    return {"message": "password updated"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="cannot delete current account")
    if admin.role == "branch_admin" and user.branch_id != admin.branch_id:
        raise HTTPException(
            status_code=403, detail="branch admin cannot delete users in another branch"
        )
    db.delete(user)
    db.commit()
    return {"message": "user deleted"}


@router.get("/structure")
def get_structure(db: Session = Depends(get_db), admin: User = Depends(get_staff_admin_user)):
    query = db.query(Branch)
    if admin.role == "branch_admin":
        query = query.filter(Branch.id == admin.branch_id)
    return [
        {
            "id": branch.id,
            "name": branch.name,
            "departments": [
                {"id": department.id, "name": department.name}
                for department in branch.departments
            ],
        }
        for branch in query.all()
    ]


@router.post("/branches")
def create_branch(
    data: BranchBase,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    if admin.role not in FULL_ORG_MANAGEMENT_ROLES:
        raise HTTPException(
            status_code=403,
            detail="only owner, super admin, and daily admin can manage branches",
        )
    branch = Branch(name=data.name, location=data.location)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return {"id": branch.id}


@router.post("/departments")
def create_dept(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_staff_admin_user),
):
    if admin.role == "branch_admin" and data.branch_id != admin.branch_id:
        raise HTTPException(
            status_code=403,
            detail="branch admin can only manage departments in the current branch",
        )
    department = Department(name=data.name, branch_id=data.branch_id)
    db.add(department)
    db.commit()
    db.refresh(department)
    return {"id": department.id}


@router.get("/role-templates")
def get_role_templates(db: Session = Depends(get_db), admin: User = Depends(get_staff_admin_user)):
    default_templates = _default_role_templates()

    try:
        templates = db.query(RoleTemplateModel).all()
        template_map = {template.role: template for template in templates}
        updated = False

        for template_data in default_templates:
            template = template_map.get(template_data["role"])
            if template is None:
                template = RoleTemplateModel(
                    role=template_data["role"],
                    permissions=json.dumps(template_data["permissions"]),
                    description=template_data["description"],
                )
                db.add(template)
                template_map[template.role] = template
                updated = True
                continue

            if template.role == "daily_admin":
                permissions_json = json.dumps(template_data["permissions"])
                if template.permissions != permissions_json:
                    template.permissions = permissions_json
                    updated = True
                if template.description != template_data["description"]:
                    template.description = template_data["description"]
                    updated = True

        if updated:
            db.commit()

        ordered_templates = [template_map[item["role"]] for item in default_templates]
        return [
            {
                "role": template.role,
                "permissions": _load_permissions(template.permissions),
                "description": template.description,
            }
            for template in ordered_templates
        ]
    except Exception as error:
        db.rollback()
        print(f"Error fetching role templates: {error}")
        return default_templates


@router.patch("/role-templates")
def update_role_templates(
    data: list[RoleTemplateUpdate],
    db: Session = Depends(get_db),
    admin: User = Depends(has_permission("manage_staff")),
):
    for item in data:
        template = db.query(RoleTemplateModel).filter(RoleTemplateModel.role == item.role).first()
        if not template:
            template = RoleTemplateModel(role=item.role)
            db.add(template)

        template.permissions = json.dumps(item.permissions)
        if item.description is not None:
            template.description = item.description

    db.commit()
    return {"message": "role templates updated"}

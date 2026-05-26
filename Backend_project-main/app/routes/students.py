from typing import List, Optional
from ..logger import audit_log
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_admin, get_current_student
from ..models.user import User
from ..schemas.student import Student as StudentSchema
from ..schemas.student import StudentCreate, StudentUpdate
from ..services.student_service import (
    create_student,
    delete_student,
    get_student,
    get_students,
    update_student,
)

router = APIRouter(prefix="/students", tags=["students"])


# ── own profile ──────────────────────

@router.get("/me", response_model=StudentSchema)
def read_my_profile(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if not current_user.student_id:
        raise HTTPException(status_code=404, detail="No student profile linked to your account")
    student = get_student(db, current_user.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


@router.put("/me", response_model=StudentSchema)
def update_my_profile(
    student_update: StudentUpdate,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if not current_user.student_id:
        raise HTTPException(status_code=404, detail="No student profile linked to your account")
    
    updated = update_student(db, current_user.student_id, student_update, current_user.id)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # ==========================================
    # اللقطة بتاعة الـ Audit Logging هتتضاف هنا بالظبط
    # ==========================================
    audit_log(
        event="student_updated",
        student_id=current_user.student_id,
        updated_by_user_id=current_user.id,
        # بنسجل البيانات اللي اتبعتت للتعديل (لو شغال بـ Pydantic v2 استخدم model_dump)
        changes=student_update.model_dump(exclude_unset=True) 
    )

    return updated


# ── Admin only ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[StudentSchema])
def read_all_students(
    skip: int = 0,
    limit: int = 10,
    department: Optional[str] = Query(None),
    min_gpa: Optional[float] = Query(None),
    max_gpa: Optional[float] = Query(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_students(db, skip=skip, limit=limit, department=department, min_gpa=min_gpa, max_gpa=max_gpa)


@router.post("/", response_model=StudentSchema, status_code=status.HTTP_201_CREATED)
def create_new_student(
    student: StudentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_student(db, student, user_id=None)


@router.get("/{student_id}", response_model=StudentSchema)
def read_student_by_id(
    student_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/{student_id}")
def delete_existing_student(
    student_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = delete_student(db, student_id, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": f"Student {student_id} deleted successfully"}
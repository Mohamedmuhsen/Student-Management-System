from sqlalchemy.orm import Session
from ..models.student import Student
from ..models.audit_log import AuditLog
from ..schemas.student import StudentCreate, StudentUpdate, StudentPartialUpdate
from typing import Optional
import json
from ..logger import logger
# استيراد الـ redis_client من المكان اللي عرفته فيه (غالباً database أو ملف خارجي)
from ..database import redis_client 

def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    department: Optional[str] = None,
    min_gpa: Optional[float] = None,
    max_gpa: Optional[float] = None
):
    # 1. بنعمل Key فريد للكاش بناءً على الـ skip والـ limit
    cache_key = f"students_list_{skip}_{limit}"
    
    # 2. بنطبق الـ Cache-Aside: لو مفيش فلترة، دور في Redis الأول
    if not (department or min_gpa or max_gpa):
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.bind(event="cache_hit", cache_key=cache_key).info("Fetching students list from Redis cache")
            return json.loads(cached_data)

    # 3. لو مش موجود في الكاش أو فيه فلترة، روح للداتا بيز
    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    if min_gpa is not None:
        query = query.filter(Student.gpa >= min_gpa)
    if max_gpa is not None:
        query = query.filter(Student.gpa <= max_gpa)
    
    students = query.offset(skip).limit(limit).all()

    # 4. لو كانت الطلبية عادية (من غير فلتر)، خزن النتيجة في Redis لمدة 5 دقائق
    if not (department or min_gpa or max_gpa):
        students_dicts = [
            {c.name: getattr(s, c.name) for c in s.__table__.columns} 
            for s in students
        ]
        redis_client.setex(cache_key, 300, json.dumps(students_dicts))

    return students

def get_student(db: Session, student_id: int) -> Optional[Student]:
    cache_key = f"student:{student_id}"
    cached_student = redis_client.get(cache_key)
    
    if cached_student:
        logger.bind(event="cache_hit", cache_key=cache_key).info("Fetching student from Redis cache")
        return json.loads(cached_student)

    student = db.query(Student).filter(Student.id == student_id).first()
    
    if student:
        student_data = {c.name: getattr(student, c.name) for c in student.__table__.columns}
        redis_client.setex(cache_key, 3600, json.dumps(student_data))
    
    return student

def create_student(db: Session, student: StudentCreate, user_id: Optional[int] = None) -> Student:
    db_student = Student(**student.model_dump(), user_id=user_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    # Invalidation: مسح كاش القوائم لأن فيه طالب جديد دخل
    clear_list_cache()
    
    log_audit(db, user_id or 0, "CREATE", "students", db_student.id, None, json.dumps(student.model_dump()))
    logger.bind(audit=True, event="student_created", student_id=db_student.id).info("AUDIT: student_created")
    return db_student

def update_student(db: Session, student_id: int, student_update: StudentUpdate, user_id: int) -> Optional[Student]:
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        return None
    
    update_data = student_update.model_dump(exclude_unset=True)
    old_values = {k: getattr(db_student, k) for k in update_data.keys()}

    for key, value in update_data.items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)
    
    # Invalidation: مسح كاش الطالب والقوائم
    redis_client.delete(f"student:{student_id}")
    clear_list_cache()

    log_audit(db, user_id, "UPDATE", "students", student_id, json.dumps(old_values), json.dumps(update_data))
    logger.bind(audit=True, event="student_updated", student_id=student_id).info("AUDIT: student_updated")
    return db_student

def partial_update_student(db: Session, student_id: int, student_update: StudentPartialUpdate, user_id: int) -> Optional[Student]:
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        return None

    update_data = student_update.model_dump(exclude_unset=True)
    old_values = {k: getattr(db_student, k) for k in update_data.keys()}

    for key, value in update_data.items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)

    # Invalidation للمسح الجزئي كمان
    redis_client.delete(f"student:{student_id}")
    clear_list_cache()

    log_audit(db, user_id, "PARTIAL_UPDATE", "students", student_id, json.dumps(old_values), json.dumps(update_data))
    return db_student

def delete_student(db: Session, student_id: int, user_id: int) -> Optional[Student]:
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        return None

    old_values = {k: getattr(db_student, k) for k in ["name", "email", "department", "gpa"]}
    db.delete(db_student)
    db.commit()

    # Invalidation
    redis_client.delete(f"student:{student_id}")
    clear_list_cache()

    log_audit(db, user_id, "DELETE", "students", student_id, json.dumps(old_values), None)
    logger.bind(audit=True, event="student_deleted", student_id=student_id).info("AUDIT: student_deleted")
    return db_student

def clear_list_cache():
    """وظيفة مساعدة لمسح كل مفاتيح كاش القوائم"""
    keys = redis_client.keys("students_list_*")
    if keys:
        redis_client.delete(*keys)

def log_audit(db: Session, user_id: int, action: str, table_name: str, record_id: int, old_values: Optional[str], new_values: Optional[str]):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values
    )
    db.add(audit_log)
    db.commit()
# =========================================================
# IMPORTS
# =========================================================

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Request
)

from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, EmailStr

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    func
)

from sqlalchemy.orm import (
    sessionmaker,
    declarative_base,
    Session
)

from reportlab.lib.pagesizes import A4

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime

import os
import re
import shutil

# =========================================================
# CREATE FOLDERS FIRST
# =========================================================

PROFILE_FOLDER = "profile_photos"
BUG_FOLDER = "bug_screenshots"

os.makedirs(PROFILE_FOLDER, exist_ok=True)
os.makedirs(BUG_FOLDER, exist_ok=True)

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(title="SeatMyPlan Backend")

# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/profile_photos",
    StaticFiles(directory="profile_photos"),
    name="profile_photos"
)

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = DATABASE_URL = "sqlite:///./seatmyplan.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DISABLE CACHE
# =========================================================

@app.middleware("http")
async def disable_cache(request: Request, call_next):

    response = await call_next(request)

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response

# =========================================================
# DATABASE MODELS
# =========================================================

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    college_organization = Column(String(200), nullable=False)


class Profile(Base):

    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    college = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False)
    photo = Column(String(500), nullable=True)
    member_since = Column(String(100), nullable=True)
    exams_created = Column(Integer, default=0)
    last_login = Column(String(100), nullable=True)


class Student(Base):

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    reg_no = Column(String(50), unique=True, nullable=False)
    branch = Column(String(100), nullable=False)
    year = Column(String(50), nullable=False)


class Room(Base):

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(50), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    building = Column(String(100), nullable=False)


class FinalReport(Base):

    __tablename__ = "final_reports"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(100), nullable=False)
    reg_no = Column(String(50), nullable=False)
    branch = Column(String(100), nullable=False)
    seat_no = Column(Integer, nullable=False)
    room_number = Column(String(50), nullable=False)
    building = Column(String(100), nullable=False)
    invigilator = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)


class Faculty(Base):

    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    experience = Column(Integer, nullable=False)
    papers = Column(Integer, nullable=False)
    rating = Column(String(20), nullable=False)
    status = Column(String(20), default="Active")


class Notification(Base):

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    message = Column(String(1000), nullable=False)
    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    sender = Column(String(100), nullable=False)


class Feedback(Base):

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    feedback_type = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    message = Column(String(5000), nullable=False)


class FeatureRequest(Base):

    __tablename__ = "feature_requests"

    id = Column(Integer, primary_key=True, index=True)
    feature_title = Column(String(300), nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(100), nullable=False)
    description = Column(String(5000), nullable=False)
    use_case = Column(String(5000), nullable=False)
    expected_benefit = Column(String(5000), nullable=False)


class ExamHistory(Base):

    __tablename__ = "exam_history"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(300), nullable=False)
    file_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    file_size = Column(String(50), nullable=False)
    exported_by = Column(String(100), nullable=False)
    export_date = Column(String(100), nullable=False)
    export_time = Column(String(100), nullable=False)

# =========================================================
# CREATE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)

# =========================================================
# PYDANTIC MODELS
# =========================================================

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str
    college_organization: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentRequest(BaseModel):
    name: str
    reg_no: str
    branch: str
    year: str


class RoomRequest(BaseModel):
    room_number: str
    capacity: int
    building: str


class FinalReportRequest(BaseModel):
    student_name: str
    reg_no: str
    branch: str
    seat_no: int
    room_number: str
    building: str
    invigilator: str
    subject: str
    date: str
    time: str


class NotificationRequest(BaseModel):
    title: str
    message: str
    date: str
    time: str
    sender: str


class FeedbackRequest(BaseModel):
    name: str
    email: str
    feedback_type: str
    rating: int
    message: str


class FeatureRequestCreate(BaseModel):
    feature_title: str
    category: str
    priority: str
    description: str
    use_case: str
    expected_benefit: str

# =========================================================
# DATABASE SESSION
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "SeatMyPlan Backend Running Successfully"
    }

# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(
    user: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$'

    if not re.match(password_regex, user.password):

        raise HTTPException(
            status_code=400,
            detail="Weak password"
        )

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=user.password,
        role=user.role,
        college_organization=user.college_organization
    )

    db.add(new_user)

    profile = Profile(
        full_name=user.full_name,
        email=user.email,
        college=user.college_organization,
        role=user.role,
        member_since="2026",
        exams_created=0,
        last_login="Today"
    )

    db.add(profile)

    db.commit()

    return {
        "message": "Registration Successful"
    }

# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing:

        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    if existing.password != user.password:

        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )

    return {
        "message": "Login Successful",
        "full_name": existing.full_name,
        "role": existing.role
    }

# =========================================================
# STUDENTS
# =========================================================

@app.post("/students")
def add_student(
    student: StudentRequest,
    db: Session = Depends(get_db)
):

    existing = db.query(Student).filter(
        Student.reg_no == student.reg_no
    ).first()

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Register number already exists"
        )

    new_student = Student(**student.dict())

    db.add(new_student)

    db.commit()

    db.refresh(new_student)

    return new_student


@app.get("/students")
def get_students(
    db: Session = Depends(get_db)
):

    return db.query(Student).all()


@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)

    db.commit()

    return {
        "message": "Student deleted successfully"
    }

# =========================================================
# ROOMS
# =========================================================

@app.post("/rooms")
def add_room(
    room: RoomRequest,
    db: Session = Depends(get_db)
):

    new_room = Room(**room.dict())

    db.add(new_room)

    db.commit()

    db.refresh(new_room)

    return new_room


@app.get("/rooms")
def get_rooms(
    db: Session = Depends(get_db)
):

    return db.query(Room).all()


@app.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db)
):

    room = db.query(Room).filter(
        Room.id == room_id
    ).first()

    if not room:

        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    db.delete(room)

    db.commit()

    return {
        "message": "Room deleted successfully"
    }

# =========================================================
# FINAL REPORTS
# =========================================================

@app.post("/final-reports")
def add_report(
    report: FinalReportRequest,
    db: Session = Depends(get_db)
):

    new_report = FinalReport(**report.dict())

    db.add(new_report)

    db.commit()

    db.refresh(new_report)

    return new_report


@app.get("/final-reports")
def get_reports(
    db: Session = Depends(get_db)
):

    return db.query(FinalReport).all()


@app.delete("/final-reports/{report_id}")
def delete_final_report(
    report_id: int,
    db: Session = Depends(get_db)
):

    report = db.query(FinalReport).filter(
        FinalReport.id == report_id
    ).first()

    if not report:

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    db.delete(report)

    db.commit()

    return {
        "message": "Final report deleted successfully"
    }

# =========================================================
# NOTIFICATIONS
# =========================================================

@app.post("/notifications")
def add_notification(
    notification: NotificationRequest,
    db: Session = Depends(get_db)
):

    new_notification = Notification(**notification.dict())

    db.add(new_notification)

    db.commit()

    db.refresh(new_notification)

    return new_notification


@app.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db)
):

    return db.query(Notification).order_by(
        Notification.id.desc()
    ).all()


@app.delete("/notifications/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):

    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:

        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    db.delete(notification)

    db.commit()

    return {
        "message": "Notification deleted successfully"
    }

# =========================================================
# FEEDBACK
# =========================================================

@app.post("/feedback")
def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):

    new_feedback = Feedback(**feedback.dict())

    db.add(new_feedback)

    db.commit()

    db.refresh(new_feedback)

    return {
        "message": "Feedback submitted successfully"
    }

# =========================================================
# FEATURE REQUEST
# =========================================================

@app.post("/feature-request")
def submit_feature_request(
    feature: FeatureRequestCreate,
    db: Session = Depends(get_db)
):

    new_feature = FeatureRequest(**feature.dict())

    db.add(new_feature)

    db.commit()

    db.refresh(new_feature)

    return {
        "message": "Feature request submitted successfully"
    }

# =========================================================
# PROFILE
# =========================================================

@app.get("/profile/{email}")
def get_profile(
    email: str,
    db: Session = Depends(get_db)
):

    profile = db.query(Profile).filter(
        Profile.email == email
    ).first()

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile

# =========================================================
# UPLOAD PROFILE PHOTO
# =========================================================

# =========================================================
# UPLOAD PROFILE PHOTO
# =========================================================

@app.post("/upload-photo/{email}")
async def upload_photo(
    email: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    profile = db.query(Profile).filter(
        Profile.email == email
    ).first()

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    extension = file.filename.split(".")[-1]

    filename = f"{email.replace('@', '_').replace('.', '_')}.{extension}"

    file_path = os.path.join(
        PROFILE_FOLDER,
        filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    photo_url = f"/profile_photos/{filename}"

    profile.photo = photo_url

    db.commit()

    return {
        "message": "Photo uploaded successfully",
        "photo_url": photo_url
    }
# =========================================================
# DASHBOARD
# =========================================================

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # OVERVIEW COUNTS
    # -----------------------------------------------------

    total_students = db.query(Student).count()

    total_rooms = db.query(Room).count()

    total_allocated = db.query(FinalReport).count()

    total_notifications = db.query(Notification).count()

    total_faculties = db.query(Faculty).count()

    total_feedbacks = db.query(Feedback).count()

    total_feature_requests = db.query(
        FeatureRequest
    ).count()

    total_exports = db.query(
        ExamHistory
    ).count()

    # -----------------------------------------------------
    # TOTAL BRANCHES
    # -----------------------------------------------------

    total_branches = db.query(
        func.count(
            func.distinct(Student.branch)
        )
    ).scalar()

    # -----------------------------------------------------
    # BRANCH DISTRIBUTION
    # -----------------------------------------------------

    branch_data = db.query(
        Student.branch,
        func.count(Student.id).label("count")
    ).group_by(
        Student.branch
    ).all()

    branch_distribution = []

    for branch_name, count in branch_data:

        branch_distribution.append({

            "branch": branch_name,

            "students": count
        })

    # -----------------------------------------------------
    # PIE CHART DATA
    # -----------------------------------------------------

    pie_chart = {

        "labels": [],

        "values": []
    }

    if total_students > 0:

        for branch_name, count in branch_data:

            percentage = round(
                (count / total_students) * 100,
                1
            )

            pie_chart["labels"].append(
                branch_name
            )

            pie_chart["values"].append(
                percentage
            )

    # -----------------------------------------------------
    # RECENT ALLOCATIONS
    # -----------------------------------------------------

    reports = db.query(
        FinalReport
    ).order_by(
        FinalReport.id.desc()
    ).limit(10).all()

    recent_allocations = []

    for report in reports:

        recent_allocations.append({

            "id": report.id,

            "student_name": report.student_name,

            "reg_no": report.reg_no,

            "room_number": report.room_number,

            "seat_no": report.seat_no,

            "branch": report.branch,

            "date": report.date,

            "time": report.time,

            "subject": report.subject,

            "status": "Assigned"
        })

    # -----------------------------------------------------
    # UPCOMING EXAM
    # -----------------------------------------------------

    latest_exam = db.query(
        FinalReport
    ).order_by(
        FinalReport.id.desc()
    ).first()

    upcoming_exam = None

    if latest_exam:

        upcoming_exam = {

            "subject": latest_exam.subject,

            "date": latest_exam.date,

            "time": latest_exam.time
        }

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return {

        "overview": {

            "students": total_students,

            "rooms": total_rooms,

            "allocated": total_allocated,

            "branches": total_branches,

            "notifications": total_notifications,

            "faculties": total_faculties,

            "feedbacks": total_feedbacks,

            "feature_requests": total_feature_requests,

            "exports": total_exports
        },

        "upcoming_exam": upcoming_exam,

        "branch_distribution": branch_distribution,

        "pie_chart": pie_chart,

        "recent_allocations": recent_allocations
    }

# =========================================================
# DASHBOARD ANALYTICS
# =========================================================

@app.get("/dashboard/analytics")
def dashboard_analytics(
    db: Session = Depends(get_db)
):

    recent_reports = db.query(
        FinalReport
    ).order_by(
        FinalReport.id.desc()
    ).limit(5).all()

    recent_notifications = db.query(
        Notification
    ).order_by(
        Notification.id.desc()
    ).limit(5).all()

    return {

        "total_students": db.query(
            Student
        ).count(),

        "total_rooms": db.query(
            Room
        ).count(),

        "total_reports": db.query(
            FinalReport
        ).count(),

        "total_notifications": db.query(
            Notification
        ).count(),

        "total_faculties": db.query(
            Faculty
        ).count(),

        "total_feedbacks": db.query(
            Feedback
        ).count(),

        "total_feature_requests": db.query(
            FeatureRequest
        ).count(),

        "total_exports": db.query(
            ExamHistory
        ).count(),

        "recent_reports": len(
            recent_reports
        ),

        "recent_notifications": len(
            recent_notifications
        )
    }

# =========================================================
# PIE CHART
# =========================================================

@app.get("/dashboard/pie-chart")
def pie_chart(
    db: Session = Depends(get_db)
):

    branches = db.query(
        Student.branch,
        func.count(Student.id).label("count")
    ).group_by(
        Student.branch
    ).all()

    total_students = db.query(
        Student
    ).count()

    labels = []

    values = []

    if total_students > 0:

        for branch_name, count in branches:

            percentage = round(
                (count / total_students) * 100,
                1
            )

            labels.append(branch_name)

            values.append(percentage)

    return {

        "labels": labels,

        "values": values
    }

# =========================================================
# BRANCH DISTRIBUTION
# =========================================================

@app.get("/dashboard/branch-distribution")
def branch_distribution(
    db: Session = Depends(get_db)
):

    branches = db.query(
        Student.branch,
        func.count(Student.id).label("count")
    ).group_by(
        Student.branch
    ).all()

    result = []

    for branch_name, count in branches:

        result.append({

            "branch": branch_name,

            "students": count
        })

    return result

# =========================================================
# RECENT ALLOCATIONS
# =========================================================

@app.get("/dashboard/recent-allocations")
def recent_allocations(
    db: Session = Depends(get_db)
):

    reports = db.query(
        FinalReport
    ).order_by(
        FinalReport.id.desc()
    ).limit(10).all()

    return [

        {

            "id": report.id,

            "student_name": report.student_name,

            "reg_no": report.reg_no,

            "room_number": report.room_number,

            "seat_no": report.seat_no,

            "branch": report.branch,

            "date": report.date,

            "time": report.time,

            "subject": report.subject,

            "status": "Assigned"
        }

        for report in reports
    ]
# =========================================================
# SEATING PLAN
# =========================================================

@app.post("/seating-plans")
def generate_seating_plan():

    return {
        "message": "Seating plan generated successfully"
    }

# =========================================================
# EXAM HISTORY
# =========================================================

@app.get("/exam-history")
def get_exam_history(
    db: Session = Depends(get_db)
):

    return db.query(
        ExamHistory
    ).order_by(
        ExamHistory.id.desc()
    ).all()

# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.get("/download-report")
def download_report(
    db: Session = Depends(get_db)
):

    reports = db.query(FinalReport).all()

    file_name = "final_report.pdf"

    doc = SimpleDocTemplate(
        file_name,
        pagesize=A4
    )

    elements = []

    styles = getSampleStyleSheet()

    title = Paragraph(
        "SeatMyPlan Final Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    data = [[
        "Student",
        "Reg No",
        "Branch",
        "Seat No",
        "Room",
        "Invigilator"
    ]]

    for report in reports:

        data.append([
            report.student_name,
            report.reg_no,
            report.branch,
            str(report.seat_no),
            report.room_number,
            report.invigilator
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')

    ]))

    elements.append(table)

    doc.build(elements)

    return FileResponse(
        path=file_name,
        filename=file_name,
        media_type='application/pdf'
    )

# =========================================================
# RUN SERVER
# =========================================================

# pip install fastapi uvicorn sqlalchemy pymysql reportlab email-validator python-multipart

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
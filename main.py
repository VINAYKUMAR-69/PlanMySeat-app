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

import os
import re
import shutil

# =========================================================
# CREATE FOLDERS
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

DATABASE_URL = os.getenv("MYSQL_PUBLIC_URL")

if not DATABASE_URL:
    raise Exception("MYSQL_PUBLIC_URL not found")

# Railway gives mysql:// but SQLAlchemy needs mysql+pymysql://
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "mysql://",
        "mysql+pymysql://",
        1
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
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

    return {

        "students": db.query(Student).count(),

        "rooms": db.query(Room).count(),

        "users": db.query(User).count(),

        "notifications": db.query(Notification).count()
    }

# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.get("/download-report")
def download_report(
    db: Session = Depends(get_db)
):

    reports = db.query(Student).all()

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
        "Year"
    ]]

    for report in reports:

        data.append([
            report.name,
            report.reg_no,
            report.branch,
            report.year
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

# pip install fastapi uvicorn sqlalchemy pymysql reportlab
# pip install email-validator python-multipart

# Run:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
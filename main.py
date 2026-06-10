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
    ForeignKey
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

from dotenv import load_dotenv

import os
import re
import shutil
import random
import smtplib

from datetime import datetime, timedelta

from email.mime.text import MIMEText
# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv("vina.env")

print("MYSQLHOST =", os.getenv("MYSQLHOST"))
print("MYSQLPORT =", os.getenv("MYSQLPORT"))
print("MYSQLUSER =", os.getenv("MYSQLUSER"))
print("MYSQLDATABASE =", os.getenv("MYSQLDATABASE"))

# =========================================================
# CREATE FOLDERS
# =========================================================

PROFILE_FOLDER = "profile_photos"

os.makedirs(PROFILE_FOLDER, exist_ok=True)

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

MYSQLHOST = os.getenv("MYSQLHOST")
MYSQLPORT = os.getenv("MYSQLPORT")
MYSQLUSER = os.getenv("MYSQLUSER")
MYSQLPASSWORD = os.getenv("MYSQLPASSWORD")
MYSQLDATABASE = os.getenv("MYSQLDATABASE")

if not all([
    MYSQLHOST,
    MYSQLPORT,
    MYSQLUSER,
    MYSQLPASSWORD,
    MYSQLDATABASE
]):
    raise Exception(
        "Database environment variables are missing"
    )

DATABASE_URL = (
    f"mysql+pymysql://{MYSQLUSER}:{MYSQLPASSWORD}"
    f"@{MYSQLHOST}:{MYSQLPORT}/{MYSQLDATABASE}"
)

print("Database URL created successfully")

# =========================================================
# DATABASE ENGINE
# =========================================================

try:

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    print("Engine created successfully")

except Exception as e:

    print("Engine creation failed")
    print(e)

    raise e

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

    user_email = Column(
        String(100),
        ForeignKey("users.email")
    )

    name = Column(String(100), nullable=False)

    reg_no = Column(String(50), nullable=False)

    branch = Column(String(100), nullable=False)

    year = Column(String(50), nullable=False)


class Room(Base):

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)

    user_email = Column(
        String(100),
        ForeignKey("users.email")
    )

    room_number = Column(String(50), nullable=False)

    capacity = Column(Integer, nullable=False)

    building = Column(String(100), nullable=False)


class Faculty(Base):

    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)

    user_email = Column(
        String(100),
        ForeignKey("users.email")
    )

    faculty_id = Column(String(50), nullable=False)

    name = Column(String(100), nullable=False)

    designation = Column(String(100), nullable=False)

    department = Column(String(100), nullable=False)

    phone = Column(String(20), nullable=False)

    experience = Column(String(50), nullable=False)

    papers = Column(String(50), nullable=False)

    rating = Column(String(50), nullable=False)

    status = Column(String(50), nullable=False)


class Notification(Base):

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_email = Column(
        String(100),
        ForeignKey("users.email")
    )

    title = Column(String(300), nullable=False)

    message = Column(String(1000), nullable=False)

    date = Column(String(50), nullable=False)

    time = Column(String(50), nullable=False)

    sender = Column(String(100), nullable=False)

# =========================================================
# FEEDBACK MODEL
# =========================================================

class Feedback(Base):

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(100), nullable=False)

    feedback_type = Column(String(100), nullable=False)

    rating = Column(String(20), nullable=False)

    message = Column(String(1000), nullable=False)


# =========================================================
# FEATURE REQUEST MODEL
# =========================================================

class FeatureRequest(Base):

    __tablename__ = "feature_requests"

    id = Column(Integer, primary_key=True, index=True)

    feature_title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=False)
    use_case = Column(String(1000), nullable=False)
    expected_benefit = Column(String(1000), nullable=False)


class OTPVerification(Base):

    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(100), nullable=False)

    otp = Column(String(10), nullable=False)

    expiry_time = Column(String(100), nullable=False)
# =========================================================
# CREATE TABLES
# =========================================================

try:

    print("Connecting to database...")

    with engine.connect() as conn:
        print("Database connected successfully")

    Base.metadata.create_all(bind=engine)

    print("ALL TABLES CREATED SUCCESSFULLY")

except Exception as e:

    print("DATABASE ERROR")
    print(e)

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
    user_email: EmailStr
    name: str
    reg_no: str
    branch: str
    year: str


class RoomRequest(BaseModel):
    user_email: EmailStr
    room_number: str
    capacity: int
    building: str


class FacultyRequest(BaseModel):
    user_email: EmailStr
    faculty_id: str
    name: str
    designation: str
    department: str
    phone: str
    experience: str
    papers: str
    rating: str
    status: str


class NotificationRequest(BaseModel):
    user_email: EmailStr
    title: str
    message: str
    date: str
    time: str
    sender: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
# =========================================================
# FEEDBACK REQUEST
# =========================================================

class FeedbackRequest(BaseModel):
    name: str
    email: EmailStr
    feedback_type: str
    rating: int
    message: str


# =========================================================
# FEATURE REQUEST REQUEST
# =========================================================

class FeatureRequestRequest(BaseModel):
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
def send_otp_email(receiver_email, otp):

    subject = "SeatMyPlan Password Reset OTP"

    body = f"""
Your OTP for password reset is:

{otp}

This OTP is valid for 5 minutes.

SeatMyPlan Team
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(msg)
# =========================================================
# FEEDBACKS
# =========================================================

@app.post("/feedbacks")
def create_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):

    new_feedback = Feedback(
        name=feedback.name,
        email=feedback.email,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        message=feedback.message
    )

    db.add(new_feedback)
    db.commit()

    return {
        "message": "Feedback submitted successfully"
    }


@app.get("/feedbacks")
def get_feedbacks(
    db: Session = Depends(get_db)
):

    return db.query(Feedback).order_by(
        Feedback.id.desc()
    ).all()


@app.delete("/feedbacks/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):

    feedback = db.query(Feedback).filter(
        Feedback.id == feedback_id
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    db.delete(feedback)
    db.commit()

    return {
        "message": "Feedback deleted successfully"
    }
@app.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    otp = str(random.randint(100000, 999999))

    expiry = datetime.now() + timedelta(minutes=5)

    existing = db.query(
        OTPVerification
    ).filter(
        OTPVerification.email == data.email
    ).first()

    if existing:
        db.delete(existing)
        db.commit()

    otp_record = OTPVerification(
        email=data.email,
        otp=otp,
        expiry_time=str(expiry)
    )

    db.add(otp_record)
    db.commit()

    send_otp_email(data.email, otp)

    return {
        "message": "OTP sent successfully"
    }


@app.post("/verify-otp")
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):

    record = db.query(
        OTPVerification
    ).filter(
        OTPVerification.email == data.email,
        OTPVerification.otp == data.otp
    ).first()

    if not record:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    expiry = datetime.fromisoformat(
        record.expiry_time
    )

    if datetime.now() > expiry:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    return {
        "message": "OTP verified successfully"
    }


@app.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password = data.new_password

    db.commit()

    db.query(
        OTPVerification
    ).filter(
        OTPVerification.email == data.email
    ).delete()

    db.commit()

    return {
        "message": "Password reset successful"
    }


# =========================================================
# FEATURE REQUESTS
# =========================================================

@app.post("/feature-requests")
def create_feature_request(
    request: FeatureRequestRequest,
    db: Session = Depends(get_db)
):

    new_request = FeatureRequest(
        feature_title=request.feature_title,
        category=request.category,
        priority=request.priority,
        description=request.description,
        use_case=request.use_case,
        expected_benefit=request.expected_benefit
    )

    db.add(new_request)
    db.commit()

    return {
        "message": "Feature request submitted successfully"
    }


@app.get("/feature-requests")
def get_feature_requests(
    db: Session = Depends(get_db)
):

    return db.query(
        FeatureRequest
    ).order_by(
        FeatureRequest.id.desc()
    ).all()


@app.delete("/feature-requests/{request_id}")
def delete_feature_request(
    request_id: int,
    db: Session = Depends(get_db)
):

    request = db.query(
        FeatureRequest
    ).filter(
        FeatureRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Feature request not found"
        )

    db.delete(request)
    db.commit()

    return {
        "message": "Feature request deleted successfully"
    }
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
        "email": existing.email,
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

    existing_student = db.query(Student).filter(
        Student.reg_no == student.reg_no,
        Student.user_email == student.user_email
    ).first()

    if existing_student:

        raise HTTPException(
            status_code=400,
            detail="Register number already exists"
        )

    new_student = Student(
        user_email=student.user_email,
        name=student.name,
        reg_no=student.reg_no,
        branch=student.branch,
        year=student.year
    )

    db.add(new_student)

    db.commit()

    db.refresh(new_student)

    return {
        "message": "Student added successfully"
    }


@app.get("/students/{email}")
def get_students(
    email: str,
    db: Session = Depends(get_db)
):

    students = db.query(Student).filter(
        Student.user_email == email
    ).all()

    return students


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

    existing_room = db.query(Room).filter(
        Room.room_number == room.room_number,
        Room.user_email == room.user_email
    ).first()

    if existing_room:

        raise HTTPException(
            status_code=400,
            detail="Room already exists"
        )

    new_room = Room(
        user_email=room.user_email,
        room_number=room.room_number,
        capacity=room.capacity,
        building=room.building
    )

    db.add(new_room)

    db.commit()

    db.refresh(new_room)

    return {
        "message": "Room added successfully"
    }


@app.get("/rooms/{email}")
def get_rooms(
    email: str,
    db: Session = Depends(get_db)
):

    rooms = db.query(Room).filter(
        Room.user_email == email
    ).all()

    return rooms


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
# FACULTIES
# =========================================================

@app.post("/faculties")
def add_faculty(
    faculty: FacultyRequest,
    db: Session = Depends(get_db)
):

    existing_faculty = db.query(Faculty).filter(
        Faculty.faculty_id == faculty.faculty_id,
        Faculty.user_email == faculty.user_email
    ).first()

    if existing_faculty:

        raise HTTPException(
            status_code=400,
            detail="Faculty already exists"
        )

    new_faculty = Faculty(
        user_email=faculty.user_email,
        faculty_id=faculty.faculty_id,
        name=faculty.name,
        designation=faculty.designation,
        department=faculty.department,
        phone=faculty.phone,
        experience=faculty.experience,
        papers=faculty.papers,
        rating=faculty.rating,
        status=faculty.status
    )

    db.add(new_faculty)

    db.commit()

    db.refresh(new_faculty)

    return {
        "message": "Faculty added successfully"
    }


@app.get("/faculties/{email}")
def get_faculties(
    email: str,
    db: Session = Depends(get_db)
):

    faculties = db.query(Faculty).filter(
        Faculty.user_email == email
    ).all()

    return faculties


@app.delete("/faculties/{faculty_id}")
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db)
):

    faculty = db.query(Faculty).filter(
        Faculty.id == faculty_id
    ).first()

    if not faculty:

        raise HTTPException(
            status_code=404,
            detail="Faculty not found"
        )

    db.delete(faculty)

    db.commit()

    return {
        "message": "Faculty deleted successfully"
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

@app.get("/dashboard/{email}")
def get_dashboard(
    email: str,
    db: Session = Depends(get_db)
):

    students_count = db.query(Student).filter(
        Student.user_email == email
    ).count()

    rooms_count = db.query(Room).filter(
        Room.user_email == email
    ).count()

    faculties_count = db.query(Faculty).filter(
        Faculty.user_email == email
    ).count()

    notifications_count = db.query(Notification).filter(
        Notification.user_email == email
    ).count()

    branches = db.query(Student.branch).filter(
        Student.user_email == email
    ).distinct().all()

    return {
        "students": students_count,
        "rooms": rooms_count,
        "faculties": faculties_count,
        "notifications": notifications_count,
        "branches": len(branches)
    }

# =========================================================
# NOTIFICATIONS
# =========================================================

@app.post("/notifications")
def create_notification(
    notification: NotificationRequest,
    db: Session = Depends(get_db)
):

    new_notification = Notification(
        user_email=notification.user_email,
        title=notification.title,
        message=notification.message,
        date=notification.date,
        time=notification.time,
        sender=notification.sender
    )

    db.add(new_notification)

    db.commit()

    db.refresh(new_notification)

    return {
        "message": "Notification created successfully"
    }


@app.get("/notifications/{email}")
def get_notifications(
    email: str,
    db: Session = Depends(get_db)
):

    notifications = db.query(Notification).filter(
        Notification.user_email == email
    ).order_by(Notification.id.desc()).all()

    return notifications


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
# DOWNLOAD REPORT
# =========================================================

@app.get("/download-report/{email}")
def download_report(
    email: str,
    db: Session = Depends(get_db)
):

    reports = db.query(Student).filter(
        Student.user_email == email
    ).all()

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

# uvicorn main:app --reload
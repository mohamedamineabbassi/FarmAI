import os

class Config:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "root123")
    DB_NAME = os.getenv("DB_NAME", "attendance_db")

    # FastAPI Server
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))

    # Backend
    BACKEND_UPLOAD_URL = "http://localhost:8081/api/upload"
    
    # Face Recognition
    FACE_MATCH_THRESHOLD = 0.85

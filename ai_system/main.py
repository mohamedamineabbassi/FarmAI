import cv2
import json
import numpy as np
import mysql.connector
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from insightface.app import FaceAnalysis
import uvicorn
import os
import logging
from mysql.connector import Error

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app_fastapi = FastAPI(title="AI Security Face API")

# Enable CORS for Spring Boot calls if needed (though usually server-to-server)
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB CONNECTION WITH ERROR HANDLING
# =========================
def get_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root123",
            database="attendance_db"
        )
        logger.info("✓ Connexion MySQL établie (main.py)")
        return db
    except Error as e:
        logger.error(f"✗ Erreur connexion MySQL: {e}")
        raise

# =========================
# IA MODEL (BUFFALO_L) WITH ERROR HANDLING
# =========================
try:
    logger.info("Chargement du modèle InsightFace...")
    face_app = FaceAnalysis(name='buffalo_l')
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    logger.info("✓ Modèle InsightFace chargé")
except Exception as e:
    logger.error(f"✗ Erreur chargement modèle: {e}")
    raise

# =========================
# UTILS
# =========================
def load_all_embeddings():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, embedding FROM employees WHERE embedding IS NOT NULL")
        data = cursor.fetchall()
        
        embeddings = []
        for row in data:
            emp_id = row[0]
            try:
                emb = np.array(json.loads(row[1]))
                emb = emb / np.linalg.norm(emb)
                embeddings.append((emp_id, emb))
            except json.JSONDecodeError:
                logger.warning(f"Embedding invalide pour employé {emp_id}")
                continue
        
        cursor.close()
        db.close()
        logger.info(f"✓ {len(embeddings)} embeddings chargés")
        return embeddings
    except Error as e:
        logger.error(f"✗ Erreur chargement embeddings: {e}")
        return []

def is_duplicate(new_emb, db_embeddings, threshold=0.6):
    for emp_id, emb in db_embeddings:
        dist = np.linalg.norm(new_emb - emb)
        logger.debug(f"Distance vérifiée: {dist:.3f}")
        if dist < threshold:
            logger.warning(f"Doublon détecté pour employé {emp_id}: dist={dist:.3f}")
            return True, emp_id
    return False, None

# =========================
# ENDPOINTS
# =========================

@app_fastapi.post("/api/face/register")
def register_face(employeeId: int):
    print(f"RECEIVED REGISTRATION REQUEST FOR ID: {employeeId}")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Could not open camera")

    print(f"REGISTERING FACE FOR ID: {employeeId}")
    
    face_registered = False
    message = ""
    status = "error"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = face_app.get(frame)
        
        if len(faces) > 0:
            face = faces[0]
            x1, y1, x2, y2 = map(int, face.bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (156, 39, 176), 2) # Purple color
            cv2.putText(frame, "Press 'S' to Capture", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (156, 39, 176), 2)
        else:
            cv2.putText(frame, "NO FACE DETECTED", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Register Face - AI Security", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            if len(faces) == 0:
                print("No face detected")
                continue
            
            new_emb = faces[0].embedding
            new_emb = new_emb / np.linalg.norm(new_emb)
            
            db_embeddings = load_all_embeddings()
            duplicate, existing_id = is_duplicate(new_emb, db_embeddings)

            if duplicate and existing_id != employeeId:
                message = f"Face already exists for employee ID {existing_id}"
                status = "duplicate"
                print(f"Error: {message}")
                break 
            
            try:
                db = get_db()
                cursor = db.cursor()
                
                # Update employee
                cursor.execute(
                    "UPDATE employees SET embedding=%s, face_registered=1 WHERE id=%s",
                    (json.dumps(new_emb.tolist()), employeeId)
                )
                
                # ✅ Mettre à jour uniquement la table employees (users n'existe pas)
                logger.info(f"Embedding sauvegardé pour employé {employeeId}")
                
                db.commit()
                cursor.close()
                db.close()
                face_registered = True
                status = "success"
                message = "Face registered successfully"
                break
            except Exception as e:
                print(f"DB ERROR: {e}")
                message = f"Database error: {str(e)}"
                break

        if key == 27: # ESC
            message = "Registration cancelled by user"
            break

    cap.release()
    cv2.destroyAllWindows()
    
    return {"status": status, "message": message, "employeeId": employeeId}

@app_fastapi.post("/api/face/recognize")
def recognize_face():
    print("RECEIVED RECOGNITION REQUEST")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Could not open camera")

    db_embeddings = load_all_embeddings()
    result = {"employeeId": None, "confidence": 0.0, "status": "no_face"}

    # Timeout after 10 seconds of no face or no match
    import time
    start_time = time.time()

    while time.time() - start_time < 15:
        ret, frame = cap.read()
        if not ret:
            break

        faces = face_app.get(frame)
        if len(faces) > 0:
            face = faces[0]
            x1, y1, x2, y2 = map(int, face.bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (156, 39, 176), 2)
            
            emb = face.embedding
            emb = emb / np.linalg.norm(emb)
            
            best_match = None
            min_dist = 999
            
            for emp_id, known_emb in db_embeddings:
                dist = np.linalg.norm(emb - known_emb)
                if dist < min_dist:
                    min_dist = dist
                    best_match = emp_id
            
            # Confidence score: 1 - dist/1.5 (approximate)
            confidence = max(0, 1 - (min_dist / 1.5))
            
            if min_dist < 1.0: # Match threshold
                result = {
                    "employeeId": best_match, 
                    "confidence": round(confidence, 2),
                    "status": "success"
                }
                break
            else:
                cv2.putText(frame, "UNKNOWN PERSON", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                result["status"] = "unknown"
        else:
            cv2.putText(frame, "SCANNING...", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (156, 39, 176), 2)
        
        cv2.imshow("Face Authentication - Scan", frame)
        if cv2.waitKey(1) == 27:
            result["status"] = "cancelled"
            break

    cap.release()
    cv2.destroyAllWindows()
    return result

@app_fastapi.delete("/api/face/delete/{employeeId}")
def delete_face(employeeId: int):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get email
        cursor.execute("SELECT email FROM employees WHERE id=%s", (employeeId,))
        result = cursor.fetchone()
        
        # Reset employee
        cursor.execute(
            "UPDATE employees SET embedding=NULL, face_registered=0 WHERE id=%s",
            (employeeId,)
        )
        
        if result:
            email = result[0]
            # Reset user
            cursor.execute(
                "UPDATE users SET face_registered=0 WHERE email=%s",
                (email,)
            )
            
        db.commit()
        cursor.close()
        db.close()
        return {"status": "success", "message": "Face data deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

# =========================
# 📸 REGISTER FACE FROM BROWSER IMAGE
# =========================
import base64
from pydantic import BaseModel
from typing import Optional

class FaceImageRequest(BaseModel):
    image: str  # base64 encoded image
    employeeId: Optional[int] = None
    email: Optional[str] = None

@app_fastapi.post("/api/face/register-from-image")
def register_face_from_image(request: FaceImageRequest):
    """Accept a base64 image from the browser webcam, extract embedding, save to DB."""
    try:
        # Decode base64 image
        image_data = request.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"status": "error", "message": "Could not decode image"}
        
        logger.info(f"Received image: {frame.shape}")
        
        # Detect faces
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"status": "no_face", "message": "No face detected in the image. Please try again."}
        
        if len(faces) > 1:
            return {"status": "error", "message": "Multiple faces detected. Please ensure only your face is visible."}
        
        face = faces[0]
        emb = face.embedding
        if emb is None:
            return {"status": "error", "message": "Could not extract face features. Try again with better lighting."}
        
        # Normalize embedding
        emb = emb / (np.linalg.norm(emb) + 1e-6)
        embedding_json = json.dumps(emb.tolist())
        
        # Save to database
        db = get_db()
        cursor = db.cursor()
        
        rows_updated = 0
        
        # Update by email if provided
        if request.email:
            # Update employees table
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, request.email)
            )
            rows_updated += cursor.rowcount
            
            # Update users table
            cursor.execute(
                "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, request.email)
            )
            rows_updated += cursor.rowcount
            logger.info(f"Updated {rows_updated} rows for email: {request.email}")
        
        # Update by employeeId if provided
        elif request.employeeId:
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE id=%s",
                (embedding_json, request.employeeId)
            )
            rows_updated += cursor.rowcount
            
            # Also try to get email and update users table
            cursor.execute("SELECT email FROM employees WHERE id=%s", (request.employeeId,))
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute(
                    "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                    (embedding_json, result[0])
                )
                rows_updated += cursor.rowcount
            logger.info(f"Updated {rows_updated} rows for employeeId: {request.employeeId}")
        else:
            cursor.close()
            db.close()
            return {"status": "error", "message": "No email or employeeId provided"}
        
        db.commit()
        cursor.close()
        db.close()
        
        if rows_updated == 0:
            return {"status": "error", "message": "User not found in database"}
        
        # Get bounding box for preview feedback
        x1, y1, x2, y2 = map(int, face.bbox)
        
        return {
            "status": "success",
            "message": "Face registered successfully!",
            "faceDetected": True,
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "confidence": float(face.det_score)
        }
        
    except Exception as e:
        logger.error(f"Error in register-from-image: {e}")
        return {"status": "error", "message": f"Server error: {str(e)}"}

@app_fastapi.post("/api/face/detect")
def detect_face(request: FaceImageRequest):
    """Quick face detection check - returns if face is visible (for live preview)."""
    try:
        image_data = request.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"detected": False}
        
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"detected": False, "count": 0}
        
        face = faces[0]
        x1, y1, x2, y2 = map(int, face.bbox)
        
        return {
            "detected": True,
            "count": len(faces),
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "confidence": float(face.det_score)
        }
    except:
        return {"detected": False}

# =========================
# 🎥 STREAM SHARED CAMERA (From camera_ai_stream.py)
# =========================
from fastapi.responses import StreamingResponse
import time

def generate_frames():
    """Reads the latest_frame.jpg saved by camera_ai_stream.py to share the feed."""
    while True:
        try:
            if os.path.exists("latest_frame.jpg"):
                with open("latest_frame.jpg", "rb") as f:
                    frame = f.read()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)
        except Exception:
            pass
        time.sleep(0.05)

@app_fastapi.get("/api/face/stream")
def video_feed():
    """Endpoint to provide live camera feed to the browser without locking the hardware."""
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


# =========================
# 📸 REGISTER FROM SHARED FRAME
# =========================
class RegisterLatestFrameRequest(BaseModel):
    employeeId: Optional[int] = None
    email: Optional[str] = None

@app_fastapi.post("/api/face/register-latest-frame")
def register_latest_frame(request: RegisterLatestFrameRequest):
    """Uses the shared latest_frame.jpg to register the face, avoiding camera conflicts."""
    try:
        if not os.path.exists("latest_frame.jpg"):
            return {"status": "error", "message": "No active camera stream found."}
            
        frame = cv2.imread("latest_frame.jpg")
        if frame is None:
            return {"status": "error", "message": "Could not read camera frame."}
            
        # Detect faces
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"status": "no_face", "message": "No face detected in the camera. Please try again."}
        
        if len(faces) > 1:
            return {"status": "error", "message": "Multiple faces detected. Please ensure only your face is visible."}
        
        face = faces[0]
        emb = face.embedding
        if emb is None:
            return {"status": "error", "message": "Could not extract face features."}
        
        # Normalize embedding
        emb = emb / (np.linalg.norm(emb) + 1e-6)
        embedding_json = json.dumps(emb.tolist())
        
        db = get_db()
        cursor = db.cursor()
        rows_updated = 0
        
        if request.email:
            cursor.execute("UPDATE employees SET embedding=%s, face_registered=1 WHERE email=%s", (embedding_json, request.email))
            rows_updated += cursor.rowcount
            cursor.execute("UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s", (embedding_json, request.email))
            rows_updated += cursor.rowcount
        elif request.employeeId:
            cursor.execute("UPDATE employees SET embedding=%s, face_registered=1 WHERE id=%s", (embedding_json, request.employeeId))
            rows_updated += cursor.rowcount
            cursor.execute("SELECT email FROM employees WHERE id=%s", (request.employeeId,))
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute("UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s", (embedding_json, result[0]))
                rows_updated += cursor.rowcount
        else:
            return {"status": "error", "message": "No email or employeeId provided"}
        
        db.commit()
        cursor.close()
        db.close()
        
        if rows_updated == 0:
            return {"status": "error", "message": "User not found in database"}
            
        return {
            "status": "success",
            "message": "Face registered successfully!",
            "confidence": float(face.det_score)
        }
    except Exception as e:
        logger.error(f"Error in register-latest-frame: {e}")
        return {"status": "error", "message": f"Server error: {str(e)}"}

# =========================
# 📸 RECOGNIZE FROM SHARED FRAME (LOGIN)
# =========================
@app_fastapi.post("/api/face/recognize-latest-frame")
def recognize_latest_frame():
    """Instantly checks the latest frame against the DB for a match. Used for fast Face ID login."""
    try:
        if not os.path.exists("latest_frame.jpg"):
            return {"status": "error", "message": "No active camera stream found."}
            
        frame = cv2.imread("latest_frame.jpg")
        if frame is None:
            return {"status": "error", "message": "Could not read camera frame."}
            
        # Detect faces
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"status": "no_match"}
        
        # Get the first face
        face = faces[0]
        emb = face.embedding
        if emb is None:
            return {"status": "no_match"}
            
        # Normalize embedding
        emb = emb / (np.linalg.norm(emb) + 1e-6)
        
        # Connect to DB and fetch all registered embeddings
        db = get_db()
        cursor = db.cursor()
        
        # Fetch from both users and employees tables to ensure we don't miss anyone
        cursor.execute("SELECT email, embedding FROM users WHERE embedding IS NOT NULL")
        users_data = cursor.fetchall()
        
        cursor.execute("SELECT email, embedding FROM employees WHERE embedding IS NOT NULL")
        employees_data = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        # Combine data
        all_data = {}
        for email, emb_json in users_data:
            if email: all_data[email] = emb_json
            
        for email, emb_json in employees_data:
            if email: all_data[email] = emb_json
            
        if not all_data:
            return {"status": "no_match"}
            
        # Find best match
        best_email = None
        best_dist = 999
        
        for email, emb_json in all_data.items():
            try:
                known_emb = np.array(json.loads(emb_json))
                known_emb = known_emb / np.linalg.norm(known_emb)
                
                dist = np.linalg.norm(emb - known_emb)
                if dist < best_dist:
                    best_dist = dist
                    best_email = email
            except:
                continue
                
        # 0.85 is the threshold used in the original script
        if best_email is not None and best_dist < 0.85:
            return {"status": "success", "email": best_email, "confidence": float(1.0 - best_dist/2.0)}
        else:
            return {"status": "no_match"}
            
    except Exception as e:
        logger.error(f"Error in recognize-latest-frame: {e}")
        return {"status": "error", "message": f"Server error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000)

import cv2
import numpy as np
import json
import requests
import mysql.connector
import time
import os
import argparse
import logging
from insightface.app import FaceAnalysis
from mysql.connector import Error

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =========================
# ARGUMENTS
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--source", type=str, default="0", help="Camera source (0, 1, or URL)")
parser.add_argument("--camera_id", type=int, default=1, help="Camera ID in DB")
args = parser.parse_args()

BACKEND_UPLOAD_URL = "http://localhost:8081/api/upload"
CAMERA_ID = args.camera_id
SOURCE = args.source

if str(SOURCE).isdigit():
    SOURCE = int(SOURCE)

# =========================
# DB CONNECTION WITH ERROR HANDLING
# =========================
def connect_db():
    """Establish database connection with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root123",
                database="attendance_db"
            )
            logger.info("✓ Connexion MySQL établie")
            return db
        except Error as e:
            logger.warning(f"✗ Tentative {attempt + 1}/{max_retries} échouée: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    logger.error("✗ Impossible de se connecter à MySQL après 3 tentatives")
    return None

db = connect_db()
if db is None:
    logger.error("Application terminée: pas de connexion MySQL")
    exit(1)

cursor = db.cursor()

# =========================
# IA MODEL WITH ERROR HANDLING
# =========================
try:
    logger.info(f"🔄 Chargement du modèle IA pour Caméra {CAMERA_ID} (Source: {SOURCE})...")
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(320,320))
    logger.info("✓ Modèle IA chargé")
except Exception as e:
    logger.error(f"✗ Erreur lors du chargement du modèle IA: {e}")
    cursor.close()
    db.close()
    exit(1)

# =========================
# CHARGER LES EMPLOYÉS
# =========================
def load_employees():
    try:
        employees = {}
        
        # 1. Load from employees table
        cursor.execute("SELECT id, name, embedding FROM employees WHERE embedding IS NOT NULL")
        data_emp = cursor.fetchall()
        for emp_id, name, emb_json in data_emp:
            try:
                emb = np.array(json.loads(emb_json))
                emb = emb / np.linalg.norm(emb)
                if name: employees[name.strip()] = emb
            except Exception:
                pass

        # 2. Load from users table (managers/admins)
        cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name), embedding FROM users WHERE embedding IS NOT NULL")
        data_users = cursor.fetchall()
        for user_id, name, emb_json in data_users:
            try:
                emb = np.array(json.loads(emb_json))
                emb = emb / np.linalg.norm(emb)
                if name and name.strip() not in employees:
                    employees[name.strip()] = emb
            except Exception:
                pass

        logger.info(f"✓ {len(employees)} visage(s) chargé(s) avec embeddings")
        if len(employees) == 0:
            logger.warning("⚠️ AUCUN VISAGE AVEC EMBEDDINGS!")
        return employees
    except Error as e:
        logger.error(f"✗ Erreur lors du chargement des visages: {e}")
        return {}

employees = load_employees()

# =========================
# CAPTURE VIDÉO UNIVERSELLE
# =========================
try:
    cap = cv2.VideoCapture(SOURCE)
    
    if not cap.isOpened():
        logger.error(f"❌ Impossible d'ouvrir la source: {SOURCE}")
        exit(1)
    
    logger.info(f"✓ Source vidéo ouverte: {SOURCE}")
except Exception as e:
    logger.error(f"✗ Erreur lors de l'ouverture de la source: {e}")
    exit(1)

logger.info(f"🚀 SYSTÈME IA DÉMARRÉ - Caméra {CAMERA_ID}, Source: {SOURCE}")

last_upload_time = 0
UPLOAD_INTERVAL = 1.0 
frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("⚠️ Flux interrompu ou terminé.")
            break

        frame_count += 1
        display_frame = cv2.resize(frame, (640, 480))

        # Save latest frame for face registration (shared with FastAPI)
        try:
            cv2.imwrite("latest_frame.jpg", display_frame)
        except:
            pass
        
        try:
            faces = app.get(display_frame)
        except Exception as e:
            logger.warning(f"Erreur détection visages: {e}")
            faces = []

        for face in faces:
            try:
                emb = face.embedding
                emb = emb / np.linalg.norm(emb)

                best_name = "INCONNU"
                min_dist = 999

                for name, known_emb in employees.items():
                    dist = np.linalg.norm(emb - known_emb)
                    if dist < min_dist:
                        min_dist = dist
                        best_name = name

                # ✅ Seuil ajusté à 0.85 pour correspondre au login
                if min_dist > 0.85:
                    best_name = "INCONNU"
                    logger.debug(f"Distance trop haute: {min_dist:.3f} > 0.85")
                else:
                    logger.info(f"Reconnu: {best_name} (distance: {min_dist:.3f})")

                x1, y1, x2, y2 = map(int, face.bbox)
                color = (0, 255, 0) if best_name != "INCONNU" else (0, 0, 255)
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_frame, best_name, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            except Exception as e:
                logger.warning(f"Erreur traitement visage: {e}")
                continue

        # 🎥 ENVOI VERS DASHBOARD
        current_time = time.time()
        if current_time - last_upload_time > UPLOAD_INTERVAL:
            try:
                cv2.imwrite("temp_stream.jpg", display_frame)
                
                with open("temp_stream.jpg", "rb") as f:
                    files = {'file': f}
                    data = {'cameraId': str(CAMERA_ID)}
                    response = requests.post(BACKEND_UPLOAD_URL, files=files, data=data, timeout=5)
                    if response.status_code == 200:
                        last_upload_time = current_time
                    else:
                        logger.warning(f"Erreur serveur: {response.status_code}")
            except requests.exceptions.Timeout:
                logger.warning("⚠️ Timeout lors de l'envoi au serveur")
            except Exception as e:
                logger.warning(f"⚠️ Erreur envoi vers serveur: {e}")

        # Optionnel: cv2.imshow si besoin en local
        cv2.imshow(f"Cam {CAMERA_ID}", display_frame)
        if cv2.waitKey(1) == 27:
            break

except KeyboardInterrupt:
    logger.info("Arrêt demandé par l'utilisateur")
finally:
    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    db.close()
    logger.info("Ressources libérées")

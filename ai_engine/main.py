import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import time
import cv2
import numpy as np
from typing import Optional
from pydantic import BaseModel

from ai_engine.core.engine import Engine
from ai_engine.core.config import Config
from ai_engine.core.model_manager import ModelManager
from ai_engine.services.db_service import DatabaseService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SOC_API")

app = FastAPI(title="SOC AI Engine API", description="Moteur d'Intelligence Artificielle Centralisé")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

soc_engine = Engine()

@app.on_event("startup")
async def startup_event():
    logger.info("✓ Engine online")
    soc_engine.start()
    # Pre-warm AI models in background so the first face scan is instant
    import threading
    def _preload():
        logger.info("⏳ Pré-chargement InsightFace + YOLOv8 en arrière-plan...")
        ModelManager().get_face_app()
        ModelManager().get_yolo_model()
        logger.info("✓ Modèles IA prêts en mémoire.")
    threading.Thread(target=_preload, daemon=True).start()

@app.on_event("shutdown")
async def shutdown_event():
    soc_engine.stop()

# =========================
# FLUX VIDEO WEBRTC / MJPEG
# =========================

def generate_frames(camera_id: int):
    """Générateur de flux vidéo en direct (MJPEG) directement depuis la RAM"""
    while True:
        frame_bytes = soc_engine.get_camera_frame(camera_id)
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)

@app.get("/api/camera/{camera_id}/stream")
async def video_feed(camera_id: int):
    """Point d'accès pour voir la caméra en direct sur Angular"""
    if camera_id not in soc_engine.camera_threads:
        logger.error(f"❌ Camera {camera_id} unavailable")
        raise HTTPException(status_code=404, detail="Caméra non active ou non trouvée.")

    logger.info(f"✓ Stream started for camera {camera_id}")
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/engine/status")
def get_status():
    """Vérifier l'état du moteur"""
    return {
        "status": "online" if soc_engine.running else "offline",
        "active_cameras": list(soc_engine.camera_threads.keys())
    }


# =========================
# 🎥 FACE LOGIN — STREAM
# =========================

def _get_first_camera_frame() -> Optional[bytes]:
    """Retourne le dernier JPEG de la première caméra active."""
    for cid, thread in soc_engine.camera_threads.items():
        frame_bytes = thread.get_latest_jpeg()
        if frame_bytes:
            return frame_bytes
    return None

def _generate_face_stream():
    """Flux MJPEG sur la première caméra active (pour le login biométrique)."""
    while True:
        frame_bytes = _get_first_camera_frame()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)

@app.get("/api/face/stream")
async def face_stream():
    """Flux vidéo pour la page de login — utilise la première caméra active."""
    if not soc_engine.camera_threads:
        raise HTTPException(status_code=503, detail="Aucune caméra active.")
    return StreamingResponse(
        _generate_face_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# 🔍 FACE LOGIN — RECONNAISSANCE
# =========================

@app.post("/api/face/recognize-latest-frame")
def recognize_latest_frame():
    """
    Lit le dernier frame de la première caméra active,
    détecte le visage et compare avec les embeddings de la BD.
    Retourne : { status, email, confidence } ou { status: 'no_match' }
    """
    # 1. Récupérer le dernier frame
    frame_bytes = _get_first_camera_frame()
    if frame_bytes is None:
        logger.warning("recognize-latest-frame: aucun frame disponible")
        return {"status": "error", "message": "Aucune caméra active. Vérifiez que le SOC Engine est bien démarré."}

    # 2. Décoder l'image JPEG
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"status": "error", "message": "Impossible de décoder le frame caméra."}

    # 3. Détection du visage
    face_app = ModelManager().get_face_app()
    if face_app is None:
        return {"status": "error", "message": "Modèle de reconnaissance faciale non chargé."}

    faces = face_app.get(frame)
    if not faces:
        logger.info("recognize-latest-frame: aucun visage détecté")
        return {"status": "no_match"}

    face = faces[0]
    emb = face.embedding
    if emb is None:
        return {"status": "no_match"}

    # 4. Normalisation de l'embedding
    emb = emb / (np.linalg.norm(emb) + 1e-6)

    # 5. Chargement des embeddings depuis la BD
    all_embeddings = DatabaseService.load_all_embeddings()
    if not all_embeddings:
        logger.warning("recognize-latest-frame: aucun embedding en BD")
        return {"status": "no_match"}

    # 6. Trouver la meilleure correspondance
    best_email = None
    best_dist = 999.0

    for email, known_emb in all_embeddings.items():
        dist = float(np.linalg.norm(emb - known_emb))
        if dist < best_dist:
            best_dist = dist
            best_email = email

    logger.info(f"recognize-latest-frame: meilleur match={best_email}, distance={best_dist:.3f}")

    if best_email is not None and best_dist < 0.85:
        return {
            "status": "success",
            "email": best_email,
            "confidence": round(float(1.0 - best_dist / 2.0), 3)
        }

    return {"status": "no_match"}


# =========================
# 📸 FACE SETUP — ENREGISTREMENT
# =========================

class RegisterLatestFrameRequest(BaseModel):
    employeeId: Optional[int] = None
    email: Optional[str] = None

@app.post("/api/face/register-latest-frame")
def register_latest_frame(request: RegisterLatestFrameRequest):
    """
    Lit le dernier frame de la première caméra active,
    extrait l'embedding et le sauvegarde en BD.
    """
    import json

    if not request.email and not request.employeeId:
        return {"status": "error", "message": "Paramètre email ou employeeId requis."}

    # 1. Récupérer le dernier frame
    frame_bytes = _get_first_camera_frame()
    if frame_bytes is None:
        return {"status": "error", "message": "Aucune caméra active. Vérifiez que le SOC Engine est bien démarré."}

    # 2. Décoder l'image
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"status": "error", "message": "Impossible de décoder le frame caméra."}

    # 3. Détection du visage
    face_app = ModelManager().get_face_app()
    if face_app is None:
        return {"status": "error", "message": "Modèle non chargé."}

    faces = face_app.get(frame)
    if not faces:
        return {"status": "no_face", "message": "Aucun visage détecté. Placez-vous face à la caméra."}
    if len(faces) > 1:
        return {"status": "error", "message": "Plusieurs visages détectés. Assurez-vous d'être seul."}

    face = faces[0]

    # Vérifier la confiance de détection (visage trop flou ou de profil)
    if hasattr(face, 'det_score') and face.det_score is not None:
        if float(face.det_score) < 0.65:
            return {"status": "no_face", "message": "Visage mal détecté. Regardez directement la caméra et assurez-vous d'être bien éclairé."}

    # Vérifier l'orientation du visage (yaw = rotation gauche/droite)
    if hasattr(face, 'pose') and face.pose is not None:
        try:
            yaw = abs(float(face.pose[1]))
            if yaw > 35:
                return {"status": "no_face", "message": "Visage trop tourné. Regardez directement la caméra (de face)."}
        except Exception:
            pass

    emb = face.embedding
    if emb is None:
        return {"status": "error", "message": "Impossible d'extraire les caractéristiques du visage."}

    # 4. Normalisation et sérialisation
    emb = emb / (np.linalg.norm(emb) + 1e-6)
    embedding_json = json.dumps(emb.tolist())

    # 5. Sauvegarde en BD
    conn = DatabaseService.get_connection()
    if not conn:
        return {"status": "error", "message": "Erreur de connexion à la base de données."}

    try:
        cursor = conn.cursor()
        rows_updated = 0

        if request.email:
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, request.email)
            )
            rows_updated += cursor.rowcount
            cursor.execute(
                "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, request.email)
            )
            rows_updated += cursor.rowcount
            logger.info(f"register-latest-frame: {rows_updated} lignes mises à jour pour email={request.email}")

        elif request.employeeId:
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE id=%s",
                (embedding_json, request.employeeId)
            )
            rows_updated += cursor.rowcount
            # Sync users table
            cursor.execute("SELECT email FROM employees WHERE id=%s", (request.employeeId,))
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute(
                    "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                    (embedding_json, result[0])
                )
                rows_updated += cursor.rowcount
            logger.info(f"register-latest-frame: {rows_updated} lignes mises à jour pour employeeId={request.employeeId}")

        conn.commit()
        cursor.close()

        if rows_updated == 0:
            return {"status": "error", "message": "Utilisateur introuvable en base de données."}

        return {
            "status": "success",
            "message": "Visage enregistré avec succès !",
            "confidence": float(face.det_score)
        }

    except Exception as e:
        logger.error(f"register-latest-frame DB error: {e}")
        return {"status": "error", "message": f"Erreur base de données : {str(e)}"}
    finally:
        conn.close()


# =========================
# 🌐 STATELESS FACE ENDPOINTS (browser-captured image)
# =========================
# Ces endpoints ne dépendent PAS du SOC Engine ni des camera_threads.
# Ils reçoivent directement une image envoyée depuis le navigateur (getUserMedia)
# → robuste, scalable, fonctionne depuis n'importe quel poste.

def _decode_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Décode une image JPEG/PNG en frame OpenCV BGR. Retourne None si invalide."""
    if not image_bytes:
        return None
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.error(f"_decode_image error: {e}")
        return None


@app.post("/api/face/recognize")
async def recognize_face_from_image(image: UploadFile = File(...)):
    """
    Reconnaissance faciale STATELESS.
    Reçoit une image (multipart/form-data) capturée par le navigateur,
    extrait l'embedding et compare avec ceux de la BD.

    Retourne : { status, email, confidence } ou { status: 'no_face' | 'no_match' }
    """
    # 1. Lire et décoder l'image
    image_bytes = await image.read()
    frame = _decode_image(image_bytes)
    if frame is None:
        return {"status": "error", "message": "Image invalide ou illisible."}

    # 2. Détection du visage
    face_app = ModelManager().get_face_app()
    if face_app is None:
        return {"status": "error", "message": "Modèle de reconnaissance faciale non chargé."}

    faces = face_app.get(frame)
    if not faces:
        logger.info("/api/face/recognize: aucun visage détecté")
        return {"status": "no_face", "message": "Aucun visage détecté."}

    # On prend le visage de plus grande surface (le plus proche de la caméra)
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    # Vérifier qualité minimale
    if hasattr(face, 'det_score') and face.det_score is not None:
        if float(face.det_score) < 0.55:
            return {"status": "no_face", "message": "Visage mal détecté. Regardez directement la caméra."}

    emb = face.embedding
    if emb is None:
        return {"status": "no_match"}

    # 3. Normalisation
    emb = emb / (np.linalg.norm(emb) + 1e-6)

    # 4. Chargement des embeddings (TODO: cacher pour performance)
    all_embeddings = DatabaseService.load_all_embeddings()
    if not all_embeddings:
        logger.warning("/api/face/recognize: aucun embedding en BD")
        return {"status": "no_match", "message": "Aucun visage enregistré en base."}

    # 5. Meilleure correspondance (distance L2 — embeddings normalisés)
    best_email = None
    best_dist = 999.0
    for email, known_emb in all_embeddings.items():
        dist = float(np.linalg.norm(emb - known_emb))
        if dist < best_dist:
            best_dist = dist
            best_email = email

    logger.info(f"/api/face/recognize: match={best_email}, dist={best_dist:.3f}")

    # Seuil de décision (ajustable)
    THRESHOLD = 0.85
    if best_email is not None and best_dist < THRESHOLD:
        return {
            "status": "success",
            "email": best_email,
            "confidence": round(float(1.0 - best_dist / 2.0), 3),
            "distance": round(best_dist, 3)
        }

    return {"status": "no_match", "message": "Visage non reconnu."}


@app.post("/api/face/register")
async def register_face_from_image(
    image: UploadFile = File(...),
    email: Optional[str] = Form(None),
    employeeId: Optional[int] = Form(None)
):
    """
    Enregistrement d'embedding STATELESS.
    Reçoit une image capturée par le navigateur + email ou employeeId,
    et stocke l'embedding dans la BD.
    """
    import json

    if not email and not employeeId:
        return {"status": "error", "message": "Paramètre email ou employeeId requis."}

    # 1. Lire et décoder l'image
    image_bytes = await image.read()
    frame = _decode_image(image_bytes)
    if frame is None:
        return {"status": "error", "message": "Image invalide ou illisible."}

    # 2. Détection du visage
    face_app = ModelManager().get_face_app()
    if face_app is None:
        return {"status": "error", "message": "Modèle non chargé."}

    faces = face_app.get(frame)
    if not faces:
        return {"status": "no_face", "message": "Aucun visage détecté. Placez-vous face à la caméra."}
    if len(faces) > 1:
        return {"status": "error", "message": "Plusieurs visages détectés. Assurez-vous d'être seul."}

    face = faces[0]
    emb = face.embedding
    if emb is None:
        return {"status": "error", "message": "Impossible d'extraire les caractéristiques."}

    # 3. Normalisation et sérialisation
    emb = emb / (np.linalg.norm(emb) + 1e-6)
    embedding_json = json.dumps(emb.tolist())

    # 4. Sauvegarde en BD
    conn = DatabaseService.get_connection()
    if not conn:
        return {"status": "error", "message": "Erreur de connexion à la base de données."}

    try:
        cursor = conn.cursor()
        rows_updated = 0

        if email:
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, email)
            )
            rows_updated += cursor.rowcount
            cursor.execute(
                "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                (embedding_json, email)
            )
            rows_updated += cursor.rowcount
        elif employeeId:
            cursor.execute(
                "UPDATE employees SET embedding=%s, face_registered=1 WHERE id=%s",
                (embedding_json, employeeId)
            )
            rows_updated += cursor.rowcount
            cursor.execute("SELECT email FROM employees WHERE id=%s", (employeeId,))
            row = cursor.fetchone()
            if row and row[0]:
                cursor.execute(
                    "UPDATE users SET embedding=%s, face_registered=1 WHERE email=%s",
                    (embedding_json, row[0])
                )
                rows_updated += cursor.rowcount

        conn.commit()
        cursor.close()

        if rows_updated == 0:
            return {"status": "error", "message": "Utilisateur introuvable en base de données."}

        return {
            "status": "success",
            "message": "Visage enregistré avec succès.",
            "confidence": float(face.det_score)
        }

    except Exception as e:
        logger.error(f"/api/face/register DB error: {e}")
        return {"status": "error", "message": f"Erreur base de données : {str(e)}"}
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info(f"Démarrage du serveur sur le port {Config.PORT}...")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

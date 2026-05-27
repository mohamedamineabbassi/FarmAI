import cv2
import numpy as np
import logging
from ai_engine.modes.base_mode import BaseMode
from ai_engine.core.model_manager import ModelManager
from ai_engine.services.db_service import DatabaseService
from ai_engine.core.config import Config
from ai_engine.alerts.alert_manager import AlertManager
from ai_engine.core.config import Config

logger = logging.getLogger(__name__)

class FaceMode(BaseMode):
    def __init__(self, camera_id: int):
        super().__init__(camera_id)
        self.face_app = ModelManager().get_face_app()
        self.embeddings = DatabaseService.load_all_embeddings()
        logger.info(f"Mode FACE_RECOGNITION initialisé pour caméra {camera_id}.")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.current_detections = []
        if self.face_app is None:
            return frame

        try:
            faces = self.face_app.get(frame)
            
            for face in faces:
                emb = face.embedding
                if emb is None: continue
                
                emb = emb / np.linalg.norm(emb)
                best_match = "INCONNU"
                min_dist = 999
                
                for email, known_emb in self.embeddings.items():
                    dist = np.linalg.norm(emb - known_emb)
                    if dist < min_dist:
                        min_dist = dist
                        best_match = email

                # Tracer Bounding Box
                x1, y1, x2, y2 = map(int, face.bbox)
                
                if min_dist <= Config.FACE_MATCH_THRESHOLD:
                    color = (0, 255, 0) # Vert
                    label = f"USER: {best_match.split('@')[0]}"
                else:
                    color = (0, 0, 255) # Rouge
                    label = "UNKNOWN"
                    # Envoyer l'alerte intrusion via le AlertManager
                    # Utilisation d'un hash basé sur la bbox temporairement comme tracking_id
                    tracking_id_tmp = f"face_{x1}_{y1}"
                    AlertManager.trigger_alert(
                        alert_type="UNKNOWN_PERSON",
                        camera_id=self.camera_id,
                        tracking_id=tracking_id_tmp,
                        frame=frame
                    )

                # Ajouter à la liste des détections pour le Line Crossing
                self.current_detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "label": label
                })

                # Dessiner HUD
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.rectangle(frame, (x1, y1 - 30), (x2, y1), color, -1)
                cv2.putText(frame, label, (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
        except Exception as e:
            logger.warning(f"Erreur traitement FaceMode: {e}")

        return frame

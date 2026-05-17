import cv2
import numpy as np
import logging
from ai_engine.modes.base_mode import BaseMode
from ai_engine.core.model_manager import ModelManager

logger = logging.getLogger(__name__)

class IntrusionMode(BaseMode):
    def __init__(self, camera_id: int):
        super().__init__(camera_id)
        self.yolo = ModelManager().get_yolo_model()
        logger.info(f"Mode INTRUSION initialisé pour caméra {camera_id}.")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        if self.yolo is None:
            return frame

        try:
            results = self.yolo(frame, classes=[0], verbose=False) # 0 = person
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf < 0.5: continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Dessiner HUD Alerte Rouge Clignotante (simplifié ici en rouge fixe)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.rectangle(frame, (x1, y1 - 40), (x2, y1), (0, 0, 255), -1)
                    cv2.putText(frame, "INTRUSION DETECTEE !", (x1 + 5, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # TODO: Envoyer alerte au service d'alerte (Websocket/DB)
                    
        except Exception as e:
            logger.warning(f"Erreur traitement IntrusionMode: {e}")

        # Ajouter un HUD Global
        cv2.putText(frame, "SYSTEME ARME - INTRUSION", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return frame

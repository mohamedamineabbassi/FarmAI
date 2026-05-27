import cv2
import numpy as np
import logging
import traceback
from ai_engine.modes.base_mode import BaseMode
from ai_engine.core.model_manager import ModelManager
from ai_engine.alerts.alert_manager import AlertManager

logger = logging.getLogger(__name__)

class RoleMode(BaseMode):
    def __init__(self, camera_id: int):
        super().__init__(camera_id)
        self.yolo = ModelManager().get_yolo_model()
        self.last_alert_time = 0
        logger.info(f"✓ Mode ROLE_DETECTION initialisé pour caméra {camera_id}.")

    def determine_color(self, img_crop: np.ndarray) -> str:
        """Détecte la couleur dominante du vêtement (Haut)"""
        if img_crop.size == 0: return "UNKNOWN"
        
        # Prendre la partie supérieure (torse)
        h, w = img_crop.shape[:2]
        torso = img_crop[0:int(h/2), 0:w]
        total_pixels = (h/2) * w
        
        if total_pixels == 0:
            return "UNKNOWN"
            
        try:
            hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
        except Exception as e:
            logger.error(f"❌ Erreur de conversion BGR vers HSV: {e}")
            return "UNKNOWN"
        
        # --- RÈGLES STRICTES HSV ---
        
        # 1. BLANC (Saturation faible, Luminosité forte)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        mask_white = cv2.inRange(hsv, lower_white, upper_white)
        
        # 2. ORANGE (Hue 5 à 25, Saturation forte, Luminosité moyenne-forte)
        lower_orange = np.array([5, 150, 150])
        upper_orange = np.array([25, 255, 255])
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)

        # 3. BLEU (Hue 90 à 130, Saturation forte, Luminosité moyenne-forte)
        lower_blue = np.array([90, 150, 100])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        # Calcul des pourcentages
        pct_white = (cv2.countNonZero(mask_white) / total_pixels) * 100
        pct_orange = (cv2.countNonZero(mask_orange) / total_pixels) * 100
        pct_blue = (cv2.countNonZero(mask_blue) / total_pixels) * 100
        
        percentages = {
            "BLANC": pct_white,
            "ORANGE": pct_orange,
            "BLEU": pct_blue
        }
        
        # Trouver la couleur dominante
        dominant_color = max(percentages, key=percentages.get)
        max_pct = percentages[dominant_color]
        
        # Si la couleur dominante représente moins de 10% du torse, c'est probablement "autre chose"
        if max_pct < 10.0:
            return "UNKNOWN"
            
        return dominant_color

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.current_detections = []
        if self.yolo is None:
            return frame

        try:
            # Protection contre les frames vides
            if frame is None or frame.size == 0:
                return frame

            results = self.yolo(frame, classes=[0], verbose=False) # 0 = person
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    if conf < 0.5: continue
                    
                    crop = frame[y1:y2, x1:x2]
                    
                    # 1. Extraction et conversion des couleurs
                    color = self.determine_color(crop)
                    
                    # 2. Classification selon la règle stricte
                    if color == "BLANC":
                        role = "MEDECIN"
                        color_box = (255, 255, 255) # Blanc BGR
                        text_color = (0, 0, 0)
                    elif color == "ORANGE":
                        role = "EMPLOYE"
                        color_box = (0, 165, 255) # Orange BGR
                        text_color = (255, 255, 255)
                    elif color == "BLEU":
                        role = "ELECTRICIEN"
                        color_box = (255, 0, 0) # Bleu BGR
                        text_color = (255, 255, 255)
                    else:
                        role = "INTRUS / UNKNOWN ROLE"
                        color_box = (0, 0, 255) # Rouge BGR
                        text_color = (255, 255, 255)
                        
                        # ALERTE BACKEND avec Cooldown local
                        import time
                        current_time = time.time()
                        if current_time - self.last_alert_time >= 10:
                            AlertManager.trigger_alert(
                                alert_type="UNKNOWN_ROLE",
                                camera_id=self.camera_id,
                                tracking_id="unknown_role_general", # ID générique
                                frame=frame
                            )
                            self.last_alert_time = current_time
                        
                    # Ajouter à la liste des détections pour le Line Crossing
                    self.current_detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "label": role
                    })
                        
                    # 3. Rendu de l'overlay HUD
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_box, 2)
                    cv2.rectangle(frame, (x1, y1 - 30), (x2, y1), color_box, -1)
                    cv2.putText(frame, f"ROLE: {role}", (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
                    
        except Exception as e:
            logger.error(f"❌ Erreur critique dans RoleMode (le stream continuera): {e}")
            logger.debug(traceback.format_exc())

        return frame

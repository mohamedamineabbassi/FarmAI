import cv2
import threading
import time
import logging

from ai_engine.modes.face_mode import FaceMode
from ai_engine.modes.role_mode import RoleMode
from ai_engine.modes.intrusion_mode import IntrusionMode
from ai_engine.services.db_service import DatabaseService
from ai_engine.services.stream_manager import StreamManager
from ai_engine.core.line_crossing import LineCrossingLayer

logger = logging.getLogger(__name__)

class CameraThread(threading.Thread):
    """
    Thread dédié à une caméra logique (camera_id). 
    Récupère les frames depuis le StreamManager partagé et applique l'IA.
    """
    def __init__(self, camera_id: int):
        super().__init__()
        self.camera_id = camera_id
        self.camera_info = DatabaseService.get_camera_info(camera_id)
        self.running = True
        self.latest_frame = None
        self.mode_instance = None
        self.source = self.camera_info.get("source", "0") if self.camera_info else "0"
        
        # Enregistrer la source physique
        self.stream_thread = StreamManager().register_source(self.source)
        
        # Couche additive Line Crossing
        self.line_crossing_layer = LineCrossingLayer()
        self.enable_line_crossing = False
        
        self.setup_mode()

    def setup_mode(self):
        if not self.camera_info:
            logger.error(f"Caméra {self.camera_id} non trouvée dans la BD.")
            return

        ai_type = self.camera_info.get("ai_type")
        if not ai_type or ai_type == "NONE":
            ai_type = "FACE"
            logger.info(f"Fallback: Mode IA par défaut (FACE) appliqué à la caméra {self.camera_id}")
        
        # Nettoyer l'ancienne instance si elle existait (libère la mémoire potentiellement)
        self.mode_instance = None
        
        if ai_type == "FACE_RECOGNITION" or ai_type == "FACE":
            self.enable_line_crossing = True
            self.mode_instance = FaceMode(self.camera_id)
        elif ai_type == "ROLE_DETECTION" or ai_type == "COLOR":
            self.enable_line_crossing = False
            self.mode_instance = RoleMode(self.camera_id)
        elif ai_type == "INTRUSION":
            self.enable_line_crossing = False
            self.mode_instance = IntrusionMode(self.camera_id)
        else:
            self.enable_line_crossing = False
            self.mode_instance = None
            logger.warning(f"Aucun mode IA ou mode par défaut pour la caméra {self.camera_id} ({ai_type})")

    def update_mode(self, new_ai_type: str):
        """Met à jour le mode IA à la volée sans couper le flux."""
        logger.info(f"🔄 Hot-Swap IA Mode pour caméra {self.camera_id} -> {new_ai_type}")
        if self.camera_info:
            self.camera_info["ai_type"] = new_ai_type
        self.setup_mode()

    def run(self):
        if not self.camera_info: return
        
        logger.info(f"✓ Camera logic connected (ID: {self.camera_id}, Source: {self.source})")

        while self.running:
            # Récupérer la dernière frame depuis le singleton physique
            frame = self.stream_thread.get_frame()
            
            if frame is None:
                # Si pas de frame, on attend
                time.sleep(0.1)
                continue

            # Appliquer l'IA selon le mode sélectionné
            if self.mode_instance:
                frame = self.mode_instance.process_frame(frame)
                
                # Récupérer les détections de l'IA (si elles existent)
                detections = getattr(self.mode_instance, 'current_detections', [])
                
                # Appliquer la couche additive Line Crossing
                if self.enable_line_crossing:
                    frame = self.line_crossing_layer.process(frame, detections, camera_id=self.camera_id)
            else:
                # Si aucun mode, juste écrire le timestamp (Mode Passif)
                cv2.putText(frame, "MODE PASSIF", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Stocker en RAM pour le streaming web
            self.latest_frame = frame
            
            # Reposer un peu le CPU (approx 30 fps)
            time.sleep(0.03)

        # Désenregistrer la source physique
        StreamManager().unregister_source(self.source)
        logger.info(f"⏹ Arrêt thread logique caméra {self.camera_id}")

    def stop(self):
        self.running = False

    def get_latest_jpeg(self):
        """Encode the frame to JPEG for web streaming."""
        if self.latest_frame is None: return None
        ret, buffer = cv2.imencode('.jpg', self.latest_frame)
        if not ret: return None
        return buffer.tobytes()

import logging
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton pour charger les modèles d'IA lourds une seule fois en RAM/VRAM.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._init_models()
        return cls._instance

    def _init_models(self):
        self.face_app = None
        self.yolo_model = None

    def get_face_app(self):
        if self.face_app is None:
            logger.info("🔄 Chargement du modèle InsightFace (buffalo_l) en mémoire...")
            try:
                self.face_app = FaceAnalysis(name='buffalo_l')
                self.face_app.prepare(ctx_id=0, det_size=(320, 320))
                logger.info("✓ InsightFace chargé avec succès.")
            except Exception as e:
                logger.error(f"✗ Erreur lors du chargement de InsightFace: {e}")
        return self.face_app

    def get_yolo_model(self):
        if self.yolo_model is None:
            logger.info("🔄 Chargement du modèle YOLOv8 en mémoire...")
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("✓ YOLOv8 chargé avec succès.")
            except Exception as e:
                logger.error(f"✗ Erreur lors du chargement de YOLOv8: {e}")
        return self.yolo_model

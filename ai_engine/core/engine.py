import logging
import threading
import time
from typing import Dict

from ai_engine.services.db_service import DatabaseService
from ai_engine.services.camera_service import CameraThread
from ai_engine.core.model_manager import ModelManager

logger = logging.getLogger(__name__)

class Engine:
    """
    Moteur principal SOC. Orchestre les threads de caméras.
    """
    def __init__(self):
        self.camera_threads: Dict[int, CameraThread] = {}
        self.running = False

    def start(self):
        logger.info("🚀 Démarrage du moteur SOC AI...")
        
        # 1. Initialiser le pool de connexion DB
        DatabaseService.init_pool()
        
        # 2. Précharger les modèles en RAM (Singleton)
        ModelManager().get_face_app()
        ModelManager().get_yolo_model()
        
        self.running = True
        
        # Thread de surveillance pour détecter les nouvelles caméras ou les changements de modes
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()

    def stop(self):
        logger.info("⏹ Arrêt du moteur SOC AI...")
        self.running = False
        for cam_id, thread in self.camera_threads.items():
            thread.stop()
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

    def _monitor_loop(self):
        """Vérifie la base de données périodiquement pour ajouter/supprimer/mettre à jour les caméras"""
        while self.running:
            try:
                conn = DatabaseService.get_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id, status, type FROM cameras")
                    cameras = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    active_cam_ids = set()

                    for cam in cameras:
                        cam_id = cam['id']
                        status = cam['status']
                        ai_type = cam.get('type', None)

                        if status == 'ACTIVE' or status == 'ON':
                            active_cam_ids.add(cam_id)
                            
                            if cam_id not in self.camera_threads:
                                # Nouvelle caméra
                                logger.info(f"➕ Nouvelle caméra détectée ({cam_id}). Démarrage...")
                                thread = CameraThread(cam_id)
                                thread.start()
                                self.camera_threads[cam_id] = thread
                            else:
                                # Vérifier si le mode a changé
                                current_thread = self.camera_threads[cam_id]
                                current_mode = current_thread.camera_info.get('ai_type')
                                if current_mode != ai_type:
                                    logger.info(f"🔄 Changement de mode détecté pour {cam_id}: {current_mode} -> {ai_type}")
                                    # Mise à jour à chaud sans redémarrer le thread logique (et sans couper le stream)
                                    current_thread.update_mode(ai_type)

                    # Arrêter les caméras qui ne sont plus actives ou supprimées
                    for cam_id in list(self.camera_threads.keys()):
                        if cam_id not in active_cam_ids:
                            logger.info(f"➖ Caméra {cam_id} désactivée. Arrêt du thread...")
                            self.camera_threads[cam_id].stop()
                            del self.camera_threads[cam_id]

            except Exception as e:
                logger.error(f"Erreur dans la boucle de monitoring: {e}")

            time.sleep(3) # Vérifie toutes les 3 secondes

    def get_camera_frame(self, camera_id: int):
        if camera_id in self.camera_threads:
            return self.camera_threads[camera_id].get_latest_jpeg()
        return None

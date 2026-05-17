import cv2
import threading
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class StreamThread(threading.Thread):
    """
    Thread dédié à une source vidéo physique (ex: 0, 1, rtsp://...).
    Il lit en continu les frames et les stocke dans un buffer partagé.
    """
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.running = True
        self.latest_frame = None
        self.lock = threading.Lock()
        
        # Convertir '0' en int(0)
        if isinstance(self.source, str) and self.source.isdigit():
            self.source = int(self.source)

    def run(self):
        logger.info(f"▶ Démarrage capture physique (Source: {self.source})")
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            logger.error(f"❌ Impossible d'ouvrir la source {self.source}")
            self.running = False

        while self.running:
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"❌ Perte de flux (Source: {self.source}). Reconnexion dans 5s...")
                time.sleep(5)
                # Tenter de rouvrir
                cap.release()
                cap = cv2.VideoCapture(self.source)
                continue
            
            with self.lock:
                self.latest_frame = frame
            
            # Reposer un peu le CPU (approx 30 fps)
            time.sleep(0.03)

        cap.release()
        logger.info(f"⏹ Arrêt capture physique (Source: {self.source})")

    def get_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None

    def stop(self):
        self.running = False


class StreamManager:
    """
    Singleton pour gérer les flux vidéos.
    Empêche d'ouvrir plusieurs cv2.VideoCapture sur la même source (webcam lock).
    Utilise le reference counting pour fermer le flux s'il n'est plus utilisé.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StreamManager, cls).__new__(cls)
                cls._instance.streams: Dict[str, StreamThread] = {}
                cls._instance.ref_counts: Dict[str, int] = {}
        return cls._instance

    def register_source(self, source) -> StreamThread:
        """Enregistre une source et retourne le thread associé."""
        # Standardiser la clé
        source_key = str(source)
        
        with self._lock:
            if source_key not in self.streams:
                # Créer un nouveau thread de stream
                logger.info(f"➕ Nouvelle source physique enregistrée: {source_key}")
                thread = StreamThread(source)
                thread.start()
                self.streams[source_key] = thread
                self.ref_counts[source_key] = 1
            else:
                # Partager le flux existant
                self.ref_counts[source_key] += 1
                logger.info(f"🔗 Partage source physique existante: {source_key} (Utilisateurs: {self.ref_counts[source_key]})")
            
            return self.streams[source_key]

    def unregister_source(self, source):
        """Désenregistre une source. Arrête le thread si plus aucune caméra ne l'utilise."""
        source_key = str(source)
        
        with self._lock:
            if source_key in self.ref_counts:
                self.ref_counts[source_key] -= 1
                logger.info(f"➖ Libération source physique: {source_key} (Reste: {self.ref_counts[source_key]} utilisateurs)")
                
                if self.ref_counts[source_key] <= 0:
                    logger.info(f"🗑️ Plus aucun utilisateur pour {source_key}. Fermeture physique du flux...")
                    thread = self.streams.pop(source_key)
                    self.ref_counts.pop(source_key)
                    thread.stop()
                    # Pas de join() ici pour ne pas bloquer

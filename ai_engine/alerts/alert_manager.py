import time
import cv2
import base64
import requests
import logging
import os
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AlertManager:
    _instance = None
    _cooldowns = {}
    _executor = ThreadPoolExecutor(max_workers=5)
    
    # URL du backend Spring Boot (ajuster si besoin)
    # Dans un environnement de prod, ceci devrait être dans un fichier de config
    BACKEND_URL = "http://localhost:8081/api/alerts/ai-detection"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlertManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def trigger_alert(cls, alert_type, camera_id, tracking_id=None, frame=None, location="Camera"):
        """
        Déclenche une alerte vers le backend Spring Boot.
        Gère le cooldown anti-spam (10 secondes par type/id).
        L'envoi HTTP et l'encodage image se font en asynchrone (ThreadPool).
        """
        # 1. Vérification Anti-Spam (10 secondes)
        cooldown_key = f"{camera_id}_{alert_type}_{tracking_id}"
        
        current_time = time.time()
        last_time = cls._cooldowns.get(cooldown_key, 0)
        
        if current_time - last_time < 10.0:
            return # Cooldown actif, on ignore silencieusement (anti-spam)
            
        # Mise à jour du cooldown
        cls._cooldowns[cooldown_key] = current_time
        
        # 2. Préparation et Envoi Asynchrone
        # On copie la frame pour éviter qu'elle soit modifiée par le thread principal pendant l'encodage
        frame_copy = frame.copy() if frame is not None else None
        
        cls._executor.submit(cls._send_alert_async, alert_type, camera_id, tracking_id, frame_copy, location)

    @classmethod
    def _send_alert_async(cls, alert_type, camera_id, tracking_id, frame, location):
        try:
            image_b64 = ""
            if frame is not None:
                # Compression JPEG (qualité 70 pour réseau rapide)
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret:
                    image_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
            
            payload = {
                "type": alert_type,
                "location": f"Camera {camera_id}",
                "cameraId": camera_id,
                "trackingId": str(tracking_id) if tracking_id is not None else None,
                "imageBase64": image_b64
            }
            
            headers = {'Content-Type': 'application/json'}
            # Note: Si Spring Boot exige un Bearer token pour cette route, il faut l'ajouter ici.
            # Dans AlertController, /ai-detection semble être publique ou autorisée sans auth dans SecurityConfig
            
            response = requests.post(cls.BACKEND_URL, json=payload, headers=headers, timeout=5)
            
            if response.status_code in [200, 201]:
                logger.info(f"🚨 [ALERT] Sent successfully: {alert_type} on Camera {camera_id}")
            else:
                logger.error(f"❌ [ALERT] Failed to send {alert_type}: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ [ALERT] Connection error sending alert {alert_type}: {e}")

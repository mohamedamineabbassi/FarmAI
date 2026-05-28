"""
AlertManager — envoi asynchrone d'alertes vers le backend Spring Boot.

Paramètres supplémentaires vs v1 :
  severity     : "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
                 CRITICAL réduit le cooldown anti-spam à 5 s.
  animal_label : libellé de l'animal détecté (ex. "LOUP / PREDATEUR")
                 transmis dans le payload JSON pour affichage frontend.
"""

import time
import cv2
import base64
import requests
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AlertManager:
    _instance  = None
    _cooldowns = {}
    _executor  = ThreadPoolExecutor(max_workers=5)

    BACKEND_URL = "http://localhost:8081/api/alerts/ai-detection"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def trigger_alert(
        cls,
        alert_type:   str,
        camera_id:    int,
        tracking_id:  str  = None,
        frame               = None,
        location:     str  = "Camera",
        severity:     str  = None,
        animal_label: str  = None,
    ):
        """
        Déclenche une alerte.

        Cooldown anti-spam
        ──────────────────
        • Alertes CRITICAL (prédateurs) : cooldown 5 s
        • Toutes les autres             : cooldown 10 s
        """
        cooldown_key = f"{camera_id}_{alert_type}_{tracking_id}"

        # Cooldown réduit pour les urgences
        cooldown_secs = 5.0 if severity == "CRITICAL" else 10.0

        now       = time.time()
        last_time = cls._cooldowns.get(cooldown_key, 0.0)
        if now - last_time < cooldown_secs:
            return  # Anti-spam silencieux

        cls._cooldowns[cooldown_key] = now

        # Copie de la frame pour éviter une modification par le thread principal
        frame_copy = frame.copy() if frame is not None else None

        cls._executor.submit(
            cls._send_async,
            alert_type, camera_id, tracking_id,
            frame_copy, location, severity, animal_label,
        )

    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _send_async(
        cls,
        alert_type:   str,
        camera_id:    int,
        tracking_id:  str,
        frame,
        location:     str,
        severity:     str,
        animal_label: str,
    ):
        try:
            # Encodage JPEG de la frame (qualité 70)
            image_b64 = ""
            if frame is not None:
                ret, buf = cv2.imencode(
                    ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                )
                if ret:
                    image_b64 = (
                        "data:image/jpeg;base64,"
                        + base64.b64encode(buf).decode("utf-8")
                    )

            payload = {
                "type":        alert_type,
                "location":    f"Camera {camera_id}",
                "cameraId":    camera_id,
                "trackingId":  str(tracking_id) if tracking_id is not None else None,
                "imageBase64": image_b64,
            }

            # Champs optionnels
            if severity:
                payload["severity"]    = severity
            if animal_label:
                payload["animalLabel"] = animal_label

            resp = requests.post(
                cls.BACKEND_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            if resp.status_code in (200, 201):
                logger.info(
                    f"[ALERT OK] {alert_type} | camera {camera_id}"
                    + (f" | {animal_label}" if animal_label else "")
                )
            else:
                logger.error(
                    f"[ALERT FAIL] {alert_type} HTTP {resp.status_code}: {resp.text}"
                )

        except Exception as e:
            logger.error(f"[ALERT ERROR] {alert_type}: {e}")

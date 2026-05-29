import cv2
import logging
from ai_engine.core.tracker import CentroidTracker
from ai_engine.alerts.alert_manager import AlertManager
from ai_engine.services.db_service import DatabaseService

logger = logging.getLogger(__name__)

class LineCrossingLayer:
    def __init__(self):
        self.tracker = CentroidTracker(max_disappeared=30, max_distance=100)
        
        # Compteurs globaux
        self.counter_in = 0
        self.counter_out = 0

    def process(self, frame, detections, camera_id=None):
        """
        frame: np.ndarray (déjà traitée par FaceMode ou RoleMode)
        detections: list of dict [{"bbox": (x1, y1, x2, y2), "label": str}]
        """
        # 1. Mettre à jour le tracker
        objects = self.tracker.update(detections)

        # 2. Dessiner la ligne virtuelle (Verte) verticale au centre
        h, w = frame.shape[:2]
        line_x = w // 2
        
        cv2.line(frame, (line_x, 0), (line_x, h), (0, 255, 0), 2)
        cv2.putText(frame, "LINE CROSSING", (line_x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 3. Analyser les franchissements
        for obj_id, obj_data in objects.items():
            # Ne pas re-compter si déjà franchi
            if obj_data["crossed"]:
                pass
            else:
                history = obj_data["history_cx"]
                if len(history) >= 2:
                    old_cx = history[0]
                    new_cx = history[-1]
                    
                    # Détection: Gauche -> Droite (ENTRÉE)
                    if old_cx < line_x and new_cx >= line_x:
                        obj_data["direction"] = "ENTREE"
                        obj_data["crossed"] = True
                        obj_data["event_cooldown"] = 30 # Afficher l'event pendant ~30 frames
                        self.counter_in += 1

                        AlertManager.trigger_alert(
                            alert_type="ENTRY_EVENT",
                            camera_id=camera_id,
                            tracking_id=str(obj_id),
                            frame=frame
                        )

                        # Persister la présence (ENTRY) en base
                        try:
                            DatabaseService.save_attendance(
                                label=obj_data.get("label", "UNKNOWN"),
                                status="ENTRY"
                            )
                        except Exception as e:
                            logger.error(f"Erreur enregistrement présence ENTRY: {e}")

                    # Détection: Droite -> Gauche (SORTIE)
                    elif old_cx > line_x and new_cx <= line_x:
                        obj_data["direction"] = "SORTIE"
                        obj_data["crossed"] = True
                        obj_data["event_cooldown"] = 30
                        self.counter_out += 1

                        AlertManager.trigger_alert(
                            alert_type="EXIT_EVENT",
                            camera_id=camera_id,
                            tracking_id=str(obj_id),
                            frame=frame
                        )

                        # Persister la présence (EXIT) en base
                        try:
                            DatabaseService.save_attendance(
                                label=obj_data.get("label", "UNKNOWN"),
                                status="EXIT"
                            )
                        except Exception as e:
                            logger.error(f"Erreur enregistrement présence EXIT: {e}")

            # 4. Afficher les informations de tracking et d'événement
            x1, y1, x2, y2 = obj_data["bbox"]
            cx, cy = obj_data["centroid"]
            
            # Point du centroïde
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)
            
            # Afficher l'ID
            cv2.putText(frame, f"ID:{obj_id}", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Afficher l'événement si cooldown actif
            if obj_data["event_cooldown"] > 0:
                direction = obj_data["direction"]
                color = (0, 255, 0) if direction == "ENTREE" else (0, 165, 255) # Vert Entrée, Orange Sortie
                text = f"{obj_data['label']} - {direction}"
                cv2.putText(frame, text, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # 5. Afficher les compteurs globaux en haut à droite
        cv2.rectangle(frame, (w - 200, 10), (w - 10, 80), (0, 0, 0), -1)
        cv2.putText(frame, f"ENTREES: {self.counter_in}", (w - 190, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"SORTIES: {self.counter_out}", (w - 190, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        return frame

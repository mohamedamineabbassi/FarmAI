"""
RoleMode v2.0 — Détection couleur vêtement + êtres vivants + alertes prédateurs

Améliorations vs v1
───────────────────
1. ANTI-MUR-BLANC
   La caméra ne confond plus le mur blanc derrière une personne avec une blouse
   blanche. Technique : mesure d'amplitude de texture locale (blur-diff) sur les
   pixels candidats-blanc.
   • Mur plat  → texture < 9 → pixels blancs ignorés
   • Blouse    → texture ≥ 9 (plis, coutures, ombres) → pixels conservés

2. DISTINCTION HUMAIN / ANIMAL
   Le modèle YOLOv8 détecte maintenant TOUTES les classes COCO pertinentes :
   • Humain  (classe 0)  → analyse couleur vêtement → rôle (MÉDECIN / EMPLOYÉ…)
   • Animaux de ferme (mouton, vache, cheval…) → étiquette verte informative
   • Prédateurs (loup ≃ dog COCO 16, renard ≃ cat COCO 15, ours COCO 21)
     → bounding box rouge clignotant + ALERTE CRITIQUE envoyée au backend

3. ALERTES URGENTES
   • PREDATOR_DETECTED  → severity CRITICAL (cooldown 15 s par espèce)
   • UNKNOWN_ROLE       → severity HIGH     (cooldown 10 s)

Note sur loup/renard : ces espèces ne font PAS partie des 80 classes COCO.
YOLOv8 les identifie régulièrement comme « dog » (grand canidé sauvage) ou
« cat » (renard roux). En milieu fermier, toute détection dog/cat extérieure
est traitée comme une menace potentielle.
"""

import cv2
import numpy as np
import logging
import traceback
import time

from ai_engine.modes.base_mode import BaseMode
from ai_engine.core.model_manager import ModelManager
from ai_engine.alerts.alert_manager import AlertManager

logger = logging.getLogger(__name__)


# ─── Taxonomie COCO pour ce mode ─────────────────────────────────────────────
PERSON_CLASS = 0

# Prédateurs potentiels → alerte CRITIQUE
PREDATOR_CLASSES = {
    15: "RENARD / PREDATEUR",   # COCO cat  → proxy renard en milieu extérieur
    16: "LOUP / PREDATEUR",     # COCO dog  → proxy loup
    21: "OURS / DANGER",        # COCO bear
}

# Animaux de ferme → affichage informatif uniquement
FARM_CLASSES = {
    17: "Cheval",
    18: "Mouton",
    19: "Vache",
    20: "Elephant",
    22: "Zebre",
    23: "Girafe",
}

# Union de toutes les classes à détecter
ALL_DETECT_CLASSES = (
    [PERSON_CLASS]
    + sorted(PREDATOR_CLASSES.keys())
    + sorted(FARM_CLASSES.keys())
)


# ─── Correspondance couleur → rôle ──────────────────────────────────────────
#   clé     : nom couleur
#   valeur  : (libellé rôle, BGR boîte/barre, BGR texte)
COLOUR_TO_ROLE = {
    "BLANC":  ("MEDECIN",      (200, 200, 200), (20,  20,  20)),
    "ORANGE": ("EMPLOYE",      (0,  165, 255),  (255, 255, 255)),
    "BLEU":   ("ELECTRICIEN",  (210,  40,   0), (255, 255, 255)),
    "VERT":   ("SECURITE",     (0,  185,   0),  (255, 255, 255)),
    "ROUGE":  ("POMPIER",      (0,    0, 215),  (255, 255, 255)),
    "JAUNE":  ("LOGISTIQUE",   (0,  210, 210),  (0,    0,   0)),
    "UNKNOWN":("INTRUS/ROLE?", (0,    0, 255),  (255, 255, 255)),
}


class RoleMode(BaseMode):

    def __init__(self, camera_id: int):
        super().__init__(camera_id)
        self.yolo              = ModelManager().get_yolo_model()
        self._last_role_alert  = 0.0
        self._last_pred_alert  = {}   # {coco_class_id: float timestamp}
        self._frame_idx        = 0
        logger.info(f"[RoleMode v2.0] Demarrage camera {camera_id}")

    # ─────────────────────────────────────────────────────────────────────────
    # DETECTION COULEUR — anti-mur-blanc
    # ─────────────────────────────────────────────────────────────────────────
    def _detect_colour(self, person_crop: np.ndarray) -> str:
        """
        Retourne la couleur dominante du vêtement.

        Étapes
        1. Extraction d'une région torse intérieure (marges 14 %) pour éviter
           que les pixels de bord (fond) contaminent l'analyse.
        2. Application de masques HSV précis pour 6 couleurs.
        3. Test de texture (amplitude locale blur-diff) sur les pixels blancs :
           si la texture moyenne < 9 → ils sont « plats » (mur) et sont
           redimensionnés vers 0. Seule une blouse avec texture passe.
        """
        if person_crop is None or person_crop.size < 300:
            return "UNKNOWN"

        h, w = person_crop.shape[:2]

        # Zone torse intérieure : 15%–65% vertical, 14% marges latérales
        my = max(1, int(h * 0.14))
        mx = max(1, int(w * 0.14))
        y0 = int(h * 0.15) + my
        y1 = int(h * 0.65) - my
        x0 = mx
        x1 = w - mx

        torso = person_crop[y0:y1, x0:x1]
        if torso.size < 200:
            return "UNKNOWN"

        hsv   = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
        total = torso.shape[0] * torso.shape[1]

        # ── Masques HSV ───────────────────────────────────────────────────────
        mask_white  = cv2.inRange(hsv, np.array([0,   0, 185]), np.array([180,  55, 255]))
        mask_orange = cv2.inRange(hsv, np.array([8,  100,  80]), np.array([28,  255, 255]))
        mask_blue   = cv2.inRange(hsv, np.array([90,  65,  45]), np.array([130, 255, 255]))
        mask_green  = cv2.inRange(hsv, np.array([35,  55,  45]), np.array([85,  255, 255]))
        mask_red1   = cv2.inRange(hsv, np.array([0,  100,  80]), np.array([8,   255, 255]))
        mask_red2   = cv2.inRange(hsv, np.array([165, 100,  80]), np.array([180, 255, 255]))
        mask_red    = cv2.bitwise_or(mask_red1, mask_red2)
        mask_yellow = cv2.inRange(hsv, np.array([22, 100, 100]), np.array([35,  255, 255]))

        # ── Test texture anti-mur-blanc ───────────────────────────────────────
        cnt_white_raw = cv2.countNonZero(mask_white)
        cnt_white     = cnt_white_raw

        if cnt_white_raw > total * 0.08:           # seuil minimal avant calcul
            gray = cv2.cvtColor(torso, cv2.COLOR_BGR2GRAY).astype(np.float32)
            blur = cv2.GaussianBlur(gray, (7, 7), 0)
            diff = np.abs(gray - blur)             # amplitude de texture locale

            white_bool = mask_white.astype(bool)
            if white_bool.any():
                texture = float(diff[white_bool].mean())
                # Mur plat : texture ≈ 2–7  → pénaliser le blanc
                # Blouse   : texture ≈ 10–25 → conserver le blanc
                if texture < 9.0:
                    cnt_white = int(cnt_white_raw * (texture / 9.0))

        # ── Pourcentages finaux ───────────────────────────────────────────────
        pct = {
            "BLANC":  (cnt_white                          / total) * 100,
            "ORANGE": (cv2.countNonZero(mask_orange)      / total) * 100,
            "BLEU":   (cv2.countNonZero(mask_blue)        / total) * 100,
            "VERT":   (cv2.countNonZero(mask_green)       / total) * 100,
            "ROUGE":  (cv2.countNonZero(mask_red)         / total) * 100,
            "JAUNE":  (cv2.countNonZero(mask_yellow)      / total) * 100,
        }

        dominant = max(pct, key=pct.get)
        return dominant if pct[dominant] >= 9.0 else "UNKNOWN"

    # ─────────────────────────────────────────────────────────────────────────
    # TRAITEMENT DE FRAME
    # ─────────────────────────────────────────────────────────────────────────
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.current_detections = []

        if self.yolo is None or frame is None or frame.size == 0:
            return frame

        self._frame_idx += 1
        # Effet clignotant ~2 Hz : 8 frames ON / 8 frames OFF @ 30 fps
        blink_on            = (self._frame_idx // 8) % 2 == 0
        predators_this_frame = []   # labels des predateurs vus dans ce frame

        try:
            results = self.yolo(frame, classes=ALL_DETECT_CLASSES, verbose=False)

            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    cls  = int(box.cls[0])
                    if conf < 0.40:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Clamp aux dimensions de la frame
                    x1 = max(0, x1);           y1 = max(0, y1)
                    x2 = min(frame.shape[1], x2); y2 = min(frame.shape[0], y2)
                    crop = frame[y1:y2, x1:x2]

                    # ════════════════════════════════════════════════════════
                    # CAS 1 — HUMAIN : analyse couleur vêtement
                    # ════════════════════════════════════════════════════════
                    if cls == PERSON_CLASS:
                        colour               = self._detect_colour(crop)
                        role, box_bgr, txt_bgr = COLOUR_TO_ROLE.get(
                            colour, COLOUR_TO_ROLE["UNKNOWN"])

                        self.current_detections.append({
                            "bbox":  (x1, y1, x2, y2),
                            "label": role,
                        })

                        # Boîte principale
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_bgr, 2)

                        # Barre de titre colorée
                        bar_top = max(0, y1 - 28)
                        cv2.rectangle(frame, (x1, bar_top), (x2, y1), box_bgr, -1)
                        cv2.putText(frame,
                                    f"HUMAIN | {role}",
                                    (x1 + 4, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, txt_bgr, 2)

                        # Mini-badge en bas de boîte
                        cv2.putText(frame,
                                    f"couleur:{colour}  conf:{conf:.0%}",
                                    (x1 + 4, y2 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                                    (240, 240, 240), 1)

                        # Alerte rôle inconnu
                        if colour == "UNKNOWN":
                            now = time.time()
                            if now - self._last_role_alert >= 10:
                                AlertManager.trigger_alert(
                                    alert_type  = "UNKNOWN_ROLE",
                                    camera_id   = self.camera_id,
                                    tracking_id = "role_inconnu",
                                    frame       = frame,
                                    severity    = "HIGH",
                                )
                                self._last_role_alert = now

                    # ════════════════════════════════════════════════════════
                    # CAS 2 — PREDATEUR : ALERTE URGENTE CRITIQUE
                    # ════════════════════════════════════════════════════════
                    elif cls in PREDATOR_CLASSES:
                        animal_label = PREDATOR_CLASSES[cls]
                        predators_this_frame.append(animal_label)

                        self.current_detections.append({
                            "bbox":  (x1, y1, x2, y2),
                            "label": animal_label,
                        })

                        # Boîte rouge (épaisseur alternée = clignotant)
                        thickness = 4 if blink_on else 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2),
                                      (0, 0, 255), thickness)

                        # Barre danger (rouge pulsé)
                        bar_top = max(0, y1 - 34)
                        bar_bgr = (0, 0, 210) if blink_on else (0, 0, 90)
                        cv2.rectangle(frame, (x1, bar_top), (x2, y1), bar_bgr, -1)
                        cv2.putText(frame,
                                    f"!! DANGER: {animal_label}",
                                    (x1 + 4, y1 - 13),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.54,
                                    (255, 255, 255), 2)
                        cv2.putText(frame,
                                    f"conf:{conf:.0%}",
                                    (x1 + 4, y1 - 2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                                    (255, 200, 200), 1)

                        # Envoi alerte CRITICAL (cooldown 15 s / espèce)
                        now  = time.time()
                        last = self._last_pred_alert.get(cls, 0.0)
                        if now - last >= 15:
                            AlertManager.trigger_alert(
                                alert_type   = "PREDATOR_DETECTED",
                                camera_id    = self.camera_id,
                                tracking_id  = f"predator_{cls}",
                                frame        = frame,
                                severity     = "CRITICAL",
                                animal_label = animal_label,
                            )
                            self._last_pred_alert[cls] = now
                            logger.warning(
                                f"PREDATEUR DETECTE : {animal_label} "
                                f"(camera {self.camera_id})"
                            )

                    # ════════════════════════════════════════════════════════
                    # CAS 3 — ANIMAL DE FERME : étiquette informative verte
                    # ════════════════════════════════════════════════════════
                    elif cls in FARM_CLASSES:
                        animal_label = FARM_CLASSES[cls]
                        farm_bgr     = (30, 180, 60)   # vert

                        cv2.rectangle(frame, (x1, y1), (x2, y2), farm_bgr, 2)
                        bar_top = max(0, y1 - 24)
                        cv2.rectangle(frame, (x1, bar_top), (x2, y1), farm_bgr, -1)
                        cv2.putText(frame,
                                    f"ANIMAL: {animal_label}",
                                    (x1 + 4, y1 - 6),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                                    (0, 0, 0), 2)

            # ── Overlay global danger si prédateur présent ce frame ───────────
            if predators_this_frame and blink_on:
                h_f, w_f = frame.shape[:2]

                # Teinte rouge légère sur toute l'image
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w_f, h_f), (0, 0, 180), -1)
                cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

                # Bandeau d'alerte plein écran en haut
                cv2.rectangle(frame, (0, 0), (w_f, 52), (0, 0, 200), -1)
                names = " | ".join(dict.fromkeys(predators_this_frame))  # deduplique
                cv2.putText(frame,
                            f"!!! ALERTE URGENTE — PREDATEUR : {names} !!!",
                            (10, 36),
                            cv2.FONT_HERSHEY_DUPLEX, 0.78,
                            (255, 60, 60), 2)

        except Exception as e:
            logger.error(f"Erreur RoleMode v2.0 : {e}")
            logger.debug(traceback.format_exc())

        return frame

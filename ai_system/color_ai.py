"""
color_ai.py — Détection couleur vêtements v2.0 (script autonome)

Améliorations :
  1. Anti-mur-blanc  : test de texture locale pour rejeter le fond blanc.
  2. Distinction humain / animal / prédateur.
  3. Alerte CRITIQUE si loup (proxy dog) ou renard (proxy cat) détecté.

Usage :
  python color_ai.py --source 0 --camera_id 1
"""

import cv2
import numpy as np
from ultralytics import YOLO
import requests
import argparse
import time

# ── Arguments ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--source",    type=str, default="0")
parser.add_argument("--camera_id", type=str, default="1")
args = parser.parse_args()

CAMERA_SOURCE = int(args.source) if args.source.isdigit() else args.source
CAMERA_ID     = args.camera_id

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_STATUS_URL = "http://localhost:8081/api/department-status"
BACKEND_ALERT_URL  = "http://localhost:8081/api/alerts/ai-detection"
SEND_INTERVAL      = 5      # secondes entre envois de statut
PRED_COOLDOWN      = 15     # secondes entre alertes prédateur

# ── Chargement modèle ─────────────────────────────────────────────────────────
model = YOLO("yolov8n.pt")

# ── Taxonomie COCO ────────────────────────────────────────────────────────────
PERSON_CLASS = 0

PREDATOR_CLASSES = {
    15: "RENARD / PREDATEUR",   # COCO cat  → proxy renard
    16: "LOUP / PREDATEUR",     # COCO dog  → proxy loup
    21: "OURS / DANGER",        # COCO bear
}

FARM_CLASSES = {
    17: "Cheval",
    18: "Mouton",
    19: "Vache",
}

ALL_CLASSES = (
    [PERSON_CLASS]
    + sorted(PREDATOR_CLASSES.keys())
    + sorted(FARM_CLASSES.keys())
)

# ── Couleur → rôle ────────────────────────────────────────────────────────────
COLOUR_TO_ROLE = {
    "BLANC":  ("MEDECIN",      (200, 200, 200), (20,  20,  20)),
    "ORANGE": ("EMPLOYE",      (0,  165, 255),  (255, 255, 255)),
    "BLEU":   ("ELECTRICIEN",  (210,  40,   0), (255, 255, 255)),
    "VERT":   ("SECURITE",     (0,  185,   0),  (255, 255, 255)),
    "ROUGE":  ("POMPIER",      (0,    0, 215),  (255, 255, 255)),
    "JAUNE":  ("LOGISTIQUE",   (0,  210, 210),  (0,    0,   0)),
    "UNKNOWN":("INTRUS/ROLE?", (0,    0, 255),  (255, 255, 255)),
}


# ─────────────────────────────────────────────────────────────────────────────
# DETECTION COULEUR — anti-mur-blanc
# ─────────────────────────────────────────────────────────────────────────────
def detect_colour(person_crop: np.ndarray) -> str:
    """
    Retourne la couleur dominante du vêtement.
    Filtre les pixels blancs « plats » (mur) par test de texture locale.
    """
    if person_crop is None or person_crop.size < 300:
        return "UNKNOWN"

    h, w = person_crop.shape[:2]

    # Zone torse intérieure (évite les bords = fond)
    my = max(1, int(h * 0.14))
    mx = max(1, int(w * 0.14))
    y0, y1 = int(h * 0.15) + my, int(h * 0.65) - my
    x0, x1 = mx, w - mx

    torso = person_crop[y0:y1, x0:x1]
    if torso.size < 200:
        return "UNKNOWN"

    hsv   = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
    total = torso.shape[0] * torso.shape[1]

    # Masques HSV
    mask_white  = cv2.inRange(hsv, np.array([0,   0, 185]), np.array([180,  55, 255]))
    mask_orange = cv2.inRange(hsv, np.array([8,  100,  80]), np.array([28,  255, 255]))
    mask_blue   = cv2.inRange(hsv, np.array([90,  65,  45]), np.array([130, 255, 255]))
    mask_green  = cv2.inRange(hsv, np.array([35,  55,  45]), np.array([85,  255, 255]))
    mask_red1   = cv2.inRange(hsv, np.array([0,  100,  80]), np.array([8,   255, 255]))
    mask_red2   = cv2.inRange(hsv, np.array([165, 100,  80]), np.array([180, 255, 255]))
    mask_red    = cv2.bitwise_or(mask_red1, mask_red2)
    mask_yellow = cv2.inRange(hsv, np.array([22, 100, 100]), np.array([35,  255, 255]))

    # Test texture anti-mur-blanc
    cnt_white_raw = cv2.countNonZero(mask_white)
    cnt_white     = cnt_white_raw

    if cnt_white_raw > total * 0.08:
        gray    = cv2.cvtColor(torso, cv2.COLOR_BGR2GRAY).astype(np.float32)
        blur    = cv2.GaussianBlur(gray, (7, 7), 0)
        diff    = np.abs(gray - blur)
        wb      = mask_white.astype(bool)
        if wb.any():
            texture = float(diff[wb].mean())
            if texture < 9.0:
                cnt_white = int(cnt_white_raw * (texture / 9.0))

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


# ─────────────────────────────────────────────────────────────────────────────
# ENVOI ALERTE BACKEND
# ─────────────────────────────────────────────────────────────────────────────
def send_alert(alert_type: str, animal_label: str = None, frame=None):
    import base64
    image_b64 = ""
    if frame is not None:
        ret, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if ret:
            image_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    payload = {
        "type":        alert_type,
        "location":    f"Camera {CAMERA_ID}",
        "cameraId":    int(CAMERA_ID),
        "severity":    "CRITICAL",
        "imageBase64": image_b64,
    }
    if animal_label:
        payload["animalLabel"] = animal_label

    try:
        requests.post(BACKEND_ALERT_URL, json=payload, timeout=3)
        print(f"🚨 ALERTE ENVOYEE : {alert_type} — {animal_label or ''}")
    except Exception as e:
        print(f"❌ ERREUR ALERTE : {e}")


# ─────────────────────────────────────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print(f"❌ Impossible d'ouvrir la source : {CAMERA_SOURCE}")
    exit(1)

print(f"🚀 COLOR AI v2.0 démarré — source:{CAMERA_SOURCE}  camera_id:{CAMERA_ID}")

last_status_time = 0.0
last_pred_alert  = {}   # {coco_cls: timestamp}
role_counts      = {}   # {role: int}
frame_idx        = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Fin du flux ou erreur de lecture.")
        break

    frame_idx += 1
    blink_on = (frame_idx // 8) % 2 == 0
    predators_frame = []

    results = model(frame, classes=ALL_CLASSES, verbose=False)

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls  = int(box.cls[0])
            if conf < 0.40:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(frame.shape[1], x2); y2 = min(frame.shape[0], y2)
            crop = frame[y1:y2, x1:x2]

            # ── HUMAIN ───────────────────────────────────────────────────────
            if cls == PERSON_CLASS:
                colour              = detect_colour(crop)
                role, box_bgr, txt  = COLOUR_TO_ROLE.get(colour, COLOUR_TO_ROLE["UNKNOWN"])
                role_counts[role]   = role_counts.get(role, 0) + 1

                cv2.rectangle(frame, (x1, y1), (x2, y2), box_bgr, 2)
                bar_top = max(0, y1 - 28)
                cv2.rectangle(frame, (x1, bar_top), (x2, y1), box_bgr, -1)
                cv2.putText(frame, f"HUMAIN | {role}",
                            (x1 + 4, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.50, txt, 2)
                cv2.putText(frame, f"couleur:{colour} conf:{conf:.0%}",
                            (x1 + 4, y2 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (240, 240, 240), 1)

            # ── PREDATEUR ────────────────────────────────────────────────────
            elif cls in PREDATOR_CLASSES:
                animal_label = PREDATOR_CLASSES[cls]
                predators_frame.append(animal_label)

                th = 4 if blink_on else 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), th)
                bar_top = max(0, y1 - 34)
                bar_bgr = (0, 0, 210) if blink_on else (0, 0, 90)
                cv2.rectangle(frame, (x1, bar_top), (x2, y1), bar_bgr, -1)
                cv2.putText(frame, f"!! DANGER: {animal_label}",
                            (x1 + 4, y1 - 13),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 255, 255), 2)
                cv2.putText(frame, f"conf:{conf:.0%}",
                            (x1 + 4, y1 - 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 200, 200), 1)

                # Alerte backend
                now  = time.time()
                last = last_pred_alert.get(cls, 0.0)
                if now - last >= PRED_COOLDOWN:
                    send_alert("PREDATOR_DETECTED", animal_label, frame)
                    last_pred_alert[cls] = now

            # ── ANIMAL DE FERME ───────────────────────────────────────────────
            elif cls in FARM_CLASSES:
                label   = FARM_CLASSES[cls]
                farm_c  = (30, 180, 60)
                cv2.rectangle(frame, (x1, y1), (x2, y2), farm_c, 2)
                bar_top = max(0, y1 - 24)
                cv2.rectangle(frame, (x1, bar_top), (x2, y1), farm_c, -1)
                cv2.putText(frame, f"ANIMAL: {label}",
                            (x1 + 4, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 2)

    # ── Overlay global prédateur ──────────────────────────────────────────────
    if predators_frame and blink_on:
        h_f, w_f = frame.shape[:2]
        ov = frame.copy()
        cv2.rectangle(ov, (0, 0), (w_f, h_f), (0, 0, 180), -1)
        cv2.addWeighted(ov, 0.18, frame, 0.82, 0, frame)
        cv2.rectangle(frame, (0, 0), (w_f, 52), (0, 0, 200), -1)
        names = " | ".join(dict.fromkeys(predators_frame))
        cv2.putText(frame,
                    f"!!! ALERTE URGENTE — PREDATEUR : {names} !!!",
                    (10, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.78, (255, 60, 60), 2)

    # ── Envoi statut périodique ───────────────────────────────────────────────
    now = time.time()
    if now - last_status_time >= SEND_INTERVAL:
        payload = {
            "cameraId":    CAMERA_ID,
            "counts":      role_counts,
            "hasPredator": bool(predators_frame),
            "timestamp":   now,
        }
        try:
            requests.post(BACKEND_STATUS_URL, json=payload, timeout=2)
            print(f"📤 STATUT : {role_counts}"
                  + (" 🚨 PREDATEUR!" if predators_frame else ""))
        except Exception as e:
            print(f"❌ STATUT ERREUR : {e}")

        last_status_time = now
        role_counts = {}

    # ── Affichage ─────────────────────────────────────────────────────────────
    cv2.imshow(f"COLOR AI v2.0 — camera {CAMERA_ID}", frame)
    if cv2.waitKey(1) == 27:   # ESC pour quitter
        break

cap.release()
cv2.destroyAllWindows()

import numpy as np
from collections import OrderedDict

class CentroidTracker:
    def __init__(self, max_disappeared=30, max_distance=100):
        # Prochain ID unique à attribuer
        self.next_object_id = 0
        
        # Dictionnaire des objets suivis. 
        # Structure : object_id -> {centroid, bbox, label, disappeared, history_cx, direction, crossed}
        self.objects = OrderedDict()
        
        # Nombre maximum de frames consécutives où l'objet peut disparaître avant d'être supprimé
        self.max_disappeared = max_disappeared
        
        # Distance maximum (en pixels) pour associer un centroïde à un objet existant
        self.max_distance = max_distance

    def register(self, centroid, bbox, label):
        self.objects[self.next_object_id] = {
            "centroid": centroid,
            "bbox": bbox,
            "label": label,
            "disappeared": 0,
            "history_cx": [centroid[0]],
            "direction": None,
            "crossed": False,
            "event_cooldown": 0
        }
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]

    def update(self, rects):
        """
        rects: list of dict [{"bbox": (x1, y1, x2, y2), "label": label}, ...]
        Retourne le dictionnaire self.objects mis à jour.
        """
        if len(rects) == 0:
            # Aucun objet détecté, on incrémente le compteur de disparition
            for object_id in list(self.objects.keys()):
                self.objects[object_id]["disappeared"] += 1
                if self.objects[object_id]["disappeared"] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # Initialiser les tableaux pour les nouvelles détections
        input_centroids = np.zeros((len(rects), 2), dtype="int")
        input_bboxes = []
        input_labels = []

        for (i, rect_info) in enumerate(rects):
            (startX, startY, endX, endY) = rect_info["bbox"]
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)
            input_bboxes.append((startX, startY, endX, endY))
            input_labels.append(rect_info["label"])

        # S'il n'y a aucun objet tracké actuellement, on enregistre tout
        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i], input_bboxes[i], input_labels[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = [obj["centroid"] for obj in self.objects.values()]

            # Calcul de la matrice de distance Euclidienne
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                # Si la distance est trop grande, ne pas associer
                if D[row, col] > self.max_distance:
                    continue

                # Association valide
                object_id = object_ids[row]
                self.objects[object_id]["centroid"] = input_centroids[col]
                self.objects[object_id]["bbox"] = input_bboxes[col]
                
                # Mise à jour du label (utile si FaceRecognition passe de UNKNOWN à USER)
                if input_labels[col] != "UNKNOWN":
                    self.objects[object_id]["label"] = input_labels[col]
                
                self.objects[object_id]["disappeared"] = 0
                
                # Historique pour calculer la direction X
                self.objects[object_id]["history_cx"].append(input_centroids[col][0])
                if len(self.objects[object_id]["history_cx"]) > 10:
                    self.objects[object_id]["history_cx"].pop(0)

                used_rows.add(row)
                used_cols.add(col)

            # Traitement des objets disparus
            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            for row in unused_rows:
                object_id = object_ids[row]
                self.objects[object_id]["disappeared"] += 1
                if self.objects[object_id]["disappeared"] > self.max_disappeared:
                    self.deregister(object_id)

            # Enregistrement des nouveaux objets
            for col in unused_cols:
                self.register(input_centroids[col], input_bboxes[col], input_labels[col])

        # Gérer le cooldown des events (affichage temporaire des overlays "ENTREE/SORTIE")
        for object_id in list(self.objects.keys()):
            if self.objects[object_id]["event_cooldown"] > 0:
                self.objects[object_id]["event_cooldown"] -= 1

        return self.objects

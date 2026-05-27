from abc import ABC, abstractmethod
import numpy as np

class BaseMode(ABC):
    """
    Classe de base (Interface/Strategy) pour tous les modes IA.
    Chaque mode (Face, Role, Intrusion) doit implémenter `process_frame`.
    """

    def __init__(self, camera_id: int):
        self.camera_id = camera_id

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Traite la frame entrante et retourne la frame modifiée (Bounding Boxes, HUD)
        """
        pass

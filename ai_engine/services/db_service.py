import mysql.connector
from mysql.connector import pooling, Error
import logging
import json
import numpy as np
from ai_engine.core.config import Config

logger = logging.getLogger(__name__)

class DatabaseService:
    _pool = None

    @classmethod
    def init_pool(cls):
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="ai_pool",
                    pool_size=5,
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASS,
                    database=Config.DB_NAME
                )
                logger.info("✓ Connection pool MySQL initialisé.")
            except Error as e:
                logger.error(f"✗ Erreur d'initialisation du pool MySQL: {e}")

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            cls.init_pool()
        try:
            return cls._pool.get_connection()
        except Error as e:
            logger.error(f"Erreur lors de la récupération d'une connexion: {e}")
            return None

    @classmethod
    def load_all_embeddings(cls):
        """Charge tous les visages enregistrés depuis la BD (Employés + Users)"""
        conn = cls.get_connection()
        if not conn: return {}

        embeddings = {}
        try:
            cursor = conn.cursor()
            
            # 1. Employés
            cursor.execute("SELECT email, embedding FROM employees WHERE embedding IS NOT NULL AND email IS NOT NULL")
            for email, emb_json in cursor.fetchall():
                try:
                    emb = np.array(json.loads(emb_json))
                    emb = emb / np.linalg.norm(emb)
                    embeddings[email] = emb
                except Exception:
                    continue
                    
            # 2. Utilisateurs
            cursor.execute("SELECT email, embedding FROM users WHERE embedding IS NOT NULL AND email IS NOT NULL")
            for email, emb_json in cursor.fetchall():
                if email not in embeddings:
                    try:
                        emb = np.array(json.loads(emb_json))
                        emb = emb / np.linalg.norm(emb)
                        embeddings[email] = emb
                    except Exception:
                        continue

            cursor.close()
        except Error as e:
            logger.error(f"Erreur de lecture des embeddings: {e}")
        finally:
            conn.close()
            
        logger.info(f"✓ {len(embeddings)} visages chargés en mémoire.")
        return embeddings

    @classmethod
    def get_camera_info(cls, camera_id: int):
        conn = cls.get_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, source, status, ai_type, department_id FROM cameras WHERE id = %s", (camera_id,))
            camera = cursor.fetchone()
            cursor.close()
            return camera
        except Error as e:
            logger.error(f"Erreur get_camera_info: {e}")
            return None
        finally:
            conn.close()

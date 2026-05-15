#!/usr/bin/env python3
"""
Test script to verify MySQL connection and database setup
"""
import mysql.connector
import sys
from mysql.connector import Error

def test_mysql_connection():
    """Test MySQL connection"""
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root123',
        'database': 'attendance_db'
    }
    
    try:
        print("[*] Tentative de connexion à MySQL...")
        conn = mysql.connector.connect(**config)
        
        if conn.is_connected():
            print("[✓] Connexion MySQL réussie!")
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"[*] Version MySQL: {version[0]}")
            
            # Test des tables essentielles
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"[*] Tables disponibles: {len(tables)}")
            for table in tables:
                print(f"    - {table[0]}")
            
            cursor.close()
            conn.close()
            return True
    except Error as e:
        print(f"[✗] Erreur MySQL: {e}")
        return False

def test_camera():
    """Test camera detection"""
    try:
        import cv2
        print("[*] Test caméra...")
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("[✓] Caméra détectée et fonctionnelle!")
                return True
            else:
                print("[✗] Impossible de lire de la caméra")
                return False
        else:
            print("[✗] Caméra non disponible")
            return False
    except Exception as e:
        print(f"[✗] Erreur caméra: {e}")
        return False

def test_ai_models():
    """Test AI models"""
    try:
        print("[*] Chargement du modèle InsightFace...")
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(name='buffalo_l')
        app.prepare(ctx_id=0, det_size=(320, 320))
        print("[✓] Modèle InsightFace chargé!")
        return True
    except Exception as e:
        print(f"[✗] Erreur modèle IA: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DIAGNOSTIC FARM-AI SYSTEM")
    print("=" * 50)
    
    results = {
        "MySQL": test_mysql_connection(),
        "Caméra": test_camera(),
        "Modèles IA": test_ai_models()
    }
    
    print("\n" + "=" * 50)
    print("RÉSUMÉ")
    print("=" * 50)
    for service, status in results.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {service}: {'OK' if status else 'ERREUR'}")
    
    sys.exit(0 if all(results.values()) else 1)

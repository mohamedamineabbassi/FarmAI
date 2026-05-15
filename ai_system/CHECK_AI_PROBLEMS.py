#!/usr/bin/env python3
"""
GUIDE DÉPANNAGE - Pourquoi l'analyse AI ne fonctionne pas?
Exécutez ce script pour identifier les 5 problèmes les plus courants
"""

import mysql.connector
import os
import sys
import json
from mysql.connector import Error

def check_ai_issues():
    print("\n" + "="*70)
    print("  🔍 DIAGNOSTIC: ANALYSE AI NE FONCTIONNE PAS?")
    print("="*70 + "\n")
    
    issues = []
    
    # ==========================================
    # PROBLÈME 1: Aucun employé en base
    # ==========================================
    print("1️⃣  Vérification: Employés en base...")
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root123",
            database="attendance_db"
        )
        cursor = db.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]
        
        if total_employees == 0:
            issues.append("❌ PROBLÈME 1: Aucun employé en base!")
            print("   ❌ PROBLÈME 1: Aucun employé en base!")
            print("   → Solution: Créez des employés d'abord (Frontend ou API)")
        else:
            print(f"   ✓ {total_employees} employé(s) trouvé(s)")
        
    except Error as e:
        print(f"   ❌ Erreur MySQL: {e}")
        issues.append(f"❌ PROBLÈME: MySQL n'est pas accessible - {e}")
        return issues
    
    # ==========================================
    # PROBLÈME 2: Aucun employé avec embeddings (visages enregistrés)
    # ==========================================
    print("\n2️⃣  Vérification: Employés avec embeddings (visages)...")
    try:
        cursor.execute("""
            SELECT id, name, 
                   IF(embedding IS NOT NULL, 'OUI', 'NON') as has_embedding 
            FROM employees
        """)
        employees = cursor.fetchall()
        
        embeddings_count = 0
        for emp_id, name, has_embedding in employees:
            if has_embedding == "OUI":
                embeddings_count += 1
                print(f"   ✓ {name} (ID {emp_id}) - Visage enregistré")
            else:
                print(f"   ❌ {name} (ID {emp_id}) - PAS DE VISAGE")
        
        if embeddings_count == 0:
            issues.append("❌ PROBLÈME 2: Aucun employé avec visage enregistré!")
            print("\n   ❌ PROBLÈME 2: AUCUN EMPLOYÉ AVEC VISAGE ENREGISTRÉ!")
            print("   → Solution: Enregistrez les visages!")
            print("   → Accédez à: http://localhost:4200/face-registration")
            print("   → Ou exécutez: python register_face.py --employee_id 1")
        else:
            print(f"\n   ✓ {embeddings_count} employé(s) avec visage")
        
    except Error as e:
        print(f"   ❌ Erreur: {e}")
        issues.append(f"❌ PROBLÈME: Erreur lecture embeddings - {e}")
    
    # ==========================================
    # PROBLÈME 3: Format des embeddings invalide
    # ==========================================
    print("\n3️⃣  Vérification: Format des embeddings...")
    try:
        cursor.execute("SELECT id, name, embedding FROM employees WHERE embedding IS NOT NULL LIMIT 5")
        employees = cursor.fetchall()
        
        invalid_count = 0
        valid_count = 0
        
        for emp_id, name, emb_json in employees:
            try:
                emb_array = json.loads(emb_json)
                if isinstance(emb_array, list) and len(emb_array) > 0:
                    valid_count += 1
                    print(f"   ✓ {name}: embedding valide ({len(emb_array)} dimensions)")
                else:
                    invalid_count += 1
                    print(f"   ❌ {name}: format invalide")
            except json.JSONDecodeError:
                invalid_count += 1
                print(f"   ❌ {name}: JSON invalide")
        
        if invalid_count > 0:
            issues.append(f"❌ PROBLÈME 3: {invalid_count} embedding(s) invalide(s)!")
            print(f"\n   ❌ PROBLÈME 3: {invalid_count} embedding(s) invalide(s)!")
            print("   → Solution: Supprimez et réenregistrez les visages")
        else:
            print(f"\n   ✓ Tous les {valid_count} embeddings sont valides")
        
    except Error as e:
        print(f"   ❌ Erreur: {e}")
        issues.append(f"❌ PROBLÈME: Erreur vérification embeddings - {e}")
    
    # ==========================================
    # PROBLÈME 4: Dépendances Python manquantes
    # ==========================================
    print("\n4️⃣  Vérification: Dépendances Python...")
    try:
        import cv2
        print("   ✓ OpenCV installé")
    except ImportError:
        print("   ❌ OpenCV NON installé")
        issues.append("❌ PROBLÈME 4a: OpenCV manquant!")
    
    try:
        from insightface.app import FaceAnalysis
        print("   ✓ InsightFace installé")
    except ImportError:
        print("   ❌ InsightFace NON installé")
        issues.append("❌ PROBLÈME 4b: InsightFace manquant!")
    
    try:
        import mysql.connector
        print("   ✓ MySQL Connector installé")
    except ImportError:
        print("   ❌ MySQL Connector NON installé")
        issues.append("❌ PROBLÈME 4c: MySQL Connector manquant!")
    
    # ==========================================
    # PROBLÈME 5: Fichier requirements.txt manquant
    # ==========================================
    print("\n5️⃣  Vérification: Fichier requirements.txt...")
    if os.path.exists("requirements.txt"):
        print("   ✓ requirements.txt existe")
        try:
            with open("requirements.txt", "r") as f:
                deps = f.read()
                print(f"   📦 Dépendances:\n{deps}")
        except Exception as e:
            print(f"   ❌ Erreur lecture: {e}")
    else:
        print("   ❌ requirements.txt MANQUANT!")
        issues.append("❌ PROBLÈME 5: requirements.txt manquant!")
        print("   → Solution: pip install opencv-python mysql-connector-python fastapi insightface uvicorn")
    
    cursor.close()
    db.close()
    
    return issues

# ==========================================
# AFFICHER LES SOLUTIONS
# ==========================================
def show_solutions(issues):
    print("\n" + "="*70)
    print("  📋 RÉSUMÉ DES PROBLÈMES")
    print("="*70 + "\n")
    
    if not issues:
        print("✅ AUCUN PROBLÈME MAJEUR TROUVÉ!")
        print("\nL'IA devrait fonctionner. Essayez:")
        print("  1. python main.py")
        print("  2. python camera_ai_stream.py --source 0 --camera_id 1")
        return
    
    print(f"🔴 {len(issues)} problème(s) détecté(s):\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    print("\n" + "="*70)
    print("  🛠️ SOLUTIONS RECOMMANDÉES")
    print("="*70 + "\n")
    
    if any("Aucun employé" in issue for issue in issues):
        print("✓ ÉTAPE 1: Créer un employé")
        print("  Accédez à: http://localhost:4200/employees")
        print("  Cliquez: 'Add Employee'")
        print("  Remplissez: Nom, Email, Téléphone, Job")
        print()
    
    if any("visage enregistré" in issue for issue in issues):
        print("✓ ÉTAPE 2: Enregistrer le visage")
        print("  Accédez à: http://localhost:4200/face-registration")
        print("  Sélectionnez l'employé")
        print("  Cliquez: 'Start Recording'")
        print("  Présentez votre visage à la caméra")
        print("  Cliquez: 'Capture'")
        print()
    
    if any("format invalide" in issue or "embedding" in issue for issue in issues):
        print("✓ ÉTAPE 3: Corriger les embeddings")
        print("  Exécutez: mysql -u root -proot123 attendance_db")
        print("  Puis: DELETE FROM employees WHERE embedding IS NULL;")
        print()
    
    if any("OpenCV" in issue or "InsightFace" in issue or "Connector" in issue for issue in issues):
        print("✓ ÉTAPE 4: Installer les dépendances")
        print("  Exécutez: pip install -r requirements.txt")
        print("  Ou: pip install opencv-python mysql-connector-python insightface fastapi uvicorn")
        print()

if __name__ == "__main__":
    issues = check_ai_issues()
    show_solutions(issues)
    
    print("\n" + "="*70)
    print("  💡 APRÈS CORRECTION, LANCEZ:")
    print("="*70)
    print("\n  Terminal 1: python main.py")
    print("  Terminal 2: python camera_ai_stream.py --source 0 --camera_id 1")
    print("\n" + "="*70 + "\n")

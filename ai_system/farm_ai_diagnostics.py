#!/usr/bin/env python3
"""
Farm-AI: Diagnostic automatique et correction des problèmes
Résout les 3 problèmes principaux:
1. Ajout d'employé
2. Système de caméra
3. Analyse AI
"""

import mysql.connector
import requests
import subprocess
import json
import sys
import os
from pathlib import Path
from mysql.connector import Error

class FarmAIDiagnostics:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.db = None
        self.cursor = None
        
    def print_header(self, msg):
        print(f"\n{'='*60}")
        print(f"  {msg}")
        print('='*60)
    
    def print_ok(self, msg):
        print(f"  ✓ {msg}")
        self.success_count += 1
        
    def print_error(self, msg):
        print(f"  ✗ {msg}")
        self.issues.append(msg)
        
    def print_warning(self, msg):
        print(f"  ⚠ {msg}")
        self.warnings.append(msg)
    
    # ==========================================
    # TEST 1: BASE DE DONNÉES
    # ==========================================
    def test_database(self):
        self.print_header("1️⃣  TEST: BASE DE DONNÉES MySQL")
        
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root123",
                database="attendance_db"
            )
            self.cursor = self.db.cursor()
            self.print_ok("Connexion MySQL établie")
            
            # Vérifier les tables essentielles
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            table_names = [t[0] for t in tables]
            
            required_tables = ['employees', 'departments', 'attendance']
            for table in required_tables:
                if table in table_names:
                    self.print_ok(f"Table '{table}' existe")
                else:
                    self.print_warning(f"Table '{table}' manquante")
            
            # Vérifier les employés
            self.cursor.execute("SELECT COUNT(*) FROM employees")
            count = self.cursor.fetchone()[0]
            print(f"  📊 {count} employé(s) en base")
            
            # Vérifier les employés avec embeddings
            self.cursor.execute("SELECT COUNT(*) FROM employees WHERE embedding IS NOT NULL")
            count_emb = self.cursor.fetchone()[0]
            print(f"  👤 {count_emb} employé(s) avec embeddings")
            
            if count_emb == 0:
                self.print_warning("Aucun employé avec embeddings - exécutez register_face.py")
                
        except Error as e:
            self.print_error(f"Erreur MySQL: {e}")
            return False
            
        return True
    
    # ==========================================
    # TEST 2: BACKEND API
    # ==========================================
    def test_backend_api(self):
        self.print_header("2️⃣  TEST: BACKEND SPRING BOOT (Port 8081)")
        
        try:
            response = requests.get("http://localhost:8081/api/employees", timeout=5)
            if response.status_code == 200:
                employees = response.json()
                self.print_ok(f"API répond - {len(employees)} employé(s)")
                return True
            else:
                self.print_error(f"API retourne: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("Backend non accessible (vérifiez port 8081)")
            return False
        except Exception as e:
            self.print_error(f"Erreur API: {e}")
            return False
    
    # ==========================================
    # TEST 3: CAMÉRA
    # ==========================================
    def test_camera(self):
        self.print_header("3️⃣  TEST: CAMÉRA ET OPENCV")
        
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self.print_ok("Caméra 0 détectée et fonctionnelle")
                    return True
                else:
                    self.print_warning("Caméra détectée mais pas d'image")
                    return False
            else:
                self.print_error("Caméra 0 non disponible")
                return False
        except Exception as e:
            self.print_error(f"Erreur caméra: {e}")
            return False
    
    # ==========================================
    # TEST 4: MODÈLES IA
    # ==========================================
    def test_ai_models(self):
        self.print_header("4️⃣  TEST: MODÈLES IA (InsightFace)")
        
        try:
            from insightface.app import FaceAnalysis
            print("  ⏳ Chargement du modèle buffalo_l...")
            app = FaceAnalysis(name='buffalo_l')
            app.prepare(ctx_id=0, det_size=(320, 320))
            self.print_ok("Modèle InsightFace chargé")
            return True
        except Exception as e:
            self.print_error(f"Erreur modèle IA: {e}")
            return False
    
    # ==========================================
    # TEST 5: AJOUTER UN EMPLOYÉ TEST
    # ==========================================
    def test_create_employee(self):
        self.print_header("5️⃣  TEST: AJOUT D'EMPLOYÉ")
        
        if not self.db:
            self.print_error("Base de données non connectée")
            return False
        
        try:
            # Insérer directement en base
            employee_data = {
                'name': 'Test Employee',
                'email': 'test@farm.com',
                'phone': '1234567890',
                'job': 'WORKER',
                'status': 'PENDING',
                'faceRegistered': False,
                'available': True
            }
            
            sql = """
            INSERT INTO employees (name, email, phone, job, status, face_registered, available, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            values = (
                employee_data['name'],
                employee_data['email'],
                employee_data['phone'],
                employee_data['job'],
                employee_data['status'],
                employee_data['faceRegistered'],
                employee_data['available']
            )
            
            self.cursor.execute(sql, values)
            self.db.commit()
            
            # Récupérer l'ID
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            emp_id = self.cursor.fetchone()[0]
            
            self.print_ok(f"Employé créé: ID={emp_id}, Email={employee_data['email']}")
            print(f"  → Utilisez cet ID pour enregistrer le visage")
            return True
            
        except Error as e:
            self.print_error(f"Erreur création employé: {e}")
            return False
    
    # ==========================================
    # CORRECTIFS AUTOMATIQUES
    # ==========================================
    def fix_issues(self):
        self.print_header("🔧 CORRECTIFS AUTOMATIQUES")
        
        if not self.issues:
            self.print_ok("Aucun problème critique détecté!")
            return
        
        # Proposer des corrections
        for issue in self.issues:
            print(f"\n  Problème: {issue}")
            if "MySQL" in issue:
                print("    → Démarrer MySQL: net start MySQL80 (Windows) ou sudo service mysql start (Linux)")
            elif "Backend" in issue:
                print("    → Démarrer le backend: cd backend && mvn spring-boot:run")
            elif "Caméra" in issue:
                print("    → Vérifier la caméra: python test_cam.py")
                print("    → Ou spécifier une autre source: --source 1")
            elif "IA" in issue:
                print("    → Installer les dépendances: pip install -r requirements.txt")
    
    # ==========================================
    # RAPPORT FINAL
    # ==========================================
    def generate_report(self):
        self.print_header("📊 RAPPORT FINAL")
        
        print(f"\n  ✓ Tests réussis: {self.success_count}")
        print(f"  ✗ Problèmes critiques: {len(self.issues)}")
        print(f"  ⚠ Avertissements: {len(self.warnings)}")
        
        if self.issues:
            print("\n  PROBLÈMES À RÉSOUDRE:")
            for i, issue in enumerate(self.issues, 1):
                print(f"    {i}. {issue}")
        
        if self.warnings:
            print("\n  AVERTISSEMENTS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"    {i}. {warning}")
        
        print("\n" + "="*60)
        if not self.issues:
            print("  ✓ Système prêt!")
        else:
            print("  ⚠ Des corrections sont nécessaires")
        print("="*60 + "\n")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("\n")
        print("╔════════════════════════════════════════════════════════╗")
        print("║          FARM-AI DIAGNOSTIC SYSTEM v1.0               ║")
        print("╚════════════════════════════════════════════════════════╝")
        
        self.test_database()
        self.test_backend_api()
        self.test_camera()
        self.test_ai_models()
        self.test_create_employee()
        
        self.fix_issues()
        self.generate_report()
        
        # Fermer la connexion
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

if __name__ == "__main__":
    diagnostics = FarmAIDiagnostics()
    diagnostics.run_all_tests()

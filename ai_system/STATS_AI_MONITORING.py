#!/usr/bin/env python3
"""
🤖 MONITORING - Vérifier les statistiques de l'IA en temps réel
Affiche: Employés reconnus, FPS, Détections, Taux de succès, etc.
"""

import mysql.connector
import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from mysql.connector import Error

class AIMonitoring:
    def __init__(self):
        self.db = None
        self.cursor = None
        self.connect_db()
        
    def connect_db(self):
        """Connecter à MySQL"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root123",
                database="attendance_db"
            )
            self.cursor = self.db.cursor(dictionary=True)
            print("✓ Connexion MySQL établie\n")
            return True
        except Error as e:
            print(f"✗ Erreur MySQL: {e}\n")
            return False
    
    def print_header(self, title):
        """Afficher un header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)
    
    # ==========================================
    # STAT 1: EMPLOYÉS EN BASE
    # ==========================================
    def get_employees_stats(self):
        """Statistiques sur les employés"""
        self.print_header("📊 STATISTIQUES EMPLOYÉS")
        
        try:
            # Total d'employés
            self.cursor.execute("SELECT COUNT(*) as total FROM employees")
            total = self.cursor.fetchone()['total']
            
            # Employés par statut
            self.cursor.execute("""
                SELECT status, COUNT(*) as count FROM employees 
                GROUP BY status
            """)
            statuses = self.cursor.fetchall()
            
            # Employés avec visage
            self.cursor.execute("SELECT COUNT(*) as count FROM employees WHERE embedding IS NOT NULL")
            with_face = self.cursor.fetchone()['count']
            
            # Employés approuvés
            self.cursor.execute("SELECT COUNT(*) as count FROM employees WHERE status = 'APPROVED'")
            approved = self.cursor.fetchone()['count']
            
            print(f"\n  📍 Total d'employés: {total}")
            print(f"  👤 Avec visage enregistré: {with_face} ({100*with_face//max(1,total)}%)")
            print(f"  ✅ Approuvés: {approved} ({100*approved//max(1,total)}%)")
            
            print(f"\n  État par statut:")
            for status_row in statuses:
                status = status_row['status']
                count = status_row['count']
                print(f"    - {status}: {count}")
            
            return total, with_face, approved
            
        except Error as e:
            print(f"  ✗ Erreur: {e}")
            return 0, 0, 0
    
    # ==========================================
    # STAT 2: DÉTAILS EMPLOYÉS
    # ==========================================
    def get_employees_details(self):
        """Liste détaillée des employés"""
        self.print_header("👥 DÉTAILS EMPLOYÉS")
        
        try:
            self.cursor.execute("""
                SELECT id, name, email, status, 
                       IF(embedding IS NOT NULL, 'OUI', 'NON') as has_face
                FROM employees
                ORDER BY id
            """)
            employees = self.cursor.fetchall()
            
            if not employees:
                print("\n  ⚠️  Aucun employé en base")
                return
            
            print(f"\n  {'ID':<5} {'NOM':<20} {'EMAIL':<25} {'STATUS':<12} {'VISAGE':<8}")
            print("  " + "-"*70)
            
            for emp in employees:
                emp_id = emp['id']
                name = emp['name'][:20]
                email = emp['email'][:25]
                status = emp['status']
                face = emp['has_face']
                
                # Couleur du visage
                face_icon = "✓" if face == "OUI" else "✗"
                
                print(f"  {emp_id:<5} {name:<20} {email:<25} {status:<12} {face_icon}")
        
        except Error as e:
            print(f"  ✗ Erreur: {e}")
    
    # ==========================================
    # STAT 3: QUALITÉ DES EMBEDDINGS
    # ==========================================
    def get_embeddings_quality(self):
        """Vérifier la qualité des embeddings"""
        self.print_header("🔍 QUALITÉ DES EMBEDDINGS")
        
        try:
            self.cursor.execute("""
                SELECT id, name, embedding 
                FROM employees 
                WHERE embedding IS NOT NULL
                ORDER BY id
            """)
            employees = self.cursor.fetchall()
            
            if not employees:
                print("\n  ⚠️  Aucun embedding en base")
                return
            
            total = len(employees)
            valid = 0
            invalid = []
            dimensions_list = []
            
            print(f"\n  Vérification de {total} embedding(s)...\n")
            
            for emp in employees:
                emp_id = emp['id']
                name = emp['name']
                emb_json = emp['embedding']
                
                try:
                    emb_array = json.loads(emb_json)
                    if isinstance(emb_array, list) and len(emb_array) > 0:
                        valid += 1
                        dimensions_list.append(len(emb_array))
                        # Afficher en vert
                        print(f"  ✓ {name} (ID {emp_id}): {len(emb_array)} dimensions")
                    else:
                        invalid.append((emp_id, name, "Format invalide"))
                        print(f"  ✗ {name} (ID {emp_id}): Format invalide")
                except json.JSONDecodeError:
                    invalid.append((emp_id, name, "JSON invalide"))
                    print(f"  ✗ {name} (ID {emp_id}): JSON invalide")
            
            print(f"\n  📊 Résumé:")
            print(f"     ✓ Valides: {valid}/{total}")
            print(f"     ✗ Invalides: {len(invalid)}/{total}")
            
            if dimensions_list:
                avg_dim = sum(dimensions_list) // len(dimensions_list)
                print(f"     📐 Dimensions moyennes: {avg_dim}")
            
            return valid, len(invalid)
            
        except Error as e:
            print(f"  ✗ Erreur: {e}")
            return 0, 0
    
    # ==========================================
    # STAT 4: RECONNAISSANCE EN TEMPS RÉEL
    # ==========================================
    def get_recognition_stats(self):
        """Statistiques de reconnaissance (depuis l'API)"""
        self.print_header("🎯 RECONNAISSANCE EN TEMPS RÉEL")
        
        try:
            # Vérifier que le serveur backend répond
            response = requests.get("http://localhost:8081/api/ai/stats", timeout=5)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n  ✓ Backend actif")
                print(f"  📸 Caméras actives: {stats.get('cameras_active', 0)}")
                print(f"  👤 Derniers reconnus: {stats.get('last_recognized', [])}")
            else:
                print(f"  ⚠️  Backend retourne: {response.status_code}")
                print("  → Vérifiez: mvn spring-boot:run")
        
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Backend non accessible (port 8081)")
            print("  → Démarrez le backend: cd backend && mvn spring-boot:run")
        except Exception as e:
            print(f"  ✗ Erreur API: {e}")
    
    # ==========================================
    # STAT 5: HISTORIQUE DE RECONNAISSANCE
    # ==========================================
    def get_attendance_history(self):
        """Historique des reconnaissances"""
        self.print_header("📜 HISTORIQUE DE RECONNAISSANCE")
        
        try:
            # Vérifier si table attendance existe
            self.cursor.execute("SHOW TABLES LIKE 'attendance'")
            if not self.cursor.fetchone():
                print("\n  ⚠️  Table 'attendance' n'existe pas")
                return
            
            # Reconnaissances de la dernière heure
            self.cursor.execute("""
                SELECT e.name, a.timestamp, a.confidence
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                WHERE a.timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY a.timestamp DESC
                LIMIT 20
            """)
            records = self.cursor.fetchall()
            
            if not records:
                print("\n  ⚠️  Aucune reconnaissance dans la dernière heure")
                return
            
            print(f"\n  Dernier(s) {len(records)} reconnaissances:")
            print(f"  {'NOM':<20} {'HEURE':<20} {'CONFIANCE':<15}")
            print("  " + "-"*55)
            
            for record in records:
                name = record['name'][:20]
                timestamp = record['timestamp'].strftime("%H:%M:%S")
                confidence = record.get('confidence', 'N/A')
                
                print(f"  {name:<20} {timestamp:<20} {confidence}")
            
            # Statistiques
            self.cursor.execute("""
                SELECT COUNT(*) as total, COUNT(DISTINCT employee_id) as unique_employees
                FROM attendance
                WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            stats = self.cursor.fetchone()
            
            print(f"\n  📊 Dernière heure:")
            print(f"     Détections: {stats['total']}")
            print(f"     Employés uniques: {stats['unique_employees']}")
            
        except Error as e:
            print(f"  ✗ Erreur: {e}")
    
    # ==========================================
    # STAT 6: PERFORMANCE SYSTÈME
    # ==========================================
    def get_performance_stats(self):
        """Performance du système IA"""
        self.print_header("⚡ PERFORMANCE SYSTÈME")
        
        try:
            # Vérifier les processus Python actifs
            import psutil
            
            print("\n  🔍 Processus Python actifs:")
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in cmdline and ('camera' in cmdline or 'main.py' in cmdline):
                        print(f"     PID {proc.info['pid']}: {proc.info['name']}")
                        
                        # CPU et mémoire
                        with proc.oneshot():
                            cpu_percent = proc.cpu_percent(interval=0.1)
                            mem_mb = proc.memory_info().rss / 1024 / 1024
                            print(f"       CPU: {cpu_percent:.1f}% | RAM: {mem_mb:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        except ImportError:
            print("\n  ⚠️  psutil non installé")
            print("     pip install psutil")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
    
    # ==========================================
    # STAT 7: VÉRIFICATION DES SERVICES
    # ==========================================
    def check_services(self):
        """Vérifier l'état des services"""
        self.print_header("🔌 ÉTAT DES SERVICES")
        
        services = [
            ("Backend API", "http://localhost:8081/api/employees", 8081),
            ("Frontend", "http://localhost:4200", 4200),
            ("API IA", "http://localhost:8000/docs", 8000),
            ("MySQL", None, 3306),
        ]
        
        for service_name, url, port in services:
            try:
                if service_name == "MySQL":
                    # Déjà connecté, donc MySQL fonctionne
                    print(f"  ✓ {service_name:<15} PORT {port} - OK")
                else:
                    response = requests.get(url, timeout=2)
                    status = "✓ OK" if response.status_code < 400 else f"⚠️ {response.status_code}"
                    print(f"  {status:<2} {service_name:<15} PORT {port} - {url}")
            except requests.exceptions.ConnectionError:
                print(f"  ✗ {service_name:<15} PORT {port} - ARRÊTÉ")
            except Exception as e:
                print(f"  ✗ {service_name:<15} PORT {port} - ERREUR: {str(e)[:30]}")
    
    # ==========================================
    # RAPPORT COMPLET
    # ==========================================
    def generate_full_report(self):
        """Générer un rapport complet"""
        print("\n")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║         🤖 RAPPORT DE STATISTIQUES - ANALYSE IA FARM-AI           ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"\nDate/Heure: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        # Exécuter tous les tests
        total_emp, with_face, approved = self.get_employees_stats()
        self.get_employees_details()
        valid_emb, invalid_emb = self.get_embeddings_quality()
        self.get_recognition_stats()
        self.get_attendance_history()
        self.get_performance_stats()
        self.check_services()
        
        # Résumé final
        self.print_header("✅ RÉSUMÉ FINAL")
        
        print(f"\n  Employés: {total_emp}")
        print(f"  Avec visages: {with_face}/{total_emp}")
        print(f"  Embeddings valides: {valid_emb}")
        
        if total_emp > 0 and with_face == 0:
            print(f"\n  ⚠️  ACTION REQUISE: Enregistrez les visages!")
        elif total_emp > 0 and with_face > 0 and valid_emb == with_face:
            print(f"\n  ✅ SYSTÈME PRÊT: L'IA devrait fonctionner!")
        else:
            print(f"\n  ⚠️  Vérifiez les problèmes identifiés ci-dessus")
        
        print("\n" + "="*70 + "\n")
    
    def close(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

if __name__ == "__main__":
    monitoring = AIMonitoring()
    monitoring.generate_full_report()
    monitoring.close()

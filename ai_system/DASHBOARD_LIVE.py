#!/usr/bin/env python3
"""
🎯 DASHBOARD - Monitoring en temps réel de l'IA (mise à jour chaque seconde)
Affiche les statistiques en direct: FPS, Employés reconnus, Détections, etc.
"""

import mysql.connector
import time
import os
import json
from mysql.connector import Error
from datetime import datetime

class RealtimeDashboard:
    def __init__(self):
        self.db = None
        self.cursor = None
        self.frame_count = 0
        self.last_stats = {}
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
            return True
        except Error as e:
            print(f"✗ Erreur MySQL: {e}")
            return False
    
    def clear_screen(self):
        """Effacer l'écran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_stats(self):
        """Récupérer les statistiques"""
        try:
            # Total employés
            self.cursor.execute("SELECT COUNT(*) as total FROM employees")
            total_employees = self.cursor.fetchone()['total']
            
            # Employés avec visage
            self.cursor.execute("SELECT COUNT(*) as total FROM employees WHERE embedding IS NOT NULL")
            employees_with_face = self.cursor.fetchone()['total']
            
            # Employés approuvés
            self.cursor.execute("SELECT COUNT(*) as total FROM employees WHERE status = 'APPROVED'")
            approved_employees = self.cursor.fetchone()['total']
            
            # Dernière reconnaissance (si table existe)
            last_recognized = "N/A"
            last_time = "N/A"
            try:
                self.cursor.execute("""
                    SELECT e.name, a.timestamp 
                    FROM attendance a
                    JOIN employees e ON a.employee_id = e.id
                    ORDER BY a.timestamp DESC LIMIT 1
                """)
                result = self.cursor.fetchone()
                if result:
                    last_recognized = result['name']
                    last_time = result['timestamp'].strftime("%H:%M:%S")
            except:
                pass
            
            # Reconnaissances de l'heure
            recognitions_today = 0
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) as total FROM attendance 
                    WHERE DATE(timestamp) = CURDATE()
                """)
                recognitions_today = self.cursor.fetchone()['total']
            except:
                pass
            
            return {
                'total_employees': total_employees,
                'employees_with_face': employees_with_face,
                'approved': approved_employees,
                'last_recognized': last_recognized,
                'last_time': last_time,
                'recognitions_today': recognitions_today,
            }
        except Error as e:
            print(f"Erreur: {e}")
            return None
    
    def get_top_recognized(self, limit=5):
        """Top employés reconnus d'aujourd'hui"""
        try:
            self.cursor.execute(f"""
                SELECT e.name, COUNT(*) as count
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                WHERE DATE(a.timestamp) = CURDATE()
                GROUP BY e.id, e.name
                ORDER BY count DESC
                LIMIT {limit}
            """)
            return self.cursor.fetchall()
        except:
            return []
    
    def get_status_by_time(self):
        """Statistiques par heure"""
        try:
            self.cursor.execute("""
                SELECT HOUR(timestamp) as hour, COUNT(*) as count
                FROM attendance
                WHERE DATE(timestamp) = CURDATE()
                GROUP BY HOUR(timestamp)
                ORDER BY hour DESC
                LIMIT 5
            """)
            return self.cursor.fetchall()
        except:
            return []
    
    def render_dashboard(self):
        """Afficher le dashboard"""
        self.clear_screen()
        
        print("\n")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║          🎯 DASHBOARD - MONITORING IA FARM-AI                 ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\n⏱️  Heure: {current_time}\n")
        
        stats = self.get_stats()
        
        if not stats:
            print("✗ Impossible de récupérer les statistiques")
            return
        
        # SECTION 1: STATISTIQUES PRINCIPALES
        print("┌─ 📊 STATISTIQUES PRINCIPALES ─────────────────────────────────┐")
        print(f"│")
        print(f"│  👥 Employés total:              {stats['total_employees']:<40}")
        print(f"│  👤 Avec visage enregistré:      {stats['employees_with_face']:<40}")
        print(f"│  ✅ Approuvés:                  {stats['approved']:<40}")
        
        # Calculer les pourcentages
        if stats['total_employees'] > 0:
            pct_face = (stats['employees_with_face'] * 100) // stats['total_employees']
            pct_approved = (stats['approved'] * 100) // stats['total_employees']
            print(f"│  📈 % avec visage:              {pct_face}%")
            print(f"│  📈 % approuvés:                {pct_approved}%")
        
        print(f"│")
        print("└────────────────────────────────────────────────────────────────┘")
        
        # SECTION 2: RECONNAISSANCES
        print("\n┌─ 🎯 RECONNAISSANCES ──────────────────────────────────────────┐")
        print(f"│")
        print(f"│  📸 Dernière reconnaissance:     {stats['last_recognized']:<40}")
        print(f"│  ⏱️  À {stats['last_time']:<41}")
        print(f"│  📊 Reconnaissances aujourd'hui: {stats['recognitions_today']:<40}")
        print(f"│")
        print("└────────────────────────────────────────────────────────────────┘")
        
        # SECTION 3: TOP EMPLOYÉS RECONNUS
        top_recognized = self.get_top_recognized()
        if top_recognized:
            print("\n┌─ 🏆 TOP EMPLOYÉS (dernières 24h) ────────────────────────────┐")
            print(f"│")
            for i, person in enumerate(top_recognized, 1):
                name = person['name'][:35]
                count = person['count']
                bar = "█" * (count // 5)
                print(f"│  {i}. {name:<35} {count:<5} {bar}")
            print(f"│")
            print("└────────────────────────────────────────────────────────────────┘")
        
        # SECTION 4: STATISTIQUES PAR HEURE
        stats_by_hour = self.get_status_by_time()
        if stats_by_hour:
            print("\n┌─ 📈 RECONNAISSANCES PAR HEURE ────────────────────────────────┐")
            print(f"│")
            for stat in stats_by_hour:
                hour = stat['hour']
                count = stat['count']
                bar = "▓" * (count // 2)
                print(f"│  {hour:02d}:00 │ {count:<3} {bar}")
            print(f"│")
            print("└────────────────────────────────────────────────────────────────┘")
        
        # SECTION 5: ÉTAT DU SYSTÈME
        print("\n┌─ 🔌 ÉTAT DU SYSTÈME ──────────────────────────────────────────┐")
        print(f"│")
        
        # Vérifier la connexion
        status_color = "✓" if self.db and self.db.is_connected() else "✗"
        print(f"│  {status_color} Base de données:       CONNECTÉE")
        
        # Vérifier s'il y a de la reconnaissance
        if stats['recognitions_today'] > 0:
            print(f"│  ✓ IA:                 ACTIF (détections en cours)")
        else:
            print(f"│  ⚠️  IA:                 INACTIF (aucune détection)")
        
        # Vérifier la configuration
        if stats['total_employees'] > 0 and stats['employees_with_face'] > 0:
            print(f"│  ✓ Configuration:      OK - Prêt pour reconnaissance")
        else:
            print(f"│  ⚠️  Configuration:      À configurer")
        
        print(f"│")
        print("└────────────────────────────────────────────────────────────────┘")
        
        # SECTION 6: COMMANDES UTILES
        print("\n┌─ 💡 COMMANDES UTILES ────────────────────────────────────────┐")
        print(f"│")
        print(f"│  Démarrer l'IA:     python main.py")
        print(f"│  Lancer caméra:     python camera_ai_stream.py --source 0 --camera_id 1")
        print(f"│  Enregistrer:       python register_face.py --employee_id 1")
        print(f"│  Diagnostic:        python CHECK_AI_PROBLEMS.py")
        print(f"│")
        print("└────────────────────────────────────────────────────────────────┘")
        
        print(f"\n  ⏱️  Mise à jour dans 5 secondes... (Appuyez Ctrl+C pour arrêter)\n")
    
    def run_live(self, update_interval=5):
        """Lancer le dashboard en temps réel"""
        try:
            while True:
                self.render_dashboard()
                time.sleep(update_interval)
        except KeyboardInterrupt:
            self.clear_screen()
            print("\n👋 Dashboard arrêté\n")
        finally:
            self.close()
    
    def close(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

if __name__ == "__main__":
    import sys
    
    # Vérifier les arguments
    update_interval = 5
    if len(sys.argv) > 1:
        try:
            update_interval = int(sys.argv[1])
        except:
            pass
    
    dashboard = RealtimeDashboard()
    dashboard.run_live(update_interval)

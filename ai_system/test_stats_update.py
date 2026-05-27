#!/usr/bin/env python3
"""
🧪 TEST - Générer des données de test pour mettre à jour les statistiques
Cet script insère des données fictives dans la base de données pour tester
le rafraîchissement automatique des statistiques du dashboard
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import time
import random

class TestStatsGenerator:
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
            print("✅ Connexion MySQL établie\n")
            return True
        except Error as e:
            print(f"❌ Erreur MySQL: {e}\n")
            return False
    
    def get_or_create_employee(self):
        """Récupérer ou créer un employé de test"""
        try:
            # Vérifier si un employé de test existe
            self.cursor.execute("""
                SELECT id FROM employees 
                WHERE name LIKE 'Test%' 
                LIMIT 1
            """)
            result = self.cursor.fetchone()
            
            if result:
                return result['id']
            
            # Créer un nouvel employé de test
            self.cursor.execute("""
                INSERT INTO employees (name, email, embedding, status, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, ('Test Employee', 'test@farm.com', b'test_embedding', 'APPROVED'))
            self.db.commit()
            
            print("✅ Employé de test créé\n")
            return self.cursor.lastrowid
            
        except Error as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def insert_attendance_record(self, employee_id):
        """Insérer un enregistrement de présence"""
        try:
            now = datetime.now()
            
            self.cursor.execute("""
                INSERT INTO attendance (employee_id, timestamp, created_at)
                VALUES (%s, %s, NOW())
            """, (employee_id, now))
            self.db.commit()
            
            print(f"✅ Présence enregistrée à {now.strftime('%H:%M:%S')}")
            return True
            
        except Error as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def update_random_attendance(self, employee_id):
        """Mettre à jour un enregistrement de présence avec une heure aléatoire"""
        try:
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            timestamp = datetime.now() - timedelta(hours=hours_ago, minutes=minutes_ago)
            
            self.cursor.execute("""
                INSERT INTO attendance (employee_id, timestamp, created_at)
                VALUES (%s, %s, NOW())
            """, (employee_id, timestamp))
            self.db.commit()
            
            print(f"✅ Présence ajoutée pour {hours_ago}h {minutes_ago}m ago")
            return True
            
        except Error as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def show_current_stats(self):
        """Afficher les statistiques actuelles"""
        try:
            # Total présences
            self.cursor.execute("SELECT COUNT(*) as total FROM attendance")
            total = self.cursor.fetchone()['total']
            
            # Présences d'aujourd'hui
            self.cursor.execute("""
                SELECT COUNT(*) as total FROM attendance 
                WHERE DATE(timestamp) = CURDATE()
            """)
            today = self.cursor.fetchone()['total']
            
            # Total employés
            self.cursor.execute("SELECT COUNT(*) as total FROM employees")
            employees = self.cursor.fetchone()['total']
            
            print("\n" + "="*60)
            print("📊 STATISTIQUES ACTUELLES")
            print("="*60)
            print(f"👥 Total employés: {employees}")
            print(f"📝 Total présences: {total}")
            print(f"📅 Présences aujourd'hui: {today}")
            print("="*60 + "\n")
            
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def run_continuous_test(self, duration_seconds=60, interval_seconds=5):
        """Exécuter un test continu qui génère des données toutes les X secondes"""
        employee_id = self.get_or_create_employee()
        
        if not employee_id:
            print("❌ Impossible de créer/récupérer un employé")
            return
        
        print(f"🔄 Test en cours - Les données changeront toutes les {interval_seconds} secondes")
        print(f"⏱️  Durée: {duration_seconds} secondes\n")
        print("👉 Ouvrez http://localhost:4200/#/dashboard/analytics dans votre navigateur\n")
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < duration_seconds:
            count += 1
            print(f"\n🔄 Insertion #{count} à {datetime.now().strftime('%H:%M:%S')}")
            
            # Ajouter de nouvelles données
            for _ in range(random.randint(1, 3)):
                self.insert_attendance_record(employee_id)
                time.sleep(0.5)
            
            self.show_current_stats()
            
            # Attendre avant la prochaine insertion
            remaining = duration_seconds - (time.time() - start_time)
            if remaining > 0:
                print(f"⏳ Prochaine insertion dans {interval_seconds}s...")
                time.sleep(interval_seconds)
        
        print("\n✅ Test terminé!\n")
    
    def manual_test(self):
        """Mode manuel - ajouter des enregistrements manuellement"""
        employee_id = self.get_or_create_employee()
        
        if not employee_id:
            print("❌ Impossible de créer/récupérer un employé")
            return
        
        print("\n" + "="*60)
        print("🧪 MODE MANUEL - Ajouter des données de test")
        print("="*60)
        print("1. Ajouter une présence (maintenant)")
        print("2. Ajouter 5 présences aléatoires")
        print("3. Afficher les statistiques")
        print("4. Quitter")
        print("="*60 + "\n")
        
        while True:
            try:
                choice = input("Choisissez une option (1-4): ").strip()
                
                if choice == '1':
                    self.insert_attendance_record(employee_id)
                    self.show_current_stats()
                
                elif choice == '2':
                    for i in range(5):
                        self.update_random_attendance(employee_id)
                        time.sleep(0.5)
                    self.show_current_stats()
                
                elif choice == '3':
                    self.show_current_stats()
                
                elif choice == '4':
                    print("👋 Au revoir!")
                    break
                
                else:
                    print("❌ Option invalide\n")
                
            except KeyboardInterrupt:
                print("\n👋 Interrompu par l'utilisateur")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}\n")
    
    def close_db(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()


if __name__ == "__main__":
    generator = TestStatsGenerator()
    
    print("\n" + "="*60)
    print("🧪 GÉNÉRATEUR DE DONNÉES DE TEST - Farm-AI")
    print("="*60)
    print("1. Test automatique (60s, mise à jour toutes les 5s)")
    print("2. Test automatique (120s, mise à jour toutes les 3s)")
    print("3. Mode manuel")
    print("="*60 + "\n")
    
    try:
        choice = input("Choisissez un mode (1-3): ").strip()
        
        if choice == '1':
            generator.run_continuous_test(duration_seconds=60, interval_seconds=5)
        
        elif choice == '2':
            generator.run_continuous_test(duration_seconds=120, interval_seconds=3)
        
        elif choice == '3':
            generator.manual_test()
        
        else:
            print("❌ Option invalide")
    
    except KeyboardInterrupt:
        print("\n👋 Test interrompu")
    
    finally:
        generator.close_db()

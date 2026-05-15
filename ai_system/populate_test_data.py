#!/usr/bin/env python3
"""
📊 POPULATE TEST DATA - Ajouter des employés, gestionnaires et observateurs pour tester
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib

class TestDataPopulator:
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
    
    def hash_password(self, password):
        """Hacher le mot de passe avec bcrypt-like hash"""
        # Pour simplifier, on utilise SHA256 (en production, utiliser bcrypt)
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_admin_user(self):
        """Ajouter un utilisateur administrateur"""
        try:
            # Vérifier si admin existe déjà
            self.cursor.execute("SELECT id FROM users WHERE email = %s", ("admin@farm.com",))
            if self.cursor.fetchone():
                print("✅ Admin utilisateur existe déjà\n")
                return
            
            hashed_pwd = self.hash_password("admin123")
            self.cursor.execute("""
                INSERT INTO users (email, password, first_name, last_name, phone, role, enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, ("admin@farm.com", hashed_pwd, "Admin", "Farm", "+33 6 00 00 00 01", "ROLE_ADMIN", True))
            self.db.commit()
            print("✅ Administrateur créé: admin@farm.com / admin123\n")
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def add_managers(self):
        """Ajouter des gestionnaires/managers"""
        managers_data = [
            {
                "firstName": "Ahmed",
                "lastName": "Mansouri",
                "email": "ahmed.mansouri@farm.com",
                "phone": "+33 6 10 20 30 40",
                "password": "manager123"
            },
            {
                "firstName": "Fatima",
                "lastName": "Benali",
                "email": "fatima.benali@farm.com",
                "phone": "+33 6 11 21 31 41",
                "password": "manager123"
            },
            {
                "firstName": "Mohamed",
                "lastName": "Saidi",
                "email": "mohamed.saidi@farm.com",
                "phone": "+33 6 12 22 32 42",
                "password": "manager123"
            }
        ]
        
        try:
            for mgr in managers_data:
                # Vérifier si existe
                self.cursor.execute("SELECT id FROM users WHERE email = %s", (mgr["email"],))
                if self.cursor.fetchone():
                    print(f"⏭️  {mgr['firstName']} existe déjà")
                    continue
                
                hashed_pwd = self.hash_password(mgr["password"])
                self.cursor.execute("""
                    INSERT INTO users (email, password, first_name, last_name, phone, role, enabled, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (mgr["email"], hashed_pwd, mgr["firstName"], mgr["lastName"], mgr["phone"], "ROLE_MANAGER", True))
                self.db.commit()
                print(f"✅ Gestionnaire créé: {mgr['firstName']} ({mgr['email']})")
            
            print()
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def add_employees(self):
        """Ajouter des employés"""
        employees_data = [
            {"name": "Ali Hassan", "email": "ali.hassan@farm.com", "phone": "+33 6 01 11 21 31", "job": "MECHANIC"},
            {"name": "Nadia Bouvier", "email": "nadia.bouvier@farm.com", "phone": "+33 6 02 12 22 32", "job": "DOCTOR"},
            {"name": "Ibrahim Khalil", "email": "ibrahim.khalil@farm.com", "phone": "+33 6 03 13 23 33", "job": "ELECTRICIAN"},
            {"name": "Leila Noor", "email": "leila.noor@farm.com", "phone": "+33 6 04 14 24 34", "job": "NURSE"},
            {"name": "Hassan Ahmed", "email": "hassan.ahmed@farm.com", "phone": "+33 6 05 15 25 35", "job": "MECHANIC"},
            {"name": "Amira El Ayouni", "email": "amira.elayouni@farm.com", "phone": "+33 6 06 16 26 36", "job": "DOCTOR"},
            {"name": "Omar Belaid", "email": "omar.belaid@farm.com", "phone": "+33 6 07 17 27 37", "job": "ENGINEER"},
            {"name": "Safia Brahim", "email": "safia.brahim@farm.com", "phone": "+33 6 08 18 28 38", "job": "ELECTRICIAN"},
        ]
        
        try:
            for emp in employees_data:
                # Vérifier si existe
                self.cursor.execute("SELECT id FROM employees WHERE name = %s", (emp["name"],))
                if self.cursor.fetchone():
                    print(f"⏭️  {emp['name']} existe déjà")
                    continue
                
                self.cursor.execute("""
                    INSERT INTO employees (name, email, phone, job, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (emp["name"], emp["email"], emp["phone"], emp["job"], "PENDING"))
                self.db.commit()
                print(f"✅ Employé créé: {emp['name']} ({emp['job']})")
            
            print()
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def add_attendance_records(self):
        """Ajouter des enregistrements de présence pour aujourd'hui"""
        try:
            # Obtenir les employés
            self.cursor.execute("SELECT id FROM employees LIMIT 5")
            employees = self.cursor.fetchall()
            
            if not employees:
                print("⚠️  Aucun employé trouvé\n")
                return
            
            # Ajouter des présences
            for emp in employees:
                self.cursor.execute("""
                    INSERT INTO attendance (employee_id, timestamp, created_at)
                    VALUES (%s, NOW(), NOW())
                """, (emp["id"],))
                self.db.commit()
            
            print(f"✅ {len(employees)} enregistrements de présence ajoutés\n")
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def add_cameras(self):
        """Ajouter des caméras"""
        cameras_data = [
            {"name": "Caméra Entrée", "location": "Entrée Principale", "source": "rtsp://localhost:8554/stream", "status": "ACTIVE"},
            {"name": "Caméra Bureau", "location": "Bureau Admin", "source": "rtsp://localhost:8555/stream", "status": "ACTIVE"},
            {"name": "Caméra Atelier", "location": "Atelier Production", "source": "rtsp://localhost:8556/stream", "status": "INACTIVE"},
            {"name": "Caméra Stockage", "location": "Zone Stockage", "source": "rtsp://localhost:8557/stream", "status": "ACTIVE"},
        ]
        
        try:
            for cam in cameras_data:
                # Vérifier si existe
                self.cursor.execute("SELECT id FROM cameras WHERE name = %s", (cam["name"],))
                if self.cursor.fetchone():
                    print(f"⏭️  {cam['name']} existe déjà")
                    continue
                
                self.cursor.execute("""
                    INSERT INTO cameras (name, location, source, status, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (cam["name"], cam["location"], cam["source"], cam["status"]))
                self.db.commit()
                print(f"✅ Caméra créée: {cam['name']} ({cam['location']})")
            
            print()
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def show_summary(self):
        """Afficher un résumé des données"""
        try:
            self.cursor.execute("SELECT COUNT(*) as total FROM users")
            users_count = self.cursor.fetchone()["total"]
            
            self.cursor.execute("SELECT COUNT(*) as total FROM employees")
            employees_count = self.cursor.fetchone()["total"]
            
            self.cursor.execute("SELECT COUNT(*) as total FROM cameras")
            cameras_count = self.cursor.fetchone()["total"]
            
            self.cursor.execute("SELECT COUNT(*) as total FROM attendance")
            attendance_count = self.cursor.fetchone()["total"]
            
            print("="*60)
            print("📊 RÉSUMÉ DES DONNÉES")
            print("="*60)
            print(f"👥 Utilisateurs: {users_count}")
            print(f"💼 Employés: {employees_count}")
            print(f"📷 Caméras: {cameras_count}")
            print(f"📝 Enregistrements de présence: {attendance_count}")
            print("="*60 + "\n")
        except Error as e:
            print(f"❌ Erreur: {e}")
    
    def run(self):
        """Exécuter la population des données"""
        print("\n" + "="*60)
        print("🌱 REMPLISSAGE DES DONNÉES DE TEST")
        print("="*60 + "\n")
        
        self.add_admin_user()
        self.add_managers()
        self.add_employees()
        self.add_cameras()
        self.add_attendance_records()
        self.show_summary()
        
        print("✅ Données de test ajoutées avec succès !\n")
    
    def close_db(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()


if __name__ == "__main__":
    populator = TestDataPopulator()
    try:
        populator.run()
    except KeyboardInterrupt:
        print("\n👋 Interrompu par l'utilisateur")
    finally:
        populator.close_db()

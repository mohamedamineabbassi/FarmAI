# 🚜 FARM-AI - GUIDE COMPLET D'INSTALLATION ET DÉPANNAGE

## 📋 PRÉREQUIS

### 1. **Base de Données MySQL**
```bash
# Installer MySQL (si pas déjà installé)
# Windows: https://dev.mysql.com/downloads/mysql/
# Linux: sudo apt-get install mysql-server

# Démarrer le service MySQL
mysql -u root -p

# Créer la base de données (si elle n'existe pas)
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE attendance_db;
```

### 2. **Backend Spring Boot**
```bash
cd backend
mvn clean install
mvn spring-boot:run  # Lance sur port 8081
```

### 3. **Dépendances Python**
```bash
cd ai_system
pip install -r requirements.txt

# Ou manuellement:
pip install opencv-python mysql-connector-python fastapi uvicorn insightface
```

### 4. **Frontend Angular**
```bash
cd forntend
npm install
ng serve  # Lance sur http://localhost:4200
```

---

## 🔍 DIAGNOSTIC - Vérifier que tout fonctionne

### **Étape 1: Tester MySQL**
```bash
cd ai_system
python test_system.py
```

✓ Si OK, vous devez voir:
```
✓ MySQL: OK
✓ Caméra: OK
✓ Modèles IA: OK
```

### **Étape 2: Tester Backend**
```bash
# Vérifier que le serveur répond
curl http://localhost:8081/api/employees

# Ajouter un employé (test)
curl -X POST http://localhost:8081/api/employees/employee \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "John Doe",
    "email": "john@farm.com",
    "phone": "1234567890",
    "job": "WORKER"
  }'
```

### **Étape 3: Tester Frontend**
- Ouvrir http://localhost:4200
- Naviguer vers la section "Employés"
- Tenter d'ajouter un nouvel employé

---

## ❌ SOLUTIONS AUX PROBLÈMES COURANTS

### **❌ Problème 1: "Impossible d'ajouter un employé"**

**Causes possibles:**
1. Authentification non configurée
2. Champs obligatoires manquants
3. Erreur de base de données

**Solution:**
```bash
# 1. Vérifier les logs du backend
tail -f backend/target/logs/spring.log

# 2. Vérifier que les champs requis sont présents:
# - name (obligatoire)
# - email (obligatoire)
# - job (obligatoire)
# - department (optionnel)

# 3. Vérifier la structure de la table employees
mysql -u root -p attendance_db -e "DESCRIBE employees;"
```

---

### **❌ Problème 2: "La caméra ne fonctionne pas"**

**Causes possibles:**
1. Caméra non disponible
2. OpenCV mal configurée
3. Numéro de caméra incorrect

**Solution:**
```bash
# 1. Vérifier la caméra
python ai_system/test_cam.py

# 2. Lancer avec numéro de caméra spécifique
python ai_system/camera_ai_stream.py --source 0 --camera_id 1

# 3. Si URL RTSP:
python ai_system/camera_ai_stream.py --source "rtsp://192.168.1.100:554/stream" --camera_id 1
```

---

### **❌ Problème 3: "L'analyse AI n'est pas lancée"**

**Causes possibles:**
1. MySQL non connectée
2. Employés sans embeddings
3. Modèle IA non chargé

**Solution:**
```bash
# 1. Vérifier MySQL
python -c "
import mysql.connector
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root123',
    database='attendance_db'
)
print('✓ MySQL OK')
db.close()
"

# 2. Vérifier les employés avec embeddings
mysql -u root -p attendance_db -e "SELECT COUNT(*) FROM employees WHERE embedding IS NOT NULL;"

# 3. Lancer le FastAPI main.py
python ai_system/main.py

# 4. Enregistrer des visages d'employés (voir section ci-dessous)
```

---

## 👤 AJOUTER UN EMPLOYÉ - WORKFLOW COMPLET

### **Étape 1: Créer l'employé (Backend)**
```bash
POST /api/employees/employee
{
  "name": "Ahmed",
  "email": "ahmed@farm.com",
  "phone": "0612345678",
  "job": "WORKER",  # ou DOCTOR, ELECTRICIAN
  "department": null
}
```
→ Status: **PENDING** (en attente)

### **Étape 2: Enregistrer le visage (Face Registration)**
```bash
# Lancer le script d'enregistrement
python ai_system/register_face.py --employee_id 1

# Ou via Frontend:
# 1. Aller à "Face Registration"
# 2. Sélectionner l'employé
# 3. Cliquer "Start Recording"
# 4. Présenter le visage à la caméra
# 5. Cliquer "Save" quand prêt
```
→ Status: **Embedding enregistré**

### **Étape 3: Valider le visage (Viewer)**
```bash
PUT /api/employees/validate-face/{id}
```
→ `faceRegistered = true`

### **Étape 4: Approuver l'employé (Admin)**
```bash
POST /api/employees/approve/{id}
```
→ Status: **APPROVED** (actif)

---

## 🎥 LANCER LES CAMÉRAS ET L'ANALYSE

### **Caméra 1: Face Recognition**
```bash
python ai_system/camera_ai_stream.py --source 0 --camera_id 1
```

### **Caméra 2: Clothes Detection**
```bash
python ai_system/clothes_live.py --source 1 --camera_id 2
```

### **Démarrer le serveur FastAPI**
```bash
python ai_system/main.py
# Lance sur http://localhost:8000
```

---

## 📊 VÉRIFIER LES EMBEDDINGS

```bash
# Lister tous les employés avec embeddings
mysql -u root -p attendance_db -e "
SELECT id, name, 
       IF(embedding IS NOT NULL, 'OUI', 'NON') as embedding 
FROM employees;
"

# Voir les détails d'un employé
mysql -u root -p attendance_db -e "
SELECT * FROM employees WHERE id = 1;
"
```

---

## 🛠️ RECONSTRUCTION COMPLÈTE

Si rien ne fonctionne, faire une réinitialisation complète:

```bash
# 1. Arrêter tous les services
# (Ctrl+C dans tous les terminaux)

# 2. Nettoyer les données anciennes
mysql -u root -p attendance_db -e "DROP DATABASE attendance_db;"
mysql -u root -p -e "CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Reconstruire le backend
cd backend
mvn clean install
mvn spring-boot:run

# 4. Dans un nouveau terminal, lancer le frontend
cd forntend
npm install
ng serve

# 5. Dans un nouveau terminal, lancer Python AI
cd ai_system
python main.py

# 6. Tester
python test_system.py
```

---

## 📞 DÉPANNAGE AVANCÉ

### **Vérifier les ports en utilisation**
```bash
# Windows
netstat -ano | findstr :8081
netstat -ano | findstr :4200
netstat -ano | findstr :3306
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8081
lsof -i :4200
lsof -i :3306
lsof -i :8000
```

### **Logs en temps réel**
```bash
# Backend (Spring Boot)
tail -f backend/target/logs/spring.log

# Frontend (Angular)
ng serve --verbose

# Python (AI)
python ai_system/camera_ai_stream.py --source 0 --camera_id 1
```

---

## ✅ CHECKLIST FINAL

- [ ] MySQL fonctionne
- [ ] Backend démarre sans erreurs
- [ ] Frontend affiche correctement
- [ ] Employé créé avec succès
- [ ] Visage enregistré
- [ ] Caméra connectée
- [ ] Analyse AI active
- [ ] API répond aux requêtes

Bonne chance! 🌾

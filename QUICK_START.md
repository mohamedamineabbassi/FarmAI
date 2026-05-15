# 🚜 FARM-AI - QUICK START GUIDE

## 🔥 DÉMARRAGE RAPIDE (5 minutes)

### **OPTION 1: Démarrage automatique (Recommandé)**

#### Sur Windows:
```bash
# Double-cliquez sur:
START_ALL_WINDOWS.bat
```

#### Sur Linux/Mac:
```bash
chmod +x start_all.sh
./start_all.sh
```

### **OPTION 2: Démarrage manuel**

**Terminal 1 - Backend:**
```bash
cd backend
mvn spring-boot:run
```

**Terminal 2 - Frontend:**
```bash
cd forntend
npm install
ng serve
```

**Terminal 3 - API IA:**
```bash
cd ai_system
python main.py
```

**Terminal 4 - Caméra:**
```bash
cd ai_system
python camera_ai_stream.py --source 0 --camera_id 1
```

---

## 🔍 AVANT DE COMMENCER

### Vérifier que tout fonctionne:
```bash
cd ai_system
python farm_ai_diagnostics.py
```

✓ Vérifiez que tout passe au vert!

---

## 👤 AJOUTER UN EMPLOYÉ

### Workflow:
1. **Accédez au frontend**: http://localhost:4200
2. **Menu**: "Employees" → "Add Employee"
3. **Remplissez**:
   - Nom: Ahmed
   - Email: ahmed@farm.com
   - Téléphone: 0612345678
   - Job: WORKER
4. **Cliquez**: "Create"
5. **Enregistrez le visage**:
   - Allez à "Face Registration"
   - Sélectionnez l'employé créé
   - Présentez votre visage à la caméra
   - Cliquez "Capture"
6. **Admin approuve**: "Employees" → "Approve"

---

## 📊 VÉRIFIER LES DONNÉES

```bash
# Voir tous les employés
mysql -u root -proot123 attendance_db -e "SELECT * FROM employees;"

# Voir les employés avec embeddings (visages enregistrés)
mysql -u root -proot123 attendance_db -e "
SELECT id, name, 
       IF(embedding IS NOT NULL, '✓', '✗') as visage 
FROM employees;"
```

---

## 🚀 LANCER LES CAMÉRAS

### Caméra 1 - Face Recognition:
```bash
cd ai_system
python camera_ai_stream.py --source 0 --camera_id 1
```

### Caméra 2 - Clothes Detection:
```bash
cd ai_system
python clothes_live.py --source 1 --camera_id 2
```

### Avec URL RTSP (IP Camera):
```bash
python camera_ai_stream.py --source "rtsp://192.168.1.100:554/stream" --camera_id 1
```

---

## ✅ ACCÈS À L'APPLICATION

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:4200 | 4200 |
| Backend API | http://localhost:8081 | 8081 |
| API IA | http://localhost:8000/docs | 8000 |
| MySQL | localhost | 3306 |

---

## ❌ PROBLÈMES COURANTS

### "L'employé ne s'ajoute pas"
```bash
# Vérifier la base de données
mysql -u root -proot123 -e "SHOW DATABASES;"

# Vérifier la table
mysql -u root -proot123 attendance_db -e "DESCRIBE employees;"
```

### "La caméra ne fonctionne pas"
```bash
# Tester la caméra
cd ai_system
python test_system.py
```

### "L'IA ne démarre pas"
```bash
# Vérifier les dépendances
pip install -r ai_system/requirements.txt

# Lancer le diagnostic
python ai_system/farm_ai_diagnostics.py
```

---

## 📦 INSTALLATION COMPLÈTE

```bash
# 1. Cloner le projet
git clone <repository>
cd farm-ai-project

# 2. Installer les dépendances Python
cd ai_system
pip install -r requirements.txt
cd ..

# 3. Installer les dépendances Frontend
cd forntend
npm install
cd ..

# 4. Créer la base de données
mysql -u root -proot123 -e "
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. Compiler le backend
cd backend
mvn clean install
cd ..

# 6. Démarrer tous les services (voir section DÉMARRAGE RAPIDE)
```

---

## 🐛 DÉPANNAGE

Voir le fichier complet: [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md)

### Ressources:
- 📖 [Guide complet d'installation](GUIDE_INSTALLATION.md)
- 🔍 [Documentation API Backend](backend/README.md)
- 🎨 [Documentation Frontend](forntend/README.md)
- 🤖 [Documentation IA](ai_system/README.md)

---

## 📞 Support

Problèmes? Consultez:
1. Les logs: `logs/` folder
2. Le diagnostic: `python ai_system/farm_ai_diagnostics.py`
3. Le guide complet: [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md)

---

**Version**: 1.0  
**Dernière mise à jour**: Mai 2026

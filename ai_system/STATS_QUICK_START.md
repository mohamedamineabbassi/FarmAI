# 🎯 VÉRIFIER LES STATS DE L'IA - GUIDE RAPIDE

## ⚡ LES 3 COMMANDES ESSENTIELLES

### 1️⃣ **DASHBOARD EN TEMPS RÉEL** (À faire d'abord!)
```bash
cd ai_system
python DASHBOARD_LIVE.py
```

**Affiche:**
```
╔════════════════════════════════════════════════════════════════╗
║          🎯 DASHBOARD - MONITORING IA FARM-AI                 ║
╚════════════════════════════════════════════════════════════════╝

⏱️  Heure: 14:32:45

┌─ 📊 STATISTIQUES PRINCIPALES ─────────────────────────────────┐
│
│  👥 Employés total:              5
│  👤 Avec visage enregistré:      5
│  ✅ Approuvés:                  5
│  📈 % avec visage:              100%
│  📈 % approuvés:                100%
│
└────────────────────────────────────────────────────────────────┘

┌─ 🎯 RECONNAISSANCES ──────────────────────────────────────────┐
│
│  📸 Dernière reconnaissance:     Ahmed
│  ⏱️  À 14:32:10
│  📊 Reconnaissances aujourd'hui: 42
│
└────────────────────────────────────────────────────────────────┘

✓ IA:                 ACTIF (détections en cours)
✓ Configuration:      OK - Prêt pour reconnaissance
```

✅ C'est votre principal monitoring!

---

### 2️⃣ **RAPPORT COMPLET DÉTAILLÉ**
```bash
cd ai_system
python STATS_AI_MONITORING.py
```

**Affiche:**
```
STATISTIQUES EMPLOYÉS
├─ Total: 5
├─ Avec visage: 5 (100%)
└─ Approuvés: 5 (100%)

QUALITÉ DES EMBEDDINGS
├─ Valides: 5/5
├─ Invalides: 0/5
└─ Dimensions moyennes: 512

HISTORIQUE DE RECONNAISSANCE (dernière heure)
├─ Dernier: Ahmed à 14:32:10
├─ Détections: 42
└─ Employés uniques: 5

PERFORMANCE SYSTÈME
├─ CPU: 15.3%
├─ RAM: 245.2MB
└─ FPS: ~28

ÉTAT DES SERVICES
✓ Backend API (port 8081)
✓ Frontend (port 4200)
✓ API IA (port 8000)
✓ MySQL (port 3306)
```

✅ Pour un diagnostic complet

---

### 3️⃣ **GÉNÉRER UN RAPPORT EXPORTABLE**
```bash
cd ai_system
python EXPORT_STATS.py
```

**Crée 3 fichiers:**
```
✓ ai_stats_20260511_143245.json  (pour analyse)
✓ employees_20260511_143245.csv  (pour Excel)
✓ rapport_ai_20260511_143245.html (pour navigateur)
```

✅ Pour archiver et analyser

---

## 📋 **TABLEAU RÉCAPITULATIF**

| Besoin | Commande | Résultat |
|--------|----------|----------|
| **Vue rapide** | `python DASHBOARD_LIVE.py` | Dashboard live + mise à jour |
| **Diagnostic complet** | `python STATS_AI_MONITORING.py` | Rapport détaillé |
| **Exporter données** | `python EXPORT_STATS.py` | JSON + CSV + HTML |
| **Check problèmes** | `python CHECK_AI_PROBLEMS.py` | Diagnostic des erreurs |
| **Requête SQL** | `mysql -u root ... -e "SELECT ..."` | Données brutes |

---

## 🎯 **COMMENT UTILISER CHAQUE STAT**

### **📊 Statistiques Principales**

**📍 Total Employés:**
- Si 0 → Créez des employés d'abord
- Si > 0 → ✓ OK

**👤 Avec Visage:**
- Si 0 → Enregistrez les visages (Face Registration)
- Si = Total → ✓ Prêt pour reconnaissance

**✅ Approuvés:**
- Si 0 → Admin doit approuver
- Si = Total → ✓ Tous actifs

**% avec visage et % approuvés:**
- Si < 50% → Beaucoup de travail à faire
- Si 75-99% → En cours de configuration
- Si 100% → ✓ Complètement prêt

---

### **🎯 Reconnaissances**

**📸 Dernière Reconnaissance:**
- Si "N/A" → Aucun visage détecté
- Si "Ahmed" → ✓ IA fonctionne

**📊 Reconnaissances Aujourd'hui:**
- Si 0 → Soit IA arrêtée, soit pas d'employés
- Si > 100 → ✓ Très actif

**🏆 Top Reconnus:**
```
1. Ahmed          15 ▓▓▓
2. Fatima         12 ▓▓
3. Mohamed         8 ▓
```
- Montre qui est le plus détecté
- Utile pour identifier les problèmes

---

### **⚡ Performance**

**CPU:**
- < 20% → ✓ Normal
- 20-50% → Acceptable
- > 50% → Trop chargé

**RAM:**
- < 500MB → ✓ Normal
- 500MB-1GB → Acceptable
- > 1GB → À surveiller

**FPS (Frames Per Second):**
- < 10 FPS → Ralentissements
- 15-30 FPS → ✓ Normal
- > 30 FPS → ✓ Excellent

---

### **🔌 Services**

**État des Services:**
```
✓ Backend API       → Django/Flask fonctionne
✓ Frontend          → Angular/React accessible
✓ API IA            → FastAPI operational
✓ MySQL             → Base de données OK
```

Si un ✗ → Service arrêté, relancez!

---

## 🚀 **WORKFLOW COMPLET**

### **Jour 1: Configuration initiale**
```bash
# 1. Diagnostic
python CHECK_AI_PROBLEMS.py

# 2. Rapport complet
python STATS_AI_MONITORING.py

# 3. Créer employés
# → Accédez à http://localhost:4200
# → Add Employee

# 4. Vérifier
python DASHBOARD_LIVE.py
```

### **Jour 2: Enregistrer les visages**
```bash
# 1. Lancer Dashboard
python DASHBOARD_LIVE.py

# 2. Enregistrer visages
# → Face Registration sur frontend

# 3. Observer le dashboard
# → % avec visage doit augmenter
```

### **Jour 3: Tester en direct**
```bash
# 1. Lancer l'IA
python main.py

# 2. Lancer caméra
python camera_ai_stream.py --source 0 --camera_id 1

# 3. Monitorer
python DASHBOARD_LIVE.py 1  # Mise à jour chaque 1 sec

# 4. Observer les chiffres augmenter!
```

### **Fin de semaine: Archivage**
```bash
# Exporter les stats
python EXPORT_STATS.py

# Cela crée:
# - rapport_ai_20260511_143245.html (ouvrir dans navigateur!)
# - ai_stats_20260511_143245.json (analyser)
# - employees_20260511_143245.csv (Excel)
```

---

## 🔍 **INTERPRÉTATION RAPIDE**

### ✅ **Parfait!**
```
Total:                    10
Avec visage:              10 (100%)
Approuvés:                10 (100%)
Dernière reconn:          Ahmed
Reconnaissances:          156 (beaucoup!)
```
→ Tout fonctionne, l'IA est très active!

### ⚠️ **À faire avant de lancer**
```
Total:                    0
Avec visage:              0
Approuvés:                0
```
→ Créez d'abord des employés!

### ⚠️ **Pas d'IA détections**
```
Total:                    10
Avec visage:              10 (100%)
Approuvés:                10 (100%)
Dernière reconn:          N/A
Reconnaissances:          0
```
→ Lancez: `python main.py` et `python camera_ai_stream.py ...`

### ⚠️ **Problème d'embeddings**
```
Embeddings valides:       5/10
Embeddings invalides:     5
```
→ Exécutez: `python CHECK_AI_PROBLEMS.py`

---

## 💡 **ASTUCES**

### **1. Mettre à jour plus rapidement**
```bash
python DASHBOARD_LIVE.py 1  # Toutes les 1 seconde
python DASHBOARD_LIVE.py 2  # Toutes les 2 secondes
```

### **2. Voir les logs en direct**
```bash
# Caméra:
python camera_ai_stream.py --source 0 --camera_id 1 2>&1 | tail -f

# API:
python main.py 2>&1 | tail -f
```

### **3. Combiner dashboard + logs**
Terminal 1:
```bash
python DASHBOARD_LIVE.py 1
```

Terminal 2:
```bash
python camera_ai_stream.py --source 0 --camera_id 1
```

→ Voir le dashboard ET les logs en même temps!

### **4. Analyser avec Excel**
```bash
python EXPORT_STATS.py
# → Ouvrir employees_TIMESTAMP.csv dans Excel
# → Trier, filtrer, analyser
```

---

## 🎓 **CYCLE DE VIE DE L'IA**

```
1️⃣ CONFIGURATION
   ↓
   python DASHBOARD_LIVE.py
   → Total: 0, Avec visage: 0
   → Créer employés
   
2️⃣ ENREGISTREMENT VISAGES
   ↓
   python DASHBOARD_LIVE.py
   → Total: 10, Avec visage: 5
   → Enregistrer 5 visages supplémentaires
   
3️⃣ APPROBATION
   ↓
   python DASHBOARD_LIVE.py
   → Total: 10, Approuvés: 10
   → Admin approuve tous
   
4️⃣ PRODUCTION
   ↓
   python DASHBOARD_LIVE.py
   → Dernière reconn: Ahmed
   → Reconnaissances: 42
   → ✅ IA ACTIVE!

5️⃣ MONITORING
   ↓
   Chaque jour: python DASHBOARD_LIVE.py
   Chaque semaine: python EXPORT_STATS.py
```

---

## 🆘 **SI LES STATS RESTENT À ZÉRO**

```bash
# 1. Vérifier MySQL
mysql -u root -proot123 -e "USE attendance_db; SELECT COUNT(*) FROM employees;"

# 2. Vérifier backend
curl http://localhost:8081/api/employees

# 3. Vérifier diagnostic
python CHECK_AI_PROBLEMS.py

# 4. Vérifier les logs
python camera_ai_stream.py --source 0 --camera_id 1 2>&1 | head -20
```

---

**Commencez maintenant:** `python DASHBOARD_LIVE.py` 🚀

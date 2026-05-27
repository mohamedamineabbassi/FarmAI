# 📊 COMMENT VÉRIFIER LES STATISTIQUES DE L'IA

## 🚀 **DÉMARRAGE RAPIDE**

### **Option 1: Dashboard en temps réel (Recommandé)**
```bash
cd ai_system
python DASHBOARD_LIVE.py
```
✅ Affiche un dashboard qui se met à jour automatiquement chaque 5 secondes

### **Option 2: Rapport complet**
```bash
cd ai_system
python STATS_AI_MONITORING.py
```
✅ Affiche un rapport détaillé avec toutes les statistiques

---

## 📋 **STATISTIQUES DISPONIBLES**

### **1. EMPLOYÉS**
| Stat | Commande | Affiche |
|------|----------|---------|
| Total employés | `python STATS_AI_MONITORING.py` | Nombre total |
| Avec visage | `python STATS_AI_MONITORING.py` | Nombre avec embedding |
| Approuvés | `python STATS_AI_MONITORING.py` | Nombre actifs |
| % progression | `python DASHBOARD_LIVE.py` | Pourcentage en barre |

### **2. RECONNAISSANCE**
| Stat | Commande | Affiche |
|------|----------|---------|
| Dernier reconnu | `python DASHBOARD_LIVE.py` | Nom + heure |
| Reconnaissances today | `python DASHBOARD_LIVE.py` | Nombre total du jour |
| Top 5 reconnus | `python DASHBOARD_LIVE.py` | Ranking |
| Par heure | `python DASHBOARD_LIVE.py` | Graphique hourly |

### **3. QUALITÉ**
| Stat | Commande | Affiche |
|------|----------|---------|
| Embeddings valides | `python STATS_AI_MONITORING.py` | Nombre + % |
| Dimensions | `python STATS_AI_MONITORING.py` | Taille moyenne |
| Services actifs | `python STATS_AI_MONITORING.py` | État backend/frontend |

---

## 🔍 **VÉRIFICATIONs PAR SCÉNARIO**

### **Scénario 1: L'IA a-t-elle démarré?**
```bash
# Vérifier que les processus Python tournent
python STATS_AI_MONITORING.py

# Section "PERFORMANCE SYSTÈME" affichera:
# ✓ python main.py (running)
# ✓ python camera_ai_stream.py (running)
```

### **Scénario 2: Est-ce qu'il y a des employés à reconnaître?**
```bash
python DASHBOARD_LIVE.py

# Vérifier:
# 👥 Employés total: X
# 👤 Avec visage enregistré: Y
# ✅ Approuvés: Z
```

Si Y = 0, personne ne sera reconnu → Enregistrez des visages!

### **Scénario 3: Est-ce que l'IA reconnait quelque chose?**
```bash
python DASHBOARD_LIVE.py

# Vérifier:
# 📸 Dernière reconnaissance: [NOM]
# 📊 Reconnaissances aujourd'hui: [NOMBRE]
```

Si NOMBRE = 0 → L'IA ne détecte rien

### **Scénario 4: Combien de personnes ont été reconnues?**
```bash
python DASHBOARD_LIVE.py

# Voir la section "TOP EMPLOYÉS":
# 1. Ahmed          15 ▓▓▓
# 2. Fatima         12 ▓▓
# 3. Mohamed         8 ▓
```

### **Scénario 5: Comment ça se passe en temps réel?**
```bash
# Lancer le dashboard
python DASHBOARD_LIVE.py 1  # mise à jour chaque 1 seconde (au lieu de 5)

# Ou laisser la caméra afficher les logs:
python camera_ai_stream.py --source 0 --camera_id 1

# Les logs affichent:
# 🚀 SYSTÈME IA DÉMARRÉ
# ✓ Reconnu: Ahmed (distance: 0.45)
# ✓ Reconnu: Fatima (distance: 0.52)
```

---

## 🗄️ **VÉRIFICATIONS VIA SQL**

### **Voir tous les employés et leurs visages**
```bash
mysql -u root -proot123 attendance_db -e "
SELECT id, name, status, 
       IF(embedding IS NOT NULL, 'OUI', 'NON') as visage
FROM employees
ORDER BY id;"
```

### **Voir les dernières reconnaissances**
```bash
mysql -u root -proot123 attendance_db -e "
SELECT e.name, a.timestamp, a.confidence
FROM attendance a
JOIN employees e ON a.employee_id = e.id
ORDER BY a.timestamp DESC
LIMIT 20;"
```

### **Reconnaissances d'aujourd'hui**
```bash
mysql -u root -proot123 attendance_db -e "
SELECT e.name, COUNT(*) as count
FROM attendance a
JOIN employees e ON a.employee_id = e.id
WHERE DATE(a.timestamp) = CURDATE()
GROUP BY e.id, e.name
ORDER BY count DESC;"
```

### **Vérifier la qualité des embeddings**
```bash
mysql -u root -proot123 attendance_db -e "
SELECT id, name, 
       IF(embedding IS NOT NULL, JSON_LENGTH(embedding), 0) as dimensions
FROM employees
WHERE embedding IS NOT NULL;"
```

---

## 🎯 **WORKFLOW COMPLET DE VÉRIFICATION**

```bash
# ÉTAPE 1: Diagnostic initial
cd ai_system
python CHECK_AI_PROBLEMS.py

# ÉTAPE 2: Voir le rapport complet
python STATS_AI_MONITORING.py

# ÉTAPE 3: Lancer le dashboard live
python DASHBOARD_LIVE.py

# ÉTAPE 4: Dans un nouveau terminal, lancer l'IA
python main.py

# ÉTAPE 5: Dans un autre terminal, lancer la caméra
python camera_ai_stream.py --source 0 --camera_id 1

# ÉTAPE 6: Observer le dashboard - vérifier les stats qui changent
# Les chiffres doivent augmenter en temps réel
```

---

## 📈 **INTERPRÉTATION DES STATISTIQUES**

### ✅ **Bon fonctionnement**
```
👥 Employés total:           5
👤 Avec visage enregistré:   5 (100%)
✅ Approuvés:                5 (100%)
📸 Dernière reconnaissance:  Ahmed
📊 Reconnaissances aujourd'hui: 42
✓ IA:                        ACTIF
✓ Configuration:             OK
```

### ⚠️ **Problème: Pas d'employés**
```
👥 Employés total:           0
👤 Avec visage enregistré:   0
✅ Approuvés:                0
📊 Reconnaissances aujourd'hui: 0
⚠️  ACTION: Créez des employés d'abord!
```

### ⚠️ **Problème: Pas de visages enregistrés**
```
👥 Employés total:           5
👤 Avec visage enregistré:   0 (0%)
✅ Approuvés:                5
📊 Reconnaissances aujourd'hui: 0
⚠️  ACTION: Enregistrez les visages!
```

### ⚠️ **Problème: IA inactif**
```
👥 Employés total:           5
👤 Avec visage enregistré:   5 (100%)
✅ Approuvés:                5
📸 Dernière reconnaissance:  N/A
📊 Reconnaissances aujourd'hui: 0
⚠️  IA:                       INACTIF
⚠️  ACTION: Démarrez main.py et camera_ai_stream.py!
```

---

## 🔧 **OPTIONS AVANCÉES**

### **Dashboard avec mise à jour rapide**
```bash
python DASHBOARD_LIVE.py 1  # Mise à jour chaque 1 seconde
python DASHBOARD_LIVE.py 2  # Mise à jour chaque 2 secondes
```

### **Exporter les statistiques**
```bash
# Créer un rapport et l'exporter
python STATS_AI_MONITORING.py > rapport_stats.txt

# Ou via SQL
mysql -u root -proot123 attendance_db -e "SELECT * FROM attendance;" > attendance.csv
```

### **Monitorer en continu**
```bash
# Lancer 2 terminaux côte à côte:

# Terminal 1: Dashboard
python DASHBOARD_LIVE.py 1

# Terminal 2: Caméra avec logs
python camera_ai_stream.py --source 0 --camera_id 1
```

---

## 📊 **TABLEAU RÉCAPITULATIF**

| Besoin | Commande | Temps |
|--------|----------|-------|
| Vue rapide | `python DASHBOARD_LIVE.py` | En temps réel |
| Rapport complet | `python STATS_AI_MONITORING.py` | 10 secondes |
| Diagnostic problèmes | `python CHECK_AI_PROBLEMS.py` | 5 secondes |
| Requête SQL | `mysql ... -e "SELECT ..."` | Immédiat |
| Exportation | `python STATS... > file.txt` | 10 secondes |

---

## 💡 **CONSEILS**

1. **Lancer le dashboard d'abord** pour voir l'état global
2. **Si problème, exécuter le diagnostic** pour identifier
3. **Corriger le problème** (créer employés, enregistrer visages, etc.)
4. **Observer le dashboard** se mettre à jour en temps réel
5. **Lancer les caméras** et vérifier que les chiffres augmentent

---

## 🆘 **SI LES STATS NE CHANGENT PAS**

1. Vérifier MySQL: `mysql -u root -proot123 -e "SELECT 1;"`
2. Vérifier backend: `curl http://localhost:8081/api/employees`
3. Vérifier les logs de la caméra: `python camera_ai_stream.py ... 2>&1 | grep -i error`
4. Exécuter le diagnostic: `python CHECK_AI_PROBLEMS.py`

---

**C'est prêt!** 🚀 Commencez par: `python DASHBOARD_LIVE.py`

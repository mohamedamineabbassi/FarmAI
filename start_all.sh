#!/bin/bash
# Script de démarrage automatique pour Farm-AI sur Linux/Mac

echo "======================================="
echo "  FARM-AI - Démarrage du système"
echo "======================================="
echo

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier si MySQL fonctionne
echo "[*] Vérification de MySQL..."
mysql -u root -proot123 -e "SELECT VERSION();" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}[✗] MySQL n'est pas démarré!${NC}"
    echo "    Veuillez démarrer MySQL d'abord."
    exit 1
fi
echo -e "${GREEN}[✓] MySQL est actif${NC}"

# Créer le dossier logs
mkdir -p logs

# Lancer le backend Spring Boot
echo "[*] Démarrage du backend (port 8081)..."
cd backend
mvn spring-boot:run > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 5
echo -e "${GREEN}[✓] Backend lancé (PID: $BACKEND_PID)${NC}"

# Lancer le Frontend Angular
echo "[*] Démarrage du frontend (port 4200)..."
cd forntend
npm install >/dev/null 2>&1
ng serve > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3
echo -e "${GREEN}[✓] Frontend lancé (PID: $FRONTEND_PID)${NC}"

# Lancer le serveur FastAPI (AI)
echo "[*] Démarrage du serveur IA FastAPI (port 8000)..."
cd ai_system
python main.py > ../logs/ai_main.log 2>&1 &
AI_MAIN_PID=$!
cd ..
echo -e "${GREEN}[✓] Serveur IA lancé (PID: $AI_MAIN_PID)${NC}"

# Lancer une caméra d'exemple
echo "[*] Lancement de la caméra 1 (Face Recognition)..."
cd ai_system
python camera_ai_stream.py --source 0 --camera_id 1 > ../logs/camera1.log 2>&1 &
CAMERA1_PID=$!
cd ..
echo -e "${GREEN}[✓] Caméra 1 lancée (PID: $CAMERA1_PID)${NC}"

echo
echo "======================================="
echo -e "${GREEN}Tous les services ont été lancés!${NC}"
echo "======================================="
echo
echo "Accédez à:"
echo "  - Frontend: http://localhost:4200"
echo "  - Backend API: http://localhost:8081"
echo "  - API IA: http://localhost:8000/docs"
echo
echo "Logs disponibles dans le dossier 'logs/'"
echo
echo "Pour arrêter tous les services:"
echo "  kill $BACKEND_PID $FRONTEND_PID $AI_MAIN_PID $CAMERA1_PID"
echo

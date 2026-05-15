import urllib.request
import json
import zlib
import base64

def generate_diagram(diagram_text, filename):
    # Method 2: Kroki with User-Agent
    url = 'https://kroki.io/plantuml/png'
    data = json.dumps({
        "diagram_source": diagram_text,
        "diagram_type": "plantuml",
        "output_format": "png"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    try:
        with urllib.request.urlopen(req) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"Successfully generated {filename}")
    except Exception as e:
        print(f"Error generating {filename} via Kroki: {e}")

# 1. Use Case Diagram
usecase = """
@startuml
left to right direction
skinparam packageStyle rectangle

actor "Administrateur" as admin
actor "Employé" as emp
actor "Caméra IA" as cam

rectangle "Système Farm AI" {
  usecase "S'authentifier" as UC1
  usecase "Gérer les employés" as UC2
  usecase "Consulter le tableau de bord" as UC3
  usecase "Enregistrer Face ID" as UC4
  usecase "Reconnaître le visage" as UC5
  usecase "Pointer (Entrée/Sortie)" as UC6
}

admin --> UC1
admin --> UC2
admin --> UC3
admin --> UC4

emp --> UC4
emp --> UC6

cam --> UC5
UC5 ..> UC6 : <<include>>
@enduml
"""

# 2. Class Diagram
class_diag = """
@startuml
class Utilisateur {
  - id : Long
  - username : String
  - motDePasse : String
  - role : String
  + seConnecter()
  + seDeconnecter()
}

class Employe {
  - id : Long
  - nom : String
  - prenom : String
  - telephone : String
  - poste : String
  - dateEmbauche : Date
  + ajouter()
  + modifier()
  + supprimer()
}

class FaceEncoding {
  - id : Long
  - encodingData : float[]
  - dateEnregistrement : Date
  + comparer(encoding: float[]) : boolean
}

class Pointage {
  - id : Long
  - heureEntree : DateTime
  - heureSortie : DateTime
  - statut : String
  - couleurVete : String
  + enregistrerEntree()
  + enregistrerSortie()
}

Utilisateur "1" -- "0..*" Employe : gère >
Employe "1" -- "1" FaceEncoding : possède >
Employe "1" -- "0..*" Pointage : effectue >
@enduml
"""

# 3. Sequence Diagram: Authentication
seq_auth = """
@startuml
actor Administrateur
participant "Frontend (Angular)" as Angular
participant "Backend (Spring Boot)" as Spring
database "Base de Données" as DB

Administrateur -> Angular : Saisir identifiants
Angular -> Spring : POST /api/auth/login
Spring -> DB : Chercher utilisateur par email
DB --> Spring : Retourner Utilisateur
Spring -> Spring : Vérifier mot de passe
alt Mot de passe correct
    Spring -> Spring : Générer Token JWT
    Spring --> Angular : 200 OK (Token JWT)
    Angular -> Administrateur : Redirection vers Dashboard
else Mot de passe incorrect
    Spring --> Angular : 401 Unauthorized
    Angular -> Administrateur : Afficher message d'erreur
end
@enduml
"""

# 4. Sequence Diagram: Recognition & Attendance
seq_ai = """
@startuml
actor "Caméra IP" as Camera
participant "Service IA (FastAPI)" as IA
participant "Backend (Spring Boot)" as Spring
database "Base de Données" as DB
participant "Frontend (Angular)" as Angular

Camera -> IA : Flux Vidéo (Frames)
IA -> IA : Détection visage (YOLO/OpenCV)
IA -> IA : Extraction encodage (dlib)
IA -> Spring : POST /api/attendance/detect
Spring -> DB : Chercher correspondance
DB --> Spring : Retourner ID Employé
alt Employé reconnu
    Spring -> Spring : Générer log pointage
    Spring -> DB : Enregistrer Pointage
    DB --> Spring : OK
    Spring --> IA : 200 OK
    Spring -> Angular : WebSocket Update
    Angular -> Angular : Mettre à jour UI
else Employé inconnu
    Spring --> IA : 404 Not Found
    IA -> IA : Ignorer
end
@enduml
"""

generate_diagram(usecase, 'usecase.png')
generate_diagram(class_diag, 'class_diagram.png')
generate_diagram(seq_auth, 'seq_auth.png')
generate_diagram(seq_ai, 'seq_ai.png')

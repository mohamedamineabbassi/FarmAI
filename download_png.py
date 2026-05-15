import urllib.request
import urllib.parse

dot = '''digraph G {
  node [shape=box, style=filled, fontname="Arial", margin="0.2,0.1"];
  edge [fontname="Arial", fontsize=10];
  
  subgraph cluster_front {
    label="Frontend (Angular)";
    style=filled; color="#ffcccc";
    UI [label="Interface Utilisateur Web"];
    Dash [label="Tableaux de bord"];
  }

  subgraph cluster_back {
    label="Backend (Spring Boot)";
    style=filled; color="#ccffcc";
    API [label="API REST"];
    Sec [label="Spring Security (JWT)"];
    WS [label="Serveur WebSocket"];
    Mail [label="Gmail SMTP"];
  }

  subgraph cluster_ai {
    label="Serveur IA (Python/FastAPI)";
    style=filled; color="#cceeff";
    FastAPI [label="Serveur FastAPI"];
    OpenCV [label="OpenCV (Vidéo)"];
    YOLO [label="YOLOv8 (Détection)"];
    Face [label="InsightFace (Reconnaissance)"];
  }

  DB [label="MySQL (Base de données)", shape=cylinder, fillcolor="#ffeecc"];
  Cam [label="Caméras IP/Webcams", shape=ellipse, fillcolor="#eeeeee"];
  Usr [label="Utilisateurs", shape=ellipse, fillcolor="#eeeeee"];

  Usr -> UI [label="Interagit"];
  UI -> API [label="HTTP JSON"];
  UI -> WS [label="Temps réel"];
  API -> Sec;
  API -> DB [label="Lecture/Écriture"];
  API -> Mail [label="Notifications"];
  
  Cam -> OpenCV [label="Flux RTSP"];
  OpenCV -> YOLO;
  OpenCV -> Face;
  FastAPI -> API [label="Résultats & Alertes"];
  OpenCV -> FastAPI [dir=none];
}'''

url = 'https://quickchart.io/graphviz?graph=' + urllib.parse.quote(dot)
urllib.request.urlretrieve(url, 'Architecture_Farm_AI.png')
print('Downloaded PNG successfully.')

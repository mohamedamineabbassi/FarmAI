import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

from ai_engine.core.engine import Engine
from ai_engine.core.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SOC_API")

app = FastAPI(title="SOC AI Engine API", description="Moteur d'Intelligence Artificielle Centralisé")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

soc_engine = Engine()

@app.on_event("startup")
async def startup_event():
    logger.info("✓ Engine online")
    soc_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    soc_engine.stop()

# =========================
# FLUX VIDEO WEBRTC / MJPEG
# =========================

def generate_frames(camera_id: int):
    """Générateur de flux vidéo en direct (MJPEG) directement depuis la RAM"""
    while True:
        frame_bytes = soc_engine.get_camera_frame(camera_id)
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        # Pause asynchrone pour ne pas bloquer l'Event Loop
        asyncio.run(asyncio.sleep(0.05))

@app.get("/api/camera/{camera_id}/stream")
async def video_feed(camera_id: int):
    """Point d'accès pour voir la caméra en direct sur Angular"""
    if camera_id not in soc_engine.camera_threads:
        logger.error(f"❌ Camera {camera_id} unavailable")
        raise HTTPException(status_code=404, detail="Caméra non active ou non trouvée.")
    
    logger.info(f"✓ Stream started for camera {camera_id}")
    logger.info(f"✓ MJPEG active")
    return StreamingResponse(
        generate_frames(camera_id), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/engine/status")
def get_status():
    """Vérifier l'état du moteur"""
    return {
        "status": "online" if soc_engine.running else "offline",
        "active_cameras": list(soc_engine.camera_threads.keys())
    }

if __name__ == "__main__":
    logger.info(f"Démarrage du serveur sur le port {Config.PORT}...")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

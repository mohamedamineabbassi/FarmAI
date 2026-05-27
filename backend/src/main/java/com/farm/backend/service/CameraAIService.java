package com.farm.backend.service;

import org.springframework.stereotype.Service;
import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class CameraAIService {

    private final Map<Long, Process> runningProcesses = new ConcurrentHashMap<>();
    
    // Chemin vers le dossier des scripts IA
    private final String aiSystemPath = "c:/Users/pc/Desktop/PFarmIA/ai_system";
    private final String pythonExecutable = "python";

    public boolean startAI(Long cameraId, String aiType, String source, String type) {
        if (runningProcesses.containsKey(cameraId)) {
            stopAI(cameraId);
        }

        try {
            String scriptName = aiType.equals("ROLE_COLOR") ? "role_detection.py" : "face_recognition.py";
            String scriptToRun = aiSystemPath + "/" + scriptName;

            ProcessBuilder pb = new ProcessBuilder(
                    pythonExecutable,
                    scriptToRun,
                    "--cameraId", String.valueOf(cameraId),
                    "--source", source,
                    "--type", type
            );
            
            pb.directory(new File(aiSystemPath));
            pb.redirectErrorStream(true);
            File logFile = new File(aiSystemPath, "ai_system_camera_" + cameraId + ".log");
            pb.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile));
            
            Process process = pb.start();
            runningProcesses.put(cameraId, process);
            
            System.out.println("🚀 AI STARTED for Camera " + cameraId + " (" + aiType + ")");
            return true;
            
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean stopAI(Long cameraId) {
        Process p = runningProcesses.remove(cameraId);
        if (p != null && p.isAlive()) {
            p.destroy();
            System.out.println("🛑 AI STOPPED for Camera " + cameraId);
            return true;
        }
        return false;
    }

    public boolean getAIStatus(Long cameraId) {
        Process p = runningProcesses.get(cameraId);
        return p != null && p.isAlive();
    }
}

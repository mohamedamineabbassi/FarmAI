package com.farm.backend.service;

import com.farm.backend.entity.Employee;
import com.farm.backend.entity.User;
import com.farm.backend.exception.FaceException;
import com.farm.backend.repository.EmployeeRepository;
import com.farm.backend.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.Map;
import java.util.Optional;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;

@Service
public class FaceService {

    private final EmployeeRepository employeeRepository;
    private final UserRepository userRepository;

    public FaceService(EmployeeRepository employeeRepository, UserRepository userRepository) {
        this.employeeRepository = employeeRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public void registerFace(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new FaceException("Utilisateur non trouvé"));

        try {
            RestTemplate restTemplate = new RestTemplate();
            String url = "http://localhost:8000/api/face/register-latest-frame";
            
            // Call the python API which reads from the shared camera frame
            Map<String, String> requestBody = Map.of("email", user.getEmail());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestBody, Map.class);
            Map<String, Object> body = response.getBody();
            
            if (body == null || !"success".equals(body.get("status"))) {
                String msg = body != null && body.containsKey("message") ? (String) body.get("message") : "Inconnue";
                throw new FaceException("Erreur lors de l'enregistrement du visage : " + msg);
            }
            
            // The Python API already saved the embedding in the database!
            // We just need to update our JPA cache/entity state.
            user.setFaceRegistered(true);
            userRepository.save(user);

            // Sync to Employee if exists (for attendance/tracking)
            employeeRepository.findByEmail(user.getEmail()).stream().findFirst().ifPresent(employee -> {
                employee.setFaceRegistered(true);
                employeeRepository.save(employee);
            });

        } catch (FaceException e) {
            throw e;
        } catch (Exception e) {
            throw new FaceException("Erreur de connexion au serveur IA : " + e.getMessage());
        }
    }

    @Transactional
    public void updateFace(Long userId) {
        // Update is essentially the same as register in this context
        registerFace(userId);
    }

    @Transactional
    public void deleteFace(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new FaceException("Utilisateur non trouvé"));

        Employee employee = employeeRepository.findByEmail(user.getEmail()).stream().findFirst()
                .orElseThrow(() -> new FaceException("Employé non trouvé pour cet utilisateur"));

        employee.setEmbedding(null);
        employee.setFaceRegistered(false);
        employeeRepository.save(employee);

        user.setFaceRegistered(false);
        userRepository.save(user);
    }

    public boolean getFaceStatus(Long userId) {
        return userRepository.findById(userId)
                .map(User::isFaceRegistered)
                .orElse(false);
    }

    @Transactional
    public void registerFaceByEmployeeId(Long employeeId) {
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new FaceException("Employé non trouvé"));

        try {
            RestTemplate restTemplate = new RestTemplate();
            String url = "http://localhost:8000/api/face/register-latest-frame";
            
            // Pass employeeId directly to the python API
            java.util.Map<String, Object> requestBody = new java.util.HashMap<>();
            requestBody.put("employeeId", employee.getId());
            if (employee.getEmail() != null && !employee.getEmail().isEmpty()) {
                requestBody.put("email", employee.getEmail());
            }
            
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestBody, Map.class);
            Map<String, Object> body = response.getBody();
            
            if (body == null || !"success".equals(body.get("status"))) {
                String msg = body != null && body.containsKey("message") ? (String) body.get("message") : "Inconnue";
                throw new FaceException("Erreur lors de l'enregistrement du visage : " + msg);
            }
            
            // Update JPA state
            employee.setFaceRegistered(true);
            employeeRepository.save(employee);

            // Sync to User if they have an account
            if (employee.getEmail() != null && !employee.getEmail().isEmpty()) {
                userRepository.findByEmail(employee.getEmail()).ifPresent(user -> {
                    user.setFaceRegistered(true);
                    userRepository.save(user);
                });
            }

        } catch (FaceException e) {
            throw e;
        } catch (Exception e) {
            throw new FaceException("Erreur de connexion au serveur IA : " + e.getMessage());
        }
    }

    @Transactional
    public void deleteFaceByEmployeeId(Long employeeId) {
        Employee employee = employeeRepository.findById(employeeId)
                .orElseThrow(() -> new FaceException("Employé non trouvé"));

        User user = userRepository.findByEmail(employee.getEmail())
                .orElseThrow(() -> new FaceException("Utilisateur non trouvé pour cet employé"));

        deleteFace(user.getId());
    }

    public Map<String, Object> recognizeFace() {
        try {
            RestTemplate restTemplate = new RestTemplate();
            String url = "http://localhost:8000/api/face/recognize-latest-frame";
            
            ResponseEntity<Map> response = restTemplate.postForEntity(url, null, Map.class);
            Map<String, Object> body = response.getBody();
            
            if (body == null || !body.containsKey("status")) {
                return Map.of("status", "error", "message", "Face recognition returned no result");
            }
            
            String status = (String) body.get("status");
            
            if ("no_match".equals(status)) {
                return Map.of("status", "error", "message", "No matching face found. Make sure your face is registered.");
            } else if ("error".equals(status)) {
                String errorMsg = body.containsKey("message") ? (String) body.get("message") : "Camera not available.";
                return Map.of("status", "error", "message", errorMsg);
            } else if ("success".equals(status)) {
                String email = (String) body.get("email");
                return Map.of("status", "success", "email", email);
            }
            
            return Map.of("status", "error", "message", "Unknown status returned");
        } catch (Exception e) {
            System.err.println("Face recognition error: " + e.getMessage());
            return Map.of("status", "error", "message", "Face recognition failed: " + e.getMessage());
        }
    }

    private String runPythonScript(String scriptName, String arg) {
        try {
            String rootPath = System.getProperty("user.dir");
            File aiDir = new File(rootPath, "ai_system");
            
            if (!aiDir.exists()) {
                aiDir = new File(new File(rootPath).getParentFile(), "ai_system");
            }
            
            System.out.println("DEBUG: AI Directory determined as: " + aiDir.getAbsolutePath());
            File scriptFile = new File(aiDir, scriptName);
            if (!scriptFile.exists()) {
                System.err.println("ERROR: Script not found at " + scriptFile.getAbsolutePath());
                return null;
            }

            ProcessBuilder pb;
            if (arg != null) {
                pb = new ProcessBuilder("python", "-u", scriptFile.getAbsolutePath(), arg);
            } else {
                pb = new ProcessBuilder("python", "-u", scriptFile.getAbsolutePath());
            }
            
            pb.directory(aiDir);
            // pb.redirectErrorStream(true);

            Process process = pb.start();
            
            StringBuilder stderr = new StringBuilder();
            new Thread(() -> {
                try (BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                    String line;
                    while ((line = errorReader.readLine()) != null) {
                        System.err.println("PYTHON [stderr] " + scriptName + ": " + line);
                        stderr.append(line).append("\n");
                    }
                } catch (Exception e) {}
            }).start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            String lastLine = null;
            while ((line = reader.readLine()) != null) {
                System.out.println("PYTHON [stdout] " + scriptName + ": " + line);
                if (!line.trim().isEmpty()) {
                    lastLine = line;
                }
            }
            
            int exitCode = process.waitFor();
            System.out.println("PYTHON EXIT CODE [" + scriptName + "]: " + exitCode);

            if (exitCode != 0) {
                throw new FaceException("Python script failed with exit code " + exitCode + ". Stderr: " + stderr.toString());
            }

            return lastLine;
        } catch (FaceException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("Error running python script " + scriptName + ": " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
}


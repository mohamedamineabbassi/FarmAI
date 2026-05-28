package com.farm.backend.service;

import com.farm.backend.entity.Alert;
import com.farm.backend.entity.Department;
import com.farm.backend.repository.AlertRepository;
import com.farm.backend.repository.DepartmentRepository;
import com.farm.backend.repository.CameraRepository;
import com.farm.backend.entity.CameraEntity;
import com.farm.backend.dto.AIDetectionDTO;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class AlertService {

    private final AlertRepository repo;
    private final DepartmentRepository departmentRepository;
    private final CameraRepository cameraRepository;

    public AlertService(AlertRepository repo,
                        DepartmentRepository departmentRepository,
                        CameraRepository cameraRepository) {
        this.repo = repo;
        this.departmentRepository = departmentRepository;
        this.cameraRepository = cameraRepository;
    }

    public Alert create(String type, String message, String severity,
                        Long cameraId, Long departmentId) {
        Alert alert = new Alert();
        alert.setType(type);
        alert.setMessage(message);
        alert.setSeverity(severity);
        alert.setCameraId(cameraId);
        alert.setDepartmentId(departmentId);
        alert.setTimestamp(LocalDateTime.now());
        return repo.save(alert);
    }

    public List<Alert> getAll() {
        List<Alert> alerts = repo.findAll();
        for (Alert alert : alerts) {
            Long deptId = alert.getDepartmentId();
            if (deptId != null) {
                departmentRepository.findById(deptId).ifPresent(dept ->
                    alert.setDepartmentName(dept.getName())
                );
            }
        }
        return alerts;
    }

    public List<Alert> getUnresolved() {
        List<Alert> alerts = repo.findTop50ByResolvedFalseOrderByTimestampDesc();
        for (Alert alert : alerts) {
            Long deptId = alert.getDepartmentId();
            if (deptId != null) {
                departmentRepository.findById(deptId).ifPresent(dept ->
                    alert.setDepartmentName(dept.getName())
                );
            }
        }
        return alerts;
    }

    public long getActiveCount() {
        return repo.countByResolvedFalse();
    }

    public Alert handleAIDetection(AIDetectionDTO dto) {
        String uniqueHash = dto.getType() + "_" + dto.getLocation() + "_";
        if (dto.getEmbeddingHash() != null) {
            uniqueHash += dto.getEmbeddingHash();
        } else if (dto.getEmployeeId() != null) {
            uniqueHash += dto.getEmployeeId();
        } else if (dto.getTrackingId() != null) {
            uniqueHash += dto.getTrackingId();
        }

        String severity = "LOW";
        String message  = "Alerte générée";

        if ("UNKNOWN_PERSON".equals(dto.getType())) {
            severity = "HIGH";
            message  = "Personne inconnue détectée";

        } else if ("UNKNOWN_ROLE".equals(dto.getType())) {
            severity = "HIGH";
            message  = "Intrus détecté — rôle inconnu";

        } else if ("ENTRY_EVENT".equals(dto.getType())) {
            severity = "LOW";
            message  = "Franchissement : Entrée";

        } else if ("EXIT_EVENT".equals(dto.getType())) {
            severity = "LOW";
            message  = "Franchissement : Sortie";

        } else if ("NO_FACE".equals(dto.getType())) {
            severity = "MEDIUM";
            message  = "Employé reconnu mais sans visage enregistré";

        } else if ("INTRUSION".equals(dto.getType())) {
            severity = "CRITICAL";
            message  = "Intrusion dans une zone sécurisée";

        } else if ("PREDATOR_DETECTED".equals(dto.getType())) {
            severity = "CRITICAL";
            String animal = (dto.getAnimalLabel() != null && !dto.getAnimalLabel().isEmpty())
                    ? dto.getAnimalLabel()
                    : "Animal dangereux";
            message = "🚨 PREDATEUR DETECTE : " + animal
                    + " — Danger pour les animaux de ferme !";

        } else if ("DANGEROUS_ANIMAL".equals(dto.getType())) {
            severity = "CRITICAL";
            message  = "Animal dangereux détecté dans la zone surveillée";
        }

        // Severity transmitted by the Python engine takes priority
        if (dto.getSeverity() != null && !dto.getSeverity().isBlank()) {
            severity = dto.getSeverity();
        }

        String imagePath = null;
        if (dto.getImageBase64() != null && !dto.getImageBase64().isEmpty()) {
            try {
                String base64Data = dto.getImageBase64();
                if (base64Data.contains(",")) {
                    base64Data = base64Data.split(",")[1];
                }
                byte[] decodedBytes = Base64.getDecoder().decode(base64Data);

                String uploadDir = System.getProperty("user.dir") + "/uploads/alerts/";
                File dir = new File(uploadDir);
                if (!dir.exists()) dir.mkdirs();

                String filename = UUID.randomUUID().toString() + ".jpg";
                Path path = Paths.get(uploadDir + filename);
                Files.write(path, decodedBytes);

                imagePath = "/uploads/alerts/" + filename;
            } catch (Exception e) {
                System.out.println("Error saving AI image: " + e.getMessage());
            }
        }

        Long deptId = null;
        if (dto.getCameraId() != null) {
            Optional<CameraEntity> camOpt = cameraRepository.findById(dto.getCameraId());
            if (camOpt.isPresent() && camOpt.get().getDepartment() != null) {
                deptId = camOpt.get().getDepartment().getId();
            }
        }

        Alert newAlert = new Alert();
        newAlert.setType(dto.getType());
        newAlert.setMessage(message);
        newAlert.setSeverity(severity);
        newAlert.setLocation(dto.getLocation());
        newAlert.setUniqueHash(uniqueHash);
        newAlert.setEmployeeId(dto.getEmployeeId());
        newAlert.setCameraId(dto.getCameraId());
        newAlert.setDepartmentId(deptId);
        newAlert.setImagePath(imagePath);
        newAlert.setTimestamp(LocalDateTime.now());
        newAlert.setResolved(false);
        newAlert.setCount(1);

        return repo.save(newAlert);
    }

    public Alert resolveAlert(Long id) {
        Alert alert = repo.findById(id)
                .orElseThrow(() -> new RuntimeException("Alert not found"));
        alert.setResolved(true);
        return repo.save(alert);
    }
}

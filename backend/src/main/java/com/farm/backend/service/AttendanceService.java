package com.farm.backend.service;

import com.farm.backend.dto.AttendanceRequest;
import com.farm.backend.entity.AttendanceRecord;
import com.farm.backend.entity.Employee;
import com.farm.backend.entity.Role;
import com.farm.backend.entity.User;
import com.farm.backend.repository.AttendanceRepository;
import com.farm.backend.repository.EmployeeRepository;
import com.farm.backend.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class AttendanceService {

    private final AttendanceRepository repository;
    private final EmployeeRepository employeeRepository;
    private final UserRepository userRepository;

    public AttendanceService(AttendanceRepository repository,
                             EmployeeRepository employeeRepository,
                             UserRepository userRepository) {
        this.repository = repository;
        this.employeeRepository = employeeRepository;
        this.userRepository = userRepository;
    }

    /**
     * Protocole de pointage Face ID (caméra de la porte).
     * Reçoit l'email reconnu par le moteur IA et enregistre ENTRÉE ou SORTIE par alternance :
     *  - dernier statut = SORTIE (ou aucun)  → nouvelle ENTRÉE
     *  - dernier statut = ENTRÉE             → nouvelle SORTIE (+ calcul de la durée)
     * Les administrateurs ne sont PAS pointés. Seuls gestionnaires, observateurs et employés le sont.
     *
     * @return une map décrivant le résultat ("status": success|skipped|unknown|error).
     */
    public Map<String, Object> checkin(String email, String imagePath) {
        Map<String, Object> resp = new HashMap<>();

        if (email == null || email.isBlank()) {
            resp.put("status", "error");
            resp.put("message", "Email requis.");
            return resp;
        }

        String name = null;
        Long employeeId = null;

        // 1) Chercher d'abord dans les comptes utilisateurs (gestionnaires / observateurs / admin)
        Optional<User> userOpt = userRepository.findByEmail(email);
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            if (user.getRole() == Role.ROLE_ADMIN) {
                resp.put("status", "skipped");
                resp.put("employeeName", buildUserName(user));
                resp.put("message", "Administrateur — non pointé.");
                return resp;
            }
            name = buildUserName(user);
        }

        // 2) Chercher dans la table des employés (prioritaire pour le nom + employeeId)
        List<Employee> emps = employeeRepository.findByEmail(email);
        if (!emps.isEmpty()) {
            Employee e = emps.get(0);
            if (e.getName() != null && !e.getName().isBlank()) {
                name = e.getName();
            }
            employeeId = e.getId();
        }

        if (name == null || name.isBlank()) {
            resp.put("status", "unknown");
            resp.put("message", "Personne non reconnue en base.");
            return resp;
        }

        // 3) Déterminer le statut par alternance à partir du dernier enregistrement
        AttendanceRecord last = repository.findFirstByEmployeeNameOrderByTimestampDesc(name);
        String newStatus;
        Long durationSeconds = null;

        if (last == null || "EXIT".equalsIgnoreCase(last.getStatus())) {
            newStatus = "ENTRY";
        } else {
            newStatus = "EXIT";
            if (last.getTimestamp() != null) {
                durationSeconds = Math.max(0,
                        Duration.between(last.getTimestamp(), LocalDateTime.now()).getSeconds());
            }
        }

        AttendanceRecord rec = new AttendanceRecord();
        rec.setEmployeeName(name);
        rec.setEmployeeId(employeeId);
        rec.setStatus(newStatus);
        rec.setUnknown(false);
        rec.setImagePath(imagePath);
        rec.setDurationSeconds(durationSeconds);
        repository.save(rec);

        resp.put("status", "success");
        resp.put("employeeName", name);
        resp.put("attendanceStatus", newStatus);
        resp.put("durationSeconds", durationSeconds);
        resp.put("timestamp", rec.getTimestamp() != null ? rec.getTimestamp().toString() : null);
        return resp;
    }

    private String buildUserName(User user) {
        String first = user.getFirstName() != null ? user.getFirstName().trim() : "";
        String last = user.getLastName() != null ? user.getLastName().trim() : "";
        String full = (first + " " + last).trim();
        return full.isBlank() ? user.getEmail() : full;
    }

    public AttendanceRecord saveAttendance(AttendanceRequest request) {

        System.out.println("DATA RECUE: " + request.getEmployeeName());

        AttendanceRecord record = new AttendanceRecord();

        record.setEmployeeName(request.getEmployeeName());
        record.setStatus(request.getStatus());
        record.setUnknown(request.isUnknown());
        record.setImagePath(request.getImagePath());

        // Try to link to employee record by name for admin display
        if (request.getEmployeeName() != null && !request.isUnknown()) {
            try {
                List<Employee> matches = employeeRepository.findAll().stream()
                        .filter(e -> e.getName() != null
                                && e.getName().equalsIgnoreCase(request.getEmployeeName()))
                        .toList();
                if (!matches.isEmpty()) {
                    record.setEmployeeId(matches.get(0).getId());
                }
            } catch (Exception ignored) {}
        }

        return repository.save(record);
    }

    public List<AttendanceRecord> getAllAttendances() {
        return repository.findAllByOrderByTimestampDesc();
    }

    public List<AttendanceRecord> searchByName(String name) {
        if (name == null || name.isBlank()) {
            return repository.findAllByOrderByTimestampDesc();
        }
        return repository.findByEmployeeNameContainingIgnoreCaseOrderByTimestampDesc(name);
    }
}

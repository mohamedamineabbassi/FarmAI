package com.farm.backend.controller;

import com.farm.backend.entity.*;
import com.farm.backend.repository.*;
import com.farm.backend.service.EmailService;

import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/employees")
@CrossOrigin
public class EmployeeController {

    private final EmployeeRepository employeeRepository;
    private final FaceNotificationRepository faceNotificationRepository;
    private final DepartmentRepository departmentRepository;
    private final EmailService emailService;
    private final com.farm.backend.service.FaceService faceService;

    // ✅ CONSTRUCTEUR
    public EmployeeController(EmployeeRepository employeeRepository,
                              DepartmentRepository departmentRepository,
                              EmailService emailService,
                              com.farm.backend.service.FaceService faceService,
                              FaceNotificationRepository faceNotificationRepository) {

        this.employeeRepository = employeeRepository;
        this.departmentRepository = departmentRepository;
        this.emailService = emailService;
        this.faceService = faceService;
        this.faceNotificationRepository = faceNotificationRepository;
    }

    // =====================================================
    // 🔥 CREATE EMPLOYEE (PENDING + NO FACE)
    // =====================================================
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER')")
    @PostMapping("/employee")
    public Employee createEmployee(@RequestBody Employee employee) {

        employee.setDepartment(null);

        // ✅ LOGIQUE CORRECTE
        employee.setStatus(EmployeeStatus.PENDING);

        employee.setCreatedAt(LocalDateTime.now());
        employee.setJob(normalizeEmployeeJob(employee.getJob().name()));
        employee.setFaceRegistered(false);
        employee.setAvailable(true);

        Employee saved = employeeRepository.save(employee);

        // 📧 Send creation email asynchronously (non-blocking)
        emailService.sendEmployeeCreated(saved.getEmail(), saved.getName());

        return saved;
    }

    // =====================================================
    // 🔥 VALIDATION FACE (PAR VIEWER)
    // =====================================================
    @PutMapping("/validate-face/{id}")
    public Employee validateFace(@PathVariable Long id) {

        Employee emp = employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));

        emp.setFaceRegistered(true);
        // emp.setStatus(EmployeeStatus.APPROVED); // ❌ Separated from approval

        return employeeRepository.save(emp);
    }

    // =====================================================
    // 🔥 APPROVAL (PAR ADMIN)
    // =====================================================
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/approve/{id}")
    public Employee approveEmployee(@PathVariable Long id) {
        Employee emp = employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));

        emp.setStatus(EmployeeStatus.APPROVED);
        Employee saved = employeeRepository.save(emp);

        // 📧 Trigger Welcome Email
        emailService.sendWelcomeEmail(saved.getEmail(), saved.getName());

        return saved;
    }

    // =====================================================
    // 🔥 CREATE MANAGER (PENDING)
    // =====================================================
    @PreAuthorize("hasAuthority('ROLE_MANAGER')")
    @PostMapping("/manager")
    public Employee createByManager(@RequestBody Employee employee) {

        Department dep = departmentRepository
                .findById(employee.getDepartment().getId())
                .orElseThrow(() -> new RuntimeException("Department not found"));

        employee.setDepartment(dep);
        employee.setStatus(EmployeeStatus.PENDING);
        employee.setCreatedAt(LocalDateTime.now());
        employee.setFaceRegistered(false);
        employee.setAvailable(true);
        employee.setJob(Job.OTHER);

        return employeeRepository.save(employee);
    }

    // =====================================================
    // 🔥 ADMIN CREATE MANAGER
    // =====================================================
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/admin")
    public Employee createByAdmin(@RequestBody Employee employee) {

        Department dep = departmentRepository
                .findById(employee.getDepartment().getId())
                .orElseThrow(() -> new RuntimeException("Department not found"));

        employee.setDepartment(dep);
        employee.setStatus(EmployeeStatus.APPROVED);
        employee.setCreatedAt(LocalDateTime.now());
        employee.setAvailable(true);
        employee.setJob(Job.OTHER);

        return employeeRepository.save(employee);
    }

    // =====================================================
    // 🔥 GET ONLY EMPLOYEES
    // =====================================================
    @GetMapping("/only-employees")
    public List<Employee> getOnlyEmployees() {
        return employeeRepository.findByJobIn(Arrays.asList(Job.DOCTOR, Job.ELECTRICIAN, Job.WORKER));
    }

    private Job normalizeEmployeeJob(String job) {
        if (job == null || job.trim().isEmpty()) {
            return Job.WORKER;
        }

        String normalized = job.trim().toUpperCase();
        if ("DOCTEUR".equals(normalized) || "MEDECIN".equals(normalized) || "MÉDECIN".equals(normalized)) {
            return Job.DOCTOR;
        }
        if ("ELECTRICIEN".equals(normalized) || "ÉLECTRICIEN".equals(normalized)) {
            return Job.ELECTRICIAN;
        }
        if ("OUVRIER".equals(normalized) || "EMPLOYE".equals(normalized) || "EMPLOYÉ".equals(normalized)) {
            return Job.WORKER;
        }

        try {
            return Job.valueOf(normalized);
        } catch (IllegalArgumentException e) {
            return Job.WORKER;
        }
    }

    // =====================================================
    // 🔥 GET BY MANAGER
    // =====================================================
    @GetMapping("/manager/{id}")
    public List<Employee> getManagerEmployees(@PathVariable Long id) {
        return employeeRepository.findByDepartmentManagerId(id);
    }

    // =====================================================
    // 🔥 GET ALL
    // =====================================================
    @GetMapping
    public List<Employee> getAll() {
        try {
            return employeeRepository.findAll();
        } catch (Exception e) {
            System.err.println("ERROR IN GET ALL EMPLOYEES: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Server error: " + e.getMessage(), e);
        }
    }

    // 🔥 NEW: GET MY PROFILE (Find or create for Admin/User)
    @GetMapping("/me")
    public Employee getMyProfile(@RequestParam String email) {
        return employeeRepository.findAll().stream()
                .filter(e -> e.getEmail() != null && e.getEmail().equalsIgnoreCase(email))
                .findFirst()
                .orElseGet(() -> {
                    // Create a default employee record if none exists for this user
                    Employee newEmp = new Employee();
                    newEmp.setEmail(email);
                    newEmp.setName(email.split("@")[0]);
                    newEmp.setJob(Job.OTHER);
                    newEmp.setStatus(EmployeeStatus.APPROVED);
                    newEmp.setFaceRegistered(false);
                    newEmp.setCreatedAt(LocalDateTime.now());
                    return employeeRepository.save(newEmp);
                });
    }

    // =====================================================
    // 🔥 GET PENDING
    // =====================================================
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @GetMapping("/pending")
    public List<Employee> getPending() {
        return employeeRepository.findByStatus(EmployeeStatus.PENDING);
    }

    // =====================================================
    // 🔥 DELETE
    // =====================================================
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @DeleteMapping("/{id}")
    public String delete(@PathVariable Long id) {
        employeeRepository.deleteById(id);
        return "Employee deleted";
    }

    // =====================================================
    // 🔥 EMPLOYEES SANS FACE
    // =====================================================
    @GetMapping("/no-face")
    public List<Employee> getWithoutFace() {
        return employeeRepository.findByFaceRegisteredFalse();
    }

    // =====================================================
    // 🎭 FACE MANAGEMENT (PYTHON INTEGRATION — SOC camera)
    // =====================================================
    @PostMapping("/register-face/{id}")
    public Object registerFace(@PathVariable Long id) {
        faceService.registerFaceByEmployeeId(id);
        return Map.of("status", "success", "message", "Face registered");
    }

    @DeleteMapping("/delete-face/{id}")
    public Object deleteFace(@PathVariable Long id) {
        faceService.deleteFaceByEmployeeId(id);
        return Map.of("status", "success", "message", "Face deleted");
    }

    // =====================================================
    // 📸 FACE REGISTER — IMAGE NAVIGATEUR (STATELESS + NOTIFICATION)
    // =====================================================
    @PostMapping(value = "/register-face-image/{id}", consumes = {"multipart/form-data"})
    public Object registerFaceImage(
            @PathVariable Long id,
            @RequestParam("image") MultipartFile image,
            Authentication auth) {

        Employee employee = employeeRepository.findById(id)
                .orElse(null);
        if (employee == null) {
            return Map.of("status", "error", "message", "Employé introuvable.");
        }

        byte[] bytes;
        try {
            bytes = image.getBytes();
        } catch (Exception e) {
            return Map.of("status", "error", "message", "Lecture image impossible.");
        }

        // Appel Python AI stateless
        Map<String, Object> result = faceService.registerFromImage(
                bytes, image.getOriginalFilename(), employee.getEmail(), employee.getId());

        if ("success".equals(result.get("status"))) {
            // Mise à jour JPA
            employee.setFaceRegistered(true);
            employeeRepository.save(employee);

            // ─── Créer la notification pour l'admin ───
            FaceNotification notif = new FaceNotification();
            notif.setEmployeeId(employee.getId());
            notif.setEmployeeName(employee.getName());
            notif.setEmployeeEmail(employee.getEmail() != null ? employee.getEmail() : "");
            notif.setEmployeeJob(employee.getJob() != null ? employee.getJob().name() : "");
            notif.setViewerEmail(auth != null ? auth.getName() : "viewer");
            notif.setRegisteredAt(LocalDateTime.now());
            notif.setRead(false);

            // Stocker la miniature en base64 (max ~100 ko)
            try {
                String b64 = Base64.getEncoder().encodeToString(bytes);
                notif.setFaceSnapshot("data:image/jpeg;base64," + b64);
            } catch (Exception ignored) {}

            faceNotificationRepository.save(notif);

            return Map.of(
                "status", "success",
                "message", "Visage enregistré avec succès !",
                "employeeName", employee.getName()
            );
        }

        return result;
    }
}

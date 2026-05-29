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

    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER', 'ROLE_VIEWER')")
    @PostMapping("/employee")
    public Employee createEmployee(@RequestBody Employee employee) {

        employee.setDepartment(null);
        employee.setStatus(EmployeeStatus.PENDING);
        employee.setCreatedAt(LocalDateTime.now());
        employee.setJob(normalizeEmployeeJob(employee.getJob().name()));
        employee.setFaceRegistered(false);
        employee.setAvailable(true);

        Employee saved = employeeRepository.save(employee);

        emailService.sendEmployeeCreated(saved.getEmail(), saved.getName());

        return saved;
    }

    @PutMapping("/validate-face/{id}")
    public Employee validateFace(@PathVariable Long id) {

        Employee emp = employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));

        emp.setFaceRegistered(true);

        return employeeRepository.save(emp);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/approve/{id}")
    public Employee approveEmployee(@PathVariable Long id) {
        Employee emp = employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));

        emp.setStatus(EmployeeStatus.APPROVED);
        Employee saved = employeeRepository.save(emp);

        emailService.sendWelcomeEmail(saved.getEmail(), saved.getName());

        return saved;
    }

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

    @GetMapping("/manager/{id}")
    public List<Employee> getManagerEmployees(@PathVariable Long id) {
        return employeeRepository.findByDepartmentManagerId(id);
    }

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

    @GetMapping("/me")
    public Employee getMyProfile(@RequestParam String email) {
        return employeeRepository.findAll().stream()
                .filter(e -> e.getEmail() != null && e.getEmail().equalsIgnoreCase(email))
                .findFirst()
                .orElseGet(() -> {
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

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @GetMapping("/pending")
    public List<Employee> getPending() {
        return employeeRepository.findByStatus(EmployeeStatus.PENDING);
    }

    @GetMapping("/{id}")
    public Employee getById(@PathVariable Long id) {
        return employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));
    }

    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER')")
    @PutMapping("/{id}")
    public Employee updateEmployee(@PathVariable Long id, @RequestBody Employee updated) {
        Employee emp = employeeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Employee not found"));

        if (updated.getName() != null && !updated.getName().isBlank()) {
            emp.setName(updated.getName());
        }
        if (updated.getEmail() != null) {
            emp.setEmail(updated.getEmail());
        }
        if (updated.getPhone() != null) {
            emp.setPhone(updated.getPhone());
        }

        return employeeRepository.save(emp);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @DeleteMapping("/{id}")
    public String delete(@PathVariable Long id) {
        employeeRepository.deleteById(id);
        return "Employee deleted";
    }

    @GetMapping("/no-face")
    public List<Employee> getWithoutFace() {
        return employeeRepository.findByFaceRegisteredFalse();
    }

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

    @PostMapping(value = "/register-face-image/{id}", consumes = {"multipart/form-data"})
    public Object registerFaceImage(
            @PathVariable Long id,
            @RequestParam("image") MultipartFile image,
            Authentication auth) {

        Employee employee = employeeRepository.findById(id).orElse(null);
        if (employee == null) {
            return Map.of("status", "error", "message", "Employé introuvable.");
        }

        byte[] bytes;
        try {
            bytes = image.getBytes();
        } catch (Exception e) {
            return Map.of("status", "error", "message", "Lecture image impossible.");
        }

        Map<String, Object> result = faceService.registerFromImage(
                bytes, image.getOriginalFilename(), employee.getEmail(), employee.getId());

        if ("success".equals(result.get("status"))) {
            employee.setFaceRegistered(true);
            employeeRepository.save(employee);

            FaceNotification notif = new FaceNotification();
            notif.setEmployeeId(employee.getId());
            notif.setEmployeeName(employee.getName());
            notif.setEmployeeEmail(employee.getEmail() != null ? employee.getEmail() : "");
            notif.setEmployeeJob(employee.getJob() != null ? employee.getJob().name() : "");
            notif.setViewerEmail(auth != null ? auth.getName() : "viewer");
            notif.setRegisteredAt(LocalDateTime.now());
            notif.setRead(false);

            try {
                String b64 = Base64.getEncoder().encodeToString(bytes);
                String dataUrl = "data:image/jpeg;base64," + b64;
                notif.setFaceSnapshot(dataUrl);
                employee.setFacePhotoData(dataUrl);
                employeeRepository.save(employee);
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

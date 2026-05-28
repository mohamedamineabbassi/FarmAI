package com.farm.backend.controller;

import com.farm.backend.entity.Role;
import com.farm.backend.entity.User;
import com.farm.backend.entity.Employee;
import com.farm.backend.entity.EmployeeStatus;
import com.farm.backend.entity.Department;
import com.farm.backend.repository.UserRepository;
import com.farm.backend.repository.EmployeeRepository;
import com.farm.backend.repository.DepartmentRepository;
import com.farm.backend.repository.AlertRepository;
import com.farm.backend.service.EmailService;
import com.farm.backend.entity.Job;
import java.time.LocalDateTime;

import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/users")
@CrossOrigin
public class UserController {

    private final UserRepository repo;
    private final PasswordEncoder encoder;
    private final EmailService emailService;
    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;
    private final AlertRepository alertRepository;

    public UserController(UserRepository repo,
                          PasswordEncoder encoder,
                          EmailService emailService,
                          EmployeeRepository employeeRepository,
                          DepartmentRepository departmentRepository,
                          AlertRepository alertRepository) {
        this.repo = repo;
        this.encoder = encoder;
        this.emailService = emailService;
        this.employeeRepository = employeeRepository;
        this.departmentRepository = departmentRepository;
        this.alertRepository = alertRepository;
    }

    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER')")
    @GetMapping("/viewers")
    public List<User> getViewers() {
        return repo.findByRole(Role.ROLE_VIEWER);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/viewers")
    public ResponseEntity<?> createViewer(@RequestBody User user) {

        if (user.getEmail() == null || user.getEmail().trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "L'adresse email est obligatoire."));
        }
        if (user.getFirstName() == null || user.getFirstName().trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Le prénom est obligatoire."));
        }

        if (repo.existsByEmail(user.getEmail().trim())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "Cet email est déjà utilisé par un autre compte."));
        }

        String password = UUID.randomUUID().toString().substring(0, 8);
        String token    = UUID.randomUUID().toString();

        user.setEmail(user.getEmail().trim());
        user.setPassword(encoder.encode(password));
        user.setRole(Role.ROLE_VIEWER);
        user.setEnabled(false);
        user.setActivationToken(token);

        User saved;
        try {
            saved = repo.save(user);
        } catch (Exception e) {
            System.out.println("❌ ERREUR SAVE VIEWER: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Erreur base de données : " + e.getMessage()));
        }

        try {
            String fullName = (user.getFirstName() != null ? user.getFirstName() : "")
                    + (user.getLastName() != null && !user.getLastName().isEmpty() ? " " + user.getLastName() : "");
            Employee emp = new Employee();
            emp.setName(fullName.trim().isEmpty() ? user.getEmail() : fullName.trim());
            emp.setEmail(user.getEmail());
            emp.setJob(Job.OTHER);
            emp.setStatus(EmployeeStatus.APPROVED);
            emp.setCreatedAt(LocalDateTime.now());
            emp.setFaceRegistered(false);
            emp.setAvailable(true);
            employeeRepository.save(emp);
        } catch (Exception e) {
            System.out.println("⚠️ ERREUR CREATION EMPLOYEE VIEWER: " + e.getMessage());
        }

        emailService.sendViewerAccount(user.getEmail(), password, token);

        return ResponseEntity.ok(saved);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PutMapping("/viewers/{id}")
    public User updateViewer(@PathVariable Long id, @RequestBody User updated) {

        User user = repo.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setFirstName(updated.getFirstName());
        user.setLastName(updated.getLastName());
        user.setPhone(updated.getPhone());

        return repo.save(user);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @DeleteMapping("/viewers/{id}")
    public ResponseEntity<Void> deleteViewer(@PathVariable Long id) {
        User user = repo.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        departmentRepository.findAllByManagerId(id).forEach(dept -> {
            dept.setManager(null);
            departmentRepository.save(dept);
        });

        try {
            employeeRepository.findByEmail(user.getEmail()).forEach(employeeRepository::delete);
        } catch (Exception e) {
            System.out.println("⚠️ No employee to delete for viewer: " + e.getMessage());
        }

        repo.deleteById(id);
        return ResponseEntity.ok().build();
    }

    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER')")
    @GetMapping("/managers")
    public List<User> getManagers(org.springframework.security.core.Authentication auth) {
        System.out.println("User role: " + (auth != null ? auth.getAuthorities() : "NULL AUTH"));
        return repo.findByRole(Role.ROLE_MANAGER);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/managers")
    public ResponseEntity<?> createManager(@RequestBody User user) {

        if (user.getEmail() == null || user.getEmail().trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "L'adresse email est obligatoire."));
        }
        if (user.getFirstName() == null || user.getFirstName().trim().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Le prénom est obligatoire."));
        }

        if (repo.existsByEmail(user.getEmail().trim())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "Cet email est déjà utilisé par un autre compte."));
        }

        String password = UUID.randomUUID().toString().substring(0, 8);
        String token    = UUID.randomUUID().toString();

        user.setEmail(user.getEmail().trim());
        user.setPassword(encoder.encode(password));
        user.setRole(Role.ROLE_MANAGER);
        user.setEnabled(false);
        user.setActivationToken(token);

        User saved;
        try {
            saved = repo.save(user);
        } catch (Exception e) {
            System.out.println("❌ ERREUR SAVE MANAGER: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Erreur base de données : " + e.getMessage()));
        }

        try {
            String fullName = (user.getFirstName() != null ? user.getFirstName() : "")
                    + (user.getLastName() != null && !user.getLastName().isEmpty() ? " " + user.getLastName() : "");
            Employee emp = new Employee();
            emp.setName(fullName.trim().isEmpty() ? user.getEmail() : fullName.trim());
            emp.setEmail(user.getEmail());
            emp.setJob(Job.OTHER);
            emp.setStatus(EmployeeStatus.APPROVED);
            emp.setCreatedAt(LocalDateTime.now());
            emp.setFaceRegistered(false);
            emp.setAvailable(true);
            employeeRepository.save(emp);
        } catch (Exception e) {
            System.out.println("⚠️ ERREUR CREATION EMPLOYEE MANAGER: " + e.getMessage());
        }

        emailService.sendManagerAccount(user.getEmail(), password, token);

        return ResponseEntity.ok(saved);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PutMapping("/managers/{id}")
    public User updateManager(@PathVariable Long id, @RequestBody User updated) {

        User user = repo.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setFirstName(updated.getFirstName());
        user.setLastName(updated.getLastName());
        user.setPhone(updated.getPhone());

        return repo.save(user);
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @DeleteMapping("/managers/{id}")
    public ResponseEntity<Void> deleteManager(@PathVariable Long id) {
        User user = repo.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        departmentRepository.findAllByManagerId(id).forEach(dept -> {
            dept.setManager(null);
            departmentRepository.save(dept);
        });

        try {
            employeeRepository.findByEmail(user.getEmail()).forEach(employeeRepository::delete);
        } catch (Exception e) {
            System.out.println("⚠️ No employee to delete for manager: " + e.getMessage());
        }

        repo.deleteById(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/test-mail")
    public String testMail() {

        emailService.sendManagerAccount(
                "bondkaamine9@gmail.com",
                "123456",
                "TEST-TOKEN"
        );

        return "EMAIL SENT ✅";
    }

    @GetMapping("/get-profile")
    public ResponseEntity<User> getProfile(org.springframework.security.core.Authentication auth) {
        String email = auth.getName();
        User user = repo.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return ResponseEntity.ok(user);
    }

    @PutMapping("/update-profile")
    public ResponseEntity<?> updateProfile(@RequestBody User dto, org.springframework.security.core.Authentication auth) {
        String email = auth.getName();
        User user = repo.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setFirstName(dto.getFirstName());
        user.setLastName(dto.getLastName());
        user.setPhone(dto.getPhone());

        return ResponseEntity.ok(repo.save(user));
    }

    @PutMapping("/change-password")
    public ResponseEntity<?> changePassword(@RequestBody com.farm.backend.dto.PasswordDto dto, org.springframework.security.core.Authentication auth) {
        String email = auth.getName();
        User user = repo.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setPassword(encoder.encode(dto.getNewPassword()));
        repo.save(user);
        return ResponseEntity.ok("Password updated ✅");
    }

    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @GetMapping("/{id}")
    public User getOne(@PathVariable Long id) {
        return repo.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));
    }
}

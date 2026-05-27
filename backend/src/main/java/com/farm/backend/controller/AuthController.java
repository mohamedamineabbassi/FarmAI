package com.farm.backend.controller;

import com.farm.backend.entity.*;
import com.farm.backend.repository.*;
import com.farm.backend.config.JwtUtil;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.Map;
import java.io.IOException;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin
public class AuthController {

    private final UserRepository repo;
    private final PasswordEncoder encoder;
    private final EmployeeRepository employeeRepository;
    private final DepartmentRepository departmentRepository;
    private final com.farm.backend.service.FaceService faceService;

    public AuthController(UserRepository repo,
                          PasswordEncoder encoder,
                          EmployeeRepository employeeRepository,
                          DepartmentRepository departmentRepository,
                          com.farm.backend.service.FaceService faceService) {
        this.repo = repo;
        this.encoder = encoder;
        this.employeeRepository = employeeRepository;
        this.departmentRepository = departmentRepository;
        this.faceService = faceService;
    }

    // =========================
    // 🔐 LOGIN
    // =========================
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody User user) {

        if (user.getEmail() == null || user.getPassword() == null) {
            return ResponseEntity.badRequest()
                    .body(Map.of("message", "Email ou mot de passe manquant"));
        }

        var db = repo.findByEmail(user.getEmail());

        if (db.isEmpty()) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Email ou mot de passe incorrect ❌"));
        }

        if (!encoder.matches(user.getPassword(), db.get().getPassword())) {
            return ResponseEntity.status(401)
                    .body(Map.of("message", "Email ou mot de passe incorrect ❌"));
        }

        // 🔥 check if enabled
        if (!db.get().isEnabled()) {
            return ResponseEntity.status(403)
                    .body(Map.of("message", "Compte non activé. Vérifiez votre email."));
        }

        String token = JwtUtil.generateToken(
                db.get().getEmail(),
                db.get().getRole().name()
        );

        return ResponseEntity.ok(Map.of(
                "token", token,
                "role", db.get().getRole().name(),
                "email", db.get().getEmail(),
                "faceRegistered", db.get().isFaceRegistered(),
                "userId", db.get().getId()
        ));
    }

    // =========================
    // 🔗 ACTIVATE
    // =========================
    @PostMapping("/activate")
    public Object activate(@RequestParam String token) {
        var db = repo.findByActivationToken(token);
        if (db.isEmpty()) {
            return Map.of("error", "Invalid activation token");
        }
        User user = db.get();
        user.setEnabled(true);
        user.setActivationToken(null);
        repo.save(user);

        String jwt = JwtUtil.generateToken(user.getEmail(), user.getRole().name());

        return Map.of(
                "message", "Activated successfully",
                "userId", user.getId(),
                "role", user.getRole().name(),
                "faceRegistered", user.isFaceRegistered(),
                "token", jwt
        );
    }

    public static class RegisterRequest {
        public String email;
        public String password;
        public String role;
        public String job;
    }

    public static class FaceRegisterRequest {
        public Long userId;
    }

    @PostMapping("/face/register")
    public Object registerFace(@RequestBody FaceRegisterRequest request) {
        if (request.userId == null) {
            return Map.of("error", "userId is missing");
        }

        var userOpt = repo.findById(request.userId);
        if (userOpt.isEmpty()) {
            return Map.of("error", "User not found");
        }

        User user = userOpt.get();

        // Call FaceService to register face (it will sync to Employee if it exists)
        faceService.registerFace(user.getId());

        return Map.of(
                "message", "Face registered successfully",
                "userId", user.getId(),
                "role", user.getRole().name(),
                "faceRegistered", true
        );
    }

    // =========================
    // 👤 FACE LOGIN (STATELESS — browser snapshot)
    // =========================
    /**
     * Reçoit une image capturée par le navigateur (getUserMedia + canvas snapshot)
     * et l'envoie au moteur IA pour reconnaissance. Si match → JWT.
     *
     * Pas de dépendance au SOC Engine côté caméra ; tout est stateless.
     */
    @PostMapping(value = "/face-login", consumes = {"multipart/form-data"})
    public Object faceLogin(@RequestParam("image") MultipartFile image) {
        if (image == null || image.isEmpty()) {
            return Map.of("status", "error", "message", "Image manquante.");
        }

        byte[] bytes;
        try {
            bytes = image.getBytes();
        } catch (IOException e) {
            return Map.of("status", "error", "message", "Lecture de l'image impossible.");
        }

        Map<String, Object> recognition = faceService.recognizeFromImage(bytes, image.getOriginalFilename());

        if (!"success".equals(recognition.get("status"))) {
            return Map.of(
                "status", "error",
                "message", recognition.get("message") != null
                    ? recognition.get("message")
                    : "Visage non reconnu."
            );
        }

        String email = (String) recognition.get("email");
        if (email == null) {
            return Map.of("status", "error", "message", "Email inconnu.");
        }

        var user = repo.findByEmail(email);
        if (user.isEmpty()) {
            return Map.of("status", "error", "message", "Compte utilisateur introuvable.");
        }

        if (!user.get().isEnabled()) {
            return Map.of("status", "error", "message", "Compte non activé.");
        }

        if (!user.get().isFaceRegistered()) {
            return Map.of("status", "error",
                "message", "Visage non enregistré. Veuillez l'enregistrer dans Paramètres.");
        }

        String token = JwtUtil.generateToken(
                user.get().getEmail(),
                user.get().getRole().name()
        );

        Map<String, Object> response = new java.util.HashMap<>();
        response.put("status", "success");
        response.put("token", token);
        response.put("role", user.get().getRole().name());
        response.put("email", user.get().getEmail());
        response.put("faceRegistered", user.get().isFaceRegistered());
        response.put("userId", user.get().getId());
        response.put("confidence", recognition.get("confidence"));

        return response;
    }

    // =========================
    // 🔥 ADMIN CREATE USER
    // =========================
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @PostMapping("/register")
    public Object register(@RequestBody RegisterRequest request) {

        try {

            if (request.email == null || request.password == null || request.role == null || request.job == null) {
                return Map.of("error", "Missing fields");
            }

            if (repo.findByEmail(request.email).isPresent()) {
                return Map.of("error", "Email already exists");
            }

            Department dep = departmentRepository.findAll()
                    .stream()
                    .findFirst()
                    .orElseThrow(() -> new RuntimeException("No department found"));

            // 🔥 employee
            Employee emp = new Employee();
            emp.setName(request.email); 
            emp.setEmail(request.email); // 🔥 FIX: Set email field

            emp.setJob(Job.valueOf(request.job.toUpperCase()));
            emp.setStatus(EmployeeStatus.APPROVED);
            emp.setDepartment(dep);
            emp.setCreatedAt(LocalDateTime.now());
            emp.setFaceRegistered(false);

            employeeRepository.save(emp);

            // 🔥 user
            User user = new User();
            user.setEmail(request.email);
            user.setPassword(encoder.encode(request.password));
            user.setRole(Role.valueOf(request.role));
            user.setFaceRegistered(false);
            repo.save(user);

            // 🔥 LANCER PYTHON (via FaceService)
            faceService.registerFace(user.getId());

            return Map.of("msg", "USER CREATED + FACE STARTED");

        } catch (Exception e) {
            e.printStackTrace();
            return Map.of("error", "Server error");
        }
    }

    // =========================
    // 🔥 MANAGER CREATE VIEWER
    // =========================
    @PreAuthorize("hasRole('MANAGER')")
    @PostMapping("/create-viewer")
    public Object createViewer(@RequestBody User user) {

        if (user.getEmail() == null || user.getPassword() == null) {
            return Map.of("error", "Missing fields");
        }

        if (repo.findByEmail(user.getEmail()).isPresent()) {
            return Map.of("error", "Email already exists");
        }

        user.setRole(Role.ROLE_VIEWER);
        user.setPassword(encoder.encode(user.getPassword()));
        user.setFaceRegistered(false);

        repo.save(user);

        return Map.of("msg", "VIEWER CREATED");
    }
}

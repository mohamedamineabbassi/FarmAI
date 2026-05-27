package com.farm.backend.controller;

import com.farm.backend.entity.FaceNotification;
import com.farm.backend.repository.FaceNotificationRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/face-notifications")
@CrossOrigin
public class FaceNotificationController {

    private final FaceNotificationRepository repo;

    public FaceNotificationController(FaceNotificationRepository repo) {
        this.repo = repo;
    }

    /** Toutes les notifications (admin uniquement) */
    @GetMapping
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public List<FaceNotification> getAll() {
        return repo.findAllByOrderByRegisteredAtDesc();
    }

    /** Nombre de notifications non lues */
    @GetMapping("/unread-count")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public Map<String, Long> unreadCount() {
        return Map.of("count", repo.countByReadFalse());
    }

    /** Marquer comme lue */
    @PutMapping("/{id}/read")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public ResponseEntity<FaceNotification> markRead(@PathVariable Long id) {
        return repo.findById(id).map(n -> {
            n.setRead(true);
            return ResponseEntity.ok(repo.save(n));
        }).orElse(ResponseEntity.notFound().build());
    }

    /** Marquer toutes comme lues */
    @PutMapping("/read-all")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public Map<String, String> readAll() {
        repo.findAll().forEach(n -> { n.setRead(true); repo.save(n); });
        return Map.of("status", "ok");
    }

    /** Supprimer une notification */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    public Map<String, String> delete(@PathVariable Long id) {
        repo.deleteById(id);
        return Map.of("status", "deleted");
    }
}

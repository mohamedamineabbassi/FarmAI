package com.farm.backend.controller;

import com.farm.backend.dto.AttendanceRequest;
import com.farm.backend.dto.CheckinRequest;
import com.farm.backend.entity.AttendanceRecord;
import com.farm.backend.service.AttendanceService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/attendance")
@CrossOrigin
public class AttendanceController {

    private final AttendanceService service;

    public AttendanceController(AttendanceService service) {
        this.service = service;
    }

    // Open to AI — no auth required
    @PostMapping
    public AttendanceRecord createAttendance(@RequestBody AttendanceRequest request) {
        return service.saveAttendance(request);
    }

    // Pointage Face ID (caméra de la porte) — protocole entrée/sortie par alternance.
    // Ouvert (permitAll sur /api/attendance/**) : appelé par la caméra de présence.
    @PostMapping("/checkin")
    public Map<String, Object> checkin(@RequestBody CheckinRequest request) {
        return service.checkin(request.getEmail(), request.getImagePath());
    }

    // Admin + Manager only
    @PreAuthorize("hasAnyAuthority('ROLE_ADMIN', 'ROLE_MANAGER')")
    @GetMapping
    public List<AttendanceRecord> getAll(@RequestParam(required = false) String name) {
        return service.searchByName(name);
    }
}

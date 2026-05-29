package com.farm.backend.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "attendance")
public class AttendanceRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "employee_name")
    private String employeeName;

    private String status;

    private boolean unknown;

    @Column(name = "employee_id")
    private Long employeeId;

    @Column(name = "image_path")
    private String imagePath;

    /** Durée de présence (en secondes) entre l'ENTRÉE et la SORTIE — renseignée uniquement sur l'enregistrement de SORTIE. */
    @Column(name = "duration_seconds")
    private Long durationSeconds;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime timestamp;

    @PrePersist
    protected void onCreate() {
        this.timestamp = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public String getEmployeeName() {
        return employeeName;
    }

    public String getStatus() {
        return status;
    }

    public boolean isUnknown() {
        return unknown;
    }

    public Long getEmployeeId() {
        return employeeId;
    }

    public void setEmployeeId(Long employeeId) {
        this.employeeId = employeeId;
    }

    public String getImagePath() {
        return imagePath;
    }

    public Long getDurationSeconds() {
        return durationSeconds;
    }

    public void setDurationSeconds(Long durationSeconds) {
        this.durationSeconds = durationSeconds;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setEmployeeName(String employeeName) {
        this.employeeName = employeeName;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setUnknown(boolean unknown) {
        this.unknown = unknown;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }
}
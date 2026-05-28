package com.farm.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "face_notifications")
public class FaceNotification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long employeeId;
    private String employeeName;
    private String employeeEmail;
    private String employeeJob;
    private String viewerEmail;

    @Column(columnDefinition = "LONGTEXT")
    private String faceSnapshot;   // image JPEG encodée en base64

    private LocalDateTime registeredAt;

    @Column(name = "is_read")
    private boolean read = false;

    public Long getId()                  { return id; }
    public Long getEmployeeId()          { return employeeId; }
    public String getEmployeeName()      { return employeeName; }
    public String getEmployeeEmail()     { return employeeEmail; }
    public String getEmployeeJob()       { return employeeJob; }
    public String getViewerEmail()       { return viewerEmail; }
    public String getFaceSnapshot()      { return faceSnapshot; }
    public LocalDateTime getRegisteredAt(){ return registeredAt; }
    public boolean isRead()              { return read; }

    public void setId(Long id)                          { this.id = id; }
    public void setEmployeeId(Long employeeId)          { this.employeeId = employeeId; }
    public void setEmployeeName(String employeeName)    { this.employeeName = employeeName; }
    public void setEmployeeEmail(String employeeEmail)  { this.employeeEmail = employeeEmail; }
    public void setEmployeeJob(String employeeJob)      { this.employeeJob = employeeJob; }
    public void setViewerEmail(String viewerEmail)      { this.viewerEmail = viewerEmail; }
    public void setFaceSnapshot(String faceSnapshot)    { this.faceSnapshot = faceSnapshot; }
    public void setRegisteredAt(LocalDateTime r)        { this.registeredAt = r; }
    public void setRead(boolean read)                   { this.read = read; }
}

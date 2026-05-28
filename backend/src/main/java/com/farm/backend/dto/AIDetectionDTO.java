package com.farm.backend.dto;

public class AIDetectionDTO {

    private String type;
    private String location;
    private String timestamp;
    private String imageBase64;
    private String embeddingHash;
    private Long   employeeId;
    private Long   cameraId;
    private String trackingId;
    private String direction;

    private String severity;

    private String animalLabel;

    public String getType()                      { return type; }
    public void   setType(String type)           { this.type = type; }

    public String getLocation()                  { return location; }
    public void   setLocation(String location)   { this.location = location; }

    public String getTimestamp()                 { return timestamp; }
    public void   setTimestamp(String timestamp) { this.timestamp = timestamp; }

    public String getImageBase64()               { return imageBase64; }
    public void   setImageBase64(String v)       { this.imageBase64 = v; }

    public String getEmbeddingHash()             { return embeddingHash; }
    public void   setEmbeddingHash(String v)     { this.embeddingHash = v; }

    public Long   getEmployeeId()                { return employeeId; }
    public void   setEmployeeId(Long v)          { this.employeeId = v; }

    public Long   getCameraId()                  { return cameraId; }
    public void   setCameraId(Long v)            { this.cameraId = v; }

    public String getTrackingId()                { return trackingId; }
    public void   setTrackingId(String v)        { this.trackingId = v; }

    public String getDirection()                 { return direction; }
    public void   setDirection(String v)         { this.direction = v; }

    public String getSeverity()                  { return severity; }
    public void   setSeverity(String severity)   { this.severity = severity; }

    public String getAnimalLabel()               { return animalLabel; }
    public void   setAnimalLabel(String v)       { this.animalLabel = v; }
}

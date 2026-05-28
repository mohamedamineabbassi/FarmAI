package com.farm.backend.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "department_requirements")
public class DepartmentRequirement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "department_id", nullable = false)
    private Department department;

    private String job;
    private int requiredCount;

    public Long getId() { return id; }
    public Department getDepartment() { return department; }
    public String getJob() { return job; }
    public int getRequiredCount() { return requiredCount; }

    public void setId(Long id) { this.id = id; }
    public void setDepartment(Department department) { this.department = department; }
    public void setJob(String job) { this.job = job; }
    public void setRequiredCount(int requiredCount) { this.requiredCount = requiredCount; }
}
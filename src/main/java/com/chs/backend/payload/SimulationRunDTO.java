package com.chs.backend.payload;

import com.chs.backend.models.SimulationStatus;

import java.time.LocalDateTime;

public class SimulationRunDTO {
    private Long id;
    private ProjectDTO project;
    private SimulationStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime completedAt;

    // Constructors, Getters, and Setters

    public SimulationRunDTO() {
    }

    public SimulationRunDTO(Long id, ProjectDTO project, SimulationStatus status, LocalDateTime createdAt, LocalDateTime completedAt) {
        this.id = id;
        this.project = project;
        this.status = status;
        this.createdAt = createdAt;
        this.completedAt = completedAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public ProjectDTO getProject() {
        return project;
    }

    public void setProject(ProjectDTO project) {
        this.project = project;
    }

    public SimulationStatus getStatus() {
        return status;
    }

    public void setStatus(SimulationStatus status) {
        this.status = status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }
}

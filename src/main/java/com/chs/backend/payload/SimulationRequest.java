package com.chs.backend.payload;

import jakarta.validation.constraints.NotNull;

public class SimulationRequest {

    @NotNull
    private Long scenarioId;

    private String fidelity; // e.g., "high", "low"

    // Getters and Setters

    public Long getScenarioId() {
        return scenarioId;
    }

    public void setScenarioId(Long scenarioId) {
        this.scenarioId = scenarioId;
    }

    public String getFidelity() {
        return fidelity;
    }

    public void setFidelity(String fidelity) {
        this.fidelity = fidelity;
    }
}

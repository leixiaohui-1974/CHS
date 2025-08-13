package com.chs.backend.payload;

import com.chs.backend.models.SimulationStatus;

import java.io.Serializable;

public class SimulationStatusUpdateMessage implements Serializable {

    private Long simulationId;
    private SimulationStatus status;
    private String details;

    public SimulationStatusUpdateMessage() {
    }

    public SimulationStatusUpdateMessage(Long simulationId, SimulationStatus status, String details) {
        this.simulationId = simulationId;
        this.status = status;
        this.details = details;
    }

    public Long getSimulationId() {
        return simulationId;
    }

    public void setSimulationId(Long simulationId) {
        this.simulationId = simulationId;
    }

    public SimulationStatus getStatus() {
        return status;
    }

    public void setStatus(SimulationStatus status) {
        this.status = status;
    }

    public String getDetails() {
        return details;
    }

    public void setDetails(String details) {
        this.details = details;
    }
}

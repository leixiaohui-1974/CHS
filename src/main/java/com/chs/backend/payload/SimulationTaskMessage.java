package com.chs.backend.payload;

import java.io.Serializable;

public class SimulationTaskMessage implements Serializable {

    private Long simulationRunId;
    private Long scenarioId;
    private String fidelity;

    public SimulationTaskMessage() {
    }

    public SimulationTaskMessage(Long simulationRunId, Long scenarioId, String fidelity) {
        this.simulationRunId = simulationRunId;
        this.scenarioId = scenarioId;
        this.fidelity = fidelity;
    }

    public Long getSimulationRunId() {
        return simulationRunId;
    }

    public void setSimulationRunId(Long simulationRunId) {
        this.simulationRunId = simulationRunId;
    }

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

    @Override
    public String toString() {
        return "SimulationTaskMessage{" +
                "simulationRunId=" + simulationRunId +
                ", scenarioId=" + scenarioId +
                ", fidelity='" + fidelity + '\'' +
                '}';
    }
}

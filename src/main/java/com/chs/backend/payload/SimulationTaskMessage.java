package com.chs.backend.payload;

import java.io.Serializable;

public class SimulationTaskMessage implements Serializable {

    private Long simulationId;

    public SimulationTaskMessage() {
    }

    public SimulationTaskMessage(Long simulationId) {
        this.simulationId = simulationId;
    }

    public Long getSimulationId() {
        return simulationId;
    }

    public void setSimulationId(Long simulationId) {
        this.simulationId = simulationId;
    }

    @Override
    public String toString() {
        return "SimulationTaskMessage{" +
                "simulationId=" + simulationId +
                '}';
    }
}

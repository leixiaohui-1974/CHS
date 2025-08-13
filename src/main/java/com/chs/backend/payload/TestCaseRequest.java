package com.chs.backend.payload;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class TestCaseRequest {

    @NotBlank
    @Size(max = 100)
    private String name;

    @Size(max = 2048)
    private String presetConditions;

    @Size(max = 2048)
    private String incentiveSignals;

    @Size(max = 2048)
    private String executionSequence;

    @Size(max = 2048)
    private String evaluationCriteria;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPresetConditions() {
        return presetConditions;
    }

    public void setPresetConditions(String presetConditions) {
        this.presetConditions = presetConditions;
    }

    public String getIncentiveSignals() {
        return incentiveSignals;
    }

    public void setIncentiveSignals(String incentiveSignals) {
        this.incentiveSignals = incentiveSignals;
    }

    public String getExecutionSequence() {
        return executionSequence;
    }

    public void setExecutionSequence(String executionSequence) {
        this.executionSequence = executionSequence;
    }

    public String getEvaluationCriteria() {
        return evaluationCriteria;
    }

    public void setEvaluationCriteria(String evaluationCriteria) {
        this.evaluationCriteria = evaluationCriteria;
    }
}

package com.chs.backend.models;

import jakarta.persistence.*;
import java.util.Objects;

@Entity
@Table(name = "test_cases")
public class TestCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(length = 2048)
    private String presetConditions;

    @Column(length = 2048)
    private String incentiveSignals;

    @Column(length = 2048)
    private String executionSequence;

    @Column(length = 2048)
    private String evaluationCriteria;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "scenario_id", nullable = false)
    private Scenario scenario;

    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

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

    public Scenario getScenario() {
        return scenario;
    }

    public void setScenario(Scenario scenario) {
        this.scenario = scenario;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TestCase testCase = (TestCase) o;
        return Objects.equals(id, testCase.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

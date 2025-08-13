package com.chs.backend.services;

import com.chs.backend.models.Scenario;
import com.chs.backend.models.TestCase;
import com.chs.backend.models.User;
import com.chs.backend.payload.TestCaseRequest;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.ScenarioRepository;
import com.chs.backend.repositories.TestCaseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class TestCaseService {

    @Autowired
    private TestCaseRepository testCaseRepository;

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private ProjectRepository projectRepository;

    public TestCase createTestCase(Long projectId, Long scenarioId, TestCaseRequest testCaseRequest, User user) {
        Scenario scenario = findScenarioAndVerifyAccess(projectId, scenarioId, user);

        TestCase testCase = new TestCase();
        testCase.setName(testCaseRequest.getName());
        testCase.setPresetConditions(testCaseRequest.getPresetConditions());
        testCase.setIncentiveSignals(testCaseRequest.getIncentiveSignals());
        testCase.setExecutionSequence(testCaseRequest.getExecutionSequence());
        testCase.setEvaluationCriteria(testCaseRequest.getEvaluationCriteria());
        testCase.setScenario(scenario);

        return testCaseRepository.save(testCase);
    }

    public List<TestCase> getAllTestCases(Long projectId, Long scenarioId, User user) {
        findScenarioAndVerifyAccess(projectId, scenarioId, user);
        return testCaseRepository.findByScenarioId(scenarioId);
    }

    public Optional<TestCase> getTestCaseById(Long projectId, Long scenarioId, Long testCaseId, User user) {
        findScenarioAndVerifyAccess(projectId, scenarioId, user);
        return testCaseRepository.findByIdAndScenarioId(testCaseId, scenarioId);
    }

    @Transactional
    public TestCase updateTestCase(Long projectId, Long scenarioId, Long testCaseId, TestCaseRequest testCaseRequest, User user) {
        findScenarioAndVerifyAccess(projectId, scenarioId, user);
        TestCase testCase = testCaseRepository.findByIdAndScenarioId(testCaseId, scenarioId)
                .orElseThrow(() -> new RuntimeException("TestCase not found"));

        testCase.setName(testCaseRequest.getName());
        testCase.setPresetConditions(testCaseRequest.getPresetConditions());
        testCase.setIncentiveSignals(testCaseRequest.getIncentiveSignals());
        testCase.setExecutionSequence(testCaseRequest.getExecutionSequence());
        testCase.setEvaluationCriteria(testCaseRequest.getEvaluationCriteria());

        return testCaseRepository.save(testCase);
    }

    public void deleteTestCase(Long projectId, Long scenarioId, Long testCaseId, User user) {
        findScenarioAndVerifyAccess(projectId, scenarioId, user);
        TestCase testCase = testCaseRepository.findByIdAndScenarioId(testCaseId, scenarioId)
                .orElseThrow(() -> new RuntimeException("TestCase not found"));

        testCaseRepository.delete(testCase);
    }

    private Scenario findScenarioAndVerifyAccess(Long projectId, Long scenarioId, User user) {
        projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));
        return scenarioRepository.findByIdAndProjectId(scenarioId, projectId)
                .orElseThrow(() -> new RuntimeException("Scenario not found in this project"));
    }
}

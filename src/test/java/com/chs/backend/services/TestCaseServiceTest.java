package com.chs.backend.services;

import com.chs.backend.models.Project;
import com.chs.backend.models.Scenario;
import com.chs.backend.models.TestCase;
import com.chs.backend.models.User;
import com.chs.backend.payload.TestCaseRequest;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.ScenarioRepository;
import com.chs.backend.repositories.TestCaseRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class TestCaseServiceTest {

    @Mock
    private TestCaseRepository testCaseRepository;

    @Mock
    private ScenarioRepository scenarioRepository;

    @Mock
    private ProjectRepository projectRepository;

    @InjectMocks
    private TestCaseService testCaseService;

    private User user;
    private Project project;
    private Scenario scenario;
    private TestCase testCase;
    private TestCaseRequest testCaseRequest;

    @BeforeEach
    void setUp() {
        user = new User();
        user.setId(1L);
        user.setUsername("testuser");

        project = new Project();
        project.setId(1L);
        project.setUser(user);

        scenario = new Scenario();
        scenario.setId(1L);
        scenario.setProject(project);

        testCase = new TestCase();
        testCase.setId(1L);
        testCase.setScenario(scenario);
        testCase.setName("Test Case");

        testCaseRequest = new TestCaseRequest();
        testCaseRequest.setName("Test Case");
    }

    @Test
    void testCreateTestCase() {
        when(projectRepository.findByIdAndUser(1L, user)).thenReturn(Optional.of(project));
        when(scenarioRepository.findByIdAndProjectId(1L, 1L)).thenReturn(Optional.of(scenario));
        when(testCaseRepository.save(any(TestCase.class))).thenReturn(testCase);

        TestCase createdTestCase = testCaseService.createTestCase(1L, 1L, testCaseRequest, user);

        assertNotNull(createdTestCase);
        assertEquals("Test Case", createdTestCase.getName());
    }

    @Test
    void testGetAllTestCases() {
        when(projectRepository.findByIdAndUser(1L, user)).thenReturn(Optional.of(project));
        when(scenarioRepository.findByIdAndProjectId(1L, 1L)).thenReturn(Optional.of(scenario));
        when(testCaseRepository.findByScenarioId(1L)).thenReturn(Collections.singletonList(testCase));

        List<TestCase> testCases = testCaseService.getAllTestCases(1L, 1L, user);

        assertNotNull(testCases);
        assertEquals(1, testCases.size());
        assertEquals("Test Case", testCases.get(0).getName());
    }
}

package com.chs.backend.services;

import com.chs.backend.models.Project;
import com.chs.backend.models.Scenario;
import com.chs.backend.models.User;
import com.chs.backend.payload.ScenarioRequest;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.ScenarioRepository;
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
public class ScenarioServiceTest {

    @Mock
    private ScenarioRepository scenarioRepository;

    @Mock
    private ProjectRepository projectRepository;

    @InjectMocks
    private ScenarioService scenarioService;

    private User user;
    private Project project;
    private Scenario scenario;
    private ScenarioRequest scenarioRequest;

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
        scenario.setName("Test Scenario");

        scenarioRequest = new ScenarioRequest();
        scenarioRequest.setName("Test Scenario");
    }

    @Test
    void testCreateScenario() {
        when(projectRepository.findByIdAndUser(1L, user)).thenReturn(Optional.of(project));
        when(scenarioRepository.save(any(Scenario.class))).thenReturn(scenario);

        Scenario createdScenario = scenarioService.createScenario(1L, scenarioRequest, user);

        assertNotNull(createdScenario);
        assertEquals("Test Scenario", createdScenario.getName());
    }

    @Test
    void testGetAllScenarios() {
        when(projectRepository.findByIdAndUser(1L, user)).thenReturn(Optional.of(project));
        when(scenarioRepository.findByProjectId(1L)).thenReturn(Collections.singletonList(scenario));

        List<Scenario> scenarios = scenarioService.getAllScenarios(1L, user);

        assertNotNull(scenarios);
        assertEquals(1, scenarios.size());
        assertEquals("Test Scenario", scenarios.get(0).getName());
    }
}

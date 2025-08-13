package com.chs.backend.services;

import com.chs.backend.models.Project;
import com.chs.backend.models.Scenario;
import com.chs.backend.models.User;
import com.chs.backend.payload.ScenarioRequest;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.ScenarioRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class ScenarioService {

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private ProjectRepository projectRepository;

    public Scenario createScenario(Long projectId, ScenarioRequest scenarioRequest, User user) {
        Project project = projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));

        Scenario scenario = new Scenario();
        scenario.setName(scenarioRequest.getName());
        scenario.setDescription(scenarioRequest.getDescription());
        scenario.setProject(project);

        return scenarioRepository.save(scenario);
    }

    public List<Scenario> getAllScenarios(Long projectId, User user) {
        projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));
        return scenarioRepository.findByProjectId(projectId);
    }

    public Optional<Scenario> getScenarioById(Long projectId, Long scenarioId, User user) {
        projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));
        return scenarioRepository.findByIdAndProjectId(scenarioId, projectId);
    }

    @Transactional
    public Scenario updateScenario(Long projectId, Long scenarioId, ScenarioRequest scenarioRequest, User user) {
        projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));
        Scenario scenario = scenarioRepository.findByIdAndProjectId(scenarioId, projectId)
                .orElseThrow(() -> new RuntimeException("Scenario not found"));

        scenario.setName(scenarioRequest.getName());
        scenario.setDescription(scenarioRequest.getDescription());

        return scenarioRepository.save(scenario);
    }

    public void deleteScenario(Long projectId, Long scenarioId, User user) {
        projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));
        Scenario scenario = scenarioRepository.findByIdAndProjectId(scenarioId, projectId)
                .orElseThrow(() -> new RuntimeException("Scenario not found"));

        scenarioRepository.delete(scenario);
    }
}

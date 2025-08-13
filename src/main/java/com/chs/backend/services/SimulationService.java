package com.chs.backend.services;

import com.chs.backend.config.RabbitMQConfig;
import com.chs.backend.config.RabbitMQConfig;
import com.chs.backend.models.*;
import com.chs.backend.payload.ProjectDTO;
import com.chs.backend.payload.SimulationRunDTO;
import com.chs.backend.payload.SimulationRequest;
import com.chs.backend.payload.SimulationTaskMessage;
import com.chs.backend.payload.UserDTO;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.ScenarioRepository;
import com.chs.backend.repositories.SimulationRunRepository;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class SimulationService {

    @Autowired
    private SimulationRunRepository simulationRunRepository;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    public SimulationRunDTO createAndRunSimulation(Long projectId, SimulationRequest simulationRequest, User user) {
        Project project = projectRepository.findByIdAndUser(projectId, user)
                .orElseThrow(() -> new AccessDeniedException("Project not found or access denied"));

        Scenario scenario = scenarioRepository.findByIdAndProjectId(simulationRequest.getScenarioId(), projectId)
                .orElseThrow(() -> new RuntimeException("Scenario not found in this project"));

        SimulationRun simulationRun = new SimulationRun();
        simulationRun.setProject(project);
        simulationRun.setScenario(scenario);
        SimulationRun savedSimulation = simulationRunRepository.save(simulationRun);

        SimulationTaskMessage message = new SimulationTaskMessage(
                savedSimulation.getId(),
                scenario.getId(),
                simulationRequest.getFidelity()
        );
        rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE_NAME, RabbitMQConfig.ROUTING_KEY_SIMULATION_TASKS, message);

        return convertToDTO(savedSimulation);
    }

    public Optional<SimulationRunDTO> getSimulationRunById(Long simulationId, User user) {
        return simulationRunRepository.findById(simulationId)
                .filter(simulationRun -> simulationRun.getProject().getUser().equals(user))
                .map(this::convertToDTO);
    }

    private SimulationRunDTO convertToDTO(SimulationRun simulationRun) {
        User user = simulationRun.getProject().getUser();
        UserDTO userDTO = new UserDTO(user.getId(), user.getUsername(), user.getEmail());

        Project project = simulationRun.getProject();
        ProjectDTO projectDTO = new ProjectDTO(project.getId(), project.getName(), userDTO);

        return new SimulationRunDTO(
                simulationRun.getId(),
                projectDTO,
                simulationRun.getStatus(),
                simulationRun.getCreatedAt(),
                simulationRun.getCompletedAt()
        );
    }
}

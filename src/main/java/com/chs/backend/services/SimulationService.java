package com.chs.backend.services;

import com.chs.backend.config.RabbitMQConfig;
import com.chs.backend.models.Project;
import com.chs.backend.models.SimulationRun;
import com.chs.backend.payload.SimulationStatusUpdateMessage;
import com.chs.backend.payload.SimulationTaskMessage;
import com.chs.backend.repositories.SimulationRunRepository;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


import java.util.Optional;

@Service
public class SimulationService {

    @Autowired
    private SimulationRunRepository simulationRunRepository;

    @Autowired
    private ProjectService projectService;

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    public Optional<SimulationRun> createSimulation(Long projectId, UserDetails userDetails) {
        return projectService.getProjectByIdForUser(projectId, userDetails)
                .map(project -> {
                    SimulationRun simulationRun = new SimulationRun();
                    simulationRun.setProject(project);
                    // The status is set to PENDING by the @PrePersist method in the entity
                    SimulationRun savedSimulation = simulationRunRepository.save(simulationRun);

                    // Publish a message to RabbitMQ to start the task
                    SimulationTaskMessage message = new SimulationTaskMessage(savedSimulation.getId());
                    rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE_NAME, RabbitMQConfig.QUEUE_SIMULATION_TASKS, message);

                    // For demonstration: immediately publish a status update
                    // In a real system, a worker would do this.
                    SimulationStatusUpdateMessage statusUpdate = new SimulationStatusUpdateMessage(savedSimulation.getId(), savedSimulation.getStatus(), "Task received by worker.");
                    rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE_NAME, "simulation.status.running", statusUpdate);

                    return savedSimulation;
                });
    }

    public Optional<SimulationRun> getSimulationById(Long simulationId, UserDetails userDetails) {
        return simulationRunRepository.findById(simulationId)
                .filter(simulationRun -> {
                    Project project = simulationRun.getProject();
                    // Check if the user has access to the project this simulation belongs to
                    return projectService.getProjectByIdForUser(project.getId(), userDetails).isPresent();
                });
    }
}

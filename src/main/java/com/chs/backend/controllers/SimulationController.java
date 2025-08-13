package com.chs.backend.controllers;

import com.chs.backend.payload.SimulationRunDTO;
import com.chs.backend.payload.SimulationRequest;
import com.chs.backend.security.UserPrincipal;
import com.chs.backend.services.SimulationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class SimulationController {

    @Autowired
    private SimulationService simulationService;

    @PostMapping("/projects/{projectId}/simulations")
    public ResponseEntity<SimulationRunDTO> submitSimulation(@PathVariable Long projectId,
                                                           @Valid @RequestBody SimulationRequest simulationRequest,
                                                           @AuthenticationPrincipal UserPrincipal currentUser) {
        SimulationRunDTO simulationRunDTO = simulationService.createAndRunSimulation(projectId, simulationRequest, currentUser.getUser());
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(simulationRunDTO);
    }

    @GetMapping("/simulations/{id}")
    public ResponseEntity<SimulationRunDTO> getSimulation(@PathVariable Long id, @AuthenticationPrincipal UserPrincipal currentUser) {
        return simulationService.getSimulationRunById(id, currentUser.getUser())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

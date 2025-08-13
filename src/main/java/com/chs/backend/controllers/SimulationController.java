package com.chs.backend.controllers;

import com.chs.backend.models.SimulationRun;
import com.chs.backend.payload.SimulationRequest;
import com.chs.backend.security.UserPrincipal;
import com.chs.backend.services.SimulationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class SimulationController {

    @Autowired
    private SimulationService simulationService;

    @PostMapping("/projects/{projectId}/simulations")
    public ResponseEntity<SimulationRun> submitSimulation(@PathVariable Long projectId,
                                                          @Valid @RequestBody SimulationRequest simulationRequest,
                                                          @AuthenticationPrincipal UserPrincipal currentUser) {
        SimulationRun simulationRun = simulationService.createAndRunSimulation(projectId, simulationRequest, currentUser.getUser());
        return ResponseEntity.ok(simulationRun);
    }

    @GetMapping("/simulations/{id}")
    public ResponseEntity<SimulationRun> getSimulation(@PathVariable Long id, @AuthenticationPrincipal UserPrincipal currentUser) {
        return simulationService.getSimulationRunById(id, currentUser.getUser())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

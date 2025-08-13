package com.chs.backend.controllers;

import com.chs.backend.models.SimulationRun;
import com.chs.backend.services.SimulationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class SimulationController {

    @Autowired
    private SimulationService simulationService;

    @PostMapping("/projects/{projectId}/simulations")
    public ResponseEntity<SimulationRun> submitSimulation(@PathVariable Long projectId, @AuthenticationPrincipal UserDetails userDetails) {
        return simulationService.createSimulation(projectId, userDetails)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build()); // Or bad request if project not found
    }

    @GetMapping("/simulations/{id}")
    public ResponseEntity<SimulationRun> getSimulation(@PathVariable Long id, @AuthenticationPrincipal UserDetails userDetails) {
        return simulationService.getSimulationById(id, userDetails)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

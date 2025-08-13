package com.chs.backend.controllers;

import com.chs.backend.models.Scenario;
import com.chs.backend.models.User;
import com.chs.backend.payload.ScenarioRequest;
import com.chs.backend.services.ScenarioService;
import com.chs.backend.security.CurrentUser;
import com.chs.backend.security.UserPrincipal;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/api/projects/{projectId}/scenarios")
public class ScenarioController {

    @Autowired
    private ScenarioService scenarioService;

    @PostMapping
    public ResponseEntity<Scenario> createScenario(@PathVariable Long projectId,
                                                   @Valid @RequestBody ScenarioRequest scenarioRequest,
                                                   @AuthenticationPrincipal UserPrincipal currentUser) {
        Scenario scenario = scenarioService.createScenario(projectId, scenarioRequest, currentUser.getUser());
        return ResponseEntity.created(URI.create("/api/projects/" + projectId + "/scenarios/" + scenario.getId()))
                .body(scenario);
    }

    @GetMapping
    public List<Scenario> getAllScenarios(@PathVariable Long projectId,
                                          @AuthenticationPrincipal UserPrincipal currentUser) {
        return scenarioService.getAllScenarios(projectId, currentUser.getUser());
    }

    @GetMapping("/{scenarioId}")
    public ResponseEntity<Scenario> getScenarioById(@PathVariable Long projectId,
                                                    @PathVariable Long scenarioId,
                                                    @AuthenticationPrincipal UserPrincipal currentUser) {
        return scenarioService.getScenarioById(projectId, scenarioId, currentUser.getUser())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{scenarioId}")
    public ResponseEntity<Scenario> updateScenario(@PathVariable Long projectId,
                                                   @PathVariable Long scenarioId,
                                                   @Valid @RequestBody ScenarioRequest scenarioRequest,
                                                   @AuthenticationPrincipal UserPrincipal currentUser) {
        Scenario updatedScenario = scenarioService.updateScenario(projectId, scenarioId, scenarioRequest, currentUser.getUser());
        return ResponseEntity.ok(updatedScenario);
    }

    @DeleteMapping("/{scenarioId}")
    public ResponseEntity<Void> deleteScenario(@PathVariable Long projectId,
                                               @PathVariable Long scenarioId,
                                               @AuthenticationPrincipal UserPrincipal currentUser) {
        scenarioService.deleteScenario(projectId, scenarioId, currentUser.getUser());
        return ResponseEntity.noContent().build();
    }
}

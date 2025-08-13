package com.chs.backend.controllers;

import com.chs.backend.models.ModelDefinition;
import com.chs.backend.models.ModelVersion;
import com.chs.backend.payload.ModelDefinitionRequest;
import com.chs.backend.payload.ModelVersionRequest;
import com.chs.backend.security.UserPrincipal;
import com.chs.backend.services.ModelRegistryService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/models")
public class ModelRegistryController {

    @Autowired
    private ModelRegistryService modelRegistryService;

    @Autowired
    private ModelDeploymentService modelDeploymentService;

    @GetMapping
    public List<ModelDefinition> getAllModels(@AuthenticationPrincipal UserPrincipal currentUser) {
        return modelRegistryService.getAllModelDefinitionsForUser(currentUser.getUser());
    }

    @PostMapping
    public ModelDefinition createModel(@Valid @RequestBody ModelDefinitionRequest modelRequest,
                                       @AuthenticationPrincipal UserPrincipal currentUser) {
        ModelDefinition modelDefinition = new ModelDefinition();
        modelDefinition.setName(modelRequest.getName());
        modelDefinition.setDescription(modelRequest.getDescription());
        return modelRegistryService.createModelDefinition(modelDefinition, currentUser.getUser());
    }

    @GetMapping("/{id}")
    public ResponseEntity<ModelDefinition> getModelById(@PathVariable Long id,
                                                        @AuthenticationPrincipal UserPrincipal currentUser) {
        return modelRegistryService.getModelDefinitionByIdForUser(id, currentUser.getUser())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}/versions")
    public ResponseEntity<ModelVersion> addVersionToModel(@PathVariable Long id, @Valid @RequestBody ModelVersionRequest versionRequest) {
        return modelRegistryService.addModelVersion(id, versionRequest)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/versions/{versionId}/deploy")
    public ResponseEntity<?> deployModel(@PathVariable Long versionId) {
        return modelRegistryService.getModelVersionById(versionId)
                .map(modelVersion -> {
                    modelDeploymentService.deploy(modelVersion);
                    return ResponseEntity.ok().build();
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/versions/{versionId}/scale")
    public ResponseEntity<?> scaleModel(@PathVariable Long versionId, @RequestParam int replicas) {
        modelDeploymentService.scale(versionId, replicas);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/versions/{versionId}/update")
    public ResponseEntity<?> updateModel(@PathVariable Long versionId, @Valid @RequestBody ModelVersionRequest versionRequest) {
        return modelRegistryService.getModelVersionById(versionId)
                .map(modelVersion -> {
                    // In a real system, you might want to update the existing modelVersion object
                    // For now, we'll just pass a new one to the deployment service
                    ModelVersion updatedVersion = new ModelVersion();
                    updatedVersion.setVersionTag(versionRequest.getVersionTag());
                    updatedVersion.setDockerImageUri(versionRequest.getDockerImageUri());
                    modelDeploymentService.update(updatedVersion);
                    return ResponseEntity.ok().build();
                })
                .orElse(ResponseEntity.notFound().build());
    }
}

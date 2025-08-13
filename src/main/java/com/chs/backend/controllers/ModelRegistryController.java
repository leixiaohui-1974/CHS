package com.chs.backend.controllers;

import com.chs.backend.models.ModelDefinition;
import com.chs.backend.models.ModelVersion;
import com.chs.backend.payload.ModelDefinitionRequest;
import com.chs.backend.payload.ModelVersionRequest;
import com.chs.backend.services.ModelRegistryService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/models")
public class ModelRegistryController {

    @Autowired
    private ModelRegistryService modelRegistryService;

    @GetMapping
    public List<ModelDefinition> getAllModels() {
        return modelRegistryService.getAllModelDefinitions();
    }

    @PostMapping
    public ModelDefinition createModel(@Valid @RequestBody ModelDefinitionRequest modelRequest) {
        ModelDefinition modelDefinition = new ModelDefinition();
        modelDefinition.setName(modelRequest.getName());
        modelDefinition.setDescription(modelRequest.getDescription());
        return modelRegistryService.createModelDefinition(modelDefinition);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ModelDefinition> getModelById(@PathVariable Long id) {
        return modelRegistryService.getModelDefinitionById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}/versions")
    public ResponseEntity<ModelVersion> addVersionToModel(@PathVariable Long id, @Valid @RequestBody ModelVersionRequest versionRequest) {
        return modelRegistryService.addModelVersion(id, versionRequest)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

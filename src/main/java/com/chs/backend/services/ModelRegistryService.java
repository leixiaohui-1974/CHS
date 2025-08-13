package com.chs.backend.services;

import com.chs.backend.models.ModelDefinition;
import com.chs.backend.models.ModelVersion;
import com.chs.backend.models.User;
import com.chs.backend.payload.ModelVersionRequest;
import com.chs.backend.repositories.ModelDefinitionRepository;
import com.chs.backend.repositories.ModelVersionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class ModelRegistryService {

    @Autowired
    private ModelDefinitionRepository modelDefinitionRepository;

    @Autowired
    private ModelVersionRepository modelVersionRepository;

    public ModelDefinition createModelDefinition(ModelDefinition modelDefinition, User user) {
        modelDefinition.setUser(user);
        return modelDefinitionRepository.save(modelDefinition);
    }

    public List<ModelDefinition> getAllModelDefinitionsForUser(User user) {
        return modelDefinitionRepository.findByUser(user);
    }

    public Optional<ModelDefinition> getModelDefinitionByIdForUser(Long id, User user) {
        return modelDefinitionRepository.findByIdAndUser(id, user);
    }

    public Optional<ModelVersion> getModelVersionById(Long id) {
        return modelVersionRepository.findById(id);
    }

    @Transactional
    public Optional<ModelVersion> addModelVersion(Long modelDefinitionId, ModelVersionRequest versionRequest) {
        return modelDefinitionRepository.findById(modelDefinitionId)
                .map(definition -> {
                    ModelVersion newVersion = new ModelVersion();
                    newVersion.setModelDefinition(definition);
                    newVersion.setVersionTag(versionRequest.getVersionTag());
                    newVersion.setDockerImageUri(versionRequest.getDockerImageUri());
                    newVersion.setSdkVersionConstraint(versionRequest.getSdkVersionConstraint());
                    return modelVersionRepository.save(newVersion);
                });
    }
}

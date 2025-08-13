package com.chs.backend.services;

import com.chs.backend.models.ModelVersion;

public interface ModelDeploymentService {
    void deploy(ModelVersion modelVersion);
    void scale(Long modelVersionId, int replicas);
    void update(ModelVersion modelVersion);
}

package com.chs.backend.models;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Objects;

@Entity
@Table(name = "model_versions")
public class ModelVersion {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "model_definition_id", nullable = false)
    private ModelDefinition modelDefinition;

    @Column(name = "version_tag", nullable = false)
    private String versionTag;

    @Column(name = "docker_image_uri")
    private String dockerImageUri;

    @Column(name = "sdk_version_constraint")
    private String sdkVersionConstraint;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public ModelDefinition getModelDefinition() {
        return modelDefinition;
    }

    public void setModelDefinition(ModelDefinition modelDefinition) {
        this.modelDefinition = modelDefinition;
    }

    public String getVersionTag() {
        return versionTag;
    }

    public void setVersionTag(String versionTag) {
        this.versionTag = versionTag;
    }

    public String getDockerImageUri() {
        return dockerImageUri;
    }

    public void setDockerImageUri(String dockerImageUri) {
        this.dockerImageUri = dockerImageUri;
    }

    public String getSdkVersionConstraint() {
        return sdkVersionConstraint;
    }

    public void setSdkVersionConstraint(String sdkVersionConstraint) {
        this.sdkVersionConstraint = sdkVersionConstraint;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ModelVersion that = (ModelVersion) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

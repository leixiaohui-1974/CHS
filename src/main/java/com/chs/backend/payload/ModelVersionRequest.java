package com.chs.backend.payload;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class ModelVersionRequest {

    @NotBlank
    @Size(min = 1, max = 50)
    private String versionTag;

    private String dockerImageUri;

    private String sdkVersionConstraint;

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
}

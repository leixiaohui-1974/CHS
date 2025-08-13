package com.chs.backend.payload;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class ScenarioRequest {

    @NotBlank
    @Size(max = 100)
    private String name;

    @Size(max = 1024)
    private String description;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}

package com.chs.backend.payload;

public class ProjectDTO {
    private Long id;
    private String name;
    private UserDTO user;

    public ProjectDTO(Long id, String name, UserDTO user) {
        this.id = id;
        this.name = name;
        this.user = user;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public UserDTO getUser() {
        return user;
    }

    public void setUser(UserDTO user) {
        this.user = user;
    }
}

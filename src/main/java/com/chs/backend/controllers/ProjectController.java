package com.chs.backend.controllers;

import com.chs.backend.models.Project;
import com.chs.backend.payload.ProjectRequest;
import com.chs.backend.services.ProjectService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/projects")
public class ProjectController {

    @Autowired
    private ProjectService projectService;

    @GetMapping
    public List<Project> getAllProjects(@AuthenticationPrincipal UserDetails userDetails) {
        return projectService.getAllProjectsForUser(userDetails);
    }

    @PostMapping
    public Project createProject(@Valid @RequestBody ProjectRequest projectRequest, @AuthenticationPrincipal UserDetails userDetails) {
        Project project = new Project();
        project.setName(projectRequest.getName());
        project.setDescription(projectRequest.getDescription());
        return projectService.createProject(project, userDetails);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Project> getProjectById(@PathVariable Long id, @AuthenticationPrincipal UserDetails userDetails) {
        return projectService.getProjectByIdForUser(id, userDetails)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}")
    public ResponseEntity<Project> updateProject(@PathVariable Long id, @Valid @RequestBody ProjectRequest projectRequest, @AuthenticationPrincipal UserDetails userDetails) {
        Project projectDetails = new Project();
        projectDetails.setName(projectRequest.getName());
        projectDetails.setDescription(projectRequest.getDescription());
        return projectService.updateProject(id, projectDetails, userDetails)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteProject(@PathVariable Long id, @AuthenticationPrincipal UserDetails userDetails) {
        if (projectService.deleteProject(id, userDetails)) {
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.notFound().build();
    }
}

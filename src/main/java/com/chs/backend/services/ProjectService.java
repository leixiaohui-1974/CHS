package com.chs.backend.services;

import com.chs.backend.models.Project;
import com.chs.backend.models.User;
import com.chs.backend.repositories.ProjectRepository;
import com.chs.backend.repositories.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class ProjectService {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;

    public List<Project> getAllProjectsForUser(UserDetails userDetails) {
        User user = getUserFromDetails(userDetails);
        return projectRepository.findByUser(user);
    }

    public Optional<Project> getProjectByIdForUser(Long id, UserDetails userDetails) {
        User user = getUserFromDetails(userDetails);
        return projectRepository.findByIdAndUser(id, user);
    }

    public Project createProject(Project project, UserDetails userDetails) {
        User user = getUserFromDetails(userDetails);
        project.setUser(user);
        return projectRepository.save(project);
    }

    public Optional<Project> updateProject(Long id, Project projectDetails, UserDetails userDetails) {
        User user = getUserFromDetails(userDetails);
        return projectRepository.findByIdAndUser(id, user)
                .map(project -> {
                    project.setName(projectDetails.getName());
                    project.setDescription(projectDetails.getDescription());
                    return projectRepository.save(project);
                });
    }

    public boolean deleteProject(Long id, UserDetails userDetails) {
        User user = getUserFromDetails(userDetails);
        return projectRepository.findByIdAndUser(id, user)
                .map(project -> {
                    projectRepository.delete(project);
                    return true;
                }).orElse(false);
    }

    private User getUserFromDetails(UserDetails userDetails) {
        return userRepository.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + userDetails.getUsername()));
    }
}

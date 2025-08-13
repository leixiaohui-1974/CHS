package com.chs.backend;

import com.chs.backend.models.*;
import com.chs.backend.payload.LoginRequest;
import com.chs.backend.payload.RegisterRequest;
import com.chs.backend.payload.SimulationRequest;
import com.chs.backend.repositories.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class SimulationIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private String token;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
        projectRepository.deleteAll();
        scenarioRepository.deleteAll();
        roleRepository.deleteAll();

        Role userRole = roleRepository.save(new Role(RoleName.ROLE_USER));
        User user = new User();
        user.setUsername("testuser");
        user.setPassword(passwordEncoder.encode("password"));
        user.setEmail("test@test.com");
        user.setRoles(Collections.singleton(userRole));
        userRepository.save(user);

        LoginRequest loginRequest = new LoginRequest();
        loginRequest.setUsername("testuser");
        loginRequest.setPassword("password");

        ResponseEntity<String> response = restTemplate.postForEntity(
                "http://localhost:" + port + "/api/auth/login", loginRequest, String.class);
        token = response.getBody().split("\"accessToken\":\"")[1].split("\"")[0];
    }

    @Test
    void testSubmitSimulation() {
        User user = userRepository.findByUsername("testuser").get();
        Project project = new Project();
        project.setName("Test Project");
        project.setUser(user);
        project = projectRepository.save(project);

        Scenario scenario = new Scenario();
        scenario.setName("Test Scenario");
        scenario.setProject(project);
        scenario = scenarioRepository.save(scenario);

        SimulationRequest simulationRequest = new SimulationRequest();
        simulationRequest.setScenarioId(scenario.getId());
        simulationRequest.setFidelity("high");

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        HttpEntity<SimulationRequest> entity = new HttpEntity<>(simulationRequest, headers);

        ResponseEntity<SimulationRun> response = restTemplate.exchange(
                "http://localhost:" + port + "/api/projects/" + project.getId() + "/simulations",
                HttpMethod.POST,
                entity,
                SimulationRun.class
        );

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(project.getId(), response.getBody().getProject().getId());
    }
}

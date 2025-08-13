package com.chs.backend.controllers;

import com.chs.backend.models.TestCase;
import com.chs.backend.payload.TestCaseRequest;
import com.chs.backend.security.UserPrincipal;
import com.chs.backend.services.TestCaseService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/api/projects/{projectId}/scenarios/{scenarioId}/testcases")
public class TestCaseController {

    @Autowired
    private TestCaseService testCaseService;

    @PostMapping
    public ResponseEntity<TestCase> createTestCase(@PathVariable Long projectId,
                                                     @PathVariable Long scenarioId,
                                                     @Valid @RequestBody TestCaseRequest testCaseRequest,
                                                     @AuthenticationPrincipal UserPrincipal currentUser) {
        TestCase testCase = testCaseService.createTestCase(projectId, scenarioId, testCaseRequest, currentUser.getUser());
        return ResponseEntity.created(URI.create("/api/projects/" + projectId + "/scenarios/" + scenarioId + "/testcases/" + testCase.getId()))
                .body(testCase);
    }

    @GetMapping
    public List<TestCase> getAllTestCases(@PathVariable Long projectId,
                                          @PathVariable Long scenarioId,
                                          @AuthenticationPrincipal UserPrincipal currentUser) {
        return testCaseService.getAllTestCases(projectId, scenarioId, currentUser.getUser());
    }

    @GetMapping("/{testCaseId}")
    public ResponseEntity<TestCase> getTestCaseById(@PathVariable Long projectId,
                                                      @PathVariable Long scenarioId,
                                                      @PathVariable Long testCaseId,
                                                      @AuthenticationPrincipal UserPrincipal currentUser) {
        return testCaseService.getTestCaseById(projectId, scenarioId, testCaseId, currentUser.getUser())
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{testCaseId}")
    public ResponseEntity<TestCase> updateTestCase(@PathVariable Long projectId,
                                                   @PathVariable Long scenarioId,
                                                   @PathVariable Long testCaseId,
                                                   @Valid @RequestBody TestCaseRequest testCaseRequest,
                                                   @AuthenticationPrincipal UserPrincipal currentUser) {
        TestCase updatedTestCase = testCaseService.updateTestCase(projectId, scenarioId, testCaseId, testCaseRequest, currentUser.getUser());
        return ResponseEntity.ok(updatedTestCase);
    }

    @DeleteMapping("/{testCaseId}")
    public ResponseEntity<Void> deleteTestCase(@PathVariable Long projectId,
                                               @PathVariable Long scenarioId,
                                               @PathVariable Long testCaseId,
                                               @AuthenticationPrincipal UserPrincipal currentUser) {
        testCaseService.deleteTestCase(projectId, scenarioId, testCaseId, currentUser.getUser());
        return ResponseEntity.noContent().build();
    }
}

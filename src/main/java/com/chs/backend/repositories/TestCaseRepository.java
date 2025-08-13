package com.chs.backend.repositories;

import com.chs.backend.models.TestCase;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TestCaseRepository extends JpaRepository<TestCase, Long> {
    List<TestCase> findByScenarioId(Long scenarioId);
    Optional<TestCase> findByIdAndScenarioId(Long id, Long scenarioId);
}

package com.chs.backend.repositories;

import com.chs.backend.models.Scenario;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ScenarioRepository extends JpaRepository<Scenario, Long> {
    List<Scenario> findByProjectId(Long projectId);
    Optional<Scenario> findByIdAndProjectId(Long id, Long projectId);
}

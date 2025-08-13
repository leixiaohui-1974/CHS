package com.chs.backend.repositories;

import com.chs.backend.models.Project;
import com.chs.backend.models.SimulationRun;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SimulationRunRepository extends JpaRepository<SimulationRun, Long> {
    List<SimulationRun> findByProject(Project project);
    Optional<SimulationRun> findByIdAndProject(Long id, Project project);
}

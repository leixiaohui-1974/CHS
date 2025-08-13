package com.chs.backend.repositories;

import com.chs.backend.models.ModelDefinition;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface ModelDefinitionRepository extends JpaRepository<ModelDefinition, Long> {
    Optional<ModelDefinition> findByName(String name);
}

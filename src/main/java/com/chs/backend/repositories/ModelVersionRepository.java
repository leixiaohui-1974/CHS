package com.chs.backend.repositories;

import com.chs.backend.models.ModelVersion;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ModelVersionRepository extends JpaRepository<ModelVersion, Long> {
}

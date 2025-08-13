package com.chs.backend.repositories;

import com.chs.backend.models.UserProgress;
import com.chs.backend.models.UserProgressId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserProgressRepository extends JpaRepository<UserProgress, UserProgressId> {
}

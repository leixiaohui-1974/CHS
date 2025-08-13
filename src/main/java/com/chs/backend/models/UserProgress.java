package com.chs.backend.models;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Objects;

@Entity
@Table(name = "user_progress")
public class UserProgress {

    @EmbeddedId
    private UserProgressId id;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("userId")
    @JoinColumn(name = "user_id")
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("lessonId")
    @JoinColumn(name = "lesson_id")
    private Lesson lesson;

    @Column(name = "completed_at", nullable = false)
    private LocalDateTime completedAt;

    // Constructors, Getters, and Setters

    public UserProgress() {
    }

    public UserProgress(User user, Lesson lesson) {
        this.user = user;
        this.lesson = lesson;
        this.id = new UserProgressId(user.getId(), lesson.getId());
        this.completedAt = LocalDateTime.now();
    }

    public UserProgressId getId() {
        return id;
    }

    public void setId(UserProgressId id) {
        this.id = id;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    public Lesson getLesson() {
        return lesson;
    }

    public void setLesson(Lesson lesson) {
        this.lesson = lesson;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UserProgress that = (UserProgress) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

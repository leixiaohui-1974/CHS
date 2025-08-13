package com.chs.backend.services;

import com.chs.backend.models.Course;
import com.chs.backend.models.Lesson;
import com.chs.backend.repositories.CourseRepository;
import com.chs.backend.repositories.LessonRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CourseServiceTest {

    @Mock
    private CourseRepository courseRepository;

    @Mock
    private LessonRepository lessonRepository;

    @InjectMocks
    private CourseService courseService;

    private Course course1;
    private Course course2;
    private Lesson lesson1;

    @BeforeEach
    void setUp() {
        course1 = new Course();
        course1.setId(1L);
        course1.setTitle("Test Course 1");

        course2 = new Course();
        course2.setId(2L);
        course2.setTitle("Test Course 2");

        lesson1 = new Lesson();
        lesson1.setId(101L);
        lesson1.setTitle("Test Lesson 1");
        lesson1.setCourse(course1);
    }

    @Test
    void testGetAllCourses() {
        when(courseRepository.findAll()).thenReturn(Arrays.asList(course1, course2));

        List<Course> courses = courseService.getAllCourses();

        assertNotNull(courses);
        assertEquals(2, courses.size());
        verify(courseRepository, times(1)).findAll();
    }

    @Test
    void testGetCourseById_found() {
        when(courseRepository.findById(1L)).thenReturn(Optional.of(course1));

        Optional<Course> result = courseService.getCourseById(1L);

        assertTrue(result.isPresent());
        assertEquals("Test Course 1", result.get().getTitle());
        verify(courseRepository, times(1)).findById(1L);
    }

    @Test
    void testGetCourseById_notFound() {
        when(courseRepository.findById(99L)).thenReturn(Optional.empty());

        Optional<Course> result = courseService.getCourseById(99L);

        assertFalse(result.isPresent());
        verify(courseRepository, times(1)).findById(99L);
    }

    @Test
    void testGetLessonsByCourseId() {
        when(lessonRepository.findByCourseIdOrderByLessonOrderAsc(1L)).thenReturn(List.of(lesson1));

        List<Lesson> lessons = courseService.getLessonsByCourseId(1L);

        assertNotNull(lessons);
        assertEquals(1, lessons.size());
        assertEquals("Test Lesson 1", lessons.get(0).getTitle());
        verify(lessonRepository, times(1)).findByCourseIdOrderByLessonOrderAsc(1L);
    }
}

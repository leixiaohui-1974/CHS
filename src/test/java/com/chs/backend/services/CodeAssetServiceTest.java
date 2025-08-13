package com.chs.backend.services;

import com.chs.backend.models.CodeSnippet;
import com.chs.backend.models.Notebook;
import com.chs.backend.repositories.CodeSnippetRepository;
import com.chs.backend.repositories.NotebookRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CodeAssetServiceTest {

    @Mock
    private CodeSnippetRepository codeSnippetRepository;

    @Mock
    private NotebookRepository notebookRepository;

    @InjectMocks
    private CodeAssetService codeAssetService;

    private CodeSnippet snippet;
    private Notebook notebook;

    @BeforeEach
    void setUp() {
        snippet = new CodeSnippet();
        snippet.setId(1L);
        snippet.setTitle("Test Snippet");

        notebook = new Notebook();
        notebook.setId(1L);
        notebook.setTitle("Test Notebook");
    }

    @Test
    void testGetAllCodeSnippets() {
        when(codeSnippetRepository.findAll()).thenReturn(Collections.singletonList(snippet));
        List<CodeSnippet> result = codeAssetService.getAllCodeSnippets();
        assertNotNull(result);
        assertEquals(1, result.size());
        verify(codeSnippetRepository, times(1)).findAll();
    }

    @Test
    void testGetCodeSnippetById() {
        when(codeSnippetRepository.findById(1L)).thenReturn(Optional.of(snippet));
        Optional<CodeSnippet> result = codeAssetService.getCodeSnippetById(1L);
        assertTrue(result.isPresent());
        assertEquals("Test Snippet", result.get().getTitle());
        verify(codeSnippetRepository, times(1)).findById(1L);
    }

    @Test
    void testGetAllNotebooks() {
        when(notebookRepository.findAll()).thenReturn(Collections.singletonList(notebook));
        List<Notebook> result = codeAssetService.getAllNotebooks();
        assertNotNull(result);
        assertEquals(1, result.size());
        verify(notebookRepository, times(1)).findAll();
    }

    @Test
    void testGetNotebookById() {
        when(notebookRepository.findById(1L)).thenReturn(Optional.of(notebook));
        Optional<Notebook> result = codeAssetService.getNotebookById(1L);
        assertTrue(result.isPresent());
        assertEquals("Test Notebook", result.get().getTitle());
        verify(notebookRepository, times(1)).findById(1L);
    }
}

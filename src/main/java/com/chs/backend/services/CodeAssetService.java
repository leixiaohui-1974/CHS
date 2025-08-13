package com.chs.backend.services;

import com.chs.backend.models.CodeSnippet;
import com.chs.backend.models.Notebook;
import com.chs.backend.repositories.CodeSnippetRepository;
import com.chs.backend.repositories.NotebookRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class CodeAssetService {

    @Autowired
    private CodeSnippetRepository codeSnippetRepository;

    @Autowired
    private NotebookRepository notebookRepository;

    public List<CodeSnippet> getAllCodeSnippets() {
        return codeSnippetRepository.findAll();
    }

    public Optional<CodeSnippet> getCodeSnippetById(Long id) {
        return codeSnippetRepository.findById(id);
    }

    public List<Notebook> getAllNotebooks() {
        return notebookRepository.findAll();
    }

    public Optional<Notebook> getNotebookById(Long id) {
        return notebookRepository.findById(id);
    }

    // Methods for creating/updating assets can be added later
}

package com.chs.backend.controllers;

import com.chs.backend.models.CodeSnippet;
import com.chs.backend.models.Notebook;
import com.chs.backend.services.CodeAssetService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/assets")
public class CodeAssetController {

    @Autowired
    private CodeAssetService codeAssetService;

    @GetMapping("/snippets")
    public List<CodeSnippet> getAllCodeSnippets() {
        return codeAssetService.getAllCodeSnippets();
    }

    @GetMapping("/snippets/{id}")
    public ResponseEntity<CodeSnippet> getCodeSnippetById(@PathVariable Long id) {
        return codeAssetService.getCodeSnippetById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/notebooks")
    public List<Notebook> getAllNotebooks() {
        return codeAssetService.getAllNotebooks();
    }

    @GetMapping("/notebooks/{id}")
    public ResponseEntity<Notebook> getNotebookById(@PathVariable Long id) {
        return codeAssetService.getNotebookById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

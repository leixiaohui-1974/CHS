package com.chs.backend.services;

import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

public interface FileStorageService {
    String storeFile(MultipartFile file, String path);
    Resource loadFileAsResource(String fileName, String path);
}

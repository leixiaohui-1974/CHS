package com.chs.backend.services;

import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class S3FileStorageService implements FileStorageService {

    private static final Logger logger = LoggerFactory.getLogger(S3FileStorageService.class);
    private final AmazonS3 s3client;

    @Value("${aws.s3.bucket}")
    private String bucketName;

    public S3FileStorageService(@Value("${aws.accessKeyId}") String accessKey,
                                @Value("${aws.secretKey}") String secretKey,
                                @Value("${aws.s3.endpoint}") String endpoint) {
        AWSCredentials credentials = new BasicAWSCredentials(accessKey, secretKey);
        this.s3client = AmazonS3ClientBuilder.standard()
                .withCredentials(new AWSStaticCredentialsProvider(credentials))
                .withEndpointConfiguration(new AwsClientBuilder.EndpointConfiguration(endpoint, null))
                .build();
        logger.info("S3 client initialized with endpoint: {}", endpoint);
    }

    @Override
    public String storeFile(MultipartFile file, String path) {
        // Placeholder implementation
        logger.info("Placeholder: Storing file {} to path {}", file.getOriginalFilename(), path);
        throw new UnsupportedOperationException("File storage is not fully implemented yet.");
    }

    @Override
    public Resource loadFileAsResource(String fileName, String path) {
        // Placeholder implementation
        logger.info("Placeholder: Loading file {} from path {}", fileName, path);
        throw new UnsupportedOperationException("File loading is not fully implemented yet.");
    }
}

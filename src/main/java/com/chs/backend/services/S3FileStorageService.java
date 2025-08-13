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
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectRequest;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.services.s3.model.S3ObjectInputStream;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

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
        String key = path + "/" + file.getOriginalFilename();
        try {
            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(file.getSize());
            metadata.setContentType(file.getContentType());
            s3client.putObject(new PutObjectRequest(bucketName, key, file.getInputStream(), metadata));
            logger.info("Successfully uploaded file {} to S3 with key {}", file.getOriginalFilename(), key);
            return key;
        } catch (IOException e) {
            logger.error("Failed to upload file {} to S3", file.getOriginalFilename(), e);
            throw new RuntimeException("Failed to store file", e);
        }
    }

    @Override
    public Resource loadFileAsResource(String fileName, String path) {
        String key = path + "/" + fileName;
        try {
            S3Object s3Object = s3client.getObject(bucketName, key);
            S3ObjectInputStream inputStream = s3Object.getObjectContent();
            return new InputStreamResource(inputStream);
        } catch (Exception e) {
            logger.error("Failed to load file {} from S3", key, e);
            throw new RuntimeException("Failed to load file", e);
        }
    }
}

package com.chs.backend.controllers;

import com.chs.backend.config.RabbitMQConfig;
import com.chs.backend.payload.ControlMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Controller;

@Controller
public class WebSocketController {

    private static final Logger logger = LoggerFactory.getLogger(WebSocketController.class);

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @MessageMapping("/control")
    public void sendControlMessage(@Payload ControlMessage controlMessage) {
        logger.info("Received control message from WebSocket: {}", controlMessage);
        rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE_NAME, RabbitMQConfig.ROUTING_KEY_CONTROL_MESSAGES, controlMessage);
    }
}

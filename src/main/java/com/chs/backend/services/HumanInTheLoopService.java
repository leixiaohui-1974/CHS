package com.chs.backend.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
public class HumanInTheLoopService {

    private static final Logger logger = LoggerFactory.getLogger(HumanInTheLoopService.class);

    @Autowired
    private SimpMessagingTemplate messagingTemplate;

    public void sendSimulationStatusUpdate(Long simulationId, Object payload) {
        String topic = "/topic/simulations/" + simulationId;
        logger.info("Sending status update to WebSocket topic {}: {}", topic, payload);
        messagingTemplate.convertAndSend(topic, payload);
    }
}

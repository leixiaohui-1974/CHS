package com.chs.backend.listeners;

import com.chs.backend.config.RabbitMQConfig;
import com.chs.backend.payload.SimulationStatusUpdateMessage;
import com.chs.backend.services.HumanInTheLoopService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("!test")
public class RabbitMQListener {

    private static final Logger logger = LoggerFactory.getLogger(RabbitMQListener.class);

    @Autowired
    private HumanInTheLoopService humanInTheLoopService;

    @RabbitListener(queues = RabbitMQConfig.QUEUE_SIMULATION_STATUS_UPDATES)
    public void receiveStatusUpdate(SimulationStatusUpdateMessage message) {
        logger.info("Received status update from RabbitMQ: {}", message.getSimulationId());
        humanInTheLoopService.sendSimulationStatusUpdate(message.getSimulationId(), message);
    }
}

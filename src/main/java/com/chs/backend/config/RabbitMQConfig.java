package com.chs.backend.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String EXCHANGE_NAME = "chs_exchange";
    public static final String QUEUE_SIMULATION_TASKS = "simulation_tasks";
    public static final String QUEUE_SIMULATION_STATUS_UPDATES = "simulation_status_updates";
    public static final String QUEUE_CONTROL_MESSAGES = "control_messages";
    public static final String ROUTING_KEY_SIMULATION_TASKS = "simulation.tasks";
    public static final String ROUTING_KEY_CONTROL_MESSAGES = "simulation.control";
    public static final String ROUTING_KEY_STATUS_UPDATE = "simulation.status.#";


    @Bean
    public TopicExchange exchange() {
        return new TopicExchange(EXCHANGE_NAME);
    }

    @Bean
    public Queue simulationTasksQueue() {
        return new Queue(QUEUE_SIMULATION_TASKS, true);
    }

    @Bean
    public Queue simulationStatusUpdatesQueue() {
        return new Queue(QUEUE_SIMULATION_STATUS_UPDATES, true);
    }

    @Bean
    public Queue controlMessagesQueue() {
        return new Queue(QUEUE_CONTROL_MESSAGES, true);
    }

    @Bean
    public Binding statusBinding(Queue simulationStatusUpdatesQueue, TopicExchange exchange) {
        return BindingBuilder.bind(simulationStatusUpdatesQueue).to(exchange).with(ROUTING_KEY_STATUS_UPDATE);
    }

    @Bean
    public Binding taskBinding(Queue simulationTasksQueue, TopicExchange exchange) {
        return BindingBuilder.bind(simulationTasksQueue).to(exchange).with(ROUTING_KEY_SIMULATION_TASKS);
    }

    @Bean
    public Binding controlBinding(Queue controlMessagesQueue, TopicExchange exchange) {
        return BindingBuilder.bind(controlMessagesQueue).to(exchange).with(ROUTING_KEY_CONTROL_MESSAGES);
    }

    @Bean
    public Jackson2JsonMessageConverter producerJackson2MessageConverter() {
        return new Jackson2JsonMessageConverter();
    }

    @Bean
    public RabbitTemplate rabbitTemplate(final ConnectionFactory connectionFactory) {
        final RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
        rabbitTemplate.setMessageConverter(producerJackson2MessageConverter());
        return rabbitTemplate;
    }
}

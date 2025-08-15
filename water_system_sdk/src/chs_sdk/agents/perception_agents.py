import pandas as pd
from .base_agent import BaseAgent
from .message import Message


class FileAdapterAgent(BaseAgent):
    """
    An agent that reads data from a CSV file and publishes it to the message bus
    at each time step. Conforms to the new AgentKernel architecture.
    """
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.filepath = self.config.get("filepath")
        self.topic_template = self.config.get("topic_template")
        self.payload_columns = self.config.get("payload_columns", [])
        self.rename_map = self.config.get("rename_map", {})

        if not self.filepath or not self.topic_template:
            raise ValueError("FileAdapterAgent requires 'filepath' and 'topic_template' in config.")

        try:
            self.data = pd.read_csv(self.filepath)
        except FileNotFoundError:
            print(f"Error: Data file not found at {self.filepath}")
            self.data = pd.DataFrame()

        self.current_index = 0

    def setup(self):
        """
        No specific setup required for this agent.
        """
        print(f"FileAdapterAgent '{self.agent_id}' initialized. Reading from {self.filepath}")

    def execute(self, current_time: float):
        """
        Publishes the next row from the CSV file if the simulation time corresponds.
        This simplified version assumes one row per time step.
        """
        if self.current_index < len(self.data):
            row = self.data.iloc[self.current_index]

            payload = {}
            # Construct payload from specified columns
            for col_name in self.payload_columns:
                if col_name in self.data.columns:
                    # Rename the key in the payload if a map is provided
                    payload_key = self.rename_map.get(col_name, col_name)
                    # Ensure value is a native Python type for serialization
                    payload[payload_key] = row[col_name].item()

            if payload:
                # The topic is static in this implementation, based on the template.
                self._publish(self.topic_template, payload)

            self.current_index += 1

    def on_message(self, message: Message):
        """
        This agent does not subscribe to any topics.
        """
        pass


class SCADAAgent(BaseAgent):
    """
    An agent that connects to a real SCADA system to fetch live data.
    This is a placeholder for future implementation.
    """
    def __init__(self, agent_id, message_bus, scada_host, scada_port, tag_map):
        super().__init__(agent_id, message_bus)
        self.scada_host = scada_host
        self.scada_port = scada_port
        self.tag_map = tag_map  # e.g., {"scada_tag_1": "topic_1", "scada_tag_2": "topic_2"}
        self.connection = None # Placeholder for the SCADA connection

    def connect(self):
        """
        Establishes a connection to the SCADA system.
        """
        print(f"Connecting to SCADA at {self.scada_host}:{self.scada_port}...")
        # Implementation-specific connection logic would go here.
        self.connection = "dummy_connection" # Simulate a successful connection
        print("Connected to SCADA.")


    def execute(self, dt=1.0):
        """
        Fetches data from the SCADA system and publishes it.
        """
        if not self.connection:
            self.connect()

        for scada_tag, topic in self.tag_map.items():
            # Implementation-specific logic to read a tag from SCADA
            value = self._read_scada_tag(scada_tag)
            if value is not None:
                self.publish(topic, {"value": value})

    def _read_scada_tag(self, tag):
        """
        A placeholder for the actual implementation of reading a SCADA tag.
        """
        # In a real implementation, this would involve a library like snap7, cpppo, etc.
        print(f"Reading tag '{tag}' from SCADA...")
        # For demonstration, we'll return a dummy value.
        import random
        return random.uniform(20, 80)


    def on_message(self, message: Message):
        """
        This agent does not subscribe to any topics for now.
        """
        pass

import pandas as pd
from .base import BaseAgent, Message


class FileAdapterAgent(BaseAgent):
    """
    An agent that reads data from a CSV file and publishes it to the message bus.
    """
    def __init__(self, agent_id, message_bus, file_path, topic, time_column, value_column):
        super().__init__(agent_id, message_bus)
        self.file_path = file_path
        self.topic = topic
        self.time_column = time_column
        self.value_column = value_column
        self.data = pd.read_csv(file_path)
        self.current_index = 0

    def execute(self, dt=1.0):
        """
        Publishes the next value from the CSV file.
        """
        if self.current_index < len(self.data):
            row = self.data.iloc[self.current_index]
            value = row[self.value_column]
            self.publish(self.topic, {"value": value})
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

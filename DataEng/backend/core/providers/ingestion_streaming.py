"""
Apache Kafka ingestion provider
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class KafkaGenerator(ComponentGenerator):
    """Generator for Apache Kafka streaming platform."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Kafka consumer/producer scripts."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign ports
        self.context.get_service_port("kafka", 9092)
        self.context.get_service_port("kafka-ui", 8080)
        
        # Create kafka scripts directory
        kafka_dir = os.path.join(output_dir, "kafka")
        os.makedirs(kafka_dir, exist_ok=True)
        
        try:
            # Create example producer
            producer_script = """
import json
from kafka import KafkaProducer
from datetime import datetime
import time

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_event(topic, data):
    \"\"\"Send an event to Kafka topic.\"\"\"
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    
    future = producer.send(topic, value=event)
    future.get(timeout=10)  # Wait for confirmation
    print(f"Sent event to {topic}: {event}")

if __name__ == "__main__":
    # Example: Send events
    for i in range(10):
        send_event('raw_events', {'event_id': i, 'value': i * 10})
        time.sleep(1)
    
    producer.close()
"""
            
            with open(os.path.join(kafka_dir, "producer.py"), 'w') as f:
                f.write(producer_script)
            
            # Create example consumer
            consumer_script = """
import json
from kafka import KafkaConsumer

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'raw_events',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='analytics-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("Consumer started. Waiting for messages...")

for message in consumer:
    event = message.value
    print(f"Received event: {event}")
    
    # Process event here
    # Example: Store in database, transform data, etc.
"""
            
            with open(os.path.join(kafka_dir, "consumer.py"), 'w') as f:
                f.write(consumer_script)
                
        except Exception as e:
            print(f"Error generating Kafka scripts: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker services for Kafka ecosystem."""
        if not self.context:
            return {}
        
        kafka_port = self.context.get_service_port("kafka", 9092)
        ui_port = self.context.get_service_port("kafka-ui", 8080)
        
        return {
            "zookeeper": {
                "image": "confluentinc/cp-zookeeper:7.5.0",
                "environment": {
                    "ZOOKEEPER_CLIENT_PORT": "2181",
                    "ZOOKEEPER_TICK_TIME": "2000"
                },
                "volumes": ["zookeeper_data:/var/lib/zookeeper/data"]
            },
            "kafka": {
                "image": "confluentinc/cp-kafka:7.5.0",
                "ports": [f"{kafka_port}:9092"],
                "environment": {
                    "KAFKA_BROKER_ID": "1",
                    "KAFKA_ZOOKEEPER_CONNECT": "zookeeper:2181",
                    "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:{kafka_port}",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                    "KAFKA_AUTO_CREATE_TOPICS_ENABLE": "true"
                },
                "volumes": ["kafka_data:/var/lib/kafka/data"],
                "depends_on": ["zookeeper"]
            },
            "kafka-ui": {
                "image": "provectuslabs/kafka-ui:latest",
                "ports": [f"{ui_port}:8080"],
                "environment": {
                    "KAFKA_CLUSTERS_0_NAME": "local",
                    "KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS": "kafka:29092"
                },
                "depends_on": ["kafka"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Kafka."""
        if not self.context:
            return {}
        
        kafka_port = self.context.get_service_port("kafka", 9092)
        
        return {
            "KAFKA_BOOTSTRAP_SERVERS": f"localhost:{kafka_port}",
            "KAFKA_TOPIC": "raw_events",
            "KAFKA_GROUP_ID": "analytics-group"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {
            "zookeeper_data": None,
            "kafka_data": None
        }


# Register provider
ProviderRegistry.register("ingestion", "Kafka", KafkaGenerator)

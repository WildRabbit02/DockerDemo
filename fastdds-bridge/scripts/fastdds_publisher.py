#!/usr/bin/env python3
"""
FastDDS Publisher Example

Simple publisher that sends messages via FastDDS.
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fastdds_publisher')

try:
    import fastdds
except ImportError:
    logger.error("fastdds module not available. Please install FastDDS Python bindings.")
    sys.exit(1)


class FastDDSPublisher:
    """Simple FastDDS publisher example."""
    
    def __init__(self, topic_name="example_topic", domain_id=0):
        self.topic_name = topic_name
        self.domain_id = domain_id
        self.initialized = False
        
        self._init_fastdds()
    
    def _init_fastdds(self):
        """Initialize FastDDS components."""
        try:
            logger.info(f"Initializing FastDDS on domain {self.domain_id}...")
            
            # Create Domain Participant
            self.factory = fastdds.DomainParticipantFactory.get_instance()
            self.participant = self.factory.create_participant(
                self.domain_id, fastdds.PARTICIPANT_QOS_DEFAULT)
            
            if self.participant is None:
                raise RuntimeError("Failed to create Domain Participant")
            
            # Register String type
            self.string_type = fastdds.TypeSupport(fastdds.StringType())
            self.string_type.register_type(self.participant)
            
            # Create Topic
            self.topic = self.participant.create_topic(
                self.topic_name,
                self.string_type.get_name(),
                fastdds.TOPIC_QOS_DEFAULT)
            
            if self.topic is None:
                raise RuntimeError("Failed to create Topic")
            
            # Create Publisher
            self.publisher = self.participant.create_publisher(
                fastdds.PUBLISHER_QOS_DEFAULT)
            
            if self.publisher is None:
                raise RuntimeError("Failed to create Publisher")
            
            # Create DataWriter
            self.writer = self.publisher.create_datawriter(
                self.topic, fastdds.DATAWRITER_QOS_DEFAULT)
            
            if self.writer is None:
                raise RuntimeError("Failed to create DataWriter")
            
            self.initialized = True
            logger.info(f"FastDDS publisher initialized successfully on topic '{self.topic_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize FastDDS: {e}")
            self.initialized = False
    
    def publish(self, message):
        """Publish a string message."""
        if not self.initialized:
            logger.error("FastDDS not initialized")
            return False
        
        try:
            data = message.encode('utf-8')
            ret = self.writer.write(data)
            
            if ret:
                logger.debug(f"Published: {message}")
                return True
            else:
                logger.error("Failed to write message")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def cleanup(self):
        """Clean up FastDDS resources."""
        try:
            if hasattr(self, 'writer') and self.writer:
                self.publisher.delete_datawriter(self.writer)
            if hasattr(self, 'publisher') and self.publisher:
                self.participant.delete_publisher(self.publisher)
            if hasattr(self, 'topic') and self.topic:
                self.participant.delete_topic(self.topic)
            if hasattr(self, 'participant') and self.participant:
                self.factory.delete_participant(self.participant)
            
            logger.info("FastDDS resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='FastDDS Publisher Example')
    parser.add_argument('--topic', '-t', default='example_topic',
                        help='Topic name (default: example_topic)')
    parser.add_argument('--domain', '-d', type=int, default=0,
                        help='Domain ID (default: 0)')
    parser.add_argument('--count', '-c', type=int, default=0,
                        help='Number of messages to send (0=infinite, default: 0)')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                        help='Interval between messages in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    publisher = FastDDSPublisher(topic_name=args.topic, domain_id=args.domain)
    
    if not publisher.initialized:
        sys.exit(1)
    
    counter = 0
    try:
        while True:
            message = f"Hello FastDDS! Message #{counter}"
            publisher.publish(message)
            counter += 1
            
            if args.count > 0 and counter >= args.count:
                break
            
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        publisher.cleanup()


if __name__ == '__main__':
    main()

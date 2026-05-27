#!/usr/bin/env python3
"""
FastDDS Subscriber Example

Simple subscriber that receives messages via FastDDS.
"""

import sys
import time
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fastdds_subscriber')

try:
    import fastdds
except ImportError:
    logger.error("fastdds module not available. Please install FastDDS Python bindings.")
    sys.exit(1)


class FastDDSSubscriber:
    """Simple FastDDS subscriber example."""
    
    def __init__(self, topic_name="example_topic", domain_id=0):
        self.topic_name = topic_name
        self.domain_id = domain_id
        self.initialized = False
        self.received_messages = []
        self.running = False
        
        self._init_fastdds()
    
    def _init_fastdds(self):
        """Initialize FastDDS components."""
        try:
            logger.info(f"Initializing FastDDS subscriber on domain {self.domain_id}...")
            
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
            
            # Create Subscriber
            self.subscriber = self.participant.create_subscriber(
                fastdds.SUBSCRIBER_QOS_DEFAULT)
            
            if self.subscriber is None:
                raise RuntimeError("Failed to create Subscriber")
            
            # Create DataReader
            self.reader = self.subscriber.create_datareader(
                self.topic, fastdds.DATAREADER_QOS_DEFAULT)
            
            if self.reader is None:
                raise RuntimeError("Failed to create DataReader")
            
            self.initialized = True
            logger.info(f"FastDDS subscriber initialized successfully on topic '{self.topic_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize FastDDS: {e}")
            self.initialized = False
    
    def _read_messages(self):
        """Read available messages from the DataReader."""
        while self.running:
            try:
                info = self.reader.take_next_sample()
                if info[0] is not None:  # sample_info
                    data = info[1]  # actual data
                    if isinstance(data, bytes):
                        message = data.decode('utf-8')
                    else:
                        message = str(data)
                    
                    self.received_messages.append(message)
                    logger.info(f"Received: {message}")
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                # No data available or other error, continue
                time.sleep(0.1)
    
    def start(self):
        """Start the subscriber in a background thread."""
        if not self.initialized:
            logger.error("FastDDS not initialized")
            return False
        
        self.running = True
        self.receive_thread = threading.Thread(target=self._read_messages, daemon=True)
        self.receive_thread.start()
        logger.info("Subscriber started")
        return True
    
    def stop(self):
        """Stop the subscriber."""
        self.running = False
        if hasattr(self, 'receive_thread'):
            self.receive_thread.join(timeout=2.0)
        logger.info("Subscriber stopped")
    
    def get_messages(self):
        """Get all received messages."""
        return self.received_messages.copy()
    
    def cleanup(self):
        """Clean up FastDDS resources."""
        self.stop()
        
        try:
            if hasattr(self, 'reader') and self.reader:
                self.subscriber.delete_datareader(self.reader)
            if hasattr(self, 'subscriber') and self.subscriber:
                self.participant.delete_subscriber(self.subscriber)
            if hasattr(self, 'topic') and self.topic:
                self.participant.delete_topic(self.topic)
            if hasattr(self, 'participant') and self.participant:
                self.factory.delete_participant(self.participant)
            
            logger.info("FastDDS resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='FastDDS Subscriber Example')
    parser.add_argument('--topic', '-t', default='example_topic',
                        help='Topic name (default: example_topic)')
    parser.add_argument('--domain', '-d', type=int, default=0,
                        help='Domain ID (default: 0)')
    parser.add_argument('--duration', '-D', type=float, default=0,
                        help='Duration to run in seconds (0=infinite, default: 0)')
    
    args = parser.parse_args()
    
    subscriber = FastDDSSubscriber(topic_name=args.topic, domain_id=args.domain)
    
    if not subscriber.initialized:
        sys.exit(1)
    
    subscriber.start()
    
    try:
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            # Run indefinitely
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        subscriber.cleanup()
        logger.info(f"Total messages received: {len(subscriber.get_messages())}")


if __name__ == '__main__':
    main()

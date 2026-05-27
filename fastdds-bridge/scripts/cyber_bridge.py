#!/usr/bin/env python3
"""
CyberRT to FastDDS Bridge

This script demonstrates bridging CyberRT channels to FastDDS data writers.
Note: Full CyberRT integration requires CyberRT to be installed separately.
This is a template that shows the bridge architecture.
"""

import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cyber_fastdds_bridge')

try:
    # Try to import fastdds
    import fastdds
    FASTDDS_AVAILABLE = True
    logger.info("FastDDS Python module available")
except ImportError:
    FASTDDS_AVAILABLE = False
    logger.warning("fastdds Python module not available")

try:
    # Try to import cyber (optional - may not be installed)
    from cyber import cyber
    from cyber.node import Node
    CYBER_AVAILABLE = True
    logger.info("CyberRT Python module available")
except ImportError:
    CYBER_AVAILABLE = False
    logger.warning("CyberRT not available - running in standalone mode")


class CyberFastDDSBridge:
    """Bridge between CyberRT channels and FastDDS topics."""
    
    def __init__(self):
        self.fastdds_initialized = False
        self.cyber_initialized = False
        
        if FASTDDS_AVAILABLE:
            self.init_fastdds()
        
        if CYBER_AVAILABLE and FASTDDS_AVAILABLE:
            self.init_cyber()
    
    def init_fastdds(self):
        """Initialize FastDDS domain participant and publishers."""
        try:
            logger.info("Initializing FastDDS...")
            
            # Create Domain Participant
            self.domain_participant_factory = fastdds.DomainParticipantFactory.get_instance()
            self.domain_id = 0
            self.participant = self.domain_participant_factory.create_participant(
                self.domain_id, fastdds.PARTICIPANT_QOS_DEFAULT)
            
            # Create Topic for string messages
            self.string_type = fastdds.TypeSupport(fastdds.StringType())
            self.string_topic = self.participant.create_topic(
                "cyber_bridge_string",
                self.string_type.get_name(),
                fastdds.TOPIC_QOS_DEFAULT)
            
            # Create Publisher
            self.publisher = self.participant.create_publisher(
                fastdds.PUBLISHER_QOS_DEFAULT)
            
            # Create DataWriter
            self.writer = self.publisher.create_datawriter(
                self.string_topic, fastdds.DATAWRITER_QOS_DEFAULT)
            
            self.fastdds_initialized = True
            logger.info("FastDDS initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize FastDDS: {e}")
            self.fastdds_initialized = False
    
    def init_cyber(self):
        """Initialize CyberRT node and subscribers."""
        try:
            logger.info("Initializing CyberRT...")
            cyber.init()
            
            self.cyber_node = Node('cyber_fastdds_bridge')
            
            # Create reader for CyberRT channel
            # Note: This is a template - actual implementation depends on message types
            self.reader = self.cyber_node.create_reader(
                "/cyber/channel/string",
                self.cyber_message_callback
            )
            
            self.cyber_initialized = True
            logger.info("CyberRT initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CyberRT: {e}")
            self.cyber_initialized = False
    
    def cyber_message_callback(self, msg):
        """Callback for incoming CyberRT messages."""
        logger.info(f"Received CyberRT message: {msg}")
        
        if self.fastdds_initialized and hasattr(self, 'writer'):
            try:
                # Publish to FastDDS
                data = str(msg).encode('utf-8')
                ret = self.writer.write(data)
                if ret:
                    logger.debug("Published to FastDDS")
            except Exception as e:
                logger.error(f"Failed to publish to FastDDS: {e}")
    
    def publish_to_fastdds(self, message):
        """Publish a message directly to FastDDS."""
        if not self.fastdds_initialized:
            logger.error("FastDDS not initialized")
            return False
        
        try:
            data = message.encode('utf-8')
            ret = self.writer.write(data)
            if ret:
                logger.info(f"Published: {message}")
                return True
            else:
                logger.error("Failed to write to FastDDS")
                return False
        except Exception as e:
            logger.error(f"Error publishing to FastDDS: {e}")
            return False
    
    def run_standalone_demo(self):
        """Run a demonstration without CyberRT."""
        logger.info("Running standalone demo mode...")
        counter = 0
        
        while True:
            msg = f"CyberRT bridge message #{counter}"
            self.publish_to_fastdds(msg)
            counter += 1
            time.sleep(1.0)
    
    def shutdown(self):
        """Clean up resources."""
        try:
            if self.fastdds_initialized and hasattr(self, 'participant'):
                self.participant.delete_contained_entities()
                self.domain_participant_factory.delete_participant(self.participant)
                logger.info("FastDDS resources cleaned up")
            
            if self.cyber_initialized:
                cyber.shutdown()
                logger.info("CyberRT shutdown")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    logger.info("Starting CyberRT to FastDDS Bridge")
    logger.info(f"FastDDS available: {FASTDDS_AVAILABLE}")
    logger.info(f"CyberRT available: {CYBER_AVAILABLE}")
    
    bridge = CyberFastDDSBridge()
    
    try:
        if CYBER_AVAILABLE and bridge.cyber_initialized:
            logger.info("Running with CyberRT integration")
            # In full implementation, this would spin the CyberRT node
            bridge.cyber_node.spin()
        else:
            logger.info("Running in standalone demo mode (CyberRT not available)")
            bridge.run_standalone_demo()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        bridge.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ROS2 to FastDDS Bridge

This script demonstrates bridging ROS2 topics to FastDDS data writers.
It subscribes to ROS2 topics and publishes the data via FastDDS.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Int32
import sys

try:
    # Try to import fastdds (if available in Python)
    import fastdds
    FASTDDS_AVAILABLE = True
except ImportError:
    FASTDDS_AVAILABLE = False
    print("Warning: fastdds Python module not available. Running in ROS2-only mode.")


class ROS2FastDDSBridge(Node):
    """Bridge node that forwards ROS2 messages to FastDDS."""
    
    def __init__(self):
        super().__init__('ros2_fastdds_bridge')
        
        self.get_logger().info("Initializing ROS2 to FastDDS bridge...")
        
        # ROS2 subscribers
        self.string_sub = self.create_subscription(
            String,
            'ros2_string_topic',
            self.string_callback,
            10
        )
        
        self.float_sub = self.create_subscription(
            Float32,
            'ros2_float_topic',
            self.float_callback,
            10
        )
        
        self.int_sub = self.create_subscription(
            Int32,
            'ros2_int_topic',
            self.int_callback,
            10
        )
        
        if FASTDDS_AVAILABLE:
            self.setup_fastdds()
        else:
            self.get_logger().warn("FastDDS not available - only logging messages")
    
    def setup_fastdds(self):
        """Initialize FastDDS domain participant and publishers."""
        try:
            # Create Domain Participant
            self.domain_participant_factory = fastdds.DomainParticipantFactory.get_instance()
            self.domain_id = 0
            self.participant = self.domain_participant_factory.create_participant(
                self.domain_id, fastdds.PARTICIPANT_QOS_DEFAULT)
            
            # Create Topic
            self.topic_type = fastdds.TypeSupport(
                fastdds.StringType())
            self.topic = self.participant.create_topic(
                "fastdds_string_topic", 
                self.topic_type.get_name(),
                fastdds.TOPIC_QOS_DEFAULT)
            
            # Create Publisher
            self.publisher = self.participant.create_publisher(
                fastdds.PUBLISHER_QOS_DEFAULT)
            
            # Create DataWriter
            self.writer = self.publisher.create_datawriter(
                self.topic, fastdds.DATAWRITER_QOS_DEFAULT)
            
            self.get_logger().info("FastDDS initialized successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize FastDDS: {e}")
    
    def string_callback(self, msg):
        """Handle incoming ROS2 string messages."""
        self.get_logger().info(f"Received ROS2 string: {msg.data}")
        
        if FASTDDS_AVAILABLE and hasattr(self, 'writer'):
            try:
                # Publish via FastDDS
                data = msg.data.encode('utf-8')
                ret = self.writer.write(data)
                if ret:
                    self.get_logger().debug("Published to FastDDS")
            except Exception as e:
                self.get_logger().error(f"Failed to publish to FastDDS: {e}")
    
    def float_callback(self, msg):
        """Handle incoming ROS2 float messages."""
        self.get_logger().info(f"Received ROS2 float: {msg.data}")
    
    def int_callback(self, msg):
        """Handle incoming ROS2 int messages."""
        self.get_logger().info(f"Received ROS2 int: {msg.data}")
    
    def destroy(self):
        """Clean up resources."""
        if FASTDDS_AVAILABLE and hasattr(self, 'participant'):
            try:
                self.participant.delete_contained_entities()
                self.domain_participant_factory.delete_participant(self.participant)
            except:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    bridge = ROS2FastDDSBridge()
    
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.destroy()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

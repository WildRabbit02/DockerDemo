# FastDDS Bridge - Docker Project

A complete Docker-based environment for FastDDS (eProsima Fast DDS) with monitoring capabilities and bridges for ROS, ROS2, and CyberRT communication.

## Project Structure

```
fastdds-bridge/
├── Dockerfile              # Main Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── docker-compose.yml.example  # Example docker run commands
├── README.md               # Documentation
├── scripts/
│   ├── entrypoint.sh       # Container entrypoint script
│   ├── ros2_bridge.py      # ROS2 to FastDDS bridge
│   ├── cyber_bridge.py     # CyberRT to FastDDS bridge
│   ├── fastdds_publisher.py    # FastDDS publisher example
│   └── fastdds_subscriber.py   # FastDDS subscriber example
└── config/
    └── qos_profiles.xml    # Default QoS profiles configuration
```

## Features

### Core Components
- **FastDDS v2.14.0**: High-performance DDS middleware implementation
- **FastDDS Monitor v1.3.0**: GUI tool for visualizing DDS network traffic
- **FastDDS-Gen v2.5.0**: IDL code generator for custom data types
- **ROS2 Humble**: Full ROS2 installation with FastDDS RMW support

### Bridge Services
- **ROS2 ↔ FastDDS Bridge**: Bidirectional communication between ROS2 topics and FastDDS
- **CyberRT ↔ FastDDS Bridge**: Template for integrating with Baidu's CyberRT framework
- **Python Examples**: Ready-to-use publisher/subscriber examples

### Performance Features
- Shared memory transport for high-performance local communication
- Configurable QoS profiles for different use cases
- UDPv4 and shared memory transport support
- Statistics collection enabled for monitoring

## Quick Start

### Build the Image

```bash
cd fastdds-bridge
docker build -t fastdds-bridge:latest .
```

**Note**: Building may take 15-30 minutes depending on your system as it compiles FastDDS from source.

### Run with Docker

#### Basic Interactive Shell
```bash
docker run -it --rm fastdds-bridge:latest bash
```

#### With Shared Memory Support (Recommended)
```bash
docker run -it --rm --device /dev/shm fastdds-bridge:latest bash
```

#### Run FastDDS Monitor (GUI)
```bash
# On Linux with X11
docker run -it --rm \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    --device /dev/shm \
    fastdds-bridge:latest fastddsgui
```

### Run with Docker Compose

#### Start Publisher and Subscriber
```bash
docker-compose up -d publisher subscriber
```

#### View Logs
```bash
docker-compose logs -f
```

#### Start FastDDS Monitor (requires X11)
```bash
docker-compose --profile gui up monitor
```

#### Stop All Services
```bash
docker-compose down
```

## Usage Examples

### Run FastDDS Publisher
```bash
docker run -it --rm --network host fastdds-bridge:latest \
    python3 /opt/bridges/fastdds_publisher.py \
    --topic my_topic \
    --interval 0.5
```

### Run FastDDS Subscriber
```bash
docker run -it --rm --network host fastdds-bridge:latest \
    python3 /opt/bridges/fastdds_subscriber.py \
    --topic my_topic
```

### Run ROS2 to FastDDS Bridge
```bash
docker run -it --rm --network host fastdds-bridge:latest \
    python3 /opt/bridges/ros2_bridge.py
```

In another terminal, publish a ROS2 message:
```bash
docker exec -it <container_id> bash
source /opt/ros/humble/setup.bash
ros2 topic pub /ros2_string_topic std_msgs/String "data: 'Hello FastDDS!'"
```

### Use Custom QoS Profiles
```bash
docker run -it --rm \
    -v ./my_qos_profiles.xml:/etc/fastdds/qos_profiles.xml \
    fastdds-bridge:latest bash
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTDDS_DEFAULT_PROFILES_FILE` | Path to QoS profiles XML | `/etc/fastdds/qos_profiles.xml` |
| `RMW_IMPLEMENTATION` | ROS2 RMW implementation | `rmw_fastrtps_cpp` |
| `DISPLAY` | X11 display for GUI | - |

### QoS Profiles

The default QoS profiles are configured in `config/qos_profiles.xml`. Key profiles include:

- `default_participant`: Standard participant configuration
- `local_high_performance`: Optimized for local communication
- `default_publisher`/`default_subscriber`: Reliable communication
- `best_effort_publisher`: For high-frequency, loss-tolerant data
- `transient_local_subscriber`: For late-joining subscribers

## Network Configuration

### Single Host Communication
Containers on the same host can communicate using:
- Same Docker network: `--network dds-network`
- Host network: `--network host`

### Multi-Host Communication
For multi-host setups:
1. Ensure UDP multicast is enabled on your network
2. Configure the discovery server or use static peer lists
3. Update QoS profiles with appropriate locator addresses

Example QoS configuration for specific peers:
```xml
<initialPeersList>
    <locator>
        <udpv4>
            <address>192.168.1.100</address>
            <port>7400</port>
        </udpv4>
    </locator>
</initialPeersList>
```

## Integration Guides

### ROS2 Integration

1. The container includes ROS2 Humble with FastDDS RMW
2. Set `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` (already set by default)
3. Use standard ROS2 tools: `ros2 topic`, `ros2 node`, etc.
4. Bridge script forwards ROS2 topics to FastDDS

### CyberRT Integration

**Note**: Full CyberRT integration requires separate CyberRT installation due to its complexity.

The included `cyber_bridge.py` provides:
- Template architecture for CyberRT ↔ FastDDS bridging
- Standalone demo mode for testing FastDDS functionality
- Extension points for custom message types

To add full CyberRT support:
1. Install CyberRT in a multi-stage build
2. Add CyberRT Python bindings
3. Extend `cyber_bridge.py` with actual channel readers/writers

### FastDDS Monitor

The FastDDS Monitor provides:
- Real-time visualization of DDS participants
- Topic and data type inspection
- Statistics and performance metrics
- Network topology graph

Requirements for GUI:
- X11 forwarding (`-e DISPLAY -v /tmp/.X11-unix`)
- Or use VNC/RDP for remote access

## Troubleshooting

### FastDDS Monitor Not Starting
```bash
# Check X11 permissions
xhost +local:docker

# Verify DISPLAY variable
echo $DISPLAY

# Test with simple X11 app
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix fastdds-bridge:latest xclock
```

### No Discovery Between Containers
```bash
# Ensure containers are on the same network
docker network create dds-network
docker run --network dds-network ...

# Check multicast is working
docker run --network host fastdds-bridge:latest ping 239.255.0.1

# Verify FASTDDS_DEFAULT_PROFILES_FILE is consistent
echo $FASTDDS_DEFAULT_PROFILES_FILE
```

### Shared Memory Issues
```bash
# Increase shared memory size
docker run --shm-size=512m ...

# Or use device mapping
docker run --device /dev/shm ...
```

## Performance Tips

1. **Use Shared Memory**: Always mount `/dev/shm` for local communication
2. **Choose Appropriate QoS**: Use BEST_EFFORT for high-frequency sensor data
3. **Batch Messages**: Combine small messages when possible
4. **Monitor Statistics**: Use FastDDS Monitor to identify bottlenecks
5. **Tune History Depth**: Adjust based on your latency requirements

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## References

- [FastDDS Documentation](https://fast-dds.docs.eprosima.com/)
- [FastDDS GitHub](https://github.com/eProsima/Fast-DDS)
- [ROS2 Documentation](https://docs.ros.org/)
- [CyberRT Documentation](https://apollo.auto/cyberrt/)

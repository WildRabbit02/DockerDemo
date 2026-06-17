# FastDDS Bridge Docker Image

Complete bridge solution for ROS1, ROS2, and CyberRT communication using FastDDS as the underlying middleware with visualization monitoring capabilities.

## Features

- **Multi-Framework Support**: ROS1 Noetic, ROS2 Humble, CyberRT integration
- **FastDDS Core**: eProsima Fast DDS v2.14+ as the communication backbone
- **FastDDS Monitor**: GUI tool for real-time DDS network visualization
- **Bidirectional Bridges**: Seamless message forwarding between frameworks
- **Performance Optimized**: Shared memory transport for low-latency local communication
- **Pre-built CyberRT**: Uses pre-compiled .deb package (no slow Bazel build)
- **Comprehensive Testing**: Automated test suites for validation

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   ROS1      │     │   ROS2       │     │   CyberRT   │
│  Noetic     │     │  Humble      │     │  (Apollo)   │
└──────┬──────┘     └──────┬───────┘     └──────┬──────┘
       │                   │                    │
       └───────────────────┼────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   FastDDS Core  │
                  │   (DDS Router)  │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ FastDDS Monitor │
                  │  (Visualization)│
                  └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 10GB+ free disk space
- Pre-downloaded CyberRT deb package: `ecdds-ubuntu20.04_1.0.0-alpha10_amd64.deb`

### Build the image

```bash
# Clone or navigate to the project directory
cd /workspace/fastdds-bridge

# Copy your CyberRT deb package
cp /path/to/ecdds-ubuntu20.04_1.0.0-alpha10_amd64.deb ./deps/

# Build the Docker image
docker build -t fastdds-bridge:latest .
```

### Run the container

```bash
# Basic run with host networking (required for DDS discovery)
docker run -it --rm --network host fastdds-bridge:latest bash

# With shared memory support
docker run -it --rm --network host --device /dev/shm fastdds-bridge:latest bash

# Run with GUI support for FastDDS Monitor
xhost +local:docker
docker run -it --rm --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  fastdds-bridge:latest bash
```

### Using Docker Compose

```bash
# Start all services including monitor
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Testing & Validation

### Quick Test Suite

Run the comprehensive test suite to validate all components:

```bash
# Inside the container
cd /workspace/fastdds-bridge/scripts
chmod +x run_tests.sh
./run_tests.sh
```

This runs 8 automated tests:
1. Environment checks (ROS1/ROS2/CyberRT/FastDDS)
2. ROS1 internal communication
3. ROS2 internal communication  
4. FastDDS service discovery
5. Bridge service startup
6. Cross-framework communication (ROS1↔ROS2)
7. CyberRT integration (if available)
8. FastDDS Monitor configuration

### End-to-End Integration Test

For full integration testing:

```bash
# Inside the container
chmod +x e2e_test.sh
./e2e_test.sh
```

This performs:
- Bidirectional ROS1↔ROS2 message forwarding
- High-frequency stress testing (100 messages)
- Multiple message type validation (String, Int32, Float64)
- CyberRT channel verification
- FastDDS participant discovery

### Performance Benchmarking

Test latency and throughput:

```bash
# Latency and throughput test
python3 performance_test.py --mode all --duration 30 --rate 100

# Generate detailed report
python3 performance_test.py --report
```

### Manual Verification Steps

See [QUICK_START_TEST.md](QUICK_START_TEST.md) for detailed manual testing procedures.

## Usage Examples

### Start the Bridge Service

```bash
# Inside container
cd /workspace/fastdds-bridge/scripts
python3 bridge_node.py
```

### ROS1 to ROS2 Communication

**Terminal 1 (ROS1 Publisher):**
```bash
source /opt/ros/noetic/setup.bash
rostopic pub -r 10 /bridge_topic std_msgs/String "data: 'Hello from ROS1'"
```

**Terminal 2 (ROS2 Subscriber):**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /bridge_topic
```

### ROS2 to CyberRT Communication

**Terminal 1 (ROS2 Publisher):**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub -r 10 /cyber_bridge std_msgs/msg/String "{data: 'To CyberRT'}"
```

**Terminal 2 (CyberRT Subscriber):**
```bash
source /apollo/cyber/setup.bash
# Your CyberRT node subscribing to /cyber_bridge
```

### FastDDS Monitor Visualization

**Method 1: GUI Application**
```bash
# Requires X11 forwarding
fastddsgui
```

**Method 2: CLI Discovery Tool**
```bash
# List all DDS participants
fastdds discovery

# Export discovery information
fastdds discovery -i > discovery.xml
```

**Method 3: Web-based Monitor**
```bash
# Start via docker-compose
docker-compose up -d monitor

# Access in browser at http://localhost:8080
```

## Configuration

### QoS Profiles

Edit `config/qos_profiles.xml` to customize Quality of Service settings:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>custom_udp_transport</transport_id>
            <type>UDPv4</type>
        </transport_descriptor>
    </transport_descriptors>
    
    <participant profile_name="bridge_participant" is_default_profile="true">
        <rtps>
            <useBuiltinTransports>false</useBuiltinTransports>
            <userTransports>
                <transport_id>custom_udp_transport</transport_id>
            </userTransports>
            <domainId>0</domainId>
        </rtps>
    </participant>
</profiles>
```

### Bridge Configuration

Configure topic mappings in `scripts/bridge_config.yaml`:

```yaml
topics:
  - ros1_name: "/sensor_data"
    ros2_name: "/sensor_data"
    cyber_name: "/apollo/sensor"
    type: "std_msgs/String"
    direction: "bidirectional"
    
  - ros1_name: "/control_cmd"
    ros2_name: "/control/command"
    cyber_name: "/control"
    type: "geometry_msgs/Twist"
    direction: "ros2_to_others"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RMW_IMPLEMENTATION` | ROS2 RMW implementation | `rmw_fastrtps_cpp` |
| `FASTRTPS_DEFAULT_PROFILES_FILE` | Path to QoS profiles XML | `/workspace/fastdds-bridge/config/qos_profiles.xml` |
| `CYBER_DOMAIN_ID` | CyberRT domain ID | `0` |
| `ROS_DOMAIN_ID` | ROS/ROS2 domain ID | `0` |

## Network Configuration

### Host Network Mode (Recommended)

For optimal DDS discovery and performance:

```bash
docker run -it --rm --network host fastdds-bridge:latest
```

### Custom Docker Network

For isolated testing:

```bash
docker network create --driver bridge dds-network
docker run -it --rm --network dds-network fastdds-bridge:latest
```

**Note:** UDP multicast must be enabled for DDS discovery to work across containers.

## Troubleshooting

### Common Issues

**1. ROS1 and ROS2 cannot communicate**
- Verify `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`
- Check DDS Domain ID consistency
- Ensure host network mode is used
- Confirm firewall allows UDP multicast

**Debug commands:**
```bash
fastdds discovery
ros2 doctor --report
tail -f /tmp/bridge.log
```

**2. CyberRT nodes not discovered**
- Source CyberRT environment: `source /apollo/cyber/setup.bash`
- Verify channel naming conventions
- Check bridge configuration mappings

**3. FastDDS Monitor won't connect**
- Confirm QoS profile file path
- Verify Domain ID matches
- Check network ports are not blocked

### Log Files

- Bridge logs: `/tmp/bridge.log`
- Test logs: `/tmp/e2e_*.log`
- ROS1 logs: `/tmp/roscore.log`
- FastDDS discovery: `/tmp/fastdds_discovery.log`

## Project Structure

```
fastdds-bridge/
├── Dockerfile                 # Main Docker build file
├── docker-compose.yml         # Service orchestration
├── config/
│   └── qos_profiles.xml      # QoS configuration
├── scripts/
│   ├── bridge_node.py        # Main bridge service
│   ├── entrypoint.sh         # Container entry point
│   ├── run_tests.sh          # Automated test suite
│   ├── e2e_test.sh           # End-to-end tests
│   └── performance_test.py   # Performance benchmarks
├── deps/                      # External dependencies (CyberRT deb)
├── README.md                  # This file
├── QUICK_START_TEST.md       # Detailed testing guide
├── BUILD.md                   # Build instructions
└── PROJECT_README.md         # Project overview
```

## Performance Expectations

Based on typical deployments:

| Metric | Local (shm) | Network (UDP) |
|--------|-------------|---------------|
| Latency (avg) | < 1ms | 2-5ms |
| Throughput | > 10K msg/s | > 5K msg/s |
| Message loss | < 0.01% | < 0.1% |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run test suite: `./scripts/run_tests.sh`
4. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [eProsima Fast DDS](https://github.com/eProsima/Fast-DDS)
- [ROS/ROS2](https://www.ros.org/)
- [Apollo CyberRT](https://github.com/ApolloAuto/apollo)

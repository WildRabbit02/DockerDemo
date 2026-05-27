# FastDDS Bridge Docker Image

This Docker image provides a complete FastDDS environment with:
- **FastDDS** (eProsima Fast DDS) - High-performance DDS middleware
- **FastDDS Monitor** - GUI tool for monitoring DDS networks
- **ROS/ROS2 Bridge** - Integration with ROS and ROS2 ecosystems
- **CyberRT Bridge** - Integration with Baidu's CyberRT framework

## Features

- Based on Ubuntu 22.04 LTS
- Pre-configured FastDDS installation
- FastDDS Monitor for network visualization
- Sample bridge services for ROS, ROS2, and CyberRT communication
- Shared memory transport support for high-performance local communication

## Quick Start

### Build the image
```bash
docker build -t fastdds-bridge:latest .
```

### Run the container
```bash
# Basic run
docker run -it --rm fastdds-bridge:latest bash

# With shared memory support (recommended for performance)
docker run -it --rm --device /dev/shm fastdds-bridge:latest bash

# Run FastDDS Monitor (requires X11 forwarding)
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix fastdds-bridge:latest fastddsgui
```

## Usage Examples

### Start FastDDS Monitor
```bash
fastddsgui
```

### Run sample bridge services
```bash
# ROS2 to FastDDS bridge
ros2_bridge_node

# CyberRT to FastDDS bridge
cyber_bridge_node
```

## Environment Variables

- `FASTDDS_DEFAULT_PROFILES_FILE`: Path to custom QoS profiles XML
- `RMW_IMPLEMENTATION`: Set to `rmw_fastrtps_cpp` for ROS2 integration

## Network Configuration

For multi-container communication, ensure all containers use the same Docker network:
```bash
docker network create dds-network
docker run -it --rm --network dds-network fastdds-bridge:latest
```

## License

MIT License

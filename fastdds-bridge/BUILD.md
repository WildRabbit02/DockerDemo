# Build instructions for FastDDS Bridge Docker Image

## Prerequisites

- Docker 20.10 or later
- At least 8GB RAM available for the build process
- At least 20GB free disk space
- Stable internet connection (for downloading dependencies)

## Build Command

```bash
cd /workspace/fastdds-bridge
docker build -t fastdds-bridge:latest .
```

## Build Options

### With Build Cache
```bash
docker build --cache-from fastdds-bridge:latest -t fastdds-bridge:latest .
```

### With Progress Output
```bash
docker build --progress=plain -t fastdds-bridge:latest .
```

### For Specific Platform
```bash
docker build --platform linux/amd64 -t fastdds-bridge:latest .
```

## Expected Build Time

- **First build**: 20-40 minutes (depending on network and CPU)
- **Subsequent builds**: 2-5 minutes (with cache)

## Build Stages

The Dockerfile performs the following major steps:

1. **Base System Setup** (~2-3 min)
   - Ubuntu 22.04 base image
   - System dependencies installation

2. **FastDDS Core** (~10-15 min)
   - Clone FastDDS repository
   - Compile with CMake
   - Install libraries and tools

3. **FastDDS-Gen** (~3-5 min)
   - Clone and build IDL code generator

4. **FastDDS Monitor** (~5-8 min)
   - Clone and build Qt-based monitoring GUI

5. **ROS2 Integration** (~5-10 min)
   - Install ROS2 Humble desktop
   - Configure FastDDS RMW

## Troubleshooting Build Issues

### Out of Memory
```bash
# Reduce parallel compilation jobs
export MAKEFLAGS="-j2"
docker build -t fastdds-bridge:latest .
```

### Network Timeout
```bash
# Increase Docker timeout
docker build --network host -t fastdds-bridge:latest .
```

### Disk Space Issues
```bash
# Clean up Docker system
docker system prune -a

# Check available space
df -h
```

### CMake Errors
```bash
# Build with verbose output
docker build --progress=plain --no-cache -t fastdds-bridge:latest . 2>&1 | tee build.log
```

## Verify Build

After successful build, verify the image:

```bash
# Check image size (should be ~3-4GB)
docker images fastdds-bridge

# Test basic functionality
docker run --rm fastdds-bridge:latest fastddsgen --version
docker run --rm fastdds-bridge:latest ros2 --version

# Test FastDDS Python bindings
docker run --rm fastdds-bridge:latest python3 -c "import fastdds; print('FastDDS OK')"
```

## Push to Registry

```bash
# Tag for registry
docker tag fastdds-bridge:latest registry.example.com/fastdds-bridge:latest

# Push
docker push registry.example.com/fastdds-bridge:latest
```

## Alternative: Pre-built Image

If building from source is not feasible, consider:
1. Using eProsima's official FastDDS images (if available)
2. Building on a more powerful machine and exporting
3. Using a CI/CD pipeline for automated builds

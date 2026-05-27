FROM ubuntu:22.04

LABEL maintainer="FastDDS Bridge"
LABEL description="FastDDS with Monitor and bridges for ROS, ROS2, and CyberRT"

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    libssl-dev \
    libasio-dev \
    libtinyxml2-dev \
    libboost-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-filesystem-dev \
    libboost-serialization-dev \
    libboost-python-dev \
    python3 \
    python3-pip \
    python3-dev \
    qtbase5-dev \
    qtchart5-dev \
    qtmultimedia5-dev \
    libqt5svg5-dev \
    libqwt-qt5-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up Python packages
RUN pip3 install --no-cache-dir \
    pyyaml \
    numpy \
    packaging

# Create workspace directory
WORKDIR /opt/fastdds

# Install FastDDS from source
RUN git clone --depth 1 -b v2.14.0 https://github.com/eProsima/Fast-DDS.git \
    && cd Fast-DDS \
    && mkdir build && cd build \
    && cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCOMPILE_EXAMPLES=OFF \
        -DBUILD_TESTING=OFF \
        -DSECURITY=ON \
        -DFASTDDS_STATISTICS=ON \
        -DSHMEM_TRANSPORT_BUILTIN=ON \
        -DUDDP_TRANSPORT_BUILTIN=ON \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd ../.. \
    && rm -rf Fast-DDS

# Install FastDDS-Gen (code generator for IDL files)
RUN git clone --depth 1 -b v2.5.0 https://github.com/eProsima/Fast-DDS-Gen.git \
    && cd Fast-DDS-Gen \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release \
    && make -j$(nproc) \
    && make install \
    && cd ../.. \
    && rm -rf Fast-DDS-Gen

# Install FastDDS Monitor
RUN git clone --depth 1 -b v1.3.0 https://github.com/eProsima/Fast-DDS-Monitor.git \
    && cd Fast-DDS-Monitor \
    && mkdir build && cd build \
    && cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DFASTDDS_MONITOR_QT5=ON \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd ../.. \
    && rm -rf Fast-DDS-Monitor

# Install ROS2 Humble for bridge support
RUN add-apt-repository universe \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | apt-key add - \
    && echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list \
    && apt-get update \
    && apt-get install -y \
        ros-humble-desktop \
        ros-humble-rmw-fastrtps-cpp \
        ros-humble-ros2cli \
        ros-humble-ros2bridge \
    && rm -rf /var/lib/apt/lists/*

# Source ROS2 setup
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

# Create bridge workspace
WORKDIR /opt/bridges

# Create sample ROS2 to FastDDS bridge code
COPY scripts/ros2_bridge.py /opt/bridges/ros2_bridge.py
COPY scripts/cyber_bridge.py /opt/bridges/cyber_bridge.py
COPY scripts/fastdds_publisher.py /opt/bridges/fastdds_publisher.py
COPY scripts/fastdds_subscriber.py /opt/bridges/fastdds_subscriber.py

# Make scripts executable
RUN chmod +x /opt/bridges/*.py

# Create QoS profiles configuration directory
RUN mkdir -p /etc/fastdds

# Copy default QoS profiles
COPY config/qos_profiles.xml /etc/fastdds/qos_profiles.xml

# Set environment variables
ENV FASTDDS_DEFAULT_PROFILES_FILE=/etc/fastdds/qos_profiles.xml
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV PYTHONPATH=/opt/bridges:${PYTHONPATH}
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}
ENV PATH=/usr/local/bin:${PATH}

# Create entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace

# Default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

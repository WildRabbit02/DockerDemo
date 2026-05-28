# 快速验证指南

本指南提供快速验证 ROS1、ROS2、CyberRT 与 FastDDS 桥接系统功能的步骤。

## 前置条件

确保 Docker 容器已启动并进入：
```bash
docker run -it --rm --network host fastdds-bridge:latest bash
```

## 一键运行完整测试套件

```bash
cd /workspace/fastdds-bridge/scripts
chmod +x run_tests.sh
./run_tests.sh
```

该脚本将自动执行以下 8 项测试：
1. 环境检查（ROS1/ROS2/CyberRT/FastDDS）
2. ROS1 内部通信测试
3. ROS2 内部通信测试
4. FastDDS 服务发现测试
5. 桥接服务启动测试
6. 跨框架通信测试（ROS1↔ROS2）
7. CyberRT 组件测试（如已安装）
8. FastDDS Monitor 配置检查

## 手动分步验证

### 步骤 1: 验证基础环境

```bash
# 检查 ROS1
source /opt/ros/noetic/setup.bash
rosversion -d  # 应输出 "noetic"

# 检查 ROS2
source /opt/ros/humble/setup.bash
ros2 --version  # 应显示 Humble 版本信息

# 检查 FastDDS
fastdds version  # 应显示 FastDDS 版本

# 检查 RMW 实现
echo $RMW_IMPLEMENTATION  # 应输出 "rmw_fastrtps_cpp"
```

### 步骤 2: 验证 ROS1 内部通信

**终端 1:**
```bash
source /opt/ros/noetic/setup.bash
roscore
```

**终端 2:**
```bash
source /opt/ros/noetic/setup.bash
rostopic pub -r 5 /test_topic std_msgs/String "data: 'Hello ROS1'"
```

**终端 3:**
```bash
source /opt/ros/noetic/setup.bash
rostopic echo /test_topic
```

预期：终端 3 应持续收到 "Hello ROS1" 消息。

### 步骤 3: 验证 ROS2 内部通信

**终端 1:**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub -r 5 /test_topic std_msgs/msg/String "{data: 'Hello ROS2'}"
```

**终端 2:**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /test_topic
```

预期：终端 2 应持续收到 "Hello ROS2" 消息。

### 步骤 4: 验证 ROS1 ↔ ROS2 跨框架通信

**启动桥接服务:**
```bash
cd /workspace/fastdds-bridge/scripts
python3 bridge_node.py
```

**终端 1 (ROS1 发布者):**
```bash
source /opt/ros/noetic/setup.bash
rostopic pub -r 5 /bridge_test std_msgs/String "data: 'From ROS1 to ROS2'"
```

**终端 2 (ROS2 订阅者):**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /bridge_test
```

预期：ROS2 应收到来自 ROS1 的消息。

**反向测试 (ROS2 → ROS1):**

**终端 3 (ROS2 发布者):**
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub -r 5 /bridge_test_reverse std_msgs/msg/String "{data: 'From ROS2 to ROS1'}"
```

**终端 4 (ROS1 订阅者):**
```bash
source /opt/ros/noetic/setup.bash
rostopic echo /bridge_test_reverse
```

预期：ROS1 应收到来自 ROS2 的消息。

### 步骤 5: 验证 CyberRT 集成（如已安装）

```bash
# 初始化 CyberRT 环境
source /apollo/cyber/setup.bash

# 列出当前通道
cyber_channel list

# 启动 CyberRT 节点示例（如有）
cyber_launch launch/sample.launch
```

### 步骤 6: 使用 FastDDS Monitor 可视化监控

**方法 1: 在容器内启动 Monitor（需要 GUI 支持）**
```bash
# 挂载 X11 并启动
docker run -it --rm --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  fastdds-bridge:latest \
  fastdds-monitor
```

**方法 2: 导出发现信息进行离线分析**
```bash
# 导出参与者发现信息
fastdds discovery -i > discovery_info.txt

# 查看导出的信息
cat discovery_info.txt
```

**方法 3: 使用 Web 版 Monitor（推荐）**
```bash
# 在容器中启动 DDS Router 和 Web Monitor
cd /workspace/fastdds-bridge
docker-compose up -d monitor

# 在宿主机浏览器访问
# http://localhost:8080
```

### 步骤 7: 性能基准测试

```bash
# 测试消息延迟
cd /workspace/fastdds-bridge/scripts
python3 performance_test.py --mode latency --duration 30

# 测试吞吐量
python3 performance_test.py --mode throughput --duration 30

# 生成性能报告
python3 performance_test.py --report
```

## 故障排查

### 常见问题 1: ROS1 和 ROS2 无法通信

**检查点:**
- 确认 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`
- 检查 DDS Domain ID 是否一致
- 验证网络模式是否为 `--network host`
- 确认防火墙未阻止 UDP 多播

**调试命令:**
```bash
# 查看 DDS 参与者
fastdds discovery

# 检查 ROS2 发现信息
ros2 doctor --report

# 查看桥接日志
tail -f /tmp/bridge.log
```

### 常见问题 2: CyberRT 节点无法发现

**检查点:**
- 确认 CyberRT 环境变量已正确设置
- 检查 channel name 命名约定
- 验证 CyberRT 与 FastDDS 的桥接配置

### 常见问题 3: FastDDS Monitor 无法连接

**检查点:**
- 确认 QoS 配置文件路径正确
- 检查 Domain ID 匹配
- 验证网络端口未被阻止

## 测试清单

完成以下检查以确保系统完全可用：

- [ ] ROS1 内部通信正常
- [ ] ROS2 内部通信正常
- [ ] ROS1 → ROS2 跨框架通信正常
- [ ] ROS2 → ROS1 跨框架通信正常
- [ ] FastDDS 服务发现正常
- [ ] 桥接服务稳定运行
- [ ] （可选）CyberRT 集成正常
- [ ] FastDDS Monitor 可显示拓扑
- [ ] 消息延迟符合预期（<10ms 本地）
- [ ] 无消息丢失（连续发送 1000 条测试）

## 下一步

测试通过后，您可以：
1. 部署实际业务节点进行端到端验证
2. 根据实际需求调整桥接配置（修改 `bridge_config.yaml`）
3. 配置 QoS 策略以优化性能
4. 设置监控系统进行长期运行测试

详细文档请参考 `/workspace/fastdds-bridge/README.md`

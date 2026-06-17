# 测试验证说明

本目录包含完整的测试验证工具，用于验证 ROS1、ROS2、CyberRT 与 FastDDS 桥接系统的功能。

## 测试文件清单

| 文件 | 描述 | 用途 |
|------|------|------|
| `run_tests.sh` | 自动化测试套件 | 快速验证所有组件是否正常工作 |
| `e2e_test.sh` | 端到端集成测试 | 验证跨框架消息转发功能 |
| `performance_test.py` | 性能基准测试 | 测量延迟和吞吐量指标 |

## 快速开始

### 1. 运行自动化测试套件

```bash
cd /workspace/fastdds-bridge/scripts
./run_tests.sh
```

**测试内容：**
- ✓ 环境检查（ROS1/ROS2/CyberRT/FastDDS）
- ✓ ROS1 内部通信
- ✓ ROS2 内部通信
- ✓ FastDDS 服务发现
- ✓ 桥接服务启动
- ✓ ROS1↔ROS2 跨框架通信
- ✓ CyberRT 集成（如已安装）
- ✓ FastDDS Monitor 配置

**预期输出：**
```
==========================================
FastDDS Bridge 测试验证套件
==========================================

=== 测试 1: 环境检查 ===
✓ PASSED: ROS1 Noetic 环境可用
✓ PASSED: ROS2 Humble 环境可用
✓ PASSED: FastDDS CLI 工具可用
...

==========================================
测试结果汇总
==========================================
通过：8
失败：0

所有测试通过！系统已准备就绪。
```

### 2. 运行端到端集成测试

```bash
./e2e_test.sh [测试持续时间秒数]
```

**示例：**
```bash
# 使用默认 10 秒测试时长
./e2e_test.sh

# 使用 30 秒测试时长
./e2e_test.sh 30
```

**测试内容：**
- 阶段 1: 启动基础服务（roscore, 桥接服务）
- 阶段 2: ROS1↔ROS2 双向通信测试
- 阶段 3: 高频消息并发测试（100 条消息）
- 阶段 4: 不同消息类型测试（String, Int32, Float64）
- 阶段 5: CyberRT 集成测试
- 阶段 6: FastDDS 参与者发现测试

**预期输出：**
```
==========================================
端到端集成测试
==========================================
测试配置:
  测试持续时间：10 秒
  消息数量：100 条

=== 阶段 1: 启动基础服务 ===
✓ roscore 已启动
✓ 桥接服务已启动

=== 阶段 2: ROS1 ↔ ROS2 双向通信测试 ===
✓ PASSED: ROS1 → ROS2 通信
✓ PASSED: ROS2 → ROS1 通信

=== 阶段 3: 多消息并发测试 ===
✓ PASSED: 高频消息测试 (接收 98/100)

...

==========================================
端到端集成测试报告
==========================================
总测试数：7
通过：7
失败：0
成功率：100.0%

所有测试通过！系统已准备就绪。
```

### 3. 运行性能基准测试

```bash
# 完整测试（延迟 + 吞吐量）
python3 performance_test.py --mode all --duration 30 --rate 100

# 仅延迟测试
python3 performance_test.py --mode latency --duration 30

# 仅吞吐量测试
python3 performance_test.py --mode throughput --duration 30 --size 1024

# 生成详细报告
python3 performance_test.py --report
```

**预期输出：**
```
============================================================
FastDDS Bridge 性能测试
============================================================

=== 延迟测试 ===

开始 ROS1 延迟测试，持续 30 秒，频率 100 Hz
开始 ROS2 延迟测试，持续 30 秒，频率 100 Hz

ROS1 延迟统计 (ms):
  平均值：  0.823
  中位数：  0.756
  标准差：  0.234
  最小值：  0.412
  最大值：  2.341
  95 百分位： 1.234
  99 百分位： 1.876
  样本数：  3000

ROS2 延迟统计 (ms):
  平均值：  0.912
  中位数：  0.834
  标准差：  0.287
  最小值：  0.523
  最大值：  2.567
  95 百分位： 1.345
  99 百分位： 1.923
  样本数：  3000

=== 吞吐量测试 ===

ROS1 吞吐量结果:
  发送消息数：3000
  接收消息数：2998
  发送速率：100.02 msg/s
  接收速率：99.95 msg/s
  数据速率：100.02 KB/s

============================================================
性能测试报告
============================================================
测试时间：2024-01-15 10:30:45
测试模式：all
持续时间：30 秒
消息频率：100 Hz
消息大小：1024 字节

详细报告已保存到：performance_report_20240115_103045.txt
```

## 手动验证步骤

如需更详细的分步验证，请参考 [`QUICK_START_TEST.md`](../QUICK_START_TEST.md)。

## 故障排查

### 测试失败常见原因

1. **网络配置问题**
   - 确保 Docker 使用 `--network host` 模式
   - 检查防火墙是否阻止 UDP 多播

2. **环境变量未设置**
   ```bash
   source /opt/ros/noetic/setup.bash
   source /opt/ros/humble/setup.bash
   export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
   ```

3. **桥接服务未启动**
   ```bash
   cd /workspace/fastdds-bridge/scripts
   python3 bridge_node.py
   ```

4. **日志查看**
   ```bash
   # 桥接日志
   tail -f /tmp/bridge.log
   
   # 测试日志
   cat /tmp/e2e_*.log
   
   # ROS 核心日志
   cat /tmp/roscore.log
   ```

### 调试命令

```bash
# 检查 DDS 参与者
fastdds discovery

# 检查 ROS2 健康状态
ros2 doctor --report

# 列出 ROS1 话题
rostopic list

# 列出 ROS2 话题
ros2 topic list

# 查看桥接进程
ps aux | grep bridge
```

## 性能指标参考

| 场景 | 延迟 (avg) | 吞吐量 | 消息丢失率 |
|------|-----------|--------|-----------|
| 本地共享内存 | < 1ms | > 10K msg/s | < 0.01% |
| 局域网 UDP | 2-5ms | > 5K msg/s | < 0.1% |
| 跨网段 | 5-15ms | > 2K msg/s | < 0.5% |

## 持续集成

可将测试脚本集成到 CI/CD 流程：

```yaml
# .gitlab-ci.yml 示例
test:
  script:
    - docker build -t fastdds-bridge:latest .
    - docker run -d --network host fastdds-bridge:latest sleep 300
    - docker exec $(docker ps -q) /workspace/fastdds-bridge/scripts/run_tests.sh
```

## 支持的消息类型

当前测试支持以下消息类型的跨框架转换：

- `std_msgs/String`
- `std_msgs/Int32`
- `std_msgs/Float64`
- `geometry_msgs/Twist` (需额外配置)
- `sensor_msgs/PointCloud2` (需额外配置)

## 扩展测试

如需添加自定义测试用例：

1. 编辑 `e2e_test.sh` 添加新的测试函数
2. 在 `run_tests.sh` 中添加环境检查
3. 使用 `performance_test.py` 作为模板创建专用性能测试

## 联系与支持

如有问题，请查看：
- 项目文档：[`README.md`](../README.md)
- 快速指南：[`QUICK_START_TEST.md`](../QUICK_START_TEST.md)
- 构建说明：[`BUILD.md`](../BUILD.md)

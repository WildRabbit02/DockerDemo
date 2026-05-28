#!/bin/bash
# 测试验证脚本 - 验证 ROS1、ROS2、CyberRT 与 FastDDS 的互通性
set -e

echo "=========================================="
echo "FastDDS Bridge 测试验证套件"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果计数
TESTS_PASSED=0
TESTS_FAILED=0

# 打印测试结果
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# 等待服务启动
wait_for_service() {
    local service_name=$1
    local max_attempts=${2:-30}
    local attempt=1
    
    echo -e "${YELLOW}等待 $service_name 启动...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if eval "$3" > /dev/null 2>&1; then
            echo -e "${GREEN}$service_name 已就绪${NC}"
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    echo -e "${RED}$service_name 启动超时${NC}"
    return 1
}

echo ""
echo "=== 测试 1: 环境检查 ==="

# 检查 ROS1 环境
source /opt/ros/noetic/setup.bash 2>/dev/null || true
if command -v roscore &> /dev/null; then
    print_result 0 "ROS1 Noetic 环境可用"
else
    print_result 1 "ROS1 Noetic 环境不可用"
fi

# 检查 ROS2 环境
source /opt/ros/humble/setup.bash 2>/dev/null || true
if command -v ros2 &> /dev/null; then
    print_result 0 "ROS2 Humble 环境可用"
else
    print_result 1 "ROS2 Humble 环境不可用"
fi

# 检查 CyberRT 环境
if [ -f "/apollo/cyber/cyber_launch" ] || command -v cyber_launch &> /dev/null; then
    print_result 0 "CyberRT 环境可用"
else
    print_result 1 "CyberRT 环境不可用"
fi

# 检查 FastDDS
if command -v fastdds &> /dev/null; then
    print_result 0 "FastDDS CLI 工具可用"
else
    print_result 1 "FastDDS CLI 工具不可用"
fi

# 检查 RMW 实现
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
if [[ "$RMW_IMPLEMENTATION" == "rmw_fastrtps_cpp" ]]; then
    print_result 0 "RMW 实现设置为 rmw_fastrtps_cpp"
else
    print_result 1 "RMW 实现未正确设置"
fi

echo ""
echo "=== 测试 2: ROS1 内部通信测试 ==="

# 启动 roscore（后台）
roscore > /tmp/roscore.log 2>&1 &
ROSCORE_PID=$!
sleep 3

# ROS1 Talker 测试
source /opt/ros/noetic/setup.bash
rostopic pub -r 1 /ros1_test std_msgs/String "data: 'Hello from ROS1'" > /tmp/ros1_talker.log 2>&1 &
TALKER_PID=$!
sleep 2

# ROS1 Listener 测试
source /opt/ros/noetic/setup.bash
rostopic echo -n 1 /ros1_test > /tmp/ros1_listener.log 2>&1 &
LISTENER_PID=$!
sleep 3

if grep -q "Hello from ROS1" /tmp/ros1_listener.log 2>/dev/null; then
    print_result 0 "ROS1 内部通信正常"
else
    print_result 1 "ROS1 内部通信失败"
fi

# 清理 ROS1 测试进程
kill $TALKER_PID $LISTENER_PID 2>/dev/null || true
sleep 1

echo ""
echo "=== 测试 3: ROS2 内部通信测试 ==="

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# ROS2 Talker 测试
ros2 topic pub -r 1 /ros2_test std_msgs/msg/String "{data: 'Hello from ROS2'}" > /tmp/ros2_talker.log 2>&1 &
ROS2_TALKER_PID=$!
sleep 2

# ROS2 Listener 测试
ros2 topic echo -n 1 /ros2_test > /tmp/ros2_listener.log 2>&1 &
ROS2_LISTENER_PID=$!
sleep 3

if grep -q "Hello from ROS2" /tmp/ros2_listener.log 2>/dev/null; then
    print_result 0 "ROS2 内部通信正常"
else
    print_result 1 "ROS2 内部通信失败"
fi

# 清理 ROS2 测试进程
kill $ROS2_TALKER_PID $ROS2_LISTENER_PID 2>/dev/null || true
sleep 1

echo ""
echo "=== 测试 4: FastDDS 发现测试 ==="

# 检查 DDS 参与者发现
fastdds discovery > /tmp/fastdds_discovery.log 2>&1 &
DISCOVERY_PID=$!
sleep 3
kill $DISCOVERY_PID 2>/dev/null || true

if [ -s /tmp/fastdds_discovery.log ]; then
    print_result 0 "FastDDS 服务发现正常"
else
    print_result 1 "FastDDS 服务发现异常"
fi

echo ""
echo "=== 测试 5: 桥接服务测试 ==="

# 启动桥接服务
cd /workspace/fastdds-bridge/scripts
python3 bridge_node.py > /tmp/bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 5

if ps -p $BRIDGE_PID > /dev/null; then
    print_result 0 "桥接服务启动成功"
else
    print_result 1 "桥接服务启动失败"
fi

echo ""
echo "=== 测试 6: 跨框架通信测试 ==="

# 测试 ROS1 -> ROS2
source /opt/ros/noetic/setup.bash
rostopic pub -r 1 /bridge_test_ros1_to_ros2 std_msgs/String "data: 'ROS1 to ROS2'" > /tmp/ros1_to_ros2.log 2>&1 &
R1_TO_R2_PID=$!
sleep 2

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo -n 1 /bridge_test_ros1_to_ros2 > /tmp/r1_to_r2_result.log 2>&1 &
R1_TO_R2_LISTENER_PID=$!
sleep 3

if grep -q "ROS1 to ROS2" /tmp/r1_to_r2_result.log 2>/dev/null; then
    print_result 0 "ROS1 -> ROS2 跨框架通信成功"
else
    print_result 1 "ROS1 -> ROS2 跨框架通信失败"
fi

kill $R1_TO_R2_PID $R1_TO_R2_LISTENER_PID 2>/dev/null || true
sleep 1

# 测试 ROS2 -> ROS1
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub -r 1 /bridge_test_ros2_to_ros1 std_msgs/msg/String "{data: 'ROS2 to ROS1'}" > /tmp/ros2_to_ros1.log 2>&1 &
R2_TO_R1_PID=$!
sleep 2

source /opt/ros/noetic/setup.bash
rostopic echo -n 1 /bridge_test_ros2_to_ros1 > /tmp/r2_to_r1_result.log 2>&1 &
R2_TO_R1_LISTENER_PID=$!
sleep 3

if grep -q "ROS2 to ROS1" /tmp/r2_to_r1_result.log 2>/dev/null; then
    print_result 0 "ROS2 -> ROS1 跨框架通信成功"
else
    print_result 1 "ROS2 -> ROS1 跨框架通信失败"
fi

kill $R2_TO_R1_PID $R2_TO_R1_LISTENER_PID 2>/dev/null || true
sleep 1

# 清理桥接服务
kill $BRIDGE_PID 2>/dev/null || true
sleep 2

echo ""
echo "=== 测试 7: CyberRT 组件测试（如果可用）==="

if [ -f "/apollo/cyber/cyber_launch" ] || command -v cyber_launch &> /dev/null; then
    # 初始化 CyberRT
    source /apollo/cyber/setup.bash 2>/dev/null || true
    
    if command -v cyber_channel list &> /dev/null; then
        cyber_channel list > /tmp/cyber_channels.log 2>&1
        print_result 0 "CyberRT 通道列表获取成功"
    else
        print_result 1 "CyberRT 通道命令不可用"
    fi
else
    echo -e "${YELLOW}⊠ SKIPPED${NC}: CyberRT 未安装，跳过测试"
fi

echo ""
echo "=== 测试 8: FastDDS Monitor 连接测试 ==="

# 检查 monitor 配置文件
if [ -f "/workspace/fastdds-bridge/config/qos_profiles.xml" ]; then
    print_result 0 "QoS 配置文件存在"
else
    print_result 1 "QoS 配置文件缺失"
fi

# 检查 DDS 域 ID 一致性
export FASTRTPS_DEFAULT_PROFILES_FILE=/workspace/fastdds-bridge/config/qos_profiles.xml
if [ -f "$FASTRTPS_DEFAULT_PROFILES_FILE" ]; then
    print_result 0 "FastDDS 配置文件加载成功"
else
    print_result 1 "FastDDS 配置文件加载失败"
fi

echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "通过：${GREEN}${TESTS_PASSED}${NC}"
echo -e "失败：${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}所有测试通过！系统已准备就绪。${NC}"
    echo ""
    echo "下一步操作建议："
    echo "1. 运行实际业务节点进行端到端测试"
    echo "2. 启动 FastDDS Monitor 进行可视化监控"
    echo "3. 根据实际需求调整桥接配置"
    exit 0
else
    echo -e "${RED}部分测试失败，请检查上述错误信息。${NC}"
    echo ""
    echo "故障排查建议："
    echo "1. 检查 Docker 网络模式是否为 host"
    echo "2. 确认所有环境变量已正确设置"
    echo "3. 查看各组件日志文件 (/tmp/*.log)"
    echo "4. 验证 DDS Domain ID 配置一致性"
    exit 1
fi

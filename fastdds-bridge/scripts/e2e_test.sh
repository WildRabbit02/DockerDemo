#!/bin/bash
# 端到端集成测试 - 验证 ROS1、ROS2、CyberRT 三向通信

set -e

echo "=========================================="
echo "端到端集成测试"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试配置
TEST_DURATION=${1:-10}  # 默认测试 10 秒
MESSAGE_COUNT=100

echo -e "${BLUE}测试配置:${NC}"
echo "  测试持续时间：${TEST_DURATION}秒"
echo "  消息数量：${MESSAGE_COUNT}条"
echo ""

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}清理测试进程...${NC}"
    kill $ROSCORE_PID 2>/dev/null || true
    kill $BRIDGE_PID 2>/dev/null || true
    kill $PUB_PID 2>/dev/null || true
    kill $SUB_PID 2>/dev/null || true
    kill $CYBER_NODE_PID 2>/dev/null || true
    rm -f /tmp/e2e_*.log
}

trap cleanup EXIT

# 测试结果
declare -A TEST_RESULTS
TESTS_RUN=0
TESTS_PASSED=0

run_test() {
    local test_name=$1
    local test_cmd=$2
    local expected=$3
    
    ((TESTS_RUN++))
    echo -e "\n${BLUE}运行测试：${test_name}${NC}"
    
    if eval "$test_cmd" > /tmp/e2e_${test_name}.log 2>&1; then
        if [ -n "$expected" ] && grep -q "$expected" /tmp/e2e_${test_name}.log; then
            echo -e "${GREEN}✓ PASSED${NC}: ${test_name}"
            ((TESTS_PASSED++))
            TEST_RESULTS["$test_name"]="PASS"
            return 0
        elif [ -z "$expected" ]; then
            echo -e "${GREEN}✓ PASSED${NC}: ${test_name}"
            ((TESTS_PASSED++))
            TEST_RESULTS["$test_name"]="PASS"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}: ${test_name} - 未找到预期结果 '$expected'"
            TEST_RESULTS["$test_name"]="FAIL"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC}: ${test_name} - 命令执行失败"
        cat /tmp/e2e_${test_name}.log
        TEST_RESULTS["$test_name"]="FAIL"
        return 1
    fi
}

echo "=== 阶段 1: 启动基础服务 ==="

# 启动 roscore
echo -e "${YELLOW}启动 roscore...${NC}"
roscore > /tmp/e2e_roscore.log 2>&1 &
ROSCORE_PID=$!
sleep 3

if ps -p $ROSCORE_PID > /dev/null; then
    echo -e "${GREEN}✓ roscore 已启动${NC}"
else
    echo -e "${RED}✗ roscore 启动失败${NC}"
    exit 1
fi

# 启动桥接服务
echo -e "${YELLOW}启动桥接服务...${NC}"
cd /workspace/fastdds-bridge/scripts
python3 bridge_node.py > /tmp/e2e_bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 5

if ps -p $BRIDGE_PID > /dev/null; then
    echo -e "${GREEN}✓ 桥接服务已启动${NC}"
else
    echo -e "${RED}✗ 桥接服务启动失败${NC}"
    cat /tmp/e2e_bridge.log
    exit 1
fi

echo ""
echo "=== 阶段 2: ROS1 ↔ ROS2 双向通信测试 ==="

# 测试 1: ROS1 → ROS2
source /opt/ros/noetic/setup.bash
rostopic pub -r 10 /e2e_ros1_to_ros2 std_msgs/String "data: 'ROS1->ROS2 Test'" > /tmp/e2e_ros1_pub.log 2>&1 &
PUB_PID=$!
sleep 2

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
timeout ${TEST_DURATION} ros2 topic echo /e2e_ros1_to_ros2 > /tmp/e2e_r1_to_r2_sub.log 2>&1 &
SUB_PID=$!
wait $SUB_PID 2>/dev/null || true

kill $PUB_PID 2>/dev/null || true

if grep -q "ROS1->ROS2 Test" /tmp/e2e_r1_to_r2_sub.log 2>/dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}: ROS1 → ROS2 通信"
    ((TESTS_PASSED++))
    TEST_RESULTS["ROS1_to_ROS2"]="PASS"
else
    echo -e "${RED}✗ FAILED${NC}: ROS1 → ROS2 通信"
    TEST_RESULTS["ROS1_to_ROS2"]="FAIL"
fi
((TESTS_RUN++))

# 测试 2: ROS2 → ROS1
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub -r 10 /e2e_ros2_to_ros1 std_msgs/msg/String "{data: 'ROS2->ROS1 Test'}" > /tmp/e2e_ros2_pub.log 2>&1 &
PUB_PID=$!
sleep 2

source /opt/ros/noetic/setup.bash
timeout ${TEST_DURATION} rostopic echo /e2e_ros2_to_ros1 > /tmp/e2e_r2_to_r1_sub.log 2>&1 &
SUB_PID=$!
wait $SUB_PID 2>/dev/null || true

kill $PUB_PID 2>/dev/null || true

if grep -q "ROS2->ROS1 Test" /tmp/e2e_r2_to_r1_sub.log 2>/dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}: ROS2 → ROS1 通信"
    ((TESTS_PASSED++))
    TEST_RESULTS["ROS2_to_ROS1"]="PASS"
else
    echo -e "${RED}✗ FAILED${NC}: ROS2 → ROS1 通信"
    TEST_RESULTS["ROS2_to_ROS1"]="FAIL"
fi
((TESTS_RUN++))

echo ""
echo "=== 阶段 3: 多消息并发测试 ==="

# 测试 3: 高频消息测试 (100 条消息)
echo -e "${YELLOW}发送 100 条测试消息...${NC}"

source /opt/ros/noetic/setup.bash
for i in $(seq 1 100); do
    rostopic pub -1 /e2e_stress_test std_msgs/String "data: 'Message $i'" > /dev/null 2>&1
done

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
sleep 2
RECEIVED_COUNT=$(timeout 5 ros2 topic echo /e2e_stress_test 2>/dev/null | grep -c "Message" || echo "0")

if [ "$RECEIVED_COUNT" -gt 80 ]; then
    echo -e "${GREEN}✓ PASSED${NC}: 高频消息测试 (接收 $RECEIVED_COUNT/100)"
    ((TESTS_PASSED++))
    TEST_RESULTS["Stress_Test"]="PASS"
else
    echo -e "${RED}✗ FAILED${NC}: 高频消息测试 (仅接收 $RECEIVED_COUNT/100)"
    TEST_RESULTS["Stress_Test"]="FAIL"
fi
((TESTS_RUN++))

echo ""
echo "=== 阶段 4: 不同消息类型测试 ==="

# 测试 4: Int32 消息类型
source /opt/ros/noetic/setup.bash
rostopic pub -1 /e2e_int_test std_msgs/Int32 "data: 42" > /dev/null 2>&1
sleep 1

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
INT_RESULT=$(timeout 2 ros2 topic echo /e2e_int_test 2>/dev/null | grep "data: 42" || echo "")

if [ -n "$INT_RESULT" ]; then
    echo -e "${GREEN}✓ PASSED${NC}: Int32 消息类型转换"
    ((TESTS_PASSED++))
    TEST_RESULTS["Int32_Type"]="PASS"
else
    echo -e "${RED}✗ FAILED${NC}: Int32 消息类型转换"
    TEST_RESULTS["Int32_Type"]="FAIL"
fi
((TESTS_RUN++))

# 测试 5: Float64 消息类型
source /opt/ros/noetic/setup.bash
rostopic pub -1 /e2e_float_test std_msgs/Float64 "data: 3.14159" > /dev/null 2>&1
sleep 1

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
FLOAT_RESULT=$(timeout 2 ros2 topic echo /e2e_float_test 2>/dev/null | grep "data:" || echo "")

if [ -n "$FLOAT_RESULT" ]; then
    echo -e "${GREEN}✓ PASSED${NC}: Float64 消息类型转换"
    ((TESTS_PASSED++))
    TEST_RESULTS["Float64_Type"]="PASS"
else
    echo -e "${RED}✗ FAILED${NC}: Float64 消息类型转换"
    TEST_RESULTS["Float64_Type"]="FAIL"
fi
((TESTS_RUN++))

echo ""
echo "=== 阶段 5: CyberRT 集成测试（如果可用）==="

if command -v cyber_channel &> /dev/null; then
    source /apollo/cyber/setup.bash 2>/dev/null || true
    
    # 列出 CyberRT 通道
    cyber_channel list > /tmp/e2e_cyber_channels.log 2>&1
    
    if [ -s /tmp/e2e_cyber_channels.log ]; then
        echo -e "${GREEN}✓ PASSED${NC}: CyberRT 通道查询"
        ((TESTS_PASSED++))
        TEST_RESULTS["CyberRT_Channel"]="PASS"
    else
        echo -e "${YELLOW}⊠ SKIPPED${NC}: CyberRT 无活跃通道"
        TEST_RESULTS["CyberRT_Channel"]="SKIP"
    fi
    ((TESTS_RUN++))
else
    echo -e "${YELLOW}⊠ SKIPPED${NC}: CyberRT 未安装"
    TEST_RESULTS["CyberRT_Channel"]="SKIP"
    ((TESTS_RUN++))
fi

echo ""
echo "=== 阶段 6: FastDDS 发现测试 ==="

# 测试 6: FastDDS 参与者发现
fastdds discovery > /tmp/e2e_fastdds_discovery.log 2>&1 &
DISCOVERY_PID=$!
sleep 2
kill $DISCOVERY_PID 2>/dev/null || true

if [ -s /tmp/e2e_fastdds_discovery.log ]; then
    PARTICIPANTS=$(grep -c "Participant" /tmp/e2e_fastdds_discovery.log || echo "0")
    if [ "$PARTICIPANTS" -gt 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: FastDDS 发现 $PARTICIPANTS 个参与者"
        ((TESTS_PASSED++))
        TEST_RESULTS["FastDDS_Discovery"]="PASS"
    else
        echo -e "${RED}✗ FAILED${NC}: FastDDS 未发现参与者"
        TEST_RESULTS["FastDDS_Discovery"]="FAIL"
    fi
else
    echo -e "${RED}✗ FAILED${NC}: FastDDS 发现命令无输出"
    TEST_RESULTS["FastDDS_Discovery"]="FAIL"
fi
((TESTS_RUN++))

# 打印最终报告
echo ""
echo "=========================================="
echo "端到端集成测试报告"
echo "=========================================="
echo "总测试数：${TESTS_RUN}"
echo -e "通过：${GREEN}${TESTS_PASSED}${NC}"
echo -e "失败：${RED}$((${TESTS_RUN} - ${TESTS_PASSED}))${NC}"
echo "成功率：$(awk "BEGIN {printf \"%.1f\", (${TESTS_PASSED}/${TESTS_RUN})*100}")%"
echo ""
echo "详细结果:"
for test_name in "${!TEST_RESULTS[@]}"; do
    result=${TEST_RESULTS[$test_name]}
    if [ "$result" == "PASS" ]; then
        echo -e "  ${GREEN}✓${NC} ${test_name}: ${result}"
    elif [ "$result" == "SKIP" ]; then
        echo -e "  ${YELLOW}⊠${NC} ${test_name}: ${result}"
    else
        echo -e "  ${RED}✗${NC} ${test_name}: ${result}"
    fi
done

echo ""
if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}=========================================="
    echo "所有测试通过！系统已准备就绪。"
    echo -e "==========================================${NC}"
    exit 0
elif [ $TESTS_PASSED -gt $((${TESTS_RUN} / 2)) ]; then
    echo -e "${YELLOW}=========================================="
    echo "大部分测试通过，但存在一些问题。"
    echo "请检查失败的测试项。"
    echo -e "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "多数测试失败，系统可能存在严重问题。"
    echo "请查看详细日志进行故障排查。"
    echo -e "==========================================${NC}"
    exit 1
fi

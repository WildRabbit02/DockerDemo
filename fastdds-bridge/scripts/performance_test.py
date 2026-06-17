#!/usr/bin/env python3
"""
性能测试工具 - 测试 ROS1、ROS2、FastDDS 之间的消息延迟和吞吐量
"""

import argparse
import time
import statistics
import sys
import os

# 尝试导入 ROS1
try:
    import rospy
    from std_msgs.msg import String
    ROS1_AVAILABLE = True
except ImportError:
    ROS1_AVAILABLE = False

# 尝试导入 ROS2
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String as ROS2String
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


class LatencyTestROS1:
    """ROS1 延迟测试"""
    
    def __init__(self):
        rospy.init_node('latency_test_ros1')
        self.latencies = []
        self.pub = rospy.Publisher('latency_test', String, queue_size=10)
        self.sub = rospy.Subscriber('latency_test', String, self.callback)
        self.start_time = None
        
    def callback(self, msg):
        try:
            timestamp = float(msg.data.split(':')[1])
            latency = (time.time() - timestamp) * 1000  # 转换为毫秒
            self.latencies.append(latency)
        except (IndexError, ValueError):
            pass
    
    def run(self, duration=30, rate=100):
        print(f"开始 ROS1 延迟测试，持续 {duration} 秒，频率 {rate} Hz")
        end_time = time.time() + duration
        r = rospy.Rate(rate)
        
        while time.time() < end_time and not rospy.is_shutdown():
            msg = String()
            msg.data = f"ts:{time.time()}"
            self.pub.publish(msg)
            r.sleep()
        
        return self.latencies


class LatencyTestROS2(Node):
    """ROS2 延迟测试"""
    
    def __init__(self):
        super().__init__('latency_test_ros2')
        self.latencies = []
        self.pub = self.create_publisher(ROS2String, 'latency_test', 10)
        self.sub = self.create_subscription(ROS2String, 'latency_test', self.callback, 10)
        
    def callback(self, msg):
        try:
            timestamp = float(msg.data.split(':')[1])
            latency = (time.time() - timestamp) * 1000
            self.latencies.append(latency)
        except (IndexError, ValueError):
            pass
    
    def run(self, duration=30, rate=100):
        print(f"开始 ROS2 延迟测试，持续 {duration} 秒，频率 {rate} Hz")
        end_time = time.time() + duration
        timer = self.create_timer(1.0/rate, self.timer_callback)
        
        while time.time() < end_time and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
        
        timer.cancel()
        return self.latencies
    
    def timer_callback(self):
        msg = ROS2String()
        msg.data = f"ts:{time.time()}"
        self.pub.publish(msg)


class ThroughputTestROS1:
    """ROS1 吞吐量测试"""
    
    def __init__(self):
        rospy.init_node('throughput_test_ros1')
        self.messages_sent = 0
        self.messages_received = 0
        self.pub = rospy.Publisher('throughput_test', String, queue_size=10)
        self.sub = rospy.Subscriber('throughput_test', String, self.callback)
        
    def callback(self, msg):
        self.messages_received += 1
    
    def run(self, duration=30, message_size=1024):
        print(f"开始 ROS1 吞吐量测试，持续 {duration} 秒，消息大小 {message_size} 字节")
        
        # 创建测试消息
        test_data = 'A' * message_size
        
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time and not rospy.is_shutdown():
            msg = String()
            msg.data = f"{self.messages_sent}:{test_data}"
            self.pub.publish(msg)
            self.messages_sent += 1
        
        # 等待最后的消息被接收
        rospy.sleep(1)
        
        elapsed = time.time() - start_time
        throughput_sent = self.messages_sent / elapsed
        throughput_received = self.messages_received / elapsed
        
        return {
            'sent': self.messages_sent,
            'received': self.messages_received,
            'sent_rate': throughput_sent,
            'received_rate': throughput_received,
            'duration': elapsed
        }


def print_statistics(latencies, framework):
    """打印统计信息"""
    if not latencies:
        print(f"\n{framework}: 无数据")
        return
    
    avg = statistics.mean(latencies)
    median = statistics.median(latencies)
    std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
    min_val = min(latencies)
    max_val = max(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max_val
    p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 100 else max_val
    
    print(f"\n{framework} 延迟统计 (ms):")
    print(f"  平均值：  {avg:.3f}")
    print(f"  中位数：  {median:.3f}")
    print(f"  标准差：  {std_dev:.3f}")
    print(f"  最小值：  {min_val:.3f}")
    print(f"  最大值：  {max_val:.3f}")
    print(f"  95 百分位： {p95:.3f}")
    print(f"  99 百分位： {p99:.3f}")
    print(f"  样本数：  {len(latencies)}")


def main():
    parser = argparse.ArgumentParser(description='FastDDS Bridge 性能测试工具')
    parser.add_argument('--mode', choices=['latency', 'throughput', 'all'], 
                        default='all', help='测试模式')
    parser.add_argument('--duration', type=int, default=30, 
                        help='测试持续时间（秒）')
    parser.add_argument('--rate', type=int, default=100, 
                        help='消息发送频率（Hz）')
    parser.add_argument('--size', type=int, default=1024, 
                        help='吞吐量测试消息大小（字节）')
    parser.add_argument('--report', action='store_true', 
                        help='生成详细报告')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("FastDDS Bridge 性能测试")
    print("=" * 60)
    
    results = {}
    
    # 延迟测试
    if args.mode in ['latency', 'all']:
        print("\n=== 延迟测试 ===\n")
        
        if ROS1_AVAILABLE:
            try:
                test_ros1 = LatencyTestROS1()
                latencies_ros1 = test_ros1.run(duration=args.duration, rate=args.rate)
                print_statistics(latencies_ros1, "ROS1")
                results['ros1_latency'] = latencies_ros1
            except Exception as e:
                print(f"ROS1 延迟测试失败：{e}")
        
        if ROS2_AVAILABLE:
            try:
                rclpy.init()
                test_ros2 = LatencyTestROS2()
                latencies_ros2 = test_ros2.run(duration=args.duration, rate=args.rate)
                print_statistics(latencies_ros2, "ROS2")
                results['ros2_latency'] = latencies_ros2
                test_ros2.destroy_node()
                rclpy.shutdown()
            except Exception as e:
                print(f"ROS2 延迟测试失败：{e}")
    
    # 吞吐量测试
    if args.mode in ['throughput', 'all']:
        print("\n=== 吞吐量测试 ===\n")
        
        if ROS1_AVAILABLE:
            try:
                test_ros1_tp = ThroughputTestROS1()
                tp_results_ros1 = test_ros1_tp.run(duration=args.duration, message_size=args.size)
                print(f"ROS1 吞吐量结果:")
                print(f"  发送消息数：{tp_results_ros1['sent']}")
                print(f"  接收消息数：{tp_results_ros1['received']}")
                print(f"  发送速率：{tp_results_ros1['sent_rate']:.2f} msg/s")
                print(f"  接收速率：{tp_results_ros1['received_rate']:.2f} msg/s")
                print(f"  数据速率：{(tp_results_ros1['sent_rate'] * args.size / 1024):.2f} KB/s")
                results['ros1_throughput'] = tp_results_ros1
            except Exception as e:
                print(f"ROS1 吞吐量测试失败：{e}")
    
    # 生成报告
    if args.report:
        print("\n" + "=" * 60)
        print("性能测试报告")
        print("=" * 60)
        print(f"测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试模式：{args.mode}")
        print(f"持续时间：{args.duration}秒")
        print(f"消息频率：{args.rate} Hz")
        print(f"消息大小：{args.size} 字节")
        print(f"ROS1 可用：{'是' if ROS1_AVAILABLE else '否'}")
        print(f"ROS2 可用：{'是' if ROS2_AVAILABLE else '否'}")
        
        # 保存报告到文件
        report_file = f"performance_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write("FastDDS Bridge 性能测试报告\n")
            f.write(f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for key, value in results.items():
                f.write(f"{key}: {value}\n")
        print(f"\n详细报告已保存到：{report_file}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()

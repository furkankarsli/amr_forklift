#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import math
from sensor_msgs.msg import LaserScan

class ScanFilterNode(Node):
    def __init__(self):
        super().__init__('scan_filter_node')
        
        # Subscribe to raw scan data
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # Publish filtered scan data
        self.publisher = self.create_publisher(
            LaserScan,
            '/scan_filtered',
            10
        )
        
        # Define pillar angle ranges (in radians)
        # Left pillar is around 0.284 rad (16.3 deg). Range: [0.22, 0.35]
        # Right pillar is around -0.284 rad (-16.3 deg). Range: [-0.35, -0.22]
        self.left_min = 0.22
        self.left_max = 0.35
        self.right_min = -0.35
        self.right_max = -0.22
        
        self.get_logger().info('Scan Filter Node initialized. Filtering ranges: [%.2f, %.2f] and [%.2f, %.2f] radians.' % 
                               (self.right_min, self.right_max, self.left_min, self.left_max))

    def scan_callback(self, msg):
        filtered_msg = msg
        ranges = list(msg.ranges)
        
        for i in range(len(ranges)):
            # Calculate angle for the current laser index
            angle = msg.angle_min + i * msg.angle_increment
            
            # Normalize angle to [-pi, pi]
            while angle > math.pi:
                angle -= 2.0 * math.pi
            while angle < -math.pi:
                angle += 2.0 * math.pi
            
            # Check if angle is in the left or right pillar obstruction zone
            if (self.left_min <= angle <= self.left_max) or (self.right_min <= angle <= self.right_max):
                # Set range to infinity so Nav2/costmap ignores it
                ranges[i] = float('inf')
                
        filtered_msg.ranges = ranges
        self.publisher.publish(filtered_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ScanFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

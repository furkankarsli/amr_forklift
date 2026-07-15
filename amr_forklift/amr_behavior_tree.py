#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGV Autonomy Behavior Tree Node
Implements a modular py_trees Behavior Tree that manages:
1. Emergency safety stop (E-Stop) when a safety hazard is detected (gas/temp).
2. Automatic battery monitoring and return-to-charge simulation.
3. Patrol/Devriye mission execution.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool
from geometry_msgs.msg import Twist

import py_trees
import time


# =====================================================================
# 1. Custom py_trees Behaviors
# =====================================================================

class CheckSafety(py_trees.behaviour.Behaviour):
    """Checks the blackboard for an active safety hazard."""
    def __init__(self, name="CheckSafety"):
        super().__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def update(self):
        try:
            hazard = self.blackboard.get("safety_hazard")
        except KeyError:
            hazard = False

        if hazard:
            self.logger.warning("Safety hazard check failed! ACTIVE HAZARD DETECTED!")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class EStopAction(py_trees.behaviour.Behaviour):
    """Stops the robot immediately by publishing zero velocities."""
    def __init__(self, name="EStopAction", node=None):
        super().__init__(name)
        self.node = node
        self.cmd_vel_pub = None

    def setup(self):
        if self.node:
            self.cmd_vel_pub = self.node.create_publisher(Twist, 'cmd_vel', 10)

    def update(self):
        self.logger.critical("EMERGENCY ESTOP: Halting AGV motors!")
        if self.cmd_vel_pub:
            msg = Twist()
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.cmd_vel_pub.publish(msg)
        return py_trees.common.Status.SUCCESS


class CheckBattery(py_trees.behaviour.Behaviour):
    """Checks the blackboard for battery voltage level."""
    def __init__(self, name="CheckBattery"):
        super().__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def update(self):
        try:
            voltage = self.blackboard.get("battery_voltage")
        except KeyError:
            # Assume healthy if no telemetry yet
            voltage = 12.6

        if voltage is not None and voltage <= 11.0:
            self.logger.warning(f"Battery voltage critical: {voltage:.1f}V (Threshold <= 11.0V)")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class BatteryChargingAction(py_trees.behaviour.Behaviour):
    """Simulates returning to a charging station and charging up."""
    def __init__(self, name="BatteryChargingAction", node=None):
        super().__init__(name)
        self.node = node
        self.blackboard = py_trees.blackboard.Blackboard()
        self.cmd_vel_pub = None
        self.last_charge_time = 0

    def setup(self):
        if self.node:
            self.cmd_vel_pub = self.node.create_publisher(Twist, 'cmd_vel', 10)

    def initialise(self):
        self.last_charge_time = time.time()

    def update(self):
        self.logger.info("Charging: Suspended normal patrol, docked at station.")
        
        # Stop the robot during charging
        if self.cmd_vel_pub:
            msg = Twist()
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.cmd_vel_pub.publish(msg)

        now = time.time()
        if now - self.last_charge_time >= 1.0:
            current_v = self.blackboard.get("battery_voltage")
            new_v = min(14.4, current_v + 0.5)
            self.blackboard.set("battery_voltage", new_v)
            self.logger.info(f"Charging... Battery Voltage: {new_v:.1f}V")
            self.last_charge_time = now

        # Charge complete check
        current_v = self.blackboard.get("battery_voltage")
        if current_v >= 14.2:
            self.logger.info("Charging complete! Resuming operations.")
            return py_trees.common.Status.SUCCESS
            
        return py_trees.common.Status.RUNNING


class PatrolAction(py_trees.behaviour.Behaviour):
    """Simulates a patrol navigation behavior by publishing walking patterns."""
    def __init__(self, name="PatrolAction", node=None):
        super().__init__(name)
        self.node = node
        self.cmd_vel_pub = None
        self.step = 0

    def setup(self):
        if self.node:
            self.cmd_vel_pub = self.node.create_publisher(Twist, 'cmd_vel', 10)

    def update(self):
        self.step = (self.step + 1) % 40
        
        msg = Twist()
        if self.step < 25:
            # Drive straight
            msg.linear.x = 0.3
            msg.angular.z = 0.0
            self.logger.info("Patrol: Driving straight...")
        else:
            # Turn
            msg.linear.x = 0.0
            msg.angular.z = 0.6
            self.logger.info("Patrol: Turning...")

        if self.cmd_vel_pub:
            self.cmd_vel_pub.publish(msg)
            
        return py_trees.common.Status.RUNNING


# =====================================================================
# 2. Main ROS2 Node wrapper
# =====================================================================

class AGVAutonomyBTNode(Node):
    def __init__(self):
        super().__init__('amr_behavior_tree')

        # Blackboard initialization
        self.blackboard = py_trees.blackboard.Blackboard()
        self.blackboard.set("battery_voltage", 12.6)
        self.blackboard.set("safety_hazard", False)

        # Subscribers
        self.create_subscription(Float32, 'battery_voltage', self.battery_callback, 10)
        self.create_subscription(Bool, 'safety_hazard', self.safety_callback, 10)

        # Build behavior tree
        self.tree_root = self.build_tree()
        self.tree_root.setup_with_descendants()

        # Tick timer (5 Hz)
        self.timer = self.create_timer(0.2, self.tick_tree)
        self.get_logger().info("AGV Autonomy Behavior Tree Node initialized.")

    def battery_callback(self, msg: Float32):
        self.blackboard.set("battery_voltage", float(msg.data))

    def safety_callback(self, msg: Bool):
        self.blackboard.set("safety_hazard", bool(msg.data))

    def build_tree(self) -> py_trees.composites.Selector:
        # Create Root Selector
        root = py_trees.composites.Selector("AGV_Main_Decision_Tree", memory=False)

        # Emergency stop branch
        estop_seq = py_trees.composites.Sequence("Safety_Emergency_Sequence", memory=True)
        check_safety = CheckSafety("CheckSafety")
        estop_action = EStopAction("EStopAction", node=self)
        estop_seq.add_children([check_safety, estop_action])

        # Battery charging branch
        charge_seq = py_trees.composites.Sequence("Battery_Charging_Sequence", memory=True)
        check_battery = CheckBattery("CheckBattery")
        charge_action = BatteryChargingAction("BatteryChargingAction", node=self)
        charge_seq.add_children([check_battery, charge_action])

        # Default Patrol branch
        patrol_action = PatrolAction("PatrolAction", node=self)

        # Add branches to root
        root.add_children([estop_seq, charge_seq, patrol_action])
        return root

    def tick_tree(self):
        self.tree_root.tick_once()


def main(args=None):
    rclpy.init(args=args)
    node = AGVAutonomyBTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

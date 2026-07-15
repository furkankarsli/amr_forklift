from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='amr_forklift',
            executable='amr_behavior_tree',
            name='amr_behavior_tree',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )
    ])

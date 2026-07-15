#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_amr_forklift = get_package_share_directory('amr_forklift')
    params_path = os.path.join(pkg_amr_forklift, 'config', 'navigation.yaml')
    map_path = os.path.join(pkg_amr_forklift, 'maps', 'map_latest.yaml')
    
    # NAV2 bringup - map parameter is REQUIRED
    nav2_cmd = ExecuteProcess(
        cmd=['bash', '-c',
             f'ros2 launch nav2_bringup bringup_launch.py autostart:=true params_file:={params_path} use_sim_time:=true map:={map_path}'],
        output='screen'
    )
    
    return LaunchDescription([nav2_cmd])

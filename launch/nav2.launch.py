import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_nav2 = FindPackageShare("nav2_bringup")
    pkg_amr_forklift = get_package_share_directory('amr_forklift')

    default_map_path = os.path.join(pkg_amr_forklift, 'maps', 'map_latest.yaml')
    params_path = os.path.join(pkg_amr_forklift, 'config', 'navigation.yaml')

    # NAV2 bringup via standard IncludeLaunchDescription
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_nav2, "launch", "bringup_launch.py"])
        ),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "autostart": "true",
            "params_file": params_path,
            "map": LaunchConfiguration("map"),
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use simulated time (true for Gazebo, false for real robot)'),
        DeclareLaunchArgument('map', 
                              default_value=default_map_path,
                              description='Full path to map yaml file to load'),
        nav2_launch
    ])

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('amr_forklift')

    use_sim_time = LaunchConfiguration('use_sim_time')

    # SLAM Toolbox başlat
    # Not: Madgwick IMU Filter ve EKF, gazebo.launch.py tarafından başlatılıyor
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')]),
        launch_arguments={
            'slam_params_file': os.path.join(pkg_share, 'config', 'slam_toolbox_mapping.yaml'),
            'use_sim_time': use_sim_time}.items(),
    )
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Sim saati kullan (Gazebo için true, gerçek robot için false)'),
        slam_launch
    ])

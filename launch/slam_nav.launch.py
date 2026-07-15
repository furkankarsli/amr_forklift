"""
slam_nav.launch.py
==================
SLAM + Nav2 navigasyonu BİRLİKTE — AMCL ve elle 2D Pose Estimate olmadan.

slam_toolbox sürekli lazer eşleştirme (scan matching) yaparak map→odom'u
otomatik ve hassas üretir. Böylece:
  - Harita kaydet / yükle dansı YOK
  - Elle 2D Pose Estimate YOK
  - AMCL açı (yaw) hatası YOK

Kullanım (Gazebo zaten açıkken):
  ros2 launch amr_forklift slam_nav.launch.py

Sonra RViz'de doğrudan "Nav2 Goal" ile hedef ver. Robot gider.
Alanı tanımak için önce teleop ile biraz gezdir (harita dolsun).
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_amr_forklift = get_package_share_directory('amr_forklift')
    pkg_slam = get_package_share_directory('slam_toolbox')
    pkg_nav2 = get_package_share_directory('nav2_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    nav2_params = os.path.join(pkg_amr_forklift, 'config', 'navigation.yaml')
    slam_params = os.path.join(pkg_amr_forklift, 'config', 'slam_toolbox_mapping.yaml')

    # 1) SLAM Toolbox — /map yayınlar, map→odom transform'unu sürekli üretir
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_slam, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'slam_params_file': slam_params,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    # 2) Nav2 navigasyon stack'i — SADECE planlama/kontrol (amcl ve map_server YOK)
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params,
            'autostart': 'true',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Gazebo için true, gerçek robot için false'),
        slam,
        navigation,
    ])

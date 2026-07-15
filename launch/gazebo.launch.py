import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get the share directory of the package
    pkg_share = get_package_share_directory('amr_forklift')

    # Setup Gazebo resource paths to load the custom textures and materials
    materials_dir = os.path.join(pkg_share, 'models', 'nebula_urdf')
    existing_resource_path = os.environ.get('GAZEBO_RESOURCE_PATH', '')
    
    # Include default gazebo resource path so basic shapes render correctly
    resource_paths = [materials_dir, '/usr/share/gazebo-11']
    if existing_resource_path:
        resource_paths.append(existing_resource_path)
        
    set_gazebo_resource = SetEnvironmentVariable(
        'GAZEBO_RESOURCE_PATH', ':'.join(resource_paths)
    )

    # Launch Configurations
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    world = os.path.join(pkg_share, 'worlds', 'nebula_arena.world')

    # Xacro Robot Model configuration
    xacro_file = os.path.join(pkg_share, 'models', 'nebula_urdf', 'model.xacro')
    rviz_config = os.path.join(pkg_share, 'rviz', 'config.rviz')

    robot_description = {
        'robot_description': ParameterValue(
            Command(['xacro ', xacro_file, ' is_sim:=true']),
            value_type=str
        )
    }

    # Declare Launch Arguments
    declared_arguments = [
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz2 visualization tool'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
    ]

    # Execute Gazebo Server
    gzserver = ExecuteProcess(
        cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world],
        output='screen'
    )

    # Execute Gazebo Client (GUI)
    gzclient = ExecuteProcess(
        cmd=['gzclient'],
        output='screen'
    )

    # Spawn Entity Node (spawns the robot description topic into Gazebo)
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'nebula_agv',
            '-x', '-6.0',
            '-y', '-3.8',
            '-z', '0.15',
            '-Y', '-1.5708',
        ],
        output='screen'
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    # RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
        condition=IfCondition(use_rviz),
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription(
        declared_arguments + [
            set_gazebo_resource,
            gzserver,
            gzclient,
            robot_state_publisher,
            spawn_robot,
            rviz_node,
        ]
    )

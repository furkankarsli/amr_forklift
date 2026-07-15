cmake_minimum_required(VERSION 3.5)
project(amr_forklift)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(action_msgs REQUIRED)

# 1. Install python module package (amr_forklift python structure)
install(DIRECTORY amr_forklift/
  DESTINATION local/lib/python3.10/dist-packages/amr_forklift
  FILES_MATCHING PATTERN "*.py"
)

# 2. Install executable python scripts to lib/amr_forklift
install(PROGRAMS
  amr_forklift/amr_behavior_tree.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME amr_behavior_tree
)
install(PROGRAMS
  amr_forklift/scan_filter_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME scan_filter_node
)

# 3. Share directories (launch, worlds, models, rviz, config, maps)
install(DIRECTORY
  launch
  worlds
  models
  rviz
  config
  maps
  DESTINATION share/${PROJECT_NAME}
)

# 4. Generate custom action interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/PlayAudio.action"
  DEPENDENCIES builtin_interfaces
)

# Export dependencies
ament_export_dependencies(rosidl_default_runtime)

# Wrap package
ament_package()

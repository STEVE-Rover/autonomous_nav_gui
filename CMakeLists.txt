cmake_minimum_required(VERSION 3.0.2)
project(autonomous_nav_gui)

find_package(catkin REQUIRED COMPONENTS
  rospy
  rqt_gui
  rqt_gui_py
)

catkin_python_setup()

catkin_package()

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

install(PROGRAMS
  scripts/autonomous_nav_gui
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  resource
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(FILES
  plugin.xml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

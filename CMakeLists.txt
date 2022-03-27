cmake_minimum_required(VERSION 2.8.3)
project(aioros_bridge)

find_package(catkin REQUIRED)

catkin_python_setup()
catkin_package()

catkin_install_python(
    PROGRAMS
     scripts/run
    DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
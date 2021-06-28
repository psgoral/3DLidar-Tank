from rplidar import RPLidar
import time

lidar = RPLidar('/dev/ttyUSB0',timeout=1)


lidar.stop()
lidar.stop_motor()
lidar.disconnect()

from logging import PlaceHolder
import sys
import math
from PyQt5 import QtWidgets, QtCore
import numpy as np
from PyQt5.QtWidgets import QPushButton, QWidget,QFrame,QVBoxLayout,QTextEdit,QGridLayout, QLineEdit
from PyQt5.QtGui import QPainter, QColor, QFont
from vispy import visuals, scene,app
from vispy.visuals.transforms.linear import MatrixTransform
import json

import socket
import time


last_angle = 0

UDP_IP = "192.168.0.110"
UDP_PORT = 5005

UDP_INFO = (UDP_IP,UDP_PORT)


def connect_UDP():


    UDP = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP


    return UDP



def receive_file(UDP):

    # UDP.bind(UDP_INFO)
    print('UDP BINDED')

    f = open('raw_scans/pokoj_live2.txt','a+')
    while True:
        data, addr = UDP.recvfrom(1024) # buffer size is 1024 bytes
        if len(data) >1:
            received = data.decode()
            f.write(received)
            print(received)
            # cmd = 'RECEIVED'
            # UDP.sendto(cmd.encode('utf-8'),address)

            # if 'END' in received:
            #     return True
        else:
            f.close()
            print('full scan received')
            return True


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.resize(1920,1080)
        self.setWindowTitle('Lidar Visualizer')
        self.setStyleSheet("background-color: rgb(0,0,0);")
        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter1.setStyleSheet('background-color: rgb(0, 0, 0);color:white;') #central

        self.MapCanvas = scene.canvas.SceneCanvas(keys='interactive',size=(1600,900),bgcolor='black')
        self.MapCanvas.create_native()
        self.MapCanvas.native.setParent(self)
        self.menuWidget = QFrame(self)

        self.buttonsLayout = QGridLayout(self.menuWidget)
        splitter1.addWidget(self.MapCanvas.native)
        splitter1.addWidget(self.menuWidget)


        self.setCentralWidget(splitter1)


    def get_map(self):
        return self.MapCanvas


    def GUI(self):
        self.LidarInfoConsole = QTextEdit(self.menuWidget)
        self.LidarIpField = QLineEdit(self.menuWidget)
        self.ConnectToLidarButton = QPushButton("Połącz z Lidarem",self.menuWidget)
        self.NewMapButton = QPushButton("Nowa mapa",self.menuWidget)
        self.LoadMapButton = QPushButton("Wczytaj mapę",self.menuWidget)
        self.clearMapButton = QPushButton("Wyczyść mapę",self.menuWidget)

        self.ConnectToLidarButton.setStyleSheet('background-color: black;color:white;')
        self.NewMapButton.setStyleSheet('background-color:black;color:white;')
        self.LoadMapButton.setStyleSheet('background-color: black;color:white;')
        self.clearMapButton.setStyleSheet('background-color: black;color:white;')

        self.buttonsLayout.addWidget(self.LidarInfoConsole,0,0,1,1)
        self.buttonsLayout.addWidget(self.LidarIpField,6,0,1,1)
        self.buttonsLayout.addWidget(self.ConnectToLidarButton,7,0,1,1)
        self.buttonsLayout.addWidget(self.NewMapButton,8,0,1,1)
        self.buttonsLayout.addWidget(self.LoadMapButton,9,0,1,1)
        self.buttonsLayout.addWidget(self.clearMapButton,10,0,1,1)


def toXYZ(radius,angle,azimuth):

    angle = angle/180.0*math.pi
    azimuth = -azimuth/180.0*math.pi

    x = radius * math.sin(angle) * math.cos(azimuth)
    y = radius * math.sin(angle) * math.sin(azimuth)
    z = radius * math.cos(angle)

    return [x,y,z]

def toXYZ2(radius,azimuth,angle,posx,posy):

    angle = angle/180.0*math.pi
    azimuth = -azimuth/180.0*math.pi

    x = posx + radius * math.sin(angle) * math.cos(azimuth)
    y = posy + radius * math.sin(angle) * math.sin(azimuth)
    z = radius * math.cos(angle)

    return [x,y,z]
    
def parse_data():
    file_name = 'pokoj2904.txt'
    data = open('raw_scans/' + file_to_open,'r+')

    
    datasets = []
    xyz_data = []
    actual_angle = 0
    actual_num_of_points = 0
    actual_dataset = []

    for line in data.readlines():
    
        # if '###' in line: #WERSJA .TXT
        #     if len(actual_dataset) > 0:
        #         datasets.append(actual_dataset)
        #     actual_dataset = []
        #     latest_angle = 0
        #     latest_dist = 0
        # if '#Angle' in line:
        #     global last_angle
        #     angle_line = (line.replace('#Angle: ',''))
        #     actual_angle = float(angle_line)
        #     actual_dataset.append(actual_angle)
        #     last_angle = actual_angle

        # if '#' not in line:
        #     dist_line = line.split(',')
        #     if len(dist_line) == 2:
        #         xyz_data.append(toXYZ(float(dist_line[1]),actual_angle,float(dist_line[0])))
        #     else:
        #         xyz_data.append(toXYZ(float(dist_line[2]),actual_angle,float(dist_line[1])))

        point = json.loads(line) #WERSJA JSON
        newpoints.append(toXYZ2(float(point['distance']),
                            float(point['angle']),
                            float(point['azimuth']),
                            int(point['posX']),
                            int(point['posY'])
        ))

    xyz_file = open('xyz_scans/' + file_name,'w+')


    for xyz in xyz_data:
        xyz_file.write(str(xyz[0]) + ', ' + str(xyz[1]) + ', ' + str(xyz[2]) + '\n')


    xyz_file.close()

def get_points():




    file_to_open = input('Podaj nazwe pliku do otworzenia...\n')
    f = open('xyz_scans/' + file_to_open,'r')

    points = []
    if 'json' in file_to_open:
        data = json.load(f)
        for point in data['point']:

            pos = toXYZ(float(point['distance']),float(point['azimuth']),float(point['angle']))
            points.append(pos)
        

    else:

        data = f.readlines()
        for line in data:
            if '{' not in line:
                point = line.replace('\n','').split(',')
                pos = [float(point[0]),float(point[1]),float(point[2])]
            # if pos[0] > -1500: #SUFIT: pos[0] > -1500, ŚCIANA BOK -> pos[2] > -500
            # if pos[0] != 0.0:
                points.append(pos)

            # dist = sqrt( np.pow(0-pos[0],2) + np.pow(0-pos[1],2) + np.pow(0-pos[2],2))
            # colors.append((1.0*dist/12000,1.0*dist/12000,1.0*dist/12000,1)
            # if pos[0] > -1200:
            #     points.append(pos)
            else:

                point = json.loads(line)
                points.append(toXYZ2(float(point['distance']),
                                float(point['angle']),
                                float(point['azimuth']),
                                int(point['posX']),
                                int(point['posY'])
                ))

    f.close()
    print('ilosc punktow: ' +  str(len(points)))
    return np.array(points)

def get_colors(points):

    colors = []
    sizes = []
    for pos in points:
        dist = float(np.sqrt( pow(0-pos[0],2) + pow(0-pos[1],2) + pow(0-pos[2],2)))
        sizes.append(2.0 + 3*dist/12000.0)
        # sizes.append(4000.0/dist*3)
        # print(dist)
        # colors.append((1.0*dist/12000.0,1.0*dist/12000.0,1.0*dist/12000.0,1))
        if dist > 4000:
            r = 0
            g = 1
            b = 0
            a = 1
        else:
            r = (4000.0 - dist)/4000.0
            g = dist/4000.0
            b = 0
            a = 1

        colors.append((r,g,b,a))

    return colors,sizes


def add_points(points,scatter):

    #colors,sizes = get_colors(points)

    if len(points) > 0:
        #scatter.set_data(points, edge_color=None, face_color=colors, size=sizes)
        scatter.set_data(points, edge_color=None, face_color=(1,1,1,1), size=2.5)




def vispy_setup(w,refresh=False):

    
    view = w.central_widget.add_view()
    view.camera = scene.cameras.fly.FlyCamera(fov=60)
    scene.cameras.fly.FlyCamera.auto_roll = False


    axis = scene.visuals.XYZAxis(parent=view.scene)
    transform = MatrixTransform()
    transform.scale((1000, 1000, 1000))
    axis.transform = transform

    scatter = scene.visuals.Markers()
    view.add(scatter)



    return scatter

def add_points_to_view(scatter):

    points = get_points()
    points = np.around(points,2)


    timer = app.Timer()
    timer.connect(add_points(points,scatter))
    timer.start(0)

def window():

    qtapp = QApplication(sys.argv)
    win = QMainWindow()
    win.setCentralWidget(vis.native)

    win.setGeometry(0,0,500,500)
    win.setWindowTitle('Lidar Visualizer - Mateusz Górski')

    win.show()
    vispy.app.run()
    sys.exit(qtapp.exec())

def main():



    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_DontCreateNativeWidgetSiblings)
    w = MainWindow()
    scatter = vispy_setup(w.get_map())
    add_points_to_view(scatter)
    w.GUI()
    w.show()
    sys.exit(app.exec_())


    
    #region DEBUG

    # w.LidarInfoConsole.append('Czekam na robota...') 
    # print('Czekam na robota...')
    # data, address = UDP.recvfrom(1024)
    # msg = data.decode('utf-8')
    # print('ROBOT: ' + msg)

    # cmd = 'START'
    # UDP.sendto(cmd.encode('utf-8'),address)
    
    # while True:
    #     data, address = UDP.recvfrom(1024)
    #     msg = data.decode('utf-8')
    #     if 'NEWANGLE' in msg:
    #         if receive_file(UDP) is True:
    #             print('received points, parsing...')
    #             parse_data()
    #             print('rendering points...')
    #             add_points_to_view(scatter)
    #             cmd = 'RECEIVED'
    #             UDP.sendto(cmd.encode('utf-8'),address)

    #     else:
    #         break


        # if receive_file(UDP) is True:
        #     parse_data()
        #     add_points_to_view(scatter)
        #     print('receiving...')

        # else:
        #     print('no data...')
            
    # vis = vispy.app.Canvas()


    
    # qtapp = QApplication(sys.argv)
    # win = QMainWindow()
    # win.setCentralWidget(vis.native)

    # win.setGeometry(0,0,500,500)
    # win.setWindowTitle('Lidar Visualizer - Mateusz Górski')
    # win.show()

    # vispy.app.run()

    # sys.exit(qtapp.exec())
    #endregion

main()


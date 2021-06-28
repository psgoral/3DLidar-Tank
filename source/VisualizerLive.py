from threading import Thread
import time
import socket
import json
import numpy as np
import math
from vispy import app, visuals,scene,use
from vispy.visuals.transforms import STTransform
from vispy.visuals.transforms.linear import MatrixTransform
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QPushButton, QWidget,QFrame,QVBoxLayout,QTextEdit,QGridLayout, QLineEdit,QApplication
from PyQt5.QtGui import QPainter, QColor, QFont

import sys
import os



HOST = '192.168.0.110'
PORT = 5005

points = []



class Canvas(scene.SceneCanvas):
    def __init__(self):
        scene.SceneCanvas.__init__(self, keys='interactive',size=(1600, 900),autoswap=True,vsync=True) #show=True,create_native=True
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.view.camera = scene.cameras.fly.FlyCamera(fov=60,interactive='True')
        scene.cameras.fly.FlyCamera.auto_roll = False
        axis = scene.visuals.XYZAxis(parent=self.view.scene)
        transform = MatrixTransform()
        transform.scale((1000, 1000, 1000))
        axis.transform = transform
        self.n_points = 0
        self._timer = app.Timer(interval=1.0/60.0,connect=self.on_timer, start=True)
        self.freeze()

    def lidar_render(self):
        global points
        cloud = scene.visuals.Markers()
        cloud.set_data(points, edge_color=None, face_color=(1,1,1,1), size=2.5)
        self.view.add(cloud)
        self.n_points += len(points)

        print('Aktualna liczba punktów:\t' + str(self.n_points))
        points = []
        return True
    
    def on_timer(self,event):
        if len(points) == 0:
            return False
        else:
            self.lidar_render()


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        # self.resize(1920,1080)
        self.resize(1600,900)
        self.setWindowTitle('Lidar Visualizer')
        self.setStyleSheet("background-color: rgb(0,0,0);")


        self.MapCanvas = Canvas()
        self.MapCanvas.create_native()
        self.MapCanvas.native.setParent(self)


        self.setCentralWidget(self.MapCanvas.native)


def toXYZ(radius,azimuth,angle,posx,posy):

    angle = angle/180.0*math.pi
    azimuth = -azimuth/180.0*math.pi

    x = posx + radius * math.sin(angle) * math.cos(azimuth)
    y = posy + radius * math.sin(angle) * math.sin(azimuth)
    z = radius * math.cos(angle)

    return [x,y,z]


def _tcp_thread(output_file):
    while True:
        print('connected!')
        json_string = ''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            while True:
                data = conn.recv(4096).decode('utf-8')
                print(data)
                if len(data) != 0:
                    json_string += data
                else:
                    break
            newpoints = []
            json_lines = json_string.split('&')
            if len(json_lines) > 2:
                for line in json_lines:
                    if '}' in line:
                        output_file.write(line + '\n')
                        point = json.loads(line)
                        newpoints.append(toXYZ(float(point['distance']),
                                            float(point['angle']),
                                            float(point['azimuth']),
                                            int(point['posX']),
                                            int(point['posY'])
                        ))
                                            
                print('Pobrano ' + str(len(newpoints)) + ' punktów!')
            global points
            points = np.array(newpoints)
            json_string = ''
            s.close()   




def _gui_thread(w):
    w.show()
    return True



def main():

    output_file_name = input('podaj nazwe pliku wyjsciowego...')
    output_file = open('xyz_lives/' + output_file_name,'w+')


    qtapp = QApplication(sys.argv)
    qtapp.setAttribute(QtCore.Qt.AA_DontCreateNativeWidgetSiblings)
    w = MainWindow()
    tcp_thread = Thread(target = _tcp_thread,args=(output_file,),daemon=True)
    tcp_thread.start()
    w.show()
    sys.exit(qtapp.exec_())
    output_file.close()

if __name__ == '__main__':
    main()
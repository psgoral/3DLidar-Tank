import socket
from rplidar import RPLidar, RPLidarException
import time
import serial
import gpiozero
import RPistepper as stp

M1_pins = [6, 13, 19, 26] #gimbal pod 360
M1 = stp.Motor(M1_pins) #gimbal pod 360, stepper object

UDP_IP = "192.168.0.110"
UDP_PORT = 5005

UDP_INFO = (UDP_IP,UDP_PORT)

start_pwm = 210

STEPPER_ANGLE = 0.3515625

def connect_360lidar():

    lidar = RPLidar('/dev/ttyUSB0',baudrate=115200,timeout=1)
    info = lidar.get_info()
    print(info)

    health = lidar.get_health()
    print(health)
    
    
    
    return lidar


def disconnect_360lidar(lidar):



    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()


def scan_lidar360(lidar,min_points):


    while True:
        try:
            for i, scan in enumerate(lidar.iter_scans(max_buf_meas=5000,min_len=1)):
                print('Got %d measurments' % (len(scan)))
                if len(scan) > min_points:
                    break

        except RPLidarException as err:
            global start_pwm
            start_pwm += 1
            print('pwm ustwione na ' + str(start_pwm))
            lidar.set_pwm(start_pwm)
            time.sleep(1)

    print(scan)

    return scan


    # for scan in lidar.iter_scans():
    #     print(scan)


def scan_points(lidar,min_points):

    points = []

    try:
        print('Recording measurments... Press Crl+C to stop.')
        for measurment in lidar.iter_measurments():

            angle = measurment[2]
            distance = measurment[3]
            #print(str(angle) + ' , ' + str(distance))
            if distance > 1:
                points.append(str(360-angle) + ',' + str(distance)) #minus angle ponieważ jest do góry nogami
            # line = '\t'.join(str(v) for v in measurment)
            # print(line)
            if len(points) == min_points:
                break

    except KeyboardInterrupt:
        print('Stoping.')


    return points

    



def connect_UDP():


    UDP = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP


    return UDP


def receive(UDP):

    try:
        UDP = connect_UDP()
        UDP.bind(UDP_INFO)
    finally:

        data, addr = UDP.recvfrom(1024) # buffer size is 1024 bytes
        print("received message: %s" % data)

    UDP.close()

    return str(data)


def send(UDP,message):

    global UDP_IP,UDP_PORT
    
    UDP.sendto(message,UDP_INFO)


def send_scan(UDP,scan):

    UDP.sendto(str.encode('NEWANGLE'),UDP_INFO)
    time.sleep(0.5)

    temp_file = open('temp_file.txt','w+')
    temp_file.write(scan)
    temp_file.close()

    temp_file = open('temp_file.txt','r+')
    data = temp_file.read(1024)
    while (data):
        UDP.sendto(str.encode(data),UDP_INFO)
        data = temp_file.read(1024)
        # time.sleep(0.05)
    print('KONIEC')
    temp_file.truncate(0)

    temp_file.close()
    
    # # data = scan.read(1024)



    # lines = scan.split('\n')
    # for line in lines:
    #     UDP.sendto(str.encode(line + '\n'),UDP_INFO)
    #     # data = file.read(1024)
    # print('Success! Scan sent!')


    return True
# def write_line_to_file(file,line):
#     file.write(line)




def main():

    lidar = connect_360lidar()

    # M1.move(1024)
    # M1.release()

    #region old
    # UDP.sendto(str.encode('READY'),UDP_INFO)

    # f = open('testtesttest' + '.txt','w+')
    # while True:
    #     print('Czekam na komende...')

    #     data, address = UDP.recvfrom(1024)
    #     msg = data.decode('utf-8')
    #     if msg == 'START':
    #         for x in range(512):
    #             while True:
    #                 try:
    #                     points = scan_points(lidar,2000)
    #                     f.write("#" * 50 + '\n')
    #                     live_scan = "#" * 50 + '\n'
    #                     f.write('#Angle: ' + str(x * STEPPER_ANGLE) + '\n')
    #                     live_scan = live_scan + str(x * STEPPER_ANGLE) + '\n'
    #                     for line in points:
    #                         f.write(str(line) + '\n')
    #                         live_scan = live_scan + str(line) + '\n'
    #                     print(str(x * STEPPER_ANGLE) + 'done!')
    #                     M1.move(4)
    #                     M1.release()
    #                     print('Sending scan...')
    #                     print(live_scan)
    #                     if send_scan(UDP,live_scan) is True:
    #                         data, address = UDP.recvfrom(1024)
    #                         msg = data.decode('utf-8')
    #                         if msg == 'RECEIVED':
    #                             time.sleep(3)
    #                             break
    #                 except RPLidarException:
    #                     print('clearing buffer...')
    #                     lidar.stop()
    #                     time.sleep(0.5)
        

    # M1.move(1024)
    # M1.release()
    #endregion
    time.sleep(1)

    filename = input('Podaj nazwe pliku (bez .txt)...')
    f = open('360lidar/' + filename + '.txt','w+')

    time.sleep(10)
    for x in range(0,1024,2):
        while True:
            try:
                points = scan_points(lidar,1000)
                f.write("#" * 50 + '\n')
                # live_scan = "#" * 50 + '\n'
                f.write('#Angle: ' + str(x * (STEPPER_ANGLE/2.0)) + '\n')
                # live_scan = live_scan + str(x * STEPPER_ANGLE) + '\n'
                for line in points:
                    f.write(str(line) + '\n')
                    # live_scan = live_scan + str(line) + '\n'
                print(str(x * (STEPPER_ANGLE/2.0)) + 'done!\t' + str(len(points)) + ' points!')
                M1.move(2)
                M1.release()
                time.sleep(0.5)
                M1.move(2)
                M1.release()
                time.sleep(0.5)
                break
            except RPLidarException:
                print('clearing buffer...')
                lidar.stop()
                time.sleep(0.5)

    M1.move(1024)
    M1.release()




    disconnect_360lidar(lidar)



if __name__ == '__main__':

    try:
        main()

    except KeyboardInterrupt:

        lidar = connect_360lidar
        disconnect_360lidar(lidar)
        exit()


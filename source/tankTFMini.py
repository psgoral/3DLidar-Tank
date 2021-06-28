import serial
import time
import json
import gpiozero
import RPi.GPIO as GPIO
import socket




GPIO.setmode(GPIO.BCM)

Azymuth_pins = [6, 13, 19, 26] #gimbal pod 360
# # azymuth_gimbal = stp.Motor(Azymuth_pins,delay=0.005) #gimbal pod 360, stepper object

Angle_pins = [12, 16, 20, 21] #gimbal pod 360
# # angle_gimbal = stp.Motor(Angle_pins,delay=0.005) #gimbal pod 360, stepper object


for pin in Azymuth_pins:
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin, False)
for pin in Angle_pins:
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin, False)

sequence = [[1,0,0,1],
        [1,0,0,0],
        [1,1,0,0],
        [0,1,0,0],
        [0,1,1,0],
        [0,0,1,0],
        [0,0,1,1],
        [0,0,0,1]
        ]
delay = 0.0015

ser = serial.Serial(
    # port='/dev/ttyS0',  # Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
    # port='/dev/ttyAMA0',  # Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
    port='/dev/serial0',  # Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0

    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0
)
HOST = '192.168.0.110'    # The remote host
PORT = 2137    



def tfRead():

    HEADER = 59
    dist = 0
    for x in range(3):
        while True:
            hexes = []
            if str(HEADER) in ser.read().hex():
                hexes.append(HEADER)
                if str(HEADER) in ser.read().hex():
                    hexes.append(HEADER)
                    for x in range(7):
                        chunk = ser.read().hex()
                        hexes.append(chunk)
                    try:
                        distance = int(hexes[2], 16) + int(hexes[3], 16) * 256.0
                        dist += distance
                        strength = int(hexes[4], 16) + int(hexes[5], 16) * 256
                        temp = int(hexes[6], 16) + int(hexes[7], 16) * 256
                        temp = (temp / 8) - 256
                        ser.flushInput()
                        ser.flushOutput()
                        break
                    except ValueError:
                        print('value error' + str(hexes))
                        ser.flushInput()
                        ser.flushOutput()
                        time.sleep(0.2)
                        continue
    out = {
        'bytes': hexes,
        'distance': dist/3,
        'strength': strength,
        'temp': temp
    }

    return out

def move(stepper,stepCounter,stepDir,steps):

    for x in range(steps):
        for pin in range(0, 4):
            xpin = stepper[pin]
            if sequence[stepCounter][pin]!=0:
                # print('Enable GPIO'  + str(xpin))
                GPIO.output(xpin, True)
            else:
                GPIO.output(xpin, False)
        time.sleep(delay)
        
        stepCounter += stepDir

        if (stepCounter>=len(sequence)):
            stepCounter = 0
        if (stepCounter<0):
            stepCounter = len(sequence)+stepDir

    return stepCounter

def serial_read():
    # values = bytearray([0x5A, 0x04, 0x02, 0x60])
    while True:
        respond = ser.read(1).hex()
        print(str(respond))
        if len(str(respond)) < 2:
            print('gowno')
            # ser.write(values)
            ser.write(b'\x5A\x04\x01\x5F')



def send_scan(data):
    start = time.time()
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((HOST, PORT))
            s.sendall(data.encode())
            break
        except socket.timeout or  socket.error:
            print('timeout')
            continue

    s.close()
    end = time.time()
    print('Wysłano! Czas wysyłania: ' + str(end - start))


def get_dist(dist1,dist2,dist3):
    return (dist1+dist2+dist3)/3
def main():

    direction = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

    AzymuthCounter = 0
    AngleCounter = 0
    angle_step = 360.0/4096.0
    json_points = ''

    for angle in range(0,512): #obrot angle
        actual_angle =  round(angle_step * angle* 4,6)
        json_points = ''
        # for azymuth in range(2048): #3/4 obrotu 
        for azymuth in range(0,256): #3/4 obrotu 
            tfdata = tfRead()
            dist = tfdata.get('distance')
            if dist > 15 and dist < 12000:
                #actual_azimuth = round(azymuth * angle_step*1,4)
                if angle%2  == 0:
                    actual_azimuth = round(azymuth * angle_step*16,6)
                else:
                    actual_azimuth = round((512-azymuth) * angle_step*16,6)
                json_line = '{"distance":' + str(round(dist,4)) + ', "azimuth":' + str(actual_azimuth) + ', "angle":' + str(actual_angle) + ', "posX": 0, "posY": 0}'
                json_points +=json_line + '&'
            if angle%2  == 0:
                AzymuthCounter = move(Azymuth_pins,AzymuthCounter,1,16)
            else:
                AzymuthCounter = move(Azymuth_pins,AzymuthCounter,-1,16)
        send_scan(json_points)

        percent = angle_step/180 * 100
        print(str(actual_angle) + 'deg done\t' + str(percent) + '% done')
        # backward(angle_stepper,delay,1)
        AngleCounter = move(Angle_pins,AngleCounter,1,4)

    send_scan('KONIEC')




main()

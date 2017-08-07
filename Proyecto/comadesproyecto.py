#!/usr/bin/env python
import sys, os
import time
import smbus
import RPi.GPIO as GPIO
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
name = MPI.Get_processor_name()

# ranks:
# 0 = rpi-lania1.local slot=0 ~ Sensor de movimiento : monitoreando sensor
# 1 = rpi-lania2.local slot=0 ~ Sensor de temperatura y humedad : monitoreando sensor
# 2 = rpi-lania2.local slot=1 ~ Sensor de temperatura y humedad : esperando peticiones
# 3 = rpi-lania3.local slot=0 ~ Sensor de distancia : monitoreando sensor
# 4 = rpi-lania3.local slot=1 ~ Sensor de distancia : esperando peticiones
# 5 = rpi-lania4.local slot=0 ~ Camara : esperando peticiones
# 6 = rpi-lania5.local slot=0 ~ Sensor de intensidad luminosa : monitoreando sensor
# 7 = rpi-lania5.local slot=1 ~ Sensor de intensidad luminosa : esperando peticiones

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN)

TRIG=23
ECHO=24
PINBUZZER=18
inicia_pulso=0
termina_pulso=0

GPIO.setup(PINBUZZER, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

if rank == 0:
    # Sensor de movimiento : monitoreando sensor

    while True:
        if GPIO.input(26):
            print name, 'Lectura movimiento'

            # Proceso que hace la peticion
            data_peticion = rank

            comm.send(data_peticion, dest=2, tag=11)
            recv_data = comm.recv(source=2, tag=11)
            print name, 'Temperatura recibida: ', recv_data['temperatura']

            comm.send(data_peticion, dest=4, tag=12)
            recv_data = comm.recv(source=4, tag=12)
            print name, 'Distancia recibida: ', recv_data['distancia']

            comm.send(data_peticion, dest=5, tag=13)
            recv_data = comm.recv(source=5, tag=13)
            print name, 'Status de Operacion:', recv_data['imagen']

            comm.send(data_peticion, dest=7, tag=14)
            recv_data = comm.recv(source=7, tag=14)
            print name, 'Intensidad de Luz:', recv_data['intensidad']

            time.sleep(6)

elif rank == 1:
    # Sensor de temperatura y humedad : monitoreando sensor

    import Adafruit_DHT

    umbral_temperatura = 25.0

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        if temperature > umbral_temperatura:
            print name, 'Lectura temperatura y humedad'

            # Proceso que hace la peticion
            data_peticion = rank

            comm.send(data_peticion, dest=4, tag=12)
            recv_data = comm.recv(source=4, tag=12)
            print name, 'Distancia recibida: ', recv_data['distancia']

            comm.send(data_peticion, dest=5, tag=13)
            recv_data = comm.recv(source=5, tag=13)
            print name, 'Status de Operacion:', recv_data['imagen']

            comm.send(data_peticion, dest=7, tag=14)
            recv_data = comm.recv(source=7, tag=14)
            print name, 'Intensidad de Luz:', recv_data['intensidad']

elif rank == 2:
    # Sensor de temperatura y humedad : esperando peticiones

    import Adafruit_DHT

    while True:
        # Proceso que hizo la peticion
        data_peticion = comm.recv(source=MPI.ANY_SOURCE, tag=11)

        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        data_temp = {'temperatura': temperature, 'humedad': humidity}

        # Enviar respuesta al proceso que hizo la peticion
        comm.send(data_temp, dest=data_peticion, tag=11)

elif rank == 3:
    # Sensor de distancia : monitoreando sensor

    umbral_distancia = 200

    while True:
        #Trigger inicia el pulso
        GPIO.output(TRIG, True)
        #Duracion del pulso 10 micro segundos
        time.sleep(6)
        #Desactiva el pulso
        GPIO.output(TRIG, False)
        #Se guarda el tiempo en segundos
        inicia_pulso = time.time()

        #Muentras la recepcion (echo) este en 0,toma el tiempo del inicio del pulso
        while GPIO.input(ECHO)==0:
            inicia_pulso = time.time()

        #Cuando se reciba el rebote del pulso en echo, se toma el tiempo de final del pulso
        while GPIO.input(ECHO)==1:
            termina_pulso = time.time()
            #Calcular el tiempo que transcurrio
            duracion  = termina_pulso - inicia_pulso

        #Calculo de distancia (tiempo * velocidad del sonido cm/s)/2  **porque es ida y vuelta
        distancia = 0
        distancia = duracion*34300
        distancia= distancia/2

        if distancia <= umbral_distancia:
            print name, 'Lectura distancia'

            # Proceso que hace la peticion
            data_peticion = rank

            comm.send(data_peticion, dest=2, tag=11)
            recv_data = comm.recv(source=2, tag=11)
            print name, 'Temperatura recibida: ', recv_data['temperatura']

            comm.send(data_peticion, dest=5, tag=13)
            recv_data = comm.recv(source=5, tag=13)
            print name, 'Status de Operacion:', recv_data['imagen']

            comm.send(data_peticion, dest=7, tag=14)
            recv_data = comm.recv(source=7, tag=14)
            print name, 'Intensidad de Luz:', recv_data['intensidad']

elif rank == 4:
    # Sensor de distancia : esperando peticiones

    while True:
        # Proceso que hizo la peticion
        data_peticion = comm.recv(source=MPI.ANY_SOURCE, tag=12)

        #Trigger inicia el pulso
        GPIO.output(TRIG, True)
        #Duracion del pulso 10 micro segundos
        time.sleep(6)
        #Desactiva el pulso
        GPIO.output(TRIG, False)
        #Se guarda el tiempo en segundos
        inicia_pulso = time.time()

        #Muentras la recepcion (echo) este en 0,toma el tiempo del inicio del pulso
        while GPIO.input(ECHO)==0:
            inicia_pulso = time.time()

        #Cuando se reciba el rebote del pulso en echo, se toma el tiempo de final del pulso
        while GPIO.input(ECHO)==1:
            termina_pulso = time.time()
            #Calcular el tiempo que transcurrio
            duracion  = termina_pulso - inicia_pulso

        #Calculo de distancia (tiempo * velocidad del sonido cm/s)/2  **porque es ida y vuelta
        distancia = 0
        distancia = duracion*34300
        distancia= distancia/2
        data_temp = {'distancia': distancia}

        # Enviar respuesta al proceso que hizo la peticion
        comm.send(data_temp, dest=data_peticion, tag=12)

elif rank == 5:
    # Camara : esperando peticiones

    import picamera
    import cv2
    from datetime import datetime
    import numpy as np
    import pylab

    while True:
        # Proceso que hizo la peticion
        data_peticion = comm.recv(source=MPI.ANY_SOURCE, tag=13)

        hora = datetime.now().strftime('%H:%M:%S.%F')[:-3]
        camara = picamera.PiCamera()
        camara.capture(hora + ".jpg")
        camara.close()

        ruta = "/home/pi/comades/python/"+str(hora)+".jpg"
        foto = cv2.imread(ruta)
        imgGris = cv2.cvtColor(foto,cv2.COLOR_BGR2GRAY)
        cv2.imwrite("/home/pi/comades/python/gris.png",imgGris)
        data_img = {'imagen': "Foto " + str(hora) + ".jpg tomada con exito"}

        # Enviar respuesta al proceso que hizo la peticion
        comm.send(data_img, dest=data_peticion, tag=13)

elif rank == 6:
    # Sensor de intensidad luminosa : monitoreando sensor

    import smbus
    import time
    DEVICE = 0x23

    ONE_TIME_HIGH_RES_MODE_1 = 0X20
    bus = smbus.SMBus(1)

    def convertToNumber(data):
        return ((data[1] + (256 * data[0])) / 1.2)

    def readLight(addr=DEVICE):
        data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
        return convertToNumber(data)

    umbral_intensidad = 5.0 # modificar a conveniencia

    while True:
        medida = readLight()
        if medida < umbral_intensidad: # modificar a conveniencia
            print name, 'Lectura intensidad luminosa'

            # Proceso que hace la peticion
            data_peticion = rank

            comm.send(data_peticion, dest=2, tag=11)
            recv_data = comm.recv(source=2, tag=11)
            print name, 'Temperatura recibida: ', recv_data['temperatura']

            comm.send(data_peticion, dest=4, tag=12)
            recv_data = comm.recv(source=4, tag=12)
            print name, 'Distancia recibida: ', recv_data['distancia']

            comm.send(data_peticion, dest=5, tag=13)
            recv_data = comm.recv(source=5, tag=13)
            print name, 'Status de Operacion:', recv_data['imagen']
        else:
            readLight()

        time.sleep(0.5)

elif rank == 7:
    # Sensor de intensidad luminosa : esperando peticiones

    import smbus
    import time
    DEVICE = 0x23

    ONE_TIME_HIGH_RES_MODE_1 = 0X20
    bus = smbus.SMBus(1)

    def convertToNumber(data):
        return ((data[1] + (256 * data[0])) / 1.2)

    def readLight(addr=DEVICE):
        data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
        return convertToNumber(data)

    while True:
        # Proceso que hizo la peticion
        data_peticion = comm.recv(source=MPI.ANY_SOURCE, tag=14)

        medida = readLight()
        data = {'intensidad': medida}

        # Enviar respuesta al proceso que hizo la peticion
        comm.send(data, dest=data_peticion, tag=14)

    # time.sleep(6)

GPIO.cleanup()

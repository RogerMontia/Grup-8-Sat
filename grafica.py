import serial
import matplotlib.pyplot as plt
from tkinter import *

device = 'COM3'   # Definimos el puerto conectado a Arduino y iniciamos la comunicación serial a 9600 baudios
mySerial = serial.Serial(device, 9600)

plt.ion()   # Activamos la gráfica interactiva de temperatura 
plt.axis([0,100,0,100])
temperaturas = []
eje_x = []
i = 0
temperaturas = []
eje_x = []
i = 0
plt.ion()   # Activamos la gráfica interactiva de temperatura 
plt.axis([0,100,0,100])


while True:
    if mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8').rstrip() # Recibimos los datos que nos envia el transmisor
        print(linea) 
        trozo = linea.split(':')

        eje_x.append(i)   
        temperatura = float(trozo[1])
        temperaturas.append(temperatura)
        plt.plot(eje_x, temperaturas)
        plt.title(str(i))
        i = i+1
      
        plt.draw()
        plt.pause(0.5)   # Con los datos recibidos, graficamos la temperatura en tiempo real y pausamos la gráfica por 0.5 segundos para que se actualice
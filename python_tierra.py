import serial
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *

# Abrir la comunicacion con el Arduino de tierra
device = 'COM3'   # Definimos el puerto conectado a Arduino y iniciamos la comunicación serial a 9600 baudios
mySerial = serial.Serial(device, 9600)
print("Puerto serie abierto:", mySerial.is_open)

# Variables para controlar la grafica y la lectura de datos
global i
i = 0
funcionando = False
temperaturas = []
eje_x = []
tiempo_inicio = time.time()

# Funcion que se ejecuta al pulsar el boton Iniciar
def IniciarClick():
   global i, funcionando, temperaturas, eje_x, tiempo_inicio

   # Evitar iniciar dos veces la lectura
   if funcionando:
      return

   tiempo_inicio = time.time()

   # Abrir el puerto si estaba cerrado
   if not mySerial.is_open:
      mySerial.open()
      mySerial.reset_input_buffer()   # Elimina los datos que ya hayan llegado antes de iniciar la gráfica

   funcionando = True
   i = 0
   temperaturas = []
   eje_x = []

   ActualizarGrafica()  # Funcion que inicializa la grafica de datos


# Leer los datos del Arduino y actualizar la grafica
def ActualizarGrafica():
   global i, funcionando

   # Si se ha pulsado Parar, dejar de actualizar
   if not funcionando:
      return

   # Comprobar si hay datos disponibles en el puerto serie
   if mySerial.is_open and mySerial.in_waiting > 0:
      linea = mySerial.readline().decode('utf-8').rstrip()

      # Comprobar si el Arduino ha enviado una alarma
      if "ALARMA" in linea:
         print("¡Alarma de comunicación!")
      elif "COMUNICACION_OK" in linea:
         print("Comunicación recuperada")

      else: 
         print(linea)
         trozo = linea.split(':') # Separar la temperatura del resto del mensaje

         if len(trozo) > 1:
            try:
               temperatura = float(trozo[1])
               tiempo = time.time() - tiempo_inicio   # Calcular el tiempo transcurrido desde el inicio
               eje_x.append(tiempo)   # Guardar los datos para dibujarlos
               temperaturas.append(temperatura)

                # Actualizar la linea de la grafica
               linea_grafica.set_data(eje_x, temperaturas)
               ax.relim()
               ax.autoscale_view()
               ax.set_xlim(0, max(100, tiempo + 1))
               canvas.draw_idle()

            except ValueError:
               print("Dato incorrecto:", linea)

   # Volver a ejecutar esta funcion dentro de 20 milisegundos
   window.after(20, ActualizarGrafica)

# Funcion que se ejecuta al pulsar el boton Parar
def PararClick():
   global funcionando

   funcionando = False

   # Dejamos un espacio en blanco en la gráfica
   eje_x.append(time.time() - tiempo_inicio)
   temperaturas.append(float('nan'))

   if mySerial.is_open:
      mySerial.close()

# Funcion que se ejecuta al pulsar el boton Reanudar
def ReanudarClick():
   global funcionando

   if funcionando:
      return

   # Volver a abrir el puerto serie si estaba cerrado
   if not mySerial.is_open:
      mySerial.open()

   funcionando = True
   ActualizarGrafica()

# Crear la ventana principal
window = Tk()
window.geometry("700x600")

# Adaptar la grafica y los botones al tamaño que queremos
for fila in range(4):
    window.rowconfigure(fila, weight=1)

for columna in range(5):
    window.columnconfigure(columna, weight=1)

# Crear los botones de la interfaz
IniciarButton = Button(window, text = "Iniciar",bg="#01f960", fg="black", command=IniciarClick)
IniciarButton.grid(row=0, column=0,columnspan = 5, padx=5, pady=5, sticky=N + S + E + W)
PararButton = Button(window, text="Parar", bg="#ff0095", fg="white",command=PararClick)
PararButton.grid(row=1, column=0,columnspan = 5, padx=5, pady=5, sticky=N + S + E + W)
ReanudarButton = Button(window, text="Reanudar", bg="#196ac7", fg="black",command=ReanudarClick)
ReanudarButton.grid(row=2, column=0,columnspan = 5, padx=5, pady=5, sticky=N + S + E + W)

# Crear la figura y configurar los ejes
fig = Figure(figsize=(6, 4))
ax = fig.add_subplot(111)
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("Temperatura (ºC)")

# Crear una linea vacia que se ira actualizando
linea_grafica, = ax.plot([], [])  

# Colocar la grafica dentro de la ventana
ax.set_ylim(0, 50)
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().grid(row=3, column=0, columnspan=5, padx=5, pady=5, sticky=N+S+E+W)

# Mantener la ventana abierta
window.mainloop()

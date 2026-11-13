import serial
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *

# Abrir la comunicacion con el Arduino de tierra
device = 'COM3'
mySerial = serial.Serial(device, 9600)

# Variables para controlar la grafica
funcionando = False
temperaturas = []
eje_x = []

tiempo_inicio = time.time()
ultimo_latido = time.time()
alarma_latido = False


# Funcion para iniciar
def IniciarClick():
    global funcionando, temperaturas, eje_x
    global tiempo_inicio, ultimo_latido, alarma_latido

    if funcionando:
        return

    tiempo_inicio = time.time()
    temperaturas = []
    eje_x = []

    linea_grafica.set_data([], [])
    ax.set_xlim(0, 10)
    canvas.draw_idle()

    mySerial.reset_input_buffer()
    mySerial.write(b'INICIAR\n')

    ultimo_latido = time.time()
    alarma_latido = False
    funcionando = True


# Funcion para actualizar la grafica y comprobar el latido
def ActualizarGrafica():
    global funcionando, ultimo_latido, alarma_latido

    # Comprobar si hay mensajes del Arduino
    if mySerial.is_open and mySerial.in_waiting > 0:

        linea = mySerial.readline().decode('utf-8').strip()

        # Si recibimos un latido
        if linea == "1":
            ultimo_latido = time.time()
            alarma_latido = False

        # Si recibimos temperatura y humedad
        elif linea.startswith("2:"):

            if funcionando:
                trozo = linea.split(':')

                try:
                    temperatura = float(trozo[1])
                    humedad = float(trozo[2])

                    print("Temperatura:", temperatura, "Humedad:", humedad)

                    tiempo = time.time() - tiempo_inicio

                    temperaturas.append(temperatura)
                    eje_x.append(tiempo)

                    # Actualizar la grafica
                    linea_grafica.set_data(eje_x, temperaturas)

                    # Adaptar el eje X al tiempo
                    if tiempo > 10:
                        ax.set_xlim(0, tiempo + 1)
                    else:
                        ax.set_xlim(0, 10)

                    canvas.draw_idle()

                except (ValueError, IndexError):
                    print("Dato incorrecto:", linea)

        # Si recibimos distancia
        elif linea.startswith("3:"):
            if funcionando:
                trozo = linea.split(':')

                try:
                    distancia = float(trozo[1])
                    print("Distancia:", distancia)
                except (ValueError, IndexError):
                    print("Dato incorrecto:", linea)

        # Si recibimos una alarma
        elif "ALARMA" in linea:
            print("Alarma de comunicacion")

        # Si recuperamos la comunicacion
        elif "COMUNICACION_OK" in linea:
            print("Comunicacion recuperada")

    # Comprobar si han pasado mas de 5 segundos sin recibir latido
    if time.time() - ultimo_latido > 5 and not alarma_latido:
        print("¡Alarma! No se recibe el latido")
        alarma_latido = True

    # Seguir comprobando los mensajes aunque la grafica este parada
    window.after(20, ActualizarGrafica)


# Funcion para parar la grafica
def PararClick():
    global funcionando

    if not funcionando:
        return

    funcionando = False

    # Crear un espacio en blanco en la grafica
    eje_x.append(time.time() - tiempo_inicio)
    temperaturas.append(float('nan'))

    linea_grafica.set_data(eje_x, temperaturas)
    canvas.draw_idle()

    mySerial.write(b'PARAR\n')


# Funcion para reanudar la grafica
def ReanudarClick():
    global funcionando

    if funcionando:
        return

    mySerial.write(b'REANUDAR\n')
    funcionando = True


# Crear la ventana principal
window = Tk()
window.geometry("700x600")

# Adaptar la grafica y los botones al tamaño que queremos
for fila in range(4):
    window.rowconfigure(fila, weight=1)

for columna in range(5):
    window.columnconfigure(columna, weight=1)

# Crear los botones de la interfaz
IniciarButton = Button(window, text="Iniciar", bg="#01f960", fg="black", command=IniciarClick)
IniciarButton.grid(row=0, column=0, columnspan=5, padx=5, pady=5, sticky=N + S + E + W)

PararButton = Button(window, text="Parar", bg="#ff0095", fg="white", command=PararClick)
PararButton.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky=N + S + E + W)

ReanudarButton = Button(window, text="Reanudar", bg="#196ac7", fg="black", command=ReanudarClick)
ReanudarButton.grid(row=2, column=0, columnspan=5, padx=5, pady=5, sticky=N + S + E + W)

# Crear la figura y configurar los ejes
fig = Figure(figsize=(6, 4))
ax = fig.add_subplot(111)
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("Temperatura (ºC)")

# Crear una linea vacia que se ira actualizando
linea_grafica, = ax.plot([], [])

# Configurar el eje Y
ax.set_ylim(0, 50)
ax.set_xlim(0, 10)

# Colocar la grafica dentro de la ventana
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().grid(row=3, column=0, columnspan=5, padx=5, pady=5, sticky=N+S+E+W)

# Empezar a comprobar los mensajes del Arduino
window.after(20, ActualizarGrafica)

# Mantener la ventana abierta
window.mainloop()

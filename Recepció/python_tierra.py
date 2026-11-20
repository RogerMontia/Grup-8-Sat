import serial
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter import messagebox

# Abrir comunicacion con Arduino de tierra
device = 'COM3'
mySerial = serial.Serial(device, 9600, timeout=0.1)

# Variables generales
funcionando = False
monitor_activo = False
temperaturas = []
eje_x = []
ultimas_temperaturas = []
medias = []
tiempos_medias = []
tiempo_inicio = time.time()
ultimo_latido = time.time()
alarma_latido = False
modo_calculo = 0  # Modo 0: calculo en tierra  Modo 1: calculo en satelite
limite = 30   
medias_superiores = 0  # Para el calculo de las medias de temperatura
alarma_temperatura_activa = False
modoRadar = 0  # 1: Rastreo, 0: Orientacion fija
ultimo_angulo_radar = None
direccion_radar = 0
cambios_sentido_radar = 0


# FUNCION PARA ACTUALIZAR LOS EJES
def ActualizarEjes(tiempo):
    if tiempo > 10:
        ax_temp.set_xlim(0, tiempo + 1)
        ax_media.set_xlim(0, tiempo + 1)
    else:
        ax_temp.set_xlim(0, 10)
        ax_media.set_xlim(0, 10)


# FUNCION PARA REGISTRAR Y COMPROBAR CADA MEDIA
def RegistrarMedia(media, tiempo):
    global medias_superiores, alarma_temperatura_activa
    medias.append(media)
    tiempos_medias.append(tiempo)
    linea_grafica_media.set_data(tiempos_medias, medias) # Actualizar la grafica de temperatura media
    ActualizarEjes(tiempo)
    canvas_media.draw_idle()

    # Comprobar el limite de temperatura
    if media > limite:
        medias_superiores += 1
        if medias_superiores >= 3 and not alarma_temperatura_activa:
            alarma_temperatura_activa = True
            messagebox.showwarning(
                "Alarma de temperatura",
                "¡ALERTA! Se han detectado tres medias consecutivas superiores al limite."
            )
    else:
        medias_superiores = 0
        alarma_temperatura_activa = False


# FUNCION PARA EL BOTON INICIAR
def IniciarClick():
    global funcionando, monitor_activo
    global temperaturas, eje_x
    global ultimas_temperaturas, medias, tiempos_medias
    global tiempo_inicio, ultimo_latido, alarma_latido
    global medias_superiores, alarma_temperatura_activa
    global modo_calculo

    if funcionando:
        return

    # Reiniciar datos
    temperaturas = []
    eje_x = []
    ultimas_temperaturas = []
    medias = []
    tiempos_medias = []
    medias_superiores = 0
    alarma_temperatura_activa = False
    tiempo_inicio = time.time()
    ultimo_latido = time.time()
    alarma_latido = False
    monitor_activo = True

    modo_calculo = modo_var.get()

    # Limpiar las dos graficas
    linea_grafica.set_data([], [])
    linea_grafica_media.set_data([], [])
    ax_temp.set_xlim(0, 10)
    ax_media.set_xlim(0, 10)
    canvas_temp.draw_idle()
    canvas_media.draw_idle()

    # Enviar modo de calculo y reanudar temperatura
    mySerial.write(("5:" + str(modo_calculo) + "\n").encode('utf-8'))
    mySerial.write(b'INICIAR\n')

    funcionando = True


# FUNCION PARA EL BOTON PARAR
def PararClick():
    global funcionando
    if not funcionando:
        return
    funcionando = False

    # Crear un espacio en blanco en las graficas
    tiempo = time.time() - tiempo_inicio
    eje_x.append(tiempo)
    temperaturas.append(float('nan'))
    tiempos_medias.append(tiempo)
    medias.append(float('nan'))

    linea_grafica.set_data(eje_x, temperaturas)
    linea_grafica_media.set_data(tiempos_medias, medias)
    canvas_temp.draw_idle()
    canvas_media.draw_idle()

    # Parar solamente el envio de temperatura
    mySerial.write(b'PARAR\n')


# FUNCION PARA EL BOTON REANUDAR
def ReanudarClick():
    global funcionando
    if funcionando:
        return
    mySerial.write(b'REANUDAR\n')
    funcionando = True


# FUNCIONES DE CONFIGURACION
def AplicarTodo():
    global modo_calculo, limite
    global ultimas_temperaturas
    global medias_superiores, alarma_temperatura_activa
    global modoRadar

    try:
        nuevo_limite = float(entrada_limite.get())
        nuevo_periodo = int(entrada_periodo.get())
        nueva_orientacion = int(entrada_orientacion.get())
        nuevo_periodo_distancia = int(entrada_periodo_distancia.get())
        nuevo_modo = modo_var.get()
        modoRadar = radar_var.get()

        if nuevo_periodo <= 0 or nuevo_periodo_distancia <= 0:
            messagebox.showerror("Error", "Los periodos deben ser mayores que cero.")
            return

        if not 0 <= nueva_orientacion <= 180:
            messagebox.showerror("Error", "La orientacion debe estar entre 0 y 180 grados.")
            return

        limite = nuevo_limite

        # Comprobar si cambia el modo de calculo
        if nuevo_modo != modo_calculo:
            ultimas_temperaturas = []
            medias_superiores = 0
            alarma_temperatura_activa = False
            modo_calculo = nuevo_modo

        # Enviar configuracion al satelite
        mySerial.write(("5:" + str(modo_calculo) + "\n").encode())
        mySerial.write(("1:" + str(nuevo_periodo) + "\n").encode())
        mySerial.write(("2:" + str(nueva_orientacion) + "\n").encode())
        mySerial.write(("7:" + str(modoRadar) + "\n").encode())
        mySerial.write(("8:" + str(nuevo_periodo_distancia) + "\n").encode())

        print("Configuracion aplicada")
        print("Limite:", limite)
        print("Modo de calculo:", modo_calculo)
        print("Periodo temperatura:", nuevo_periodo)
        print("Orientacion:", nueva_orientacion)
        print("Modo radar:", modoRadar)
        print("Periodo distancia:", nuevo_periodo_distancia)

    except ValueError:
        messagebox.showerror("Error", "Introduce valores numericos validos.")


# FUNCION PARA RECIBIR Y PROCESAR MENSAJES
def ActualizarGrafica():
    global ultimo_latido, alarma_latido
    global ultimas_temperaturas
    global ultimo_angulo_radar, direccion_radar, cambios_sentido_radar
    global radar_angulos, radar_distancias

    if mySerial.is_open and mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8').strip()
        if linea != "":
            trozos = linea.split(':')
            codigo = trozos[0]

            # Temperatura y humedad
            if codigo == "1":
                if funcionando:
                    try:
                        temperatura = float(trozos[1])
                        humedad = float(trozos[2])
                        print("Temperatura:", temperatura, "Humedad:", humedad)

                        tiempo = time.time() - tiempo_inicio
                        temperaturas.append(temperatura)
                        eje_x.append(tiempo)

                        # Actualizar grafica de temperatura
                        linea_grafica.set_data(eje_x, temperaturas)
                        ActualizarEjes(tiempo)
                        canvas_temp.draw_idle()

                        # Calcular media en tierra si se ha seleccionado
                        if modo_calculo == 0:
                            ultimas_temperaturas.append(temperatura)
                            if len(ultimas_temperaturas) > 10:
                                ultimas_temperaturas.pop(0)
                            if len(ultimas_temperaturas) == 10:
                                media = sum(ultimas_temperaturas) / 10
                                RegistrarMedia(media, tiempo)

                    except (ValueError, IndexError):
                        print("Dato de temperatura incorrecto:", linea)

            # Distancia
            elif codigo == "2":
                try:
                    angulo = float(trozos[1])
                    distancia = float(trozos[2])
                    print("Angulo:", angulo, "Distancia:", distancia)
                    if distancia >= 0:

                        radar_angulos.append(angulo * 3.14159 / 180)
                        radar_distancias.append(distancia)
                        # Traza amarilla que une los puntos detectados
                        linea_traza_radar.set_data([0] + radar_angulos, [0] + radar_distancias)
                        # Haz verde hasta la ultima deteccion
                        linea_haz_radar.set_data([0, radar_angulos[-1]], [0, distancia])
                        punto_radar.set_data([radar_angulos[-1]], [distancia])
                        canvas_radar.draw_idle()
            
                except (ValueError, IndexError):
                    print("Dato de distancia incorrecto:", linea)

            # Error de temperatura
            elif codigo == "3":
                print("Error al capturar temperatura o humedad")

            # Temperatura media calculada en el satelite
            elif codigo == "4":
                if funcionando and modo_calculo == 1:
                    try:
                        media = float(trozos[1])
                        print("Temperatura media:", media)
                        tiempo = time.time() - tiempo_inicio
                        RegistrarMedia(media, tiempo)
                    except (ValueError, IndexError):
                        print("Dato de media incorrecto:", linea)

            # Latido
            elif codigo == "5":
                ultimo_latido = time.time()
                alarma_latido = False 

            # Reiniciar el radar
            elif codigo == "6":
                radar_angulos = []
                radar_distancias = []

                linea_traza_radar.set_data([], [])
                linea_haz_radar.set_data([], [])
                punto_radar.set_data([], [])

                canvas_radar.draw_idle()
            # Alarma del satelite
            elif codigo == "ALARMA":
                print("ALARMA: Fallo persistente del sensor")
        
            else:
                print("Mensaje desconocido:", linea)


    # Comprobar el latido incluso cuando la grafica esta parada
    if monitor_activo:
        if time.time() - ultimo_latido > 5 and not alarma_latido:
            alarma_latido = True
            messagebox.showwarning(
                "Alarma de comunicacion",
                "No se reciben latidos del satelite."
            )
    # Continuar leyendo mensajes
    window.after(20, ActualizarGrafica)


window = Tk()
window.title("Estacion de tierra")
window.geometry("1000x700")
window.minsize(600, 400)   # Tamaño minimo de la 
window.configure(bg="#f2f4f7") # Color de fondo

# Ajustamos la distribucion de filas y columnas al cambiar el tamaño de la ventana
window.columnconfigure(0, weight=1)
window.rowconfigure(8, weight=1) 


# TITULO 
titulo = Label(window,text="ESTACION DE TIERRA",font=("Arial",20,"bold"),bg="#f2f4f7",fg="#263445")
titulo.grid(row=0,column=0,pady=10,padx=10)


# BOTONES PRINCIPALES
frame_botones = Frame(window, bg="#f2f4f7")
frame_botones.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
for columna in range(3):
    frame_botones.columnconfigure(columna, weight=1, minsize=150) # Damos el mismo espacio a las tres columnas

IniciarButton = Button(frame_botones, text="INICIAR", bg="#28a745", fg="white", command=IniciarClick).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
PararButton = Button(frame_botones, text="PARAR", bg="#e32b44", fg="white", command=PararClick).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ReanudarButton = Button(frame_botones, text="REANUDAR", bg="#196ac7", fg="white", command=ReanudarClick).grid(row=0, column=2, padx=5, pady=5, sticky="ew")


# CONFIGURACION DE DATOS
 
# Agrupamos la configuracion en una cajita
config_frame = LabelFrame(window,text=" CONFIGURACIÓN ",font=("Arial", 12, "bold"),padx=15,pady=12)
config_frame.grid(row=2, column=0, sticky=E+W, padx=20, pady=10)

# Seleccionar donde calcular la media
Label(config_frame, text="Calculo de la media:").grid(row=0, column=0, pady=5, sticky=E+W)
modo_var = IntVar(value=0)
Radiobutton(config_frame, text="En tierra (Python)", variable=modo_var, value=0).grid(row=0, column=1)
Radiobutton(config_frame, text="En el satelite (Arduino)",variable=modo_var, value=1).grid(row=0, column=2)

# Introducir limite de temperatura
Label(config_frame, text="Limite de temperatura (ºC):").grid(row=0, column=4, padx=5, pady=5)
entrada_limite = Entry(config_frame)
entrada_limite.insert(0, "30")
entrada_limite.grid(row=0, column=5)

# Cambiar periodo de temperatura
Label(config_frame, text="Periodo de temperatura (segundos):").grid(row=1, column=4, padx=5, pady=5)
entrada_periodo = Entry(config_frame)
entrada_periodo.insert(3, "5")
entrada_periodo.grid(row=1, column=5)

# Cambiar orientacion
Label(config_frame, text="Orientacion del sensor(grados):").grid(row=2, column=0, padx=5, pady=5)
entrada_orientacion = Entry(config_frame)
entrada_orientacion.insert(0, "90")
entrada_orientacion.grid(row=2, column=1)

# Seleccionar modo del radar
Label(config_frame, text="Modo del radar:").grid(row=1, column=0, padx=5, pady=5)
radar_var = IntVar(value=0)
Radiobutton(config_frame, text="Rastreo automatico",variable=radar_var, value=1).grid(row=1, column=1)
Radiobutton(config_frame, text="Orientacion fija",variable=radar_var, value=0).grid(row=1, column=2)

# Cambiar periodo de distancia
Label(config_frame, text="Periodo de distancia (segundos):").grid(row=2, column=4, padx=5, pady=5)
entrada_periodo_distancia = Entry(config_frame)
entrada_periodo_distancia.insert(0, "5")
entrada_periodo_distancia.grid(row=2, column=5)

# Botón para aplicar todos los cambios
AplicarButton = Button(window, text="Aplicar configuracion", bg="#bb2dee", command=AplicarTodo)
AplicarButton.grid(row=3, column=0, padx=10, pady=10,sticky=E+W)


# ESPACIO PARA LAS GRAFICAS
frame_graficas = Frame(window)
frame_graficas.grid(row=4,column=0,columnspan=5,padx=10,pady=10,sticky=N+S+E+W)
frame_graficas.columnconfigure(0, weight=1, uniform="graficas")
frame_graficas.columnconfigure(1, weight=1, uniform="graficas")
frame_graficas.columnconfigure(2, weight=1, uniform="graficas")


# GRAFICA DE TEMPERATURA
fig_temp = Figure(figsize=(4, 3.5), dpi=100)
fig_temp.subplots_adjust(left=0.22,right=0.97,top=0.83,bottom=0.23)
ax_temp = fig_temp.add_subplot(111)

ax_temp.set_title("Temperatura", fontsize=11, fontweight="bold", pad=25, loc='center')
ax_temp.set_xlabel("Tiempo (s)", fontsize=9)
ax_temp.set_ylabel("Temperatura (ºC)", fontsize=9)
ax_temp.set_ylim(0, 50)
ax_temp.set_xlim(0, 10)
ax_temp.grid(True, alpha=0.3)

linea_grafica, = ax_temp.plot([], [],linewidth=2,color="#e67e22")
canvas_temp = FigureCanvasTkAgg(fig_temp,master=frame_graficas)
canvas_temp.get_tk_widget().grid(row=0, column=0,padx=8, pady=5,sticky=N+S+E+W)

# GRAFICA DE TEMPERATURA MEDIA
fig_media = Figure(figsize=(4, 3.5), dpi=100)
fig_media.subplots_adjust(left=0.22,right=0.97,top=0.83,bottom=0.23)
ax_media = fig_media.add_subplot(111)

ax_media.set_title("Temperatura media (10 medidas)",fontsize=9, fontweight="bold",pad=25, loc='center')
ax_media.set_xlabel("Tiempo (s)", fontsize=9)
ax_media.set_ylabel("Temperatura media (ºC)", fontsize=9)
ax_media.set_ylim(0, 50)
ax_media.set_xlim(0, 10)
ax_media.grid(True, alpha=0.3)
linea_grafica_media, = ax_media.plot([], [])

canvas_media = FigureCanvasTkAgg(fig_media, master=frame_graficas)
canvas_media.get_tk_widget().grid(row=0, column=1, padx=8, pady=5, sticky=N+S+E+W)


# GRAFICA DEL RADAR
fig_radar = Figure(figsize=(4, 3.5), dpi=100)
ax_radar = fig_radar.add_subplot(111, projection='polar')
ax_radar.set_theta_zero_location('E')   # 0º a la derecha
ax_radar.set_theta_direction(1)         # Angulos en sentido antihorario
ax_radar.set_thetamin(0)
ax_radar.set_thetamax(180)
ax_radar.set_thetagrids(range(0, 180, 25))  # 0º, 25º, 50º ... 175º
ax_radar.set_ylim(0, 200)
ax_radar.set_rticks([0, 40, 80, 120, 160, 200])
ax_radar.grid(True)

# Lineas del radar: traza amarilla, haz verde y punto verde
radar_angulos = []
radar_distancias = []
linea_traza_radar, = ax_radar.plot([], [], color='g')
linea_haz_radar, = ax_radar.plot([], [], color='g')
punto_radar, = ax_radar.plot([], [], 'go')

# Aprovechar mejor el espacio disponible
ax_radar.set_position([0.08, 0.08, 0.84, 0.78])
ax_radar.set_title("Radar", fontsize=13, fontweight="bold")

canvas_radar = FigureCanvasTkAgg(fig_radar, master=frame_graficas)
canvas_radar.get_tk_widget().grid(row=0, column=2,padx=5, pady=5,sticky="nsew")


# Iniciar lectura de mensajes
window.after(20, ActualizarGrafica)
window.mainloop()

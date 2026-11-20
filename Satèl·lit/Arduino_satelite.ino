#include <DHT.h>
#include <SoftwareSerial.h>
#include <Servo.h>

//SENSORES Y PINES 

#define DHTPIN 2
#define DHTTYPE DHT11

#define TRIG 4
#define ECHO 5
#define PIN_SERVO 3

DHT dht(DHTPIN, DHTTYPE);

SoftwareSerial tierra(10, 11);
Servo servo;


//  VARIABLES GENERALES 

int cont = 0;
int periodoTH = 3;
int periodoDistancia = 3;
int orientacion = 90;

bool enviandoDatos = false;
bool radarActivo = false;

bool falloDetectado = false;
bool alarmaEnviada = false;

bool modoRastreo = false;
bool calcularMediaSat = false;


//  CONTROL DEL TIEMPO 

unsigned long proximaLectura = 0;
unsigned long momentoAlarma = 0;
unsigned long ultimoLatido = 0;

unsigned long proximaMedicionRadar = 0;
unsigned long proximoMovimientoServo = 0;

const unsigned long intervaloMovimientoServo = 20;
const unsigned long intervaloMedicionRastreo = 400;
int ultimoAnguloOrdenado = -1;

//  VARIABLES DE LA MEDIA 
// Cola circular que almacena las ultimas 10 temperaturas
float ultimasTemperaturasSat[10];

float sumaTemperaturas = 0;
int numeroTemperaturas = 0;

// Indica la posicion donde se guardara la siguiente temperatura
int indiceTemperatura = 0;

//  VARIABLES DEL RADAR 

int anguloRadar = 90;
int direccionRadar = 1;

//  RECEPCION DE COMANDOS 

String comando = "";

//SETUP

void setup() {

    Serial.begin(9600);
    tierra.begin(9600);

    dht.begin();

    // Arranque siempre en modo fijo y a 90 grados
    orientacion = 90;
    anguloRadar = 90;
    modoRastreo = false;
    radarActivo = false;

    // Conectar el servo y llevarlo a su posicion inicial
    servo.attach(PIN_SERVO);
    servo.write(90);
    ultimoAnguloOrdenado = 90;
    delay(700);

    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);

    digitalWrite(TRIG, LOW);

    anguloRadar = orientacion;

    proximaLectura = millis();
    proximaMedicionRadar = millis();

    Serial.println("Arduino satelite iniciado");
}

//LOOP 
void loop() {

    // Recibir comandos desde tierra
RecibirComandos();


    // Enviar latido cada segundo
    if (millis() - ultimoLatido >= 1000) {

        ultimoLatido = millis();

        tierra.println("5:");
    }


    //  TEMPERATURA Y HUMEDAD 

    if (enviandoDatos &&
        (long)(millis() - proximaLectura) >= 0) {

        proximaLectura = millis() + periodoTH * 1000UL;

        float h = dht.readHumidity();
        float t = dht.readTemperature();


        // Comprobar errores del sensor
        if (isnan(h) || isnan(t) || t > 31) {

            if (!falloDetectado) {

                falloDetectado = true;
                alarmaEnviada = false;

                momentoAlarma = millis() + 5000;

                tierra.println("3:");

                Serial.println("Error en el sensor");
            }
        }

        else {

            falloDetectado = false;
            alarmaEnviada = false;


            // Enviar temperatura y humedad
            tierra.print("1:");
            tierra.print(t);
            tierra.print(":");
            tierra.println(h);

            Serial.print("1:");
            Serial.print(t);
            Serial.print(":");
            Serial.println(h);

            // Calcular y enviar la media
            // Calcular y enviar la media de las ultimas 10 temperaturas

        if (calcularMediaSat) {

        // Si todavia no tenemos 10 temperaturas
            if (numeroTemperaturas < 10) {

                ultimasTemperaturasSat[indiceTemperatura] = t;
                sumaTemperaturas += t;
                numeroTemperaturas++;
            }

        // Si ya tenemos 10, sustituimos la temperatura mas antigua
            else {

                sumaTemperaturas -= ultimasTemperaturasSat[indiceTemperatura];
                ultimasTemperaturasSat[indiceTemperatura] = t;
                sumaTemperaturas += t;
            }

        // Avanzar a la siguiente posicion de la cola circular
            indiceTemperatura = (indiceTemperatura + 1) % 10;

        // Calcular y enviar la media cuando tengamos 10 temperaturas
            if (numeroTemperaturas == 10) {

                float media = sumaTemperaturas / 10;

                tierra.print("4:");
                tierra.println(media);

                Serial.print("4:");
                Serial.println(media);
            }

        }
    }
    }


    //  COMPROBAR ALARMA 

    if (falloDetectado && !alarmaEnviada &&
        (long)(millis() - momentoAlarma) >= 0) {

        tierra.println("ALARMA");

        alarmaEnviada = true;

        Serial.println("ALARMA activada");
    }


    //  ACTUALIZAR RADAR 

    ActualizarRadar();

}


// RECIBIR COMANDOS

void RecibirComandos() {

    while (tierra.available() > 0) {

        char caracter = tierra.read();

        if (caracter == '\n') {

            comando.trim();

            if (comando.length() > 0) {

                ProcesarComando(comando);
            }

            comando = "";
        }

        else {

            comando += caracter;
        }
    }
}

// PROCESAR COMANDOS
void ProcesarComando(String mensaje) {

    mensaje.trim();
    //  INICIAR 
    if (mensaje == "INICIAR") {

        enviandoDatos = true;
        radarActivo = true;
        
        proximaLectura = millis();
        proximaMedicionRadar = millis();
        if (modoRastreo) {

            if (!servo.attached()) {
                servo.attach(PIN_SERVO);
            }

            servo.write(anguloRadar);

            proximoMovimientoServo =
                millis() + intervaloMovimientoServo;
        }
        else {

            MoverServoFijo(orientacion);
        }

        Serial.println("Envio y radar iniciados");
    }

    //  PARAR 
    else if (mensaje == "PARAR") {
        enviandoDatos = false;
        radarActivo = false;
       
       Serial.println("Envio y radar parados");
    }

    //  REANUDAR 
    else if (mensaje == "REANUDAR") {

        enviandoDatos = true;
        radarActivo = true;

        proximaLectura = millis();
        proximaMedicionRadar = millis();

        if (modoRastreo) {

            if (!servo.attached()) {
                servo.attach(PIN_SERVO);
            }

            servo.write(anguloRadar);

            proximoMovimientoServo =
                millis() + intervaloMovimientoServo;
        }
        else {

            MoverServoFijo(orientacion);
        }
        Serial.println("Envio y radar reanudados");
    }

    //  COMANDOS NUMERICOS 
    else {

        int separador = mensaje.indexOf(':');

        if (separador == -1) {
            return;
        }

        int codigo = mensaje.substring(0, separador).toInt();
        String dato = mensaje.substring(separador + 1);

        dato.trim();


        // 1: Periodo de temperatura y humedad
        if (codigo == 1) {

            int nuevoPeriodo = dato.toInt();

            if (nuevoPeriodo > 0) {

                periodoTH = nuevoPeriodo;

                proximaLectura = millis();

                Serial.print("Nuevo periodo TH: ");
                Serial.println(periodoTH);
            }
        }


        // 2: Orientacion fija del servo
        else if (codigo == 2) {

            int nuevoAngulo = dato.toInt();

            if (nuevoAngulo >= 0 && nuevoAngulo <= 180) {

                orientacion = nuevoAngulo;

                if (!modoRastreo) {

                    MoverServoFijo(orientacion);
                }

                Serial.print("Nueva orientacion: ");
                Serial.println(orientacion);
            }
        }

        // 5: Modo de calculo de la media
        else if (codigo == 5) {

            int nuevoModo = dato.toInt();

            if (nuevoModo == 0 || nuevoModo == 1) {

                calcularMediaSat = (nuevoModo == 1);

                sumaTemperaturas = 0;
                numeroTemperaturas = 0;
                indiceTemperatura = 0;

                Serial.print("Modo de calculo de media: ");
                Serial.println(nuevoModo);
            }
        }

        // 7: Modo del radar
        else if (codigo == 7) {

            int nuevoModo = dato.toInt();

            if (nuevoModo == 0) {

                modoRastreo = false;

                MoverServoFijo(orientacion);

                Serial.println("RADAR EN MODO FIJO");
            }

            else if (nuevoModo == 1) {

                modoRastreo = true;

                anguloRadar = 0;
                direccionRadar = 1;

                if (!servo.attached()) {
                    servo.attach(PIN_SERVO);
                }

                servo.write(anguloRadar);
                ultimoAnguloOrdenado = anguloRadar;

                proximoMovimientoServo =
                    millis() + intervaloMovimientoServo;

                Serial.println("RADAR EN MODO RASTREO");
            }

            proximaMedicionRadar = millis();
        }

        // 8: Periodo de medicion del radar
        else if (codigo == 8) {

            int nuevoPeriodo = dato.toInt();

            if (nuevoPeriodo > 0) {

                periodoDistancia = nuevoPeriodo;

                proximaMedicionRadar = millis();

                Serial.print("Nuevo periodo del radar: ");
                Serial.println(periodoDistancia);
            }
        }
    }
}

// MOVER SERVO EN MODO FIJO

void MoverServoFijo(int angulo) {

    angulo = constrain(angulo, 0, 180);

    // Conectar el servo si fuera necesario
    if (!servo.attached()) {
        servo.attach(PIN_SERVO);
    }

    // Guardar la orientacion solicitada
    orientacion = angulo;
    anguloRadar = angulo;

    // No repetir la misma orden: evita correcciones innecesarias
    if (angulo != ultimoAnguloOrdenado) {
        servo.write(angulo);
        ultimoAnguloOrdenado = angulo;
    }
}


// ACTUALIZAR RADAR
void ActualizarRadar() {

    // Si el radar esta parado, no mover el servo ni medir distancia
    if (!radarActivo) {
        return;
    }

    //  MOVIMIENTO DEL SERVO 

    if (modoRastreo) {

        if (!servo.attached()) {
            servo.attach(PIN_SERVO);
        }

        if ((long)(millis() - proximoMovimientoServo) >= 0) {

            anguloRadar += direccionRadar * 2;

            if (anguloRadar >= 180) {
                anguloRadar = 180;
                direccionRadar = -1;
            }
            else if (anguloRadar <= 0) {
                anguloRadar = 0;
                direccionRadar = 1;
                cont = cont + 1;
            }
            if (cont ==1){
                tierra.println("6:");
                cont = 0;
            }
            servo.write(anguloRadar);
            ultimoAnguloOrdenado = anguloRadar;

            proximoMovimientoServo =
                millis() + intervaloMovimientoServo;
        }
    }

    //  MEDICION DE DISTANCIA 

    if ((long)(millis() - proximaMedicionRadar) < 0) {
        return;
    }

    // Medir distancia
    float distancia = MedirDistancia();

// Actualizar el siguiente momento de medicion
    if (modoRastreo) {
        proximaMedicionRadar = millis() + intervaloMedicionRastreo;
    }
    else {
        proximaMedicionRadar = millis() + periodoDistancia * 1000UL;
        anguloRadar = orientacion;
    }

// Enviar los datos
    if (distancia > 0) {
        tierra.print("2:");
        tierra.print(anguloRadar);
        tierra.print(":");
        tierra.println(distancia);
    }
    //else {
        //Serial.println("Medicion de distancia no valida");
    //}
}

//MEDIR DISTANCIA


float MedirDistancia() {

    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);

    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);

    digitalWrite(TRIG, LOW);

    unsigned long duracion = pulseIn(ECHO, HIGH, 25000);

    // Si no se recibe respuesta
    if (duracion == 0) {

        return -1;
    }

    // Calcular distancia en centimetros
    float distancia = duracion * 0.0343 / 2;

    return distancia;
}

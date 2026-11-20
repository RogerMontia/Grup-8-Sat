
#include <DHT.h>
#include <SoftwareSerial.h>
#include <Servo.h>
 
#define DHTPIN 2
#define DHTTYPE DHT11
#define TRIG 4   // ultrasonidos
#define ECHO 5
#define PIN_SERVO 3
 
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial tierra(10, 11);   // comunicacion con la estacion de tierra
Servo servo;
 
int periodoTH = 3;          // en segundos
int periodoDistancia = 3;   // en segundos, solo en modo fijo
int orientacion = 90;
 
bool enviandoDatos = false;
bool radarActivo = false;
bool falloDetectado = false;
bool alarmaEnviada = false;
bool modoRastreo = false;      // false = fijo, true = barrido
bool calcularMediaSat = false; // si es true la media la hace el arduino
 
unsigned long proximaLectura = 0;
unsigned long momentoAlarma = 0;
unsigned long ultimoLatido = 0;
unsigned long proximaMedicionRadar = 0;
unsigned long proximoMovimientoServo = 0;
 
const unsigned long intervaloMovimientoServo = 10;   // ms entre pasos del barrido
const unsigned long intervaloMedicionRastreo = 500;  // ms entre medidas en barrido
int ultimoAnguloOrdenado = -1;
 
float sumaTemperaturas = 0;
int numeroTemperaturas = 0;
 
int anguloRadar = 90;
int direccionRadar = 1;   // 1 sube, -1 baja
 
String comando = "";
 
void setup() {
    Serial.begin(9600);
    tierra.begin(9600);
    dht.begin();
 
    // empieza en fijo mirando a 90
    orientacion = 90;
    anguloRadar = 90;
    modoRastreo = false;
    radarActivo = false;
 
    servo.attach(PIN_SERVO);
    servo.write(90);
    ultimoAnguloOrdenado = 90;
    delay(700);   // le damos tiempo a llegar
 
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);
    digitalWrite(TRIG, LOW);
 
    anguloRadar = orientacion;
    proximaLectura = millis();
    proximaMedicionRadar = millis();
 
    Serial.println("Arduino satelite iniciado");
}
 
void loop() {
    RecibirComandos();
 
    // latido para que tierra sepa que seguimos vivos
    if (millis() - ultimoLatido >= 1000) {
        ultimoLatido = millis();
        tierra.println("5:");
    }
 
    // lectura del DHT cada periodoTH segundos
    if (enviandoDatos &&
        (long)(millis() - proximaLectura) >= 0) {
        proximaLectura = millis() + periodoTH * 1000UL;
 
        float h = dht.readHumidity();
        float t = dht.readTemperature();
 
        // lectura mala o temperatura demasiado alta
        if (isnan(h) || isnan(t) || t > 31) {
            if (!falloDetectado) {
                falloDetectado = true;
                alarmaEnviada = false;
                momentoAlarma = millis() + 5000;   // si sigue mal en 5 s salta la alarma
                tierra.println("3:");
                Serial.println("Error en el sensor");
            }
        }
        else {
            falloDetectado = false;
            alarmaEnviada = false;
 
            // formato 1:temp:hum
            tierra.print("1:");
            tierra.print(t);
            tierra.print(":");
            tierra.println(h);
 
            if (calcularMediaSat) {
                sumaTemperaturas += t;
                numeroTemperaturas++;
                float media = sumaTemperaturas / numeroTemperaturas;
                tierra.print("4:");
                tierra.println(media);
            }
        }
    }
 
    if (falloDetectado && !alarmaEnviada &&
        (long)(millis() - momentoAlarma) >= 0) {
        tierra.println("ALARMA");
        alarmaEnviada = true;
        Serial.println("ALARMA activada");
    }
 
    ActualizarRadar();
}
 
// va juntando caracteres hasta que llega un salto de linea
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
 
void ProcesarComando(String mensaje) {
    mensaje.trim();
 
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
    else if (mensaje == "PARAR") {
        enviandoDatos = false;
        radarActivo = false;
        Serial.println("Envio y radar parados");
    }
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
    else {
        // comandos tipo codigo:valor
        int separador = mensaje.indexOf(':');
        if (separador == -1) {
            return;
        }
 
        int codigo = mensaje.substring(0, separador).toInt();
        String dato = mensaje.substring(separador + 1);
        dato.trim();
 
        // 1 -> periodo del DHT
        if (codigo == 1) {
            int nuevoPeriodo = dato.toInt();
            if (nuevoPeriodo > 0) {
                periodoTH = nuevoPeriodo;
                proximaLectura = millis();
                Serial.print("Nuevo periodo TH: ");
                Serial.println(periodoTH);
            }
        }
        // 2 -> angulo en modo fijo
        else if (codigo == 2) {
            int nuevoAngulo = dato.toInt();
            if (nuevoAngulo >= 0 && nuevoAngulo <= 180) {
                orientacion = nuevoAngulo;
                if (!modoRastreo) {   // en barrido solo se guarda para luego
                    MoverServoFijo(orientacion);
                }
                Serial.print("Nueva orientacion: ");
                Serial.println(orientacion);
            }
        }
        // 5 -> quien calcula la media (0 tierra, 1 satelite)
        else if (codigo == 5) {
            int nuevoModo = dato.toInt();
            if (nuevoModo == 0 || nuevoModo == 1) {
                calcularMediaSat = (nuevoModo == 1);
                sumaTemperaturas = 0;
                numeroTemperaturas = 0;
                Serial.print("Modo de calculo de media: ");
                Serial.println(nuevoModo);
            }
        }
        // 7 -> modo del radar (0 fijo, 1 barrido)
        else if (codigo == 7) {
            int nuevoModo = dato.toInt();
 
            if (nuevoModo == 0) {
                modoRastreo = false;
                MoverServoFijo(orientacion);
                Serial.println("RADAR EN MODO FIJO");
            }
            else if (nuevoModo == 1) {
                modoRastreo = true;
                anguloRadar = 0;   // el barrido empieza desde 0
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
        // 8 -> periodo de medida del radar
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
 
void MoverServoFijo(int angulo) {
    angulo = constrain(angulo, 0, 180);
 
    if (!servo.attached()) {
        servo.attach(PIN_SERVO);
    }
 
    orientacion = angulo;
    anguloRadar = angulo;
 
    // si ya esta ahi no le mandamos nada, asi no tiembla
    if (angulo != ultimoAnguloOrdenado) {
        servo.write(angulo);
        ultimoAnguloOrdenado = angulo;
    }
}
 
void ActualizarRadar() {
    if (!radarActivo) {
        return;
    }
 
    // en barrido movemos 2 grados cada paso y rebotamos en los extremos
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
            }
 
            servo.write(anguloRadar);
            ultimoAnguloOrdenado = anguloRadar;
            proximoMovimientoServo =
                millis() + intervaloMovimientoServo;
        }
    }
 
    // todavia no toca medir
    if ((long)(millis() - proximaMedicionRadar) < 0) {
        return;
    }
 
    float distancia = MedirDistancia();
 
    if (modoRastreo) {
        proximaMedicionRadar =
            millis() + intervaloMedicionRastreo;
    }
    else {
        proximaMedicionRadar =
            millis() + periodoDistancia * 1000UL;
    }
 
    // si sale -1 no lo enviamos, que en python da problemas
    if (distancia > 0) {
        tierra.print("2:");
        tierra.print(anguloRadar);
        tierra.print(":");
        tierra.println(distancia);
    }
    else {
        Serial.println("Medicion de distancia no valida; no se envia");
    }
}
 
float MedirDistancia() {
    // pulso de 10 us para disparar el HC-SR04
    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG, LOW);
 
    unsigned long duracion = pulseIn(ECHO, HIGH, 25000);   // timeout de 25 ms, unos 4 m
 
    if (duracion == 0) {   // no ha vuelto el eco
        return -1;
    }
 
    // velocidad del sonido 0.0343 cm/us, entre 2 por ida y vuelta
    float distancia = duracion * 0.0343 / 2;
    return distancia;
}

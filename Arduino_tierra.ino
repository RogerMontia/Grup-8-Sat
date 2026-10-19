#include <SoftwareSerial.h>   // Permite comunicarse con el Arduino satelite

SoftwareSerial tierra (10, 11);  // Pines RX y TX de la comunicacion

const int ledAlarma = 12;  // Pin del LED de alarma
const unsigned long tiempoMaximo = 5000;   // Tiempo maximo sin recibir mensajes
unsigned long ultimoMensaje = 0;   // Momento del ultimo mensaje recibido
bool alarmaActiva = false;   // Indica si la alarma esta activada
String mensaje = "";   // Guarda el mensaje recibido

void setup() {
  Serial.begin(9600);   // Comunicacion con el ordenador por USB
  tierra.begin(9600);   // Comunicacion con el Arduino satelite
  pinMode(ledAlarma, OUTPUT);
  digitalWrite(ledAlarma, LOW);   // Empezar con el LED apagado
}

void loop() {
  while (tierra.available() > 0) {
    char dato = tierra.read();

    if (dato == '\n') {
      mensaje.trim();

      if (mensaje.length() > 0) {
        ultimoMensaje = millis();

        // Enviar el mensaje a Python
        Serial.println(mensaje);

        // Si el satelite envia una alarma
        if (mensaje.indexOf("ALARMA") >= 0) {
          alarmaActiva = true;
        }
        // Si vuelve a llegar una temperatura
        else if (mensaje.indexOf("T:") >= 0) {
          alarmaActiva = false;
        }
      }

      mensaje = "";
    }
    else {
      mensaje += dato;
    }
  }

  // Comprobar si se ha perdido la comunicacion
  if (ultimoMensaje != 0 && millis() - ultimoMensaje >= tiempoMaximo) {
    alarmaActiva = true;
    digitalWrite(ledAlarma, HIGH);  // Encender el LED inmediatamente
    Serial.println("ALARMA: Se ha perdido la comunicacion con el satelite");
    delay(3000); 
  }

   
  if (alarmaActiva == false) {    // Apagar el LED segun el estado de la alarma
    digitalWrite(ledAlarma, LOW); 
  }

}


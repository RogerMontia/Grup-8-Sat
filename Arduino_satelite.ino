#include <DHT.h>   // Libreria para el sensor de temperatura y humedad
#include <SoftwareSerial.h>  // Permite comunicarse usando otros pines
#define DHTPIN 2    // Pin donde esta conectado el sensor
#define DHTTYPE DHT11   // Tipo de sensor utilizado


DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial tierra(10, 11); // Comunicacion con tierra: RX, TX


unsigned long proximaLectura = 0;  // Momento de la siguiente lectura
unsigned long momentoAlarma = 0;  // Momento en que se activa la alarma
bool falloDetectado = false;  // Indica si hay un fallo


void setup() {
 Serial.begin(9600);    // Comunicacion con el ordenador del satelite
 tierra.begin(9600);  // Comunicacion con el Arduino de tierra
 dht.begin();    // Inicia el sensor
}


void loop() {
 if (millis() >= proximaLectura) {    // Leer temperatura y humedad cada 3 segundos
    proximaLectura = millis() + 3000;   
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (isnan(h) || (t>31) || isnan(t)) {  // Si falla la lectura o la temperatura supera los 31 grados
      if (!falloDetectado) {       // Iniciar la cuenta atras solo la primera vez que se detecta el fallo
        falloDetectado = true;
        momentoAlarma = millis() + 5000; 
      }
    }

    else {
      falloDetectado = false;  // Si todo vuelve a ser correcto, cancelar la alarma
      Serial.print("T:");    // Mostrar los datos en el monitor serie del ordenador
      Serial.print(t);
      Serial.print(";H:");
      Serial.println(h);

      tierra.print("T:");   // Enviar los datos al Arduino de tierra
      tierra.print(t);
      tierra.print(";H:");
      tierra.println(h);
   }
 }
 if (falloDetectado && (millis() >= momentoAlarma)) {   // Si el fallo dura 5 segundos, enviar una alarma a tierra
   Serial.println("Fallo");
   tierra.println("ALARMA");    
   momentoAlarma = millis() + 3000;   // repite la alarma cada 3 s mientras falle
 }
}


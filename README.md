**Grup-8-Sat
**
Versió 1: https://www.youtube.com/watch?v=b4j67Jj1C08

Versió 2:

Projecte de comunicació entre un satèl·lit i una estació de terra realitzat amb dos Arduinos.

El satèl·lit mesura la temperatura i la humitat amb un sensor DHT11 i, a la versió 2, també la distància als objectes propers amb un sensor d'ultrasons HC-SR04 muntat sobre un servo. Envia les dades a l'Arduino de terra. Aquest les passa a l'ordinador. Allà, un programa a Python dibuixa les gràfiques i mostra el radar. Si hi ha cap problema, s'encén un LED d'alarma.

Versions
Versió 1: mesura de temperatura i humitat, gràfica a l'ordinador, botons per iniciar, parar i reanudar, alarma per fallada del sensor i LED de pèrdua de comunicació.
Versió 2: sensor de distància amb servo (radar), càlcul de la mitjana de les 10 últimes temperatures (al satèl·lit o a terra), canvi dels períodes d'enviament des de la interfície i protocol d'aplicació entre les dues plaques.
Fitxers
Arduino_satelite.ino: Codi de l'Arduino del satèl·lit. Llegeix els sensors, mou el servo i envia les dades.
Arduino_tierra/Arduino_tierra.ino: Codi de l'Arduino de terra. Rep les dades, les envia a l'ordinador, passa les ordres al satèl·lit i controla el LED.
python_tierra.py: Programa de l'ordinador amb les gràfiques, el radar i els botons de control.
tests/: tests unitaris (entre ells el del sensor de distància).
Connexions

**Satèl·lit:
**
Sensor DHT11 al pin 2
Servo al pin 3
HC-SR04: TRIG al pin 4 i ECHO al pin 5
Pins 10 (RX) i 11 (TX) per comunicar-se amb terra

**Terra:
**
LED d'alarma al pin 12
Pins 10 (RX) i 11 (TX) per comunicar-se amb el satèl·lit

Els pins RX i TX de les dues plaques es creuen. Els GND es connecten.

Com utilitzar
Puja Arduino_satelite.ino a l'Arduino del satèl·lit.
Puja Arduino_tierra.ino a l'Arduino de tierra.
Connecta Arduino de terra a l'ordinador. Mira quin port COM utilitza.
Cal canviar el port a la variable device de python_tierra.py. Ara és COM3.
Instal·leu les llibreries de Python amb aquesta ordre: pip install pyserial matplotlib
Executa python python_tierra.py i prem Iniciar.

Cal tenir tancat el monitor sèrie de l'Arduino IDE. Si no, el port està ocupat. També cal instal·lar la llibreria DHT a Arduino IDE.

Ús de la interfície
Iniciar / Parar / Reanudar: comença, atura o continua l'enviament de dades de temperatura, humitat i distància.
Període de temperatura i humitat: canvia cada quants segons s'envien les dades del DHT11.
Període del radar: canvia cada quants segons es mesura la distància (en mode fix).
Orientació: posa el sensor de distància en un angle concret, de 0 a 180 graus.
Mode radar: fix (mira a l'angle triat) o rastreig (fa un escombrat continu de 0 a 180 graus).
Càlcul de la mitjana: es pot triar si la mitjana la fa el satèl·lit o l'ordinador.
Temperatura màxima: valor límit per a l'alarma de la mitjana.
Protocol d'aplicació

Tots els missatges són text acabat en salt de línia. Van formats com codi:dada, separats per :.

Del satèl·lit a terra:

Missatge	Significat
1:temperatura:humitat	Dades del DHT11
2:angle:distància	Mesura de distància (en cm) amb l'angle del servo
3:	Fallada en la captura de temperatura i humitat
4:mitjana	Mitjana de temperatura calculada pel satèl·lit
5:	Latido, s'envia cada segon per saber que el satèl·lit segueix funcionant
ALARMA	El sensor porta 5 segons fallant o passa de 31 ºC

**De Terra a Satèl·lit:
**
Missatge	Significat
INICIAR	Comença l'enviament de dades i el radar
PARAR	Atura l'enviament de dades i el radar
REANUDAR	Continua l'enviament de dades i el radar
1:segons	Nou període d'enviament de temperatura i humitat
2:angle	Nova orientació fixa del sensor de distància (0-180)
5:0 o 5:1	Mitjana calculada a terra (0) o al satèl·lit (1)
7:0 o 7:1	Radar en mode fix (0) o en mode rastreig (1)
8:segons	Nou període de mesura del radar
Mitjana de temperatures

La interfície mostra una gràfica amb la mitjana dels 10 últims valors de temperatura. Per calcular-la s'utilitza una cua circular. L'usuari tria si el càlcul es fa al satèl·lit (reacciona més ràpid, però gasta energia) o a l'ordinador. Si salten tres mitjanes seguides per sobre del límit que posa l'usuari, es mostra una alarma.

**Alarmes
**
Si el sensor falla o la temperatura passa de 31 ºC durant 5 segons, el satèl·lit envia "ALARMA" al terra. Si no rep cap resposta durant 5 segons, s'encén el LED perquè s'ha perdut la comunicació. Quan tornen a arribar dades de forma normal, el LED s'apaga. Quan una mesura de distància no és vàlida (el sensor no rep eco), no s'envia a terra.

**Ús donat a la IA
**
Per tal de solucionar errors en el codi que els membres del grup no han pogut solucionar s'ha usat la I.A. Les eines que principalment s'han usat han estat Claude i ChatGPT.

Un exemple d'input entregat al chatbot és el següent:




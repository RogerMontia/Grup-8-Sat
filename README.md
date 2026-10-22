# Grup-8-Sat

https://www.youtube.com/watch?v=b4j67Jj1C08


Projecte de comunicació entre un satèl·lit i una estació de terra realitzat amb dos Arduinos.

El satèl·lit mesura la temperatura i la humitat amb un sensor DHT11. Envia les dades a Arduino de terra. Aquest passa a lordinador. Allà, un programa a Python dibuixa la gràfica de la temperatura. Si hi ha cap problema, s'encén un LED d'alarma.

# Fitxers

- `Arduino_satelite.ino`: codi de l'Arduino del satèl·lit. Arriba el sensor i envia les dades.
- `Arduino_tierra/Arduino_tierra.ino`: codi de l'Arduino de terra. Rep les dades, les envia a l'ordinador i controla el LED.
- `python_tierra.py`: programa de l'ordinador amb la gràfica i els botons Iniciar, Parar i Reanudar.

# Connexions

Satèl·lit:
- Sensor DHT11 al pin 2
- Pins 10 (RX) i 11 (TX) per comunicar-se amb terra

Terra:
- LED d'alarma al pin 12
- Pins 10 (RX) i 11 (TX) per comunicar-se amb el satèl·lit

Els pins RX i TX de les dues plaques es creuen. Els GND es connecten.

# Com utilitzar

1. Puja `Arduino_satelite.ino` a l'Arduino del satèl·lit.
2. Puja `Arduino_tierra.ino` a l'Arduino de tierra.
3. Connecta Arduino de terra a l'ordinador. Mira quin port COM utilitza.
4. Cal canviar el port a la variable `device` de `python_tierra.py`. Ara és `COM3`.
5. Instal·leu les llibreries de Python amb aquesta ordre: `pip install pyserial matplotlib`
6. Executa `python python_tierra.py` i prem **Iniciar**.

Cal tenir tancat el monitor sèrie de l'Arduino IDE. Si no, el port està ocupat. També cal instal·lar la llibreria DHT a Arduino IDE.

# Alarmes

Si el sensor falla o la temperatura passa de 31 ºC durant 5 segons, el satèl·lit envia “ALARMA” al terra.
Si no rep cap resposta durant 5 segons, s'encén el LED perquè s'ha perdut la comunicació.
Quan tornen a arribar dades de forma normal, el LED s'apaga.

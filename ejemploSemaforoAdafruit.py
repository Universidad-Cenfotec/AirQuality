# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Importanción de librerias.
import board
from ideaboard import IdeaBoard
import time
import board
import adafruit_bme680

# Conexión a I2C, creación de las instancias sensor e ib.
i2c = board.I2C()
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
ib = IdeaBoard()

# Declaración de las variables de los colores en RGB.
VERDE = (0,255,0)
AMARILLO = (255,255,0)
ROJO = (255,0,0)
NEGRO = (0,0,0)

# Calculos para calidad del aire.
# Declaración de variables mediciones.
meanTemp = 0.0
meanHumidity = 0.0
meanGas = 0.0

# Constante samples.
samples = 200

# La variables inicializadas almacenan las mediciones del sensor.
meanTemp = 0
meanHumidity = 0
meanGas = 0
for i in range(samples):
    meanTemp += sensor.temperature
    meanHumidity += sensor.humidity
    meanGas += sensor.gas
    time.sleep(0.02)

meanTemp = meanTemp / samples
meanHumidity = meanHumidity / samples
meanGas = meanGas / samples

# Calcula porcentaje de contribución de humedad.
pHumidity=0
if meanHumidity < 40:
    pHumidity = round(0.10/40*meanHumidity*100)
else:
    pHumidity =round( ((-0.10/(100 - 40)* meanHumidity) + 0.166667)* 100)


# Calcula porcentaje de contribución de temperatura.
pTemp=0
if meanTemp < 21:
    pTemp = round(10/41*meanTemp + 5)
else:
    pTemp =round(((-10/(100 - 21)*meanTemp + 12.658228)))
  

# Calcula el gas.
pGas = round((0.80/(50000 - 5000)*meanGas - (5000*(0.80/(50000 - 5000))))*100)

# Finalmente, se calcula la calidad del aire.
AQ = pHumidity+pTemp+pGas

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
import time
from random import randint

import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

### WiFi ###
# Añade secrets.py a tu sistema de archivos que tiene un diccionario llamado secrets con claves
# "ssid" y "password" on sus credenciales de WiFi. NO COMPARTAS este archivo.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Configure su nombre de usuario y clave de Adafruit IO en secrets.py
# (visita io.adafruit.com si necesitas crear una cuenta,
# o si necesitas tu clave de Adafruit IO.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

# Define funciones de devolución de llamada que se llamarán cuando ocurran ciertos eventos.
# pylint: disable=unused-argument
def connected(client):
    # Se llamará a la función conectada cuando el cliente esté conectado a Adafruit IO.
    # Este es un buen lugar para suscribirse a los cambios del feed.  El parámetro de
    # cliente que se pasa a esta función es el cliente Adafruit IO MQTT para que pueda
    # realizar llamadas fácilmente.
    print("Connected to Adafruit IO!  Listening for Semaforo inteligente changes...")
    # Suscríbete a los cambios en un feed llamado comandos.
    client.subscribe("temperaturaaq")
    client.subscribe("humedadaq")
    client.subscribe("gasaq")
    client.subscribe("calidadaireaq")



def subscribe(client, userdata, topic, granted_qos):
    # Este método se llama cuando el cliente se suscribe a un nuevo feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(client, userdata, topic, pid):
    # Este método se llama cuando el cliente se da de baja de un feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


# pylint: disable=unused-argument
def disconnected(client):
    # Función de desconexión será llamada cuando el cliente desconecte.
    print("Disconnected from Adafruit IO!")


# pylint: disable=unused-argument
def message(client, feed_id, payload):
    
    # La función de mensaje será llamada cuando un feed suscrito tenga un nuevo valor.
    # El parámetro feed_id identifica el feed, y el parámetro payload
    # tiene el nuevo valor.
    print("Feed {0} received new value: {1}".format(feed_id, payload))


# Crear un socket pool
pool = socketpool.SocketPool(wifi.radio)

# Inicializar un nuevo objeto Cliente MQTT.
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=1883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Se inicializa Adafruit IO MQTT Client.
io = IO_MQTT(mqtt_client)

# Conecta los métodos de callback definidos arriba a Adafruit IO.
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe
io.on_unsubscribe = unsubscribe
io.on_message = message

# Conexión a Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()
        
# Se publican los datos en Adafruit IO.
last = 0
print("Publishing a new message every 10 seconds...")
while True:
    if AQ < 100:
        ib.pixel = VERDE #Calidad del aire: Buena calidad
    elif AQ >= 100:
        ib.pixel = AMARILLO # Calidad del aire: Moderadamente contaminado
    elif AQ >= 200:
        ib.pixel = ROJO # Calidad del aire: Extremadamente contaminado
    else:
        ib.pixel = NEGRO
        
    if (time.monotonic() - last) >= 10:
        print("Publishing {0} to Temperatura.".format(meanTemp))
        print("Publishing {0} to Humedad.".format(meanHumidity))
        print("Publishing {0} to Gas.".format(meanGas))
        print("Publishing {0} to Calidad Aire.".format(AQ))
        print("-----------------------------------------")
        io.publish("temperaturaaq", meanTemp)
        io.publish("humedadaq", meanHumidity)
        io.publish("gasaq", meanGas)
        io.publish("calidadaireaq", AQ)
        print("-----------------------------------------")
        last = time.monotonic()
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
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
ib = IdeaBoard()

# Presión al nivel del mar.
bme680.sea_level_pressure = 1013.25

# Compensación para la temperatura del sensor. Puede variar.
temperature_offset = -5

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
# pylint: disable=no-name-in-module, wrong-import-order
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
    print("Connected to Adafruit IO!  Listening for Sensor inteligente changes...")
    # Suscríbete a los cambios de los feeds.
    client.subscribe("temperatura")
    client.subscribe("humedad")
    client.subscribe("presion")
    client.subscribe("altitud")
    client.subscribe("gas")

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


# Crear un socket pool.
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

# Conexión a Adafruit IO.
print("Connecting to Adafruit IO...")
io.connect()

# Se publican los datos en Adafruit IO.
last = 0
print("Publishing a new message every 10 seconds...")
while True:
    if (time.monotonic() - last) >= 10:
        print("\nTemperature: %0.1f C" % (bme680.temperature + temperature_offset))
        print("Humidity: %0.1f %%" % bme680.relative_humidity)
        print("Pressure: %0.3f hPa" % bme680.pressure)
        print("Altitude = %0.2f meters" % bme680.altitude)
        print("Gas: %d KOhm" % bme680.gas)
        print("Publishing {0} to Temperatura.".format(bme680.temperature + temperature_offset))
        print("Publishing {0} to Humedad.".format(bme680.relative_humidity))
        print("Publishing {0} to Presion.".format(bme680.pressure))
        print("Publishing {0} to Altitud.".format(bme680.altitude))
        print("Publishing {0} to Gas.".format(bme680.gas))
        print("-----------------------------------------")
        io.publish("temperatura", bme680.temperature + temperature_offset)
        io.publish("humedad", bme680.relative_humidity)
        io.publish("presion", bme680.pressure)
        io.publish("altitud", bme680.altitude)
        io.publish("gas", bme680.gas)
        print("-----------------------------------------")
        last = time.monotonic()
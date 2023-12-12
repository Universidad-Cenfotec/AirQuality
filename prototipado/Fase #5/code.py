# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Importación de librerias.
import microcontroller
import board
from ideaboard import IdeaBoard
import time
import board
import adafruit_bme680
import time
from random import randint
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# Conexión a I2C, creación de las instancias sensor e ib.
i2c = board.I2C()
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
ib = IdeaBoard()

# Calculos para calidad del aire.
# Declaración de variables mediciones.
mean_temp = 0.0
mean_humidity = 0.0
mean_gas = 0.0

# Constante samples.
samples = 200

for i in range(samples):
    mean_temp += sensor.temperature
    mean_humidity += sensor.humidity
    mean_gas += sensor.gas
    time.sleep(0.02)

mean_temp = mean_temp / samples
mean_humidity = mean_humidity / samples
mean_gas = mean_gas / samples

# Calcula porcentaje de contribución de humedad.
p_humidity = 0
if mean_humidity < 40:
    p_humidity = round(0.10/40 * mean_humidity * 100)
else:
    p_humidity = round(((-0.10/(100 - 40) * mean_humidity) + 0.166667) * 100)

# Calcula porcentaje de contribución de temperatura.
p_temp = 0
if mean_temp < 21:
    p_temp = round(10/41 * mean_temp + 5)
else:
    p_temp = round(((-10/(100 - 21) * mean_temp + 12.658228)))

# Calcula el gas.
p_gas = round((0.80/(50000 - 5000) * mean_gas - (5000 * (0.80/(50000 - 5000)))) * 100)

# Finalmente, se calcula la calidad del aire.
aq = p_humidity + p_temp + p_gas

### WiFi ###
# Añade secrets.py a tu sistema de archivos que tiene un diccionario llamado secrets con claves
# "ssid" y "password" en sus credenciales de WiFi. NO COMPARTAS este archivo.
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

virtual_button_feed = "reset"
io.subscribe(virtual_button_feed)

# Callback para manejar mensajes recibidos
def message(client, feed_id, payload):
    global button_pressed
    
    if feed_id == virtual_button_feed:
        if payload == "pressed":
            if not button_pressed:
                print("Botón virtual presionado. Reiniciando el dispositivo...")
                microcontroller.reset()
                button_pressed = True
        elif payload == "released":
            button_pressed = False

io.on_message = message

button_pressed = False

# Logica de encendido y apagado de luces.
# El relay module es inverso, por lo que al estar True esta apagado y al estar False esta encendido.
verde = ib.DigitalOut(board.IO27)
amarillo = ib.DigitalOut(board.IO33)
rojo = ib.DigitalOut(board.IO32)

# Se publican los datos en Adafruit IO.
last = 0
print("Publishing a new message every 10 seconds...")
while True:
    io.loop()

    if aq < 100:
        # Calidad del aire: Buena calidad
        verde.value = False
        amarillo.value = True
        rojo.value = True  
    elif aq >= 100:
        # Calidad del aire: Moderadamente contaminado
        verde.value = True
        amarillo.value = False
        rojo.value = True
    elif aq >= 200:
        # Calidad del aire: Extremadamente contaminado
        verde.value = True
        amarillo.value = True
        rojo.value = False
    else:
        # Caso default
        verde.value = True
        amarillo.value = True
        rojo.value = True
    
    # Publica los datos a Adafruit.
    if (time.monotonic() - last) >= 10:
        io.publish("temperaturaaq", mean_temp)
        io.publish("humedadaq", mean_humidity)
        io.publish("gasaq", mean_gas)
        io.publish("calidadaireaq", aq)
        last = time.monotonic()

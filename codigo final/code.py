# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Importación de librerias.
import adafruit_scd4x
import board
from ideaboard import IdeaBoard
import board
import time
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# Conexión a I2C, creación de las instancias sensor e ib.
i2c = board.I2C()
sensor = adafruit_scd4x.SCD4X(i2c)
ib = IdeaBoard()

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

# Logica de encendido y apagado de luces.
# El relay module es inverso, por lo que al estar True esta apagado y al estar False esta encendido.
verde = ib.DigitalOut(board.IO27)
amarillo = ib.DigitalOut(board.IO33)
rojo = ib.DigitalOut(board.IO32)

# Constante samples.
samples = 200

# Se inician mediciones periódicas en el sensor SCD-41.
scd4x.start_periodic_measurement()

# Se publican los datos en Adafruit IO cada 10 minutos.
while True:
    try:
        # Calculos para calidad del aire.
        # Declaración de variables mediciones.
        air_quality = 0
        
        # Empieza un temporizador para medir el tiempo que tarda en medirse la calidad del aire.
        start_time = time.monotonic()
        
        # Muestreo de 200 medidas.
        for i in range(samples):
            air_quality += sensor.CO2
            time.sleep(0.02)

        air_quality /= samples
    
        if air_quality < 1000:
            # Calidad del aire: Baja.
            verde.value = False
            amarillo.value = True
            rojo.value = True
        elif air_quality >= 1000 and air_quality < 1500:
            # Calidad del aire: Media.
            verde.value = True
            amarillo.value = False
            rojo.value = True
        elif air_quality >= 1500:
            # Calidad del aire: Alta.
            verde.value = True
            amarillo.value = True
            rojo.value = False
        else:
            # Caso default
            verde.value = True
            amarillo.value = True
            rojo.value = True
            
        # Conecta con Adafruit IO.
        io.connect()
        
        # Inicia el loop de IO.
        io.loop()
        
        # Publica los datos a Adafruit.
        print("Acaboo de publicar...................")
        io.publish("calidadaireaq", air_quality)
        time.sleep(5)
        
        # Desconecta de Adafruit IO
        io.disconnect()
        
        # Termina el temporazador.
        end_time = time.monotonic()
        
        # Se resta inicio temporizador - final temporizador, para obtener tiempo transcurrido.
        elapsed_time = round(end_time - start_time)
    except Exception as e:
        # Manejo de excepciones
        print("Error:", e)
        # En caso de error, desconecta y espera un tiempo antes de intentar nuevamente.
        io.disconnect()
        time.sleep(5)
        continue
    # Se resta tiempo transcurrido menos 10 minutos, para tomar las medidas en tiempo exacto de 10 minutos.
    time.sleep(600 - elapsed_time)
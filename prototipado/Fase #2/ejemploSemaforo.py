# Ejemplo medición de gases con semafaro utilizando pixel.
# Importanción de librerias necesarias.
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

# Declaración de variables mediciones.
meanTemp = 0.0
meanHumidity = 0.0
meanGas = 0.0

# Constante samples.
samples = 200

# Las variables inicializadas almacenan las mediciones del sensor.
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

# Ciclo del que se obtiene los compuestos orgánicos volátiles en el aire cada 1 segundo.
while True:
    # Se imprimen las mediciones.
    print("Temperatura: %d" % meanTemp)
    print("Gas: %d" % meanGas)
    print("Humedad: %d" % meanHumidity)
    
    # Ejemplo
    # Condicional "semaforo" en el que se cambia el color del pixel según el sensor gas.
    if AQ < 100:
        print("Calidad del aire: Buena calidad")
        print("-------------------------------")
        ib.pixel = VERDE
    elif AQ >= 100:
        print("Calidad del aire: Moderadamente contaminado")
        print("-------------------------------------------")
        ib.pixel = AMARILLO
    elif AQ >= 200:
        print("Calidad del aire: Extremadamente contaminado")
        print("--------------------------------------------")
        ib.pixel = ROJO
    else:
        ib.pixel = NEGRO
    

import board
import time
# Se debe importar la libreria adafruit_circuitpython_bme680.
import adafruit_bme680 

i2c = board.I2C()
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

# Establecer la presión al nivel del mar para su ubicación esto para obtener la medida más
# precisa (recuerde que estos sensores solo pueden inferir la altitud en función de la presión
# y necesitan un punto de calibración establecido.)
sensor.sea_level_pressure = 1013.25 

# Se suele agregar una compensación para la temperatura del sensor. Puede variar.
temperature_offset = -5

while True:
    print('-------------------------------------------------------')
    # sensor.temperature mide la temperatura en grados Celcius.
    print('Temperature: {} grados C'.format(sensor.temperature)) 
    print('Gas: {} Ohms'.format(sensor.gas))
    # sensor.humidity mide el porcentaje de humedad de 0 a 100%
    print('Humidity: {}%'.format(sensor.humidity))
    # sensor.pressure mide la presión en hPa.
    print('Pressure: {}hPa'.format(sensor.pressure))
    # sensor.altitude mide la altitud en metros.
    print("Altitude = %0.2f metros" % sensor.altitude)
    time.sleep(1)
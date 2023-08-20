/*
   This sketch shows how nicla can be used in standalone mode.
   Without the need for an host, nicla can run sketches that
   are able to configure the bhi sensors and are able to read all
   the bhi sensors data.
*/

#include "Arduino.h"
#include "Arduino_BHY2.h"
#include "Nicla_System.h"

Sensor temp(SENSOR_ID_TEMP);
Sensor gas(SENSOR_ID_GAS);
Sensor pressure(SENSOR_ID_BARO);
Sensor humidity(SENSOR_ID_HUM);

float meanTemp = 0;
float meanHumidity = 0;
float meanGas = 0;

const int samples = 200;

void setup()
{
  Serial.begin(115200);
  while (!Serial);


  BHY2.begin();

  temp.begin();
  gas.begin();
  humidity.begin();

  //to use led
  nicla::begin();
  nicla::leds.begin();
  nicla::leds.setColor(green);

}

void loop()
{
  static auto printTime = millis();

  // Update function should be continuously polled
  BHY2.update();


  meanTemp = 0;
  meanHumidity = 0;
  meanGas = 0;
  for (int i = 0; i < samples; i++) {
    meanTemp += temp.value();
    meanHumidity += humidity.value();
    meanGas += gas.value();
    delay(20);
  }

  meanTemp = meanTemp / samples;
  meanHumidity = meanHumidity / samples;
  meanGas = meanGas / samples;

// calcula procerntaje de contribución de humedad
  int pHumidity=0;
  if(meanHumidity<40){
    pHumidity = round(0.10/40*meanHumidity*100);
  }else{
    pHumidity =round( ((-0.10/(100 - 40)* meanHumidity) + 0.166667)* 100);
  }

  
  
// calcula procerntaje de contribución de temperatura
  int pTemp=0;
  if(meanTemp<21){
    pTemp = round(10/41*meanTemp + 5);
  }else{
    pTemp =round(((-10/(100 - 21)*meanTemp + 12.658228)));
  }


  int pGas = round((0.80/(50000 - 5000)*meanGas - (5000*(0.80/(50000 - 5000))))*100);

  int AQ = pHumidity+pTemp+pGas;

  Serial.println("*****************************");
  Serial.println(String("temperature: ") + String(meanTemp, 1));
  Serial.println(String("gas: ") + String(meanGas, 0));
  Serial.println(String("Humidity: ") + String(meanHumidity, 1));
  Serial.println("_______________________");
  Serial.print("Calidad de Aire: ");
  Serial.print(AQ);
  Serial.println("%");
  Serial.println("_______________________");
  Serial.println(" ");
  Serial.println(" ");
  
}

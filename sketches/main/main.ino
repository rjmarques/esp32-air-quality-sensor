#include <Arduino.h>
#include <WiFi.h>
#include <FreeRTOS.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <SoftwareSerial.h>
#include <MHZ19.h>
#include <DFRobot_SGP40.h>
#include <PMS.h>

#define BAUDRATE 9600
#define MHZ_RX_PIN 33
#define MHZ_TX_PIN 32

// network info

const char *ssid = "my_wifi";
const char *password = "change_me";
String hostname = "ESP32 Air Quality Sensor";

// device state information
unsigned long bootTime;
unsigned long connectionTime;

PMS pms(Serial2);

// effectively the PMS sensor will flip between sleeping for 1 minute and taking readings also for 1 minute
// this is used to prolong the lifetime of the lazer beyond the stated 5years that a 24h usage would give
// additionally the sensor needs to warm up for 30 seconds before new readings are trustworthy
static const uint32_t PMS_CYCLE_DURATION = 60000;
static const uint32_t PMS_WARM_UP_DURATION = 30000;

struct AqiAvg
{
  uint16_t sumPM1;
  uint16_t sumPM2;
  uint16_t sumPM10;
  int count;
};

bool pmsSleeping;
bool pmsWarmingUp;
uint32_t pmsTimer;
AqiAvg aqiData = {0, 0, 0, 1};

DFRobot_SGP40 sgp40;
uint16_t voc;

// for the first 3 minutes CO2 readings must not be considered accurate
static const uint32_t MHZ19_PREHEAT_DURATION = 180000;

MHZ19 mhz19;
SoftwareSerial mhzSerial(MHZ_RX_PIN, MHZ_TX_PIN);
int co2;
bool mhzPreheating;

WebServer server(80);

void setup()
{
  Serial.begin(115200);
  while (!Serial)
    delay(10);
  delay(1000);

  bootTime = millis();

  setupSGP40();
  setupPM25();
  setupMHZ();

  WiFi.mode(WIFI_STA);
  xTaskCreatePinnedToCore(ConnectWiFi, "Connect WiFi", 5000, NULL, 1, NULL, 1);

  xTaskCreate(ReadSensors, "Read Sensors", 1000, NULL, 1, NULL);

  delay(1000);
  setupRouting();
}

void setupMHZ()
{
  mhzSerial.begin(BAUDRATE);
  mhz19.begin(mhzSerial);
  mhz19.autoCalibration(false);
  mhzPreheating = true;
  Serial.println("MHZ19 initialized successfully!");
}

void setupPM25()
{
  Serial2.begin(BAUDRATE);

  pms.passiveMode();
  pms.wakeUp();
  pmsWarmingUp = true;
  Serial.println("PM25 initialized successfully!");
}

void setupSGP40()
{
  /*
    Sensor preheat time: 10s
    duration: init wait time. Unit: ms. It is suggested: duration>=10000ms
  */
  while (sgp40.begin(10000) != true)
  {
    Serial.println("failed to init sgp40 chip, please check if the chip connection is fine");
    delay(1000);
  }
  Serial.println("sgp40 initialized successfully!");
}

void ReadSensors(void *parameter)
{
  uint32_t startTime = millis(); // initial timestamp

  pmsTimer = millis();      // start counting now
  AqiAvg initPMS = aqiData; // initial values (empty state)
  for (;;)
  {
    uint32_t timerNow = millis();

    // read VOC index
    /*
       VOC index can directly indicate the condition of air quality. The larger the value, the worse the air quality
        0-100，no need to ventilate,purify
        100-200，no need to ventilate,purify
        200-400，ventilate,purify
        400-500，ventilate,purify intensely
    */
    voc = sgp40.getVoclndex();

    // only record CO2 values after preheat phase
    int co2Reading = mhz19.getCO2();
    if (mhz19.errorCode != RESULT_OK)
    {
      Serial.printf("Error found in communication: %d", mhz19.errorCode);
    }
    else if (mhzPreheating)
    {
      if (timerNow - startTime >= MHZ19_PREHEAT_DURATION)
      {
        mhzPreheating = false;
      }
    }
    else
    {
      co2 = co2Reading;
    }

    // read PM values
    uint32_t pmsDuration = timerNow - pmsTimer;
    if (pmsSleeping)
    {
      if (pmsDuration >= PMS_CYCLE_DURATION)
      {
        // wake up and enter warm up phase
        pms.wakeUp();
        pmsSleeping = false;
        pmsWarmingUp = true;
        pmsTimer = timerNow;
      }
      // else keep sleeping...zzz
    }
    else
    {
      if (pmsDuration >= PMS_CYCLE_DURATION)
      {
        pms.sleep();
        pmsSleeping = true;
        pmsTimer = timerNow;
        // go to sleep...zzz
      }
      else if (pmsDuration >= PMS_WARM_UP_DURATION)
      {
        // take readings
        pms.requestRead();

        PMS::DATA aqiReadings;
        if (pms.readUntil(aqiReadings))
        {
          AqiAvg data;

          // just finished warming up, reset local data
          if (pmsWarmingUp)
          {
            pmsWarmingUp = false;
            data = initPMS;
          }
          else
          {
            data = aqiData;
          }

          data.sumPM1 += aqiReadings.PM_AE_UG_1_0;
          data.sumPM2 += aqiReadings.PM_AE_UG_2_5;
          data.sumPM10 += aqiReadings.PM_AE_UG_10_0;
          data.count++;

          aqiData = data;
        }
      }
    }

    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

void ConnectWiFi(void *parameter)
{
  for (;;)
  {
    if ((WiFi.status() != WL_CONNECTED))
    {
      // delete old config
      WiFi.disconnect(true);
      vTaskDelay(1000 / portTICK_PERIOD_MS);

      WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE, INADDR_NONE);
      WiFi.setHostname(hostname.c_str());

      WiFi.begin(ssid, password);
      int count = 0;
      bool connected = false;
      while (count < 10)
      {
        if (WiFi.status() == WL_CONNECTED)
        {
          connected = true;
          break;
        }
        count++;
        vTaskDelay(2000 / portTICK_PERIOD_MS);
      }

      if (connected)
      {
        Serial.println(WiFi.localIP());
      }
    }

    // pause the task for 10 seconds
    // essentially running the check every 10 seconds
    vTaskDelay(10000 / portTICK_PERIOD_MS);
  }
}

void setupRouting()
{
  server.on("/metrics", getMetrics);
  server.on("/readings", getReadings);
  server.on("/", getInfo);

  // start server
  server.begin();
}

// prometheus style metrics
void getMetrics()
{
  String metrics = "# Various air quality sensor metrics\n";
  metrics += "sensor_voc_index " + String(voc) + "\n";
  AqiAvg pmsData = aqiData;
  metrics += "sensor_particulate_matter{size=\"1.0\"} " + String((float)pmsData.sumPM1 / pmsData.count) + "\n";
  metrics += "sensor_particulate_matter{size=\"2.5\"} " + String((float)pmsData.sumPM2 / pmsData.count) + "\n";
  metrics += "sensor_particulate_matter{size=\"10.0\"} " + String((float)pmsData.sumPM10 / pmsData.count) + "\n";
  metrics += "sensor_co2 " + String(co2) + "\n";
  server.send(200, "text/plain", metrics);
}

// readings in JSON
void getReadings()
{
  StaticJsonDocument<512> readings;
  AqiAvg pmsData = aqiData;

  readings["voc"] = String(voc);
  readings["pm1.0"] = String((float)pmsData.sumPM1 / pmsData.count);
  readings["pm2.5"] = String((float)pmsData.sumPM2 / pmsData.count);
  readings["pm10.0"] = String((float)pmsData.sumPM10 / pmsData.count);
  readings["co2"] = String(co2);

  String buf;
  serializeJson(readings, buf);

  server.send(200, "application/json", buf);
}

// device info JSON
void getInfo()
{
  StaticJsonDocument<256> info;

  esp_chip_info_t chip_info;
  esp_chip_info(&chip_info);

  // get chip id
  String chipId = String((uint32_t)ESP.getEfuseMac(), HEX);
  chipId.toUpperCase();

  info["chipID"] = chipId.c_str();
  info["coreCount"] = String(chip_info.cores);
  info["siliconRevision"] = String(chip_info.revision);
  info["flash"] = String(spi_flash_get_chip_size() / (1024 * 1024)) + "MB";
  info["macAddress"] = WiFi.macAddress();

  String buf;
  serializeJson(info, buf);

  server.send(200, "application/json", buf);
}

void loop()
{
  server.handleClient();
}
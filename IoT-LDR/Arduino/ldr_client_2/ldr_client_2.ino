#include "string.h"
#include "WiFi.h"
#include "WiFiUdp.h"
#include "coap-simple.h"
#include "IPAddress.h"
#include "PubSubClient.h"
#include "esp_sleep.h"
#include "esp_random.h"
#include "InfluxDbClient.h"

#define WIFI_SSID "xxxxxxxx"
#define WIFI_PW   "xxxxxxxx"
#define WIFI_TIMEOUT 15000

#define COAP_SERVER IPAddress(x, x, x, x)   
#define COAP_PORT 5684
#define COAP_TIMEOUT 5000
String COAP_URL = "ldrData2";

#define DB_URL "https://eu-central-1-1.aws.cloud2.influxdata.com"
#define DB_ORG "IoT"
#define DB_BUCKET "IoTLDR"
#define DB_TOKEN "xxxxxxxx"

#define MQTT_SERVER "x.x.x.x"
#define MQTT_PORT 1883
#define MQTT_USER "xxxxxxxx"
#define MQTT_PASSWORD "xxxxxxxx"
#define MQTT_TIMEOUT 10000

#define SAMPLING_PERIOD_TOPIC "home/ldr2/sampling_period"
#define POSITION_TOPIC "home/ldr2/position"
String LDR_num = "2";

const uint8_t ldr_pin = 0;
unsigned long time_coap_send_start, time_coap_send_stop;
bool coap_received = 0;

WiFiUDP udp;
Coap coap(udp);
WiFiClient espClient;
PubSubClient mqtt(espClient);

RTC_DATA_ATTR int sampling_period = 10000; // Default sampling period in ms (persistent)
RTC_DATA_ATTR char position[50] = "kitchen"; // Default position (persistent)
RTC_DATA_ATTR unsigned long latency_accum = 0;
RTC_DATA_ATTR unsigned long latency_len = 0;
RTC_DATA_ATTR unsigned long missed_tx = 0;


float custom_normalization(float x, float in_min, float in_max, float out_min, float out_max) {
  float run = in_max - in_min;
  if (run == 0) {
    log_e("map(): Invalid input range, min == max");
    return -1;
  }
  float rise = out_max - out_min;
  float delta = x - in_min;
  return (delta * rise) / run + out_min;
}


// ~~ Wi-Fi ~~
void wiFiInit(){
  WiFi.begin(WIFI_SSID, WIFI_PW);
  Serial.print("[LOG] Connecting to Wi-Fi...");
  unsigned long wifi_connection_start_time = millis();
  while ( WiFi.status() != WL_CONNECTED && (millis() - wifi_connection_start_time) < WIFI_TIMEOUT ) {
    delay(2000);
    Serial.print(".");
  }
  if ( WiFi.status() == WL_CONNECTED ) {
    Serial.print("\n[LOG] Connected to Wi-Fi with IP ");
    Serial.println(WiFi.localIP());
  } else {
    missed_tx++;
    Serial.print("[ERR] Failed to connect to Wi-Fi. Going to sleep now.");
    Serial.flush();
    esp_sleep_enable_timer_wakeup(sampling_period * 1000);
    esp_deep_sleep_start();
  }
}


// ~~ CoAP ~~
void coapInit(){
  if ( coap.start() ) coap.response(coapResponse);
  else Serial.println("[ERR] Failed to initialize CoAP protocol.");
}

void sendCoapData(String sensor_id, String sensor_position) {
  Serial.println("[LOG] CoAP session starting.");
  uint16_t ldr_value = analogRead(ldr_pin);
  if (!isnan(ldr_value)) {
    float normalized_ldr_value = custom_normalization(ldr_value, 0, 4095, 0, 100);
    
    char ldr_str[10];
    snprintf(ldr_str, sizeof(ldr_str), "%.2f", normalized_ldr_value);

    String sensor_data = "sensor_id=" + sensor_id + "&location=" + sensor_position + "&data=" + ldr_str;
    Serial.println("[LOG] Sending data: " + sensor_data);

    uint8_t tokenLen = 4;
    uint8_t token[tokenLen];
    esp_fill_random(token, tokenLen);
    uint16_t messageID = (uint16_t) esp_random();
    time_coap_send_start = millis();

    coap.send(COAP_SERVER, COAP_PORT, COAP_URL.c_str(), COAP_CON, COAP_PUT, token, tokenLen, 
          (uint8_t*) sensor_data.c_str(), sensor_data.length(), COAP_TEXT_PLAIN, messageID);
    
    unsigned long coap_start_time = millis();
    while( millis() - coap_start_time < COAP_TIMEOUT ) coap.loop();

    if ( coap_received ) {
      coap_received = 0;
      Serial.println("[LOG] CoAP packet successfully delivered.");
    } else {
      Serial.println("[ERR] CoAP packet delivery failed. Sending data to InfluxDB.");
      sendToDB("ldrValue", "ldr", normalized_ldr_value);
    }
    Serial.println("[LOG] CoAP session terminated.");
  } else {
    Serial.println("[ERR] Failed to read LDR");
  }
}

void coapResponse(CoapPacket &packet, IPAddress ip, int port) {
  time_coap_send_stop = millis();
  char response[packet.payloadlen + 1];
  memcpy(response, packet.payload, packet.payloadlen);
  response[packet.payloadlen] = '\0';

  Serial.print("[LOG] Response from data proxy: ");
  Serial.println(response);

  if(strcmp(response, "OK") == 0) coap_received = 1;
  else coap_received = 0;
}


// ~~ InfluxDB ~~
bool sendToDB(String measurement, String field, float value) {
  InfluxDBClient client(DB_URL, DB_ORG, DB_BUCKET, DB_TOKEN);
  Point p(measurement);
  p.clearTags();
  p.clearFields();
  p.addTag("sensor", LDR_num);
  p.addField(field, value);

  if ( !client.writePoint(p) ) {
    missed_tx++;
    Serial.print("[ERR] InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
    return false;
  } else{
    Serial.println("[LOG] "+ measurement +" stored in InfluxDB");
    return true;
  }
    
}

void storeLatAndMiss(unsigned long time_start, unsigned long time_stop) {
  unsigned long latency = time_stop - time_start;
  Serial.print("[LOG] CoAP message latency: ");
  Serial.print(latency);
  Serial.println("ms.");
  if ( latency < COAP_TIMEOUT ) {
    Serial.print("[LOG] Latency step: ");
    Serial.println(latency_len);
    latency_accum += latency;
    latency_len++;
    unsigned int latency_window = 30 * 60 * 1000 / sampling_period;  // store latency every 30mins.
    if ( latency_len >= latency_window ) {
      Serial.print("[LOG] Sending mean latency ");
      Serial.print(float(latency_accum) / float(latency_len));
      Serial.print("ms of the last ");
      Serial.print(latency_window);
      Serial.println(" CoAP messages to DB.");
      bool sent = sendToDB("meanLat", "mean_lat", float(latency_accum) / float(latency_len));
      if ( sent ){
        latency_len = 0;
        latency_accum = 0;
        
        Serial.print("[LOG] Sending missings ");
        Serial.println(missed_tx);
        sendToDB("miss", "miss", missed_tx);
        missed_tx = 0;
      } else {
        missed_tx++;
      }
    }
  }
}


// ~~ MQTT ~~
void mqtt_reconnect() {
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setKeepAlive(60).setSocketTimeout(60);
  mqtt.setCallback(mqtt_callback);
  Serial.println("[LOG] MQTT session starting.");
  unsigned long mqtt_start_time = millis();
  while ( !mqtt.connected() && (millis() - mqtt_start_time) < MQTT_TIMEOUT ) {
    Serial.print("[LOG] Attempting MQTT connection... ");
    if ( mqtt.connect("LDR2", MQTT_USER, MQTT_PASSWORD) ) {
      Serial.print("Connected to ");
      Serial.println(MQTT_SERVER);
      if ( mqtt.subscribe(SAMPLING_PERIOD_TOPIC) && mqtt.subscribe(POSITION_TOPIC) ) {
        Serial.println("[LOG] Subscription successful.");
      }
      else {
        Serial.println("[ERR] Subscription failed.");
      }
    } else {
      Serial.print("[ERR] Failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(", try again in 5 seconds");
      delay(5000);
    }
  }

  unsigned long mqtt_listen = millis();
  while ( millis() - mqtt_listen < (MQTT_TIMEOUT / 2) ) {
    mqtt.loop();
  }
  Serial.println("[LOG] MQTT session terminated.");

  esp_sleep_enable_timer_wakeup(sampling_period * 1000);
  Serial.println("[LOG] Setup ESP32-C6 to sleep every "+String(sampling_period / 1000)+ "s");
}

void mqtt_callback(char *topic, byte *payload, unsigned int length) {
  payload[length] = '\0';
  String message = String((char *)payload);

  if (String(topic) == SAMPLING_PERIOD_TOPIC) {
    int new_sampling_period = message.toInt() * 1000;
    if ( new_sampling_period > 1000 ) {
      if ( new_sampling_period != sampling_period ) {
        sampling_period = new_sampling_period;
        Serial.print("[LOG] New sampling period detected: ");
        Serial.print(sampling_period / 1000);
        Serial.println("s.");
      }
    } else
      Serial.println("[ERR] Sampling period must > 1s.");
  } else if (String(topic) == POSITION_TOPIC) {
    String new_position = message;
    if (new_position != String(position)) {
      strncpy(position, new_position.c_str(), sizeof(position) - 1);
      position[sizeof(position) - 1] = '\0'; // Null-terminate
      Serial.println("[LOG] New position detected: " + String(position));
    }
  }
}

void deepSleep(){
  Serial.print("[LOG] Entering deep sleep for ");
  Serial.print(sampling_period / 1000);
  Serial.println("s.");
  Serial.flush();
  delay(1000);
  esp_deep_sleep_start();
}
  

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("==============================================");

  // GPIO pins initialization
  pinMode(ldr_pin, INPUT);

  // WiFi initialization
  wiFiInit();
  // CoAP initialization
  coapInit();
  // MQTT initialization and loop
  mqtt_reconnect();

  // Send initial data
  sendCoapData(LDR_num, String(position));
  storeLatAndMiss(time_coap_send_start, time_coap_send_stop);
  
    

  deepSleep();
}

void loop() {
  // Nothing to do here; execution resumes in `setup()` after deep sleep.
}

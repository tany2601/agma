#include <Arduino.h>
#include <Wire.h>  // Include the Wire library for I2C communication
#include <LiquidCrystal_I2C.h>  // Include the LiquidCrystal_I2C library
#if defined(ESP32)
  #include <WiFi.h>
#elif defined(ESP8266)
  #include <ESP8266WiFi.h>
#endif
#include <Firebase_ESP_Client.h>
#include <time.h>
#include "sntp.h"

//Provide the token generation process info.
#include "addons/TokenHelper.h"
//Provide the RTDB payload printing info and other helper functions.
#include "addons/RTDBHelper.h"

// Insert your network credentials
#define WIFI_SSID "Tany Wifi-tp-link"
#define WIFI_PASSWORD "Tany@2608MS"

// Insert Firebase project API Key
#define API_KEY "AIzaSyD9b4P5-XEbP1lfw4oRGMxQKjwAPyBD81c"

// Insert RTDB URLefine the RTDB URL */
#define DATABASE_URL "https://fir-1ae2b-default-rtdb.firebaseio.com/" 

#define THERMISTOR_PIN 32
#define WATER_SENSOR_PIN 34
#define VIBRATION_SENSOR_PIN 33

const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";

//Define Firebase Data object
FirebaseData fbdo;

FirebaseAuth auth;
FirebaseConfig config;

FirebaseJson json;
FirebaseJson json2;

bool signupOK = false;

// LCD configuration
#define LCD_ADDRESS 0x27  // I2C address of your LCD display
#define LCD_COLUMNS 16    // Number of columns in your LCD display
#define LCD_ROWS 2        // Number of rows in your LCD display

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLUMNS, LCD_ROWS);  // Initialize the LCD object

void setup(){
  Serial.begin(115200);

  lcd.init();  // Initialize the LCD display
  lcd.backlight();  // Turn on the backlight

  pinMode(WATER_SENSOR_PIN, INPUT);
  pinMode(VIBRATION_SENSOR_PIN, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(300);
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  /* Assign the api key (required) */
  config.api_key = API_KEY;

  /* Assign the RTDB URL (required) */
  config.database_url = DATABASE_URL;

  /* Sign up */
  if (Firebase.signUp(&config, &auth, "", "")){
    Serial.println("ok");
    signupOK = true;
  }
  else{
    Serial.printf("%s\n", config.signer.signupError.message.c_str());
  }

  /* Assign the callback function for the long running token generation task */
  config.token_status_callback = tokenStatusCallback; //see addons/TokenHelper.h

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  sntp_set_time_sync_notification_cb(NULL); // Disable time adjustment callback
  sntp_servermode_dhcp(1); // Enable SNTP server mode
  configTime(19800, 0, ntpServer1, ntpServer2); // Start NTP time synchronization
}

String getFormattedLocalTime()
{
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
    Serial.println("No time available (yet)");
    return "000000000000"; // Return a default value if time is not available
  }

  char buffer[15]; 
  sprintf(buffer, "%04d%02d%02d%02d%02d%02d", 
          timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
          timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  return String(buffer);
}

void pushDataToFirebase() {

  int button = 0;
 
  String username;
  String machine;

  if (button == 1) {
    username = "lohith";
    machine = "machine1";
  } else {
    username = "lohith";
    machine = "machine2";
  }

  int rawValue = analogRead(THERMISTOR_PIN);
  float resistance = (4095.0 / rawValue) - 1.0;
  resistance = 10000.0 / resistance;
  float temperature = 1.0 / ((log(resistance / 10000.0) / 3950.0) + (1.0 / 298.15)) - 273.15;
  if (temperature > 33) {
    updateLCD("High Temperature");
    delay(1000);
    lcd.clear();
    Serial.println("Temperature highhhhhhhhhhhhhhh");
  }
 
  String formattedTime = getFormattedLocalTime();

  String path = "/" + username + "/" + machine + "/temperature_value";
  json.clear();
  json.add("id", formattedTime);
  json.add("value", temperature);
  if (Firebase.RTDB.pushJSON(&fbdo, path, &json)) {
    Serial.println("Temperature data pushed to Firebase");
  } else {
    Serial.println("Error pushing temperature data to Firebase");
    Serial.println(fbdo.errorReason());
  }

  String path1 = "/" + username + "/" + machine + "/Vibration";
  int vibrationLevel = digitalRead(VIBRATION_SENSOR_PIN);
  json.clear();
  json.add("id", formattedTime);
  json.add("value", vibrationLevel);
  if (Firebase.RTDB.pushJSON(&fbdo, path1, &json)) {
    Serial.println("Vibration data pushed to Firebase");
  } else {
    Serial.println("Error pushing vibration data to Firebase");
    Serial.println(fbdo.errorReason());
  }
  
  String path2 = "/" + username + "/" + machine + "/Water_level";
  int waterLevel = digitalRead(WATER_SENSOR_PIN);
  json.clear();
  json.add("id", formattedTime);
  json.add("value", waterLevel);
  if (Firebase.RTDB.pushJSON(&fbdo, path2, &json)) {
    Serial.println("Water level data pushed to Firebase");
  } else {
    Serial.println("Error pushing water level data to Firebase");
    Serial.println(fbdo.errorReason());
  }
}

void updateLCD(const String& message) {
  lcd.clear();               
  lcd.setCursor(0, 0);      
  lcd.print(message);        
}

void loop() {
  static unsigned long lastPushTime = 0;
  const unsigned long pushInterval = 5000;

  unsigned long currentMillis = millis();
  if (currentMillis - lastPushTime >= pushInterval) {
    pushDataToFirebase();
    lastPushTime = currentMillis;
  }

 
  
  delay(100); 
}
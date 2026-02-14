#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// -------- PIN CONFIG --------
const int flexPins[5] = {20, 21, 22, 23, 51};  // adjust if needed

// -------- SETTINGS --------
const unsigned long SAMPLE_INTERVAL_MS = 30;     // every 10 ms
const unsigned long RECORD_DURATION_MS = 3000;   // 3 seconds
const unsigned long BREAK_DURATION_MS  = 2000;   // 5 seconds
const int TOTAL_LOOPS = 5;

// -------- DATA STORAGE --------
String csvData = "id,label,flex1,flex2,flex3,flex4,flex5,accX,accY,accZ,gyroX,gyroY,gyroZ\n";

String label = "";
unsigned long sampleId = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  // -------- I2C SETUP --------
  Wire.begin(7, 8);   // SDA = 7, SCL = 8 (ESP32 supported, Mega ignores custom pins)
  Wire.setClock(400000);

  // -------- MPU INIT --------
  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection failed!");
    while (1);
  }

  Serial.println("MPU6050 connected.");

  // -------- GET LABEL --------
  Serial.println("Enter LABEL (word name), then press ENTER:");
  while (label.length() == 0) {
    if (Serial.available()) {
      label = Serial.readStringUntil('\n');
      label.trim();
    }
  }

  Serial.print("Recording label: ");
  Serial.println(label);
}

void loop() {

  for (int loopCount = 1; loopCount <= TOTAL_LOOPS; loopCount++) {

    // -------- COUNTDOWN --------
    Serial.print("Loop ");
    Serial.print(loopCount);
    Serial.println(" starting in:");

    for (int i = 5; i > 0; i--) {
      Serial.println(i);
      delay(1000);
    }

    Serial.println("Recording...");

    unsigned long startTime = millis();
    unsigned long lastSampleTime = 0;

    while (millis() - startTime < RECORD_DURATION_MS) {
      unsigned long now = millis();

      if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
        lastSampleTime = now;

        // -------- READ FLEX --------
        int flex[5];
        for (int i = 0; i < 5; i++) {
          flex[i] = analogRead(flexPins[i]);
        }

        // -------- READ MPU --------
        int16_t ax, ay, az, gx, gy, gz;
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

        // -------- BUILD CSV ROW --------
        csvData += String(sampleId) + ",";
        csvData += label + ",";

        for (int i = 0; i < 5; i++) {
          csvData += String(flex[i]) + ",";
        }

        csvData += String(ax) + ",";
        csvData += String(ay) + ",";
        csvData += String(az) + ",";
        csvData += String(gx) + ",";
        csvData += String(gy) + ",";
        csvData += String(gz) + "\n";

        sampleId++;
      }
    }

    Serial.println("Recording complete.");
    delay(BREAK_DURATION_MS);
  }

  // -------- PRINT FINAL CSV --------
  Serial.println("===== CSV DATA START =====");
  Serial.println(csvData);
  Serial.println("===== CSV DATA END =====");

  Serial.println("Done. Program stopped.");
  while (1);
}

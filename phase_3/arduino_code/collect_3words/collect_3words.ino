#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

// Your pins
const int flexPins[5] = {51, 23, 22, 21, 20};

// Sampling
const int SAMPLE_HZ = 50;
const uint32_t DT_MS = 1000 / SAMPLE_HZ;

bool recording = false;
int currentLabel = -1;
uint32_t lastSample = 0;

void setup() {
  Serial.begin(115200);
  delay(500);

  Wire.begin(7, 8);
  if (!mpu.begin()) {
    Serial.println("ERR: MPU not found");
    while (1) delay(100);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);

  Serial.println("READY");
  Serial.println("Send: START <label>  (0/1/2), or STOP");
  Serial.println("CSV: t_ms,label,f1,f2,f3,f4,f5,ax,ay,az,gx,gy,gz");
}

void handleSerial() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.startsWith("START")) {
    currentLabel = line.substring(5).toInt();
    recording = true;
    Serial.print("OK START "); Serial.println(currentLabel);
  } else if (line == "STOP") {
    recording = false;
    Serial.println("OK STOP");
  }
}

void loop() {
  handleSerial();
  if (!recording) return;

  uint32_t now = millis();
  if (now - lastSample < DT_MS) return;
  lastSample = now;

  int f[5];
  for (int i = 0; i < 5; i++) f[i] = analogRead(flexPins[i]);

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  Serial.print(now); Serial.print(",");
  Serial.print(currentLabel); Serial.print(",");

  Serial.print(f[0]); Serial.print(",");
  Serial.print(f[1]); Serial.print(",");
  Serial.print(f[2]); Serial.print(",");
  Serial.print(f[3]); Serial.print(",");
  Serial.print(f[4]); Serial.print(",");

  Serial.print(a.acceleration.x); Serial.print(",");
  Serial.print(a.acceleration.y); Serial.print(",");
  Serial.print(a.acceleration.z); Serial.print(",");

  Serial.print(g.gyro.x); Serial.print(",");
  Serial.print(g.gyro.y); Serial.print(",");
  Serial.println(g.gyro.z);
}
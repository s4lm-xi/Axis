#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(7, 8);  

  Serial.println("Looking for MPU6500...");

  if (!mpu.begin()) {
    Serial.println("MPU not found! Check wiring.");
    while (1);
  }

  Serial.println("MPU6500 connected!");

  // Basic settings
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Gyro (rad/s)
  Serial.print("GX: "); Serial.print(g.gyro.x);
  Serial.print(" | GY: "); Serial.print(g.gyro.y);
  Serial.print(" | GZ: "); Serial.print(g.gyro.z);

  // Accel (m/s^2)
  Serial.print(" || AX: "); Serial.print(a.acceleration.x);
  Serial.print(" | AY: "); Serial.print(a.acceleration.y);
  Serial.print(" | AZ: "); Serial.print(a.acceleration.z);

  // Temperature (°C)
  Serial.print(" || T: "); Serial.println(temp.temperature);

  delay(200);
}
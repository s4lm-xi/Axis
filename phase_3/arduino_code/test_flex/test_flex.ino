// FireBeetle 2 ESP32-P4 (ADC pins)
// Good set for 5 flex sensors: 51, 23, 22, 21, 20

const int flexPins[5] = {51, 23, 22, 21, 20};

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("5x Flex Sensor Test Started (GPIO 51,23,22,21,20)");

  // Optional (usually default is 12-bit anyway):
  // analogReadResolution(12);  // 0..4095
}

void loop() {
  int v[5];
  for (int i = 0; i < 5; i++) {
    v[i] = analogRead(flexPins[i]);
  }

  Serial.print("F51: "); Serial.print(v[0]);
  Serial.print(" | F23: "); Serial.print(v[1]);
  Serial.print(" | F22: "); Serial.print(v[2]);
  Serial.print(" | F21: "); Serial.print(v[3]);
  Serial.print(" | F20: "); Serial.println(v[4]);

  delay(200);
}

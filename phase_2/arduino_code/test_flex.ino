const int flexPin = A5;

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("Flex Sensor Test Started...");
}

void loop() {
  int flexValue = analogRead(flexPin);

  Serial.print("Flex Reading: ");
  Serial.println(flexValue);

  delay(200); // slow enough to watch, fast enough to see change
}

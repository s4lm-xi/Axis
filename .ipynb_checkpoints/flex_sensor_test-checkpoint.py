import RPi.GPIO as GPIO
import time

sensors = [4, 17, 27, 22, 23]
sensor_names = {4: "Sensor 1", 17: "Sensor 2", 27: "Sensor 3", 22: "Sensor 4", 23: "Sensor 5"}

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensors, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
	while True:
		for sensor in sensors:
			print(GPIO.input(sensor))
			if GPIO.input(sensor) == GPIO.HIGH:
				print(f"{sensor_names[sensor]} is not bent")
			else:
				print(f"{sensor_names[sensor]} is bent")
				
		print("\n")
				
		time.sleep(0.5)
		
except KeyboardInterrupt:
	print("Stopping program")
	
finally:
	GPIO.cleanup()									

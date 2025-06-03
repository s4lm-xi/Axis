import RPi.GPIO as GPIO
import time
import mpu6050
import json

# Sensor setup
flex_sensors = [4, 17, 27, 22, 23]
sensor_names = {4: "Sensor 1", 17: "Sensor 2", 27: "Sensor 3", 22: "Sensor 4", 23: "Sensor 5"}
GPIO.setmode(GPIO.BCM)
GPIO.setup(flex_sensors, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# MPU6050 setup
mpu6050_sensor = mpu6050.mpu6050(0x68)

# Global variables
recording = False
data_records = []
label = ""
max_duration = 30  # Total recording time in seconds
window_duration = 3  # Duration of each recording window (in seconds)

# Button setup
button_pin = 26  # GPIO pin for button
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def read_sensor_data():
    """Read the flex and gyro sensor data."""
    accelerometer_data = mpu6050_sensor.get_accel_data()
    gyroscope_data = mpu6050_sensor.get_gyro_data()
    
    flex_data = [GPIO.input(sensor) for sensor in flex_sensors]
    
    return flex_data, accelerometer_data, gyroscope_data

def record_action():
    """Record the sensor data for a specified duration in 3-second windows."""
    global recording, data_records

    start_time = time.time()
    end_time = start_time + max_duration
    current_time = time.time()

    print(f"Recording started. You have {max_duration} seconds.")

    # Record in 3-second windows
    while recording and current_time < end_time:
        window_start_time = time.time()
        print(f"Window starts at {window_start_time - start_time:.2f} seconds.")
        
        window_data = []
        # Record for 3 seconds
        while time.time() - window_start_time < window_duration:
            flex_data, accel_data, gyro_data = read_sensor_data()
            timestamp = time.time() - start_time
            window_data.append({
                "timestamp": timestamp,
                "flex_data": flex_data,
                "accelerometer": accel_data,
                "gyroscope": gyro_data
            })
            time.sleep(0.1)  # Wait for next sample

        # Store the 3-second window data
        data_records.append(window_data)
        print(f"Window ends at {time.time() - start_time:.2f} seconds.")
        
        # Update the current time
        current_time = time.time()

def button_callback(channel):
    """Callback function for button press to start/stop recording."""
    global recording, data_records, label

    if recording:
        recording = False
        print("Finished recording.")
    else:
        label = input("Enter the label for this action: ")
        data_records = []
        print("Started recording...")
        recording = True
        record_action()

# Setup button event detection
GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=button_callback, bouncetime=300)

try:
    while True:
        if not recording:
            time.sleep(0.1)
            continue

        # Once 30 seconds have passed, stop the recording
        if len(data_records) >= (max_duration // window_duration):
            recording = False
            print("Finished recording.")
            break

except KeyboardInterrupt:
    print("Stopping program.")

finally:
    # Save data to JSON
    if data_records and label:
        dataset = {"label": label, "data": data_records}
        with open(f"{label}.json", "w") as json_file:
            json.dump(dataset, json_file)
        print(f"Data saved to {label}.json")

    GPIO.cleanup()
